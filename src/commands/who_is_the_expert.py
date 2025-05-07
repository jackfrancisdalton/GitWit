from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List
import typer
from git import Repo
from rich.table import Table
from models.blame_line import BlameLine
from utils.console_singleton import ConsoleSingleton
from utils.git_helpers import fetch_file_gitblame

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
    num_results: int = typer.Option(5, help="Number of top authors to display")
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

    authors = _compute_author_activity(blame_entries)
    table = _generate_table(target, authors, num_results)
    console.print(table)

# TODO: this need to be improved to ignore untracked directories
def _gather_blame_entries(repo: Repo, target: Path) -> List[BlameLine]:
    """
    Return a combined list of blame entries for a file or all files under a directory.
    """
    entries = []

    if target.is_dir(): # if directory was passed
        files_in_target_dir = [file for file in target.rglob("*") if file.is_file()]
        for file in files_in_target_dir:
            try:
                entries.extend(fetch_file_gitblame(repo, file))
            except Exception:
                continue
    else: # If file was passed
        try:
            entries = fetch_file_gitblame(repo, target)
        except Exception:
            pass

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


def _generate_table(
    target: Path,
    authors: list[AuthorActivityData],
    num_results: int
) -> Table:
    """
    Generate a Rich Table summarizing author activity.
    """
    total_lines = sum(a.line_count for a in authors)
    table = Table(title=f"Blame Summary for {target}")
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
