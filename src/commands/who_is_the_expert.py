from collections import Counter
from pathlib import Path
from rich.console import Console
import typer
from git import Repo
from rich.table import Table

console = Console()

def command(
    file: str = typer.Option(..., help="Path to the file to analyze")
):
    """
    Determine who the expert is for a given file based on who has comitted the most and who comitted latest
    """
    number_of_experts_to_print = 5

    repo = Repo(".", search_parent_directories=True)
    file_path = Path(file)

    if not file_path.exists():
        console.print(f"[red]Error:[/red] File '{file}' does not exist.")
        raise typer.Exit(code=1)

    try:
        blame_info = repo.git.blame("--line-porcelain", str(file_path)).splitlines()
    except Exception as e:
        console.print(f"[red]Error running git blame:[/red] {str(e)}")
        raise typer.Exit(code=1)

    authors = _generate_author_list(blame_info)

    if not authors:
        console.print("[yellow]No blame data found for this file.[/yellow]")
        raise typer.Exit()

    author_counts = Counter(authors)
    total_lines = sum(author_counts.values())
    table = _generate_table(file, author_counts, number_of_experts_to_print, total_lines)

    console.print(table)
    console.print(f"\n[bold green]Total lines analyzed:[/bold green] {total_lines}")

def _generate_author_list(blame_info: str) -> list:
    """
    Generate a list of authors from the blame information.
    """
    authors = []

    for line in blame_info:
        if line.startswith("author "):
            author = line[len("author "):]
            authors.append(author)

    return authors

def _generate_table(file: str, author_counts: Counter, number_of_authors: int, total_lines: int) -> Table:
    """
    Generate a table for display in the CLI.   
    """
    table = Table(title=f"Blame Summary for {file}")
    table.add_column("Author", style="magenta")
    table.add_column("Lines", justify="right", style="cyan")
    table.add_column("Ownership %", justify="right", style="green")
    table.add_column("Last Touched", justify="right", style="cyan")

    for author, count in author_counts.most_common(number_of_authors):
        table.add_row(
            author, 
            str(count), 
            f"{((count / total_lines) * 100):.1f}%", 
            'TODO'
        )

    return table