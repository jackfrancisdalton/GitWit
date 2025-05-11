from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass
import typer
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

from gitwit.utils.console_singleton import ConsoleSingleton
from gitwit.utils.date_utils import convert_to_datetime
from gitwit.utils.fetch_git_log_entries import fetch_git_log_entries_of_added_files
from gitwit.utils.git_helpers import fetch_file_paths_tracked_by_git

console = ConsoleSingleton.get_console()


@dataclass
class LatestFileExample:
    path: str
    created_at: datetime
    author: str


def command(
    search_term: str = typer.Argument(
        ..., help="Substring to match in file names (e.g. .py, controller.py)"
    ),
    directories: Optional[List[str]] = typer.Option(
        None, "--dir", "-d", help="Filter examples to these directory paths"
    ),
    authors: Optional[List[str]] = typer.Option(
        None, "--author", "-a", help="Filter examples to commits by these authors"
    ),
    limit: int = typer.Option(
        10, "--limit", "-n", help="Maximum number of examples to show"
    ),
):
    """
    Find the latest examples of files matching a search term in the git history.
    """

    examples = _find_latest_examples(search_term, directories, authors, limit)

    if examples:
        table = _generate_table(search_term, examples)
        console.print(table)
    else:
        console.print(f"[yellow]No examples found for prefix '{search_term}'.[/yellow]")


def _find_latest_examples(
    search_term: str,
    directories: Optional[List[str]],
    authors: Optional[List[str]],
    limit: int,
) -> List[LatestFileExample]:
    # 1) Generate a list of all filees that match search and directory requiremensts and exist in git history
    matched_files = fetch_file_paths_tracked_by_git(search_term, directories)

    # 2) If no files match, fast return empty list
    if not matched_files:
        return []

    # 3) Populate data for respective files based on git data, and filter by author
    examples = _hydrate_examples_and_filter_based_on_git_data(matched_files, authors)

    # 4) sort & limit
    examples.sort(key=lambda x: x.created_at, reverse=True)
    return examples[:limit]


def _hydrate_examples_and_filter_based_on_git_data(
    target_files: List[str], authors: Optional[List[str]]
) -> List[LatestFileExample]:
    # Fetch all git commits that have added files and parse into blocks
    git_log_blocks = fetch_git_log_entries_of_added_files()

    latest_examples_of: List[LatestFileExample] = []
    seen_files: set[str] = set()

    # Loop over blocks, extract commit information, and filter by author if provided
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total} commits"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning git history", total=len(git_log_blocks))

        for block in git_log_blocks:
            author = block.author
            created_at_iso = block.created_at_iso

            if authors and not any(a.lower() in author.lower() for a in authors):
                progress.advance(task)
                continue

            for path in block.files:
                path = path.strip()

                if not path or path not in target_files or path in seen_files:
                    continue

                latest_examples_of.append(
                    LatestFileExample(
                        path=path,
                        created_at=convert_to_datetime(created_at_iso),
                        author=author,
                    )
                )
                seen_files.add(path)

            progress.advance(task)

            # If we've seen as many files as we need, break early
            if len(seen_files) >= len(target_files):
                break

    return latest_examples_of


def _generate_table(search_term: str, examples: List[LatestFileExample]) -> Table:
    table = Table(title=f"Latest examples for '{search_term}'")
    table.add_column("File Path", style="cyan")
    table.add_column("Created At", style="green")
    table.add_column("Author", style="magenta")

    for example in examples:
        table.add_row(
            example.path,
            example.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            example.author,
        )

    return table
