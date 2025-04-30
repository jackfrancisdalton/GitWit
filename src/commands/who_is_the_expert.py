from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import typer
from git import List, Repo
from rich.table import Table
from src.utils.console_singleton import ConsoleSingleton
from src.utils.fetch_git_blame import fetch_file_gitblame

@dataclass
class AuthorActivityData:
    author: str
    line_count: int
    last_commit_date: datetime
    last_commit_message: str

console = ConsoleSingleton.get_console()

def command(
    file: str = typer.Option(..., help="Path to the file to analyze"),
    num_results: int = typer.Option(5, help="Number of top experts to display")
):
    """
    Determine who the expert is for a given file based on who has committed the most and who committed latest
    """

    file_path = Path(file)
    authors_data = _compute_author_activity_data(file_path)

    if not authors_data:
        console.print("[yellow]No blame data found for this file.[/yellow]")
        raise typer.Exit()
    
    table = _generate_table(file, authors_data, num_results)

    console.print(table)


def _compute_author_activity_data(file_path: Path) -> List[AuthorActivityData]:
    """
    Generate a dict of authors mapping to:
      - count: how many lines they’re blamed for
      - last_touched: the most recent commit datetime of any of their lines
      - last_message: the commit message for that most recent line
    """
    repo = Repo(".", search_parent_directories=True)

    if not file_path.exists():
        console.print(f"[red]Error:[/red] File '{file_path}' does not exist.")
        raise typer.Exit(code=1)

    try:
        blame_list = fetch_file_gitblame(repo, file_path)
    except Exception as e:
        console.print(f"[red]Error running git blame:[/red] {e}")
        raise typer.Exit(code=1)

    authors_data = {}
    
    for line in blame_list:
        author = line.author
        commit_date = datetime.fromtimestamp(line.author_time)
        
        if author not in authors_data:
            authors_data[author] = AuthorActivityData(
                author=author,
                line_count=0,
                last_commit_date=commit_date,
                last_commit_message=line.summary,
            )

        authors_data[author].line_count += line.num_lines

        if commit_date > authors_data[author].last_commit_date:
            authors_data[author].last_commit_date = commit_date
            authors_data[author].last_commit_message = line.summary

    return list(authors_data.values())


def _generate_table(
    file: str,
    author_data: List[AuthorActivityData],
    num_results: int
) -> Table:
    """
    Generate a table for display in the CLI consuming the authorGitData dict.
    Each author entry in authorGitData is expected to have:
      - count: int
      - last_touched: datetime or None
    """
    # Calculate total lines across all authors
    total_lines = sum(data.line_count for data in author_data)

    # Create the table
    table = Table(title=f"Blame Summary for {file}")
    table.add_column("Author", style="magenta")
    table.add_column("Lines", justify="right", style="cyan")
    table.add_column("Ownership %", justify="right", style="green")
    table.add_column("Last Touched", justify="right", style="cyan")
    table.add_column("Last Commit Message", style="yellow")

    # Sort by line count descending and take top N
    top_authors = sorted(
        author_data,
        key=lambda data: data.line_count,
        reverse=True
    )[:num_results]

    for data in top_authors:
        ownership = f"{(data.line_count / total_lines * 100):.1f}%" if total_lines else "0.0%"

        last_touched = data.last_commit_date
        last_str = last_touched.isoformat(sep=" ") if isinstance(last_touched, datetime) else "N/A"

        table.add_row(
            data.author,
            str(data.line_count),
            ownership,
            last_str,
            data.last_commit_message
        )

    return table
