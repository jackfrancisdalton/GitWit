from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List
import typer
from git import Repo
from rich.table import Table
from ..utils.console_singleton import ConsoleSingleton

@dataclass
class DeveloperActivity:
    developer: str
    prs_merged: int
    lines_added: int
    lines_deleted: int
    reviews_done: int
    review_time_avg: timedelta
    new_files: int

console = ConsoleSingleton.get_console()

def command(
    period: str = typer.Option(
        "week", help="Period to summarize: day, week, or month"
    )
):
    """
    Summarize developer activity for a given period.
    """
    period_mapping = {"day": 1, "week": 7, "month": 30}
    if period not in period_mapping:
        console.print(f"[red]Invalid period '{period}'. Choose 'day', 'week', or 'month'.[/red]")
        raise typer.Exit(1)

    days_ago = datetime.now() - timedelta(days=period_mapping[period])

    repo = Repo(".", search_parent_directories=True)

    developer_activities = _fetch_developer_activities(repo, days_ago)
    table = _generate_activity_table(developer_activities)

    console.print(table)


def _fetch_developer_activities(repo: Repo, since: datetime) -> List[DeveloperActivity]:
    developers = {}

    for commit in repo.iter_commits(since=since.isoformat()):
        author = commit.author.name
        stats = commit.stats

        if author not in developers:
            developers[author] = DeveloperActivity(
                developer=author,
                prs_merged=0,
                lines_added=0,
                lines_deleted=0,
                reviews_done=0,
                review_time_avg=timedelta(),
                new_files=0,
            )

        dev_activity = developers[author]

        dev_activity.lines_added += stats.total["insertions"]
        dev_activity.lines_deleted += stats.total["deletions"]
        dev_activity.new_files += len(stats.files)
        dev_activity.prs_merged += 1  # Simplified assumption: one commit == one PR TODO: implement actual PR fetching

    return list(developers.values())


def _generate_activity_table(developers: List[DeveloperActivity]) -> Table:
    table = Table(title="Developer Activity Summary")

    table.add_column("Developer", style="magenta")
    table.add_column("PRs Merged", justify="right", style="cyan")
    table.add_column("Lines Added", justify="right", style="green")
    table.add_column("Lines Deleted", justify="right", style="red")
    table.add_column("Reviews Done", justify="right", style="cyan")
    table.add_column("Review Time Avg", justify="right", style="yellow")
    table.add_column("New Files", justify="right", style="green")

    for dev in developers:
        review_time = (
            f"{dev.review_time_avg.seconds//3600}h {(dev.review_time_avg.seconds//60)%60}m"
            if dev.reviews_done else "-"
        )

        table.add_row(
            dev.developer,
            str(dev.prs_merged),
            str(dev.lines_added),
            str(dev.lines_deleted),
            str(dev.reviews_done),
            review_time,
            str(dev.new_files),
        )

    return table