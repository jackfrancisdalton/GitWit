from collections import Counter
from pathlib import Path
import typer
from git import Repo
from rich.table import Table
from src.utils.console_singleton import ConsoleSingleton

# TODO Add support for a path based version of the command

console = ConsoleSingleton.get_console()

def command(
    file: str = typer.Option(..., help="Path to the file to analyze"),
    num_experts: int = typer.Option(5, help="Number of top experts to display")
):
    """
    Determine who the expert is for a given file based on who has committed the most and who committed latest
    """

    file_path = Path(file)
    authors = _generate_author_list(file_path)

    if not authors:
        console.print("[yellow]No blame data found for this file.[/yellow]")
        raise typer.Exit()

    table = _generate_table(file, authors, num_experts)

    console.print(table)

def _generate_author_list(file_path: Path) -> list:
    """
    Generate a list of authors from the blame information.
    """
    authors = []

    repo = Repo(".", search_parent_directories=True)

    if not file_path.exists():
        console.print(f"[red]Error:[/red] File '{file_path}' does not exist.")
        raise typer.Exit(code=1)

    try:
        blame_info = repo.git.blame("--line-porcelain", str(file_path)).splitlines()
    except Exception as e:
        console.print(f"[red]Error running git blame:[/red] {str(e)}")
        raise typer.Exit(code=1)

    for line in blame_info:
        if line.startswith("author "):
            author = line[len("author "):]
            authors.append(author)

    return authors

def _generate_table(
    file: str, 
    authors: list,
    num_experts: int
) -> Table:
    """
    Generate a table for display in the CLI.   
    """

    author_counts = Counter(authors)
    total_lines = sum(author_counts.values())

    table = Table(title=f"Blame Summary for {file}")
    table.add_column("Author", style="magenta")
    table.add_column("Lines", justify="right", style="cyan")
    table.add_column("Ownership %", justify="right", style="green")
    table.add_column("Last Touched", justify="right", style="cyan")

    for author, count in author_counts.most_common(num_experts):
        table.add_row(
            author, 
            str(count), 
            f"{((count / total_lines) * 100):.1f}%", 
            'TODO' # TODO: implement logic to get the last touched date
        )

    return table