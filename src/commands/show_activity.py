"""Show activity (commits) between two dates."""
from typing import Sequence
from git import Commit
from rich.console import Console
from rich.table import Table
import typer
from src.utils.fetch_commits import fetch_commits_in_date_range
from src.utils.date_utils import convert_to_datetime

# TODO: create a singleton console with helper functions for easier testing and code reading
console = Console()

def command(
    since: str = typer.Option(...,  help="Start date in YYYY-MM-DD"),
    until: str = typer.Option(..., help="End date in YYYY-MM-DD")
):
    """
    Show activity (commits) between two dates.
    """
    try:
        since_date = convert_to_datetime(since)
        until_date = convert_to_datetime(until)
    except ValueError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(code=1)

    commits = fetch_commits_in_date_range(since_date, until_date)

    if not commits:
        console.print("[yellow]No commits found in this date range.[/yellow]")
        raise typer.Exit()

    console.print(_generate_table(since, until, commits))
    console.print(f"\n[bold green]Summary:[/bold green] {len(commits)} commits.")

def _generate_table(since: str, until: str, commits: Sequence[Commit]) -> Table:
    """
    Generate a table for display in the CLI.   
    """
    table = Table(title=f"Commits from {since} to {until}")
    table.add_column("Date", style="cyan")
    table.add_column("Author", style="magenta")
    table.add_column("Message", style="green")

    for commit in commits:
        message = commit.message
        if isinstance(message, bytes):
            message = message.decode("utf-8")

        table.add_row(
            str(commit.committed_datetime.date()),
            commit.author.name,
            str(message).strip()
        )

    return table