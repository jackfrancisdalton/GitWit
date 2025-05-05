import os
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass
import typer
from git import Repo
from rich.table import Table
from models.git_log_entry import GitLogEntry
from utils.console_singleton import ConsoleSingleton
from utils.fetch_git_log_entries import fetch_git_log_entries
from utils.fetch_tracked_git_file_paths import fetch_tracked_git_file_paths

console = ConsoleSingleton.get_console()

@dataclass
class LatestFileExample:
    path: str
    created_at: datetime
    author: str

def command(
    search_term: str = typer.Argument(
        ..., help="Substring to match in file names (e.g. .py, controller, testcontroller.py)"
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
    Show the most recently created files whose basenames contain FILE_PREFIX.
    Optionally filter by directory paths and commit authors.
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
    limit: int
) -> List[LatestFileExample]:
    repo = Repo('.', search_parent_directories=True)

    # 1) Generate a list of all filees that match search and directory requiremensts and exist in git history
    matched_files = fetch_tracked_git_file_paths(repo, search_term, directories)

    # 2) If no files match, fast return empty list
    if not matched_files:
        return []
    
    # 3) Populate data for respective files based on git data, and filter by author if provided
    examples = _hydrate_examples_and_filter_based_on_git_data(repo, matched_files, authors)

    # 4) sort & limit
    examples.sort(key=lambda x: x.created_at, reverse=True)
    return examples[:limit]


def _hydrate_examples_and_filter_based_on_git_data(
    repo: Repo,
    target_files: List[str],
    authors: Optional[List[str]]
) -> List[LatestFileExample]:
    # Fetch all git commits that have added files and parse into blocks
    git_log_blocks = fetch_git_log_entries(repo)

    latest_examples_of: List[LatestFileExample] = []
    seen_files: set[str] = set()

    # Loop over blocks, extract commit information, and filter by author if provided
    for block in git_log_blocks:
        author = block.author
        created_at_iso = block.created_at_iso

        if authors and not any(a.lower() in author.lower() for a in authors):
            continue

        for path in block.files:
            path = path.strip()

            if not path:
                continue
            
            if path in target_files and path not in seen_files:
                latest_examples_of.append(
                    LatestFileExample(
                        path=path,
                        created_at=datetime.fromisoformat(created_at_iso),
                        author=author
                    )
                )
                seen_files.add(path)

        # If we've seen as many files as we need, break early
        if len(seen_files) == len(target_files):
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
            example.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            example.author,
        )

    return table
