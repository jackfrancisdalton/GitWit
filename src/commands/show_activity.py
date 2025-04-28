"""Show activity (commits) between two dates."""
from datetime import datetime
from typing import Sequence
from git import Commit, Repo
from rich.console import Console
from rich.table import Table
import typer

console = Console()

def command(
    since: str = typer.Option(..., help="Start date in YYYY-MM-DD"),
    until: str = typer.Option(..., help="End date in YYYY-MM-DD")
):
    """
    Show activity (commits) between two dates.
    """
    _validate_date_format(since, until)
    commits = _fetch_commits(since, until)

    if not commits:
        console.print("[yellow]No commits found in this date range.[/yellow]")
        raise typer.Exit()

    table = _generate_activity_table(since, until, commits)
    _print_output(table, commits)


def _validate_date_format(since: str, until: str) -> None:
    """
    Validate date format YYYY-MM-DD.
    """
    try:
        _ = datetime.strptime(since, "%Y-%m-%d")
        _ = datetime.strptime(until, "%Y-%m-%d")
    except ValueError:
        console.print("[red]Error: Dates must be in YYYY-MM-DD format.[/red]")
        raise typer.Exit(code=1)
    

def _generate_activity_table(since: str, until: str, commits: Sequence[Commit]) -> Table:
    """
    Generate a table of commits.   
    """
    table = Table(title=f"Commits from {since} to {until}")
    table.add_column("Date", style="cyan")
    table.add_column("Author", style="magenta")
    table.add_column("Message", style="green")

    for commit in commits:
        table.add_row(
            str(commit.committed_datetime.date()),
            commit.author.name,
            commit.message.strip() # TODO: resolve byte|string handling 
        )

    return table

def _fetch_commits(since: str, until: str) -> Sequence[Commit]:
    """
    Fetch commits from the repository between two dates.
    """
    repo = Repo(".")
    return list(repo.iter_commits(since=since, until=until))

def _print_output(table: Table, commits) -> None:
    """
    Print the table and summary.
    """
    console.print(table)
    console.print(f"\n[bold green]Summary:[/bold green] {len(commits)} commits.")


