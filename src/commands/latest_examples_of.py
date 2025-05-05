import os
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass
import typer
from git import Repo
from rich.table import Table
from utils.console_singleton import ConsoleSingleton

console = ConsoleSingleton.get_console()

@dataclass
class LatestFileExample:
    path: str
    created_at: datetime
    author: str

@dataclass
class GitLogBlock:
    commit_hash: str
    created_at_iso: str
    author: str
    files: List[str]


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
    matched_files = _get_file_paths_matching_conditions_from_git_history(repo, search_term, directories)

    # 2) If no files match, fast return empty list
    if not matched_files:
        return []
    
    # 3) Populate data for respective files based on git data, and filter by author if provided
    examples = _hydrate_examples_and_filter_based_on_git_data(repo, matched_files, authors)

    # 4) sort & limit
    examples.sort(key=lambda x: x.created_at, reverse=True)
    return examples[:limit]


def _get_file_paths_matching_conditions_from_git_history(repo: Repo, search_term: str, directories) -> List[str]:
    all_files = repo.git.ls_files().splitlines()
    matching_files = [f for f in all_files if search_term in os.path.basename(f)]

    if directories:
        dirs = [d.rstrip('/') + '/' for d in directories]
        matching_files = [f for f in matching_files if any(f.startswith(d) for d in dirs)]

    return matching_files


def _hydrate_examples_and_filter_based_on_git_data(
    repo: Repo,
    target_files: List[str],
    authors: Optional[List[str]]
) -> List[LatestFileExample]:
    # Fetch all git commits that have added files and parse into blocks
    raw = repo.git.log(
        '--diff-filter=A',
        '--format=%H%x00%aI%x00%an',
        '--name-only'
    )
    git_log_blocks = _convert_git_log_to_blocks(raw)

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


# TODO: move function to utils
def _convert_git_log_to_blocks(raw: str) -> List[GitLogBlock]:
    blocks: List[GitLogBlock] = []

    current_hash: Optional[str] = None
    current_iso_date: Optional[str] = None
    current_author: Optional[str] = None
    current_files: List[str] = []

    for line in raw.splitlines():
        if '\x00' in line:
            # flush the previous block if we had one
            if current_hash is not None:
                blocks.append(GitLogBlock(
                    commit_hash=current_hash,
                    created_at_iso=current_iso_date,
                    author=current_author,
                    files=current_files
                ))
            # parse new header
            commit_hash, iso_date, author = line.split('\x00')
            current_hash = commit_hash
            current_iso_date = iso_date
            current_author = author
            current_files = []
        else:
            path = line.strip()
            if path:
                current_files.append(path)

    # flush the final block
    if current_hash is not None:
        blocks.append(GitLogBlock(
            commit_hash=current_hash,
            created_at_iso=current_iso_date, 
            author=current_author,
            files=current_files
        ))

    return blocks


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
