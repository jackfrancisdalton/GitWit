"""Enhanced Git activity report between two dates."""

from typing import Sequence, Dict, Any, Tuple
from git import Commit
from rich.console import Console
from rich.table import Table
from collections import defaultdict, Counter
import typer
from datetime import datetime, timedelta, timezone
from src.utils.fetch_commits import fetch_commits_in_date_range
from src.utils.date_utils import convert_to_datetime


# TODO: move to dedicated shared file in utils module
class ConsoleSingleton:
    """Singleton Console instance for consistent output formatting."""

    _console = None

    @classmethod
    def get_console(cls) -> Console:
        if cls._console is None:
            cls._console = Console()
        return cls._console


console = ConsoleSingleton.get_console()


def command(
    since: str = typer.Option(
        (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d"), # Default to 10 days ago
        help="Start date in YYYY-MM-DD",
    ),
    until: str = typer.Option(
        datetime.now(timezone.utc).strftime("%Y-%m-%d"), # Default to today
        help="End date in YYYY-MM-DD",
    ),
):
    """Main command to show detailed Git activity report."""

    since_date, until_date = _parse_dates(since, until)
    commits = fetch_commits_in_date_range(since_date, until_date)

    if not commits:
        console.print("[yellow]No commits found in this date range.[/yellow]")
        raise typer.Exit()

    _show_activity_summary(commits, since_date, until_date)


def _parse_dates(since: str, until: str):
    """Convert input dates to timezone-aware datetime objects."""
    try:
        return convert_to_datetime(since).replace(tzinfo=timezone.utc), convert_to_datetime(until).replace(tzinfo=timezone.utc)
    except ValueError as e:
        console.print(f"[red]Date Error: {str(e)}[/red]")
        raise typer.Exit(code=1)


def _show_activity_summary(commits: Sequence[Commit], since_date, until_date) -> None:
    """Display detailed summary of Git activity."""

    file_stats = _compute_file_statistics(commits, since_date, until_date)
    file_stats_table = _generate_file_statistics_table(file_stats)

    filtered_commits, author_activity = _compute_activity_summary(commits, since_date, until_date)
    activity_summary_table = _generate_activity_summary_table(author_activity, filtered_commits)

    console.print(file_stats_table)
    console.print(activity_summary_table)


def _compute_file_statistics(commits: Sequence[Commit], since_date, until_date, result_limit: int = 10) -> Dict[str, Any]:
    """Compute statistics about file activity considering date range."""
    file_stats = defaultdict(lambda: {"commits": 0, "lines": 0, "authors": Counter()})

    for commit in commits:
        commit_datetime = commit.committed_datetime.astimezone(timezone.utc)
        if since_date <= commit_datetime <= until_date:
            for file, details in commit.stats.files.items():
                file_stats[file]["commits"] += 1
                file_stats[file]["lines"] += details.get("lines", 0)
                file_stats[file]["authors"][commit.author.name] += 1

    sorted_file_stats = dict(
        sorted(file_stats.items(), key=lambda item: item[1]["lines"], reverse=True)[:result_limit]
    )

    return sorted_file_stats


def _generate_file_statistics_table(file_stats: Dict[str, Any]) -> Table:
    """Generate a table of file statistics."""
    table = Table(title="File Statistics")
    table.add_column("File", style="cyan")
    table.add_column("Commits", style="magenta")
    table.add_column("Lines Changed", style="green")
    table.add_column("Top Authors", style="yellow")

    for file, stats in file_stats.items():
        top_authors = ", ".join(
            f"{author} ({count})" for author, count in stats["authors"].most_common(3)
        )
        table.add_row(
            file,
            str(stats["commits"]),
            str(stats["lines"]),
            top_authors,
        )

    return table


def _compute_activity_summary(commits: Sequence[Commit], since_date, until_date) -> Tuple[Sequence[Commit], Counter]:
    """Filter commits and count author activity considering date range."""
    filtered_commits = [commit for commit in commits if since_date <= commit.committed_datetime.astimezone(timezone.utc) <= until_date]
    author_activity = Counter(commit.author.name for commit in filtered_commits)

    return filtered_commits, author_activity


def _generate_activity_summary_table(author_activity: Counter, filtered_commits: Sequence[Commit]) -> Table:
    """Generate a summary table of commit activity."""
    table = Table(title="Commit Activity Summary")
    table.add_column("Total Commits", style="bold green")
    table.add_column("Contributors", style="bold cyan")
    table.add_column("Top Contributor", style="bold magenta")
    table.add_column("Lines Committed", style="bold blue")
    table.add_column("Last Commit Date", style="bold yellow")

    total_commits = len(filtered_commits)
    contributors = len(author_activity)
    top_contributor, top_commits = ("", 0)
    if author_activity:
        top_contributor, top_commits = author_activity.most_common(1)[0]

    total_lines = sum(
        details.get("lines", 0)
        for commit in filtered_commits
        for details in commit.stats.files.values()
    )

    last_commit_date = max(
        (commit.committed_datetime.astimezone(timezone.utc) for commit in filtered_commits),
        default="N/A"
    )
    last_commit_date_str = last_commit_date.strftime("%Y-%m-%d") if last_commit_date != "N/A" else "N/A"

    table.add_row(
        str(total_commits),
        str(contributors),
        f"{top_contributor} ({top_commits} commits)",
        str(total_lines),
        last_commit_date_str,
    )

    return table


if __name__ == "__main__":
    typer.run(command)
