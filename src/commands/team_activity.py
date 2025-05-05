from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List
import typer
from git import Repo
from rich.table import Table
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from utils.console_singleton import ConsoleSingleton

@dataclass
class DeveloperActivity:
    developer: str
    prs_merged: int
    lines_added: int
    lines_deleted: int
    reviews_done: int
    review_time_avg: timedelta
    files_touched: int

console = ConsoleSingleton.get_console()

def command(
    period: str = typer.Option(
        "week", help="Period to summarize: day, week, or month"
    )
):
    """
    Summarize developer activity for a given period.
    """
    period_mapping = {"day": 1, "week": 7, "month": 30, "year": 365 }

    if period not in period_mapping:
        console.print(f"[red]Invalid period '{period}'. Choose 'day', 'week', or 'month'.[/red]")
        raise typer.Exit(1)

    days_ago = datetime.now() - timedelta(days=period_mapping[period])

    developer_activities = _fetch_developer_activities(days_ago)
    table = _generate_activity_table(developer_activities)

    console.print(table)


def _fetch_developer_activities(since: datetime):
    repo = Repo(".", search_parent_directories=True)
    commits = list(repo.iter_commits(since=since.isoformat()))
    total = len(commits)

    activities = {}
    files_seen = {}

    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning commits", total=total)

        for commit in commits:
            author = commit.author.name
            stats = commit.stats

            if author not in activities:
                activities[author] = DeveloperActivity(
                    developer=author,
                    prs_merged=0,
                    lines_added=0,
                    lines_deleted=0,
                    reviews_done=0,
                    review_time_avg=timedelta(),
                    files_touched=0,
                )
                files_seen[author] = set()

            dev = activities[author]
            dev.lines_added += stats.total["insertions"]
            dev.lines_deleted += stats.total["deletions"]

            for fn in stats.files:
                if fn not in files_seen[author]:
                    files_seen[author].add(fn)
                    dev.files_touched += 1

            progress.advance(task)

    return list(activities.values())


def _generate_activity_table(developers: List[DeveloperActivity]) -> Table:
    table = Table(title="Developer Activity Summary")

    table.add_column("Developer", style="magenta")
    table.add_column("Lines Added", justify="right", style="green")
    table.add_column("Lines Deleted", justify="right", style="red")
    table.add_column("Files Touched", justify="right", style="yellow")
    table.add_column("PRs Merged", justify="right", style="cyan")
    table.add_column("Reviews Done", justify="right", style="cyan")
    table.add_column("Review Time Avg", justify="right", style="cyan")

    for dev in developers:
        review_time = (
            f"{dev.review_time_avg.seconds//3600}h {(dev.review_time_avg.seconds//60)%60}m"
            if dev.reviews_done else "-"
        )

        table.add_row(
            dev.developer,
            str(dev.lines_added),
            str(dev.lines_deleted),
            str(dev.files_touched),
            str(dev.prs_merged),
            str(dev.reviews_done),
            review_time,
        )

    return table