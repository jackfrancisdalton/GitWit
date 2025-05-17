from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import typer
from git import Repo
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

from gitwit.models.blame_line import BlameLine
from gitwit.utils.console_singleton import ConsoleSingleton
from gitwit.utils.git_helpers import fetch_file_gitblame


@dataclass
class AuthorActivityData:
    author: str
    line_count: int
    last_commit_date: datetime
    last_commit_message: str


console = ConsoleSingleton.get_console()
app = typer.Typer(name="blame_expert", help="Determine file or directory experts via git blame.")


def command(
    path: str = typer.Option(..., help="Path to file or directory to analyze"),
    num_results: int = typer.Option(5, help="Number of top authors to display"),
):
    """
    Determine who the expert is for a given file or directory based on blame ownership and recency.
    """
    target = Path(path)
    repo = Repo(".", search_parent_directories=True)

    if not target.exists():
        console.print(f"[red]Error:[/red] Path '{target}' does not exist.")
        raise typer.Exit(code=1)

    try:
        blame_entries = _gather_blame_entries(repo, target)
    except Exception as e:
        console.print(f"[red]Error running git blame:[/red] {e}")
        raise typer.Exit(code=1)

    if not blame_entries:
        console.print("[yellow]No blame data found for path.[/yellow]")
        raise typer.Exit()

    authors_activity_list = _compute_author_activity(blame_entries)
    table = _generate_table(target, authors_activity_list, num_results)

    console.print(table)


# TODO: this need to be improved to ignore untracked directories
def _gather_blame_entries(repo: Repo, target: Path) -> list[BlameLine]:
    """
    Return a combined list of BlameLine entries for a file or all files under a directory,
    fetching each in parallel with a progress bar.
    """

    if target.is_dir():
        files_to_process = repo.git.ls_files(str(target)).splitlines()
    else:
        files_to_process = [str(target)]

    entries: list[BlameLine] = []

    # 2) Kick off parallel fetches and track progress
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching blame entries", total=len(files_to_process))

        # cap workers to number of files
        max_workers = min(8, len(files_to_process))
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(fetch_file_gitblame, repo, path): path for path in files_to_process
            }

            for future in as_completed(futures):
                path = futures[future]

                try:
                    result = future.result()  # List[BlameLine]
                    entries.extend(result)
                except Exception as e:
                    console.log(f"Blame failed for {path}: {e}", style="yellow")
                finally:
                    progress.advance(task)

    return entries


def _compute_author_activity(blame_list) -> list[AuthorActivityData]:
    """
    Aggregate blame entries into per-author activity data.
    """
    data = {}
    for blame in blame_list:
        author = blame.author
        commit_date = datetime.fromtimestamp(blame.author_time)

        if author not in data:
            data[author] = AuthorActivityData(
                author=author,
                line_count=0,
                last_commit_date=commit_date,
                last_commit_message=blame.summary,
            )

        data[author].line_count += blame.num_lines

        if commit_date > data[author].last_commit_date:
            data[author].last_commit_date = commit_date
            data[author].last_commit_message = blame.summary

    return list(data.values())


def _generate_table(target: Path, authors: list[AuthorActivityData], num_results: int) -> Table:
    """
    Generate a Rich Table summarizing author activity.
    """

    total_lines = sum(a.line_count for a in authors)
    table = Table(title=f"Experts for {target}, showing top {num_results} of {len(authors)}")
    table.add_column("Author", style="magenta")
    table.add_column("Lines", justify="right", style="cyan")
    table.add_column("Ownership %", justify="right", style="green")
    table.add_column("Last Touched", justify="right", style="cyan")
    table.add_column("Last Commit Message", style="yellow")

    top = sorted(authors, key=lambda a: a.line_count, reverse=True)[:num_results]

    for a in top:
        pct = f"{(a.line_count / total_lines * 100):.1f}%" if total_lines else "0.0%"
        last = a.last_commit_date.isoformat(sep=" ")
        table.add_row(a.author, str(a.line_count), pct, last, a.last_commit_message)

    return table
