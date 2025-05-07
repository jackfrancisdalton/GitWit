"""Enhanced Git activity report between two dates."""

from dataclasses import dataclass, field
from typing import List, Sequence, Dict
from git import Commit
from rich.table import Table
from collections import Counter
import typer
from datetime import datetime, timedelta, timezone
from utils.repo_helpers import fetch_commits_in_date_range, get_filtered_commits
from utils.date_utils import convert_to_datetime
from utils.console_singleton import ConsoleSingleton
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

console = ConsoleSingleton.get_console()

@dataclass
class FileStats:
    file: str
    commits: int = 0
    lines: int = 0
    authors: Counter = field(default_factory=Counter)

@dataclass
class AuthorActivityStats:
    total_commits: int
    num_authors: int
    top_contributor: str
    top_contributor_commits: int
    total_lines: int
    last_commit_date: str


def command(
    since: str = typer.Option(
        (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"), # Default to 10 days ago
        help="Start date in YYYY-MM-DD",
    ),
    until: str = typer.Option(
        datetime.now().strftime("%Y-%m-%d"), # Default to today
        help="End date in YYYY-MM-DD",
    ),
):
    since_date, until_date = _handle_date_arguments(since, until)

    commits = list(get_filtered_commits(
        since=since_date,
        until=until_date,
    ))

    if not commits:
        console.print("[yellow]No commits found in this date range.[/yellow]")
        raise typer.Exit()

    commits_in_time_range = [
        commit for commit in commits
        if since_date <= commit.committed_datetime.astimezone(timezone.utc) <= until_date
    ]
    
    file_stats = _compute_file_statistics(commits_in_time_range)
    activity_stats = _compute_author_activity_statistics(commits_in_time_range)

    file_stats_table = _generate_file_statistics_table(file_stats)
    activity_summary_table = _generate_activity_summary_table(activity_stats)

    console.print(file_stats_table)
    console.print(activity_summary_table)


def _handle_date_arguments(since: str, until: str) -> tuple[datetime, datetime]:
    try:
        since_datetime = convert_to_datetime(since)
        until_datetime = convert_to_datetime(until)
    except ValueError:
        console.print("[red]Invalid date format. Use YYYY-MM-DD.[/red]")
        raise typer.Exit(1)

    if since_datetime > until_datetime:
        console.print("[red]Start date cannot be after end date.[/red]")
        raise typer.Exit(1)

    return since_datetime, until_datetime

# ================================================================================
# Computation Functions
# ================================================================================

def _compute_file_statistics(
    commits: Sequence[Commit],
    result_limit: int = 10
) -> List[FileStats]:
    """
    Compute statistics about file activity considering date range,
    returning a sorted list of FileStats.
    """
    stats_map: Dict[str, FileStats] = {}

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing commits...", total=len(commits))
        for commit in commits:
            for fname, details in commit.stats.files.items():
                fname = str(fname)
                fs = stats_map.get(fname)
                
                if fs is None:
                    fs = FileStats(file=fname)
                    stats_map[fname] = fs

                fs.commits += 1
                fs.lines += details.get("lines", 0)
                fs.authors[commit.author.name] += 1
            progress.update(task, advance=1)

    # sort by total lines changed, descending, and trim to limit
    sorted_list = sorted(
        stats_map.values(),
        key=lambda fs: fs.lines,
        reverse=True
    )[:result_limit]

    return sorted_list



def _compute_author_activity_statistics(commits: Sequence[Commit]) -> AuthorActivityStats:
    """Filter commits and count author activity considering date range."""
    author_commit_count = Counter(c.author.name for c in commits)

    total_commits = len(commits)
    num_authors = len(author_commit_count)
    top_contributor, top_contributor_commits = ("", 0)

    if author_commit_count:
        top_contributor, top_contributor_commits = author_commit_count.most_common(1)[0]

    total_lines = sum(
        details.get("lines", 0)
        for commit in commits
        for details in commit.stats.files.values()
    )

    last_commit_date = max(
        (commit.committed_datetime.astimezone(timezone.utc) for commit in commits),
        default="N/A"
    )
    last_commit_date_str = last_commit_date.strftime("%Y-%m-%d") if last_commit_date != "N/A" else "N/A"

    return AuthorActivityStats(
        total_commits=total_commits,
        num_authors=num_authors,
        top_contributor=top_contributor or "",
        top_contributor_commits=top_contributor_commits,
        total_lines=total_lines,
        last_commit_date=last_commit_date_str,
    )



# ================================================================================
# Table Generators
# ================================================================================

def _generate_file_statistics_table(file_stats: List[FileStats]) -> Table:
    """Generate a table of file statistics."""
    table = Table(title="File Statistics")
    table.add_column("File", style="cyan")
    table.add_column("Commits", style="magenta")
    table.add_column("Lines Changed", style="green")
    table.add_column("Top Authors", style="yellow")

    for stats in file_stats:
        top_authors = ", ".join(
            f"{author} ({count})" for author, count in stats.authors.most_common(3)
        )
        table.add_row(
            stats.file,
            str(stats.commits),
            str(stats.lines),
            top_authors,
        )

    return table

def _generate_activity_summary_table(activityStats: AuthorActivityStats) -> Table:
    """Generate a summary table of commit activity."""
    table = Table(title="Commit Activity Summary")
    table.add_column("Total Commits", style="bold green")
    table.add_column("Contributors", style="bold cyan")
    table.add_column("Top Contributor", style="bold magenta")
    table.add_column("Lines Committed", style="bold blue")
    table.add_column("Last Commit Date", style="bold yellow")

    table.add_row(
        str(activityStats.total_commits),
        str(activityStats.num_authors),
        f"{activityStats.top_contributor} ({activityStats.top_contributor_commits} commits)",
        str(activityStats.total_lines),
        activityStats.last_commit_date,
    )

    return table


if __name__ == "__main__":
    typer.run(command)
