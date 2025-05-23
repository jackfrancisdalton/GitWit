from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple
import typer
from git import Commit
from rich.table import Table

from gitwit.utils.console_singleton import ConsoleSingleton
from gitwit.utils.git_helpers import get_filtered_commits
from gitwit.utils.typer_helpers import handle_since_until_arguments


@dataclass
class RiskFactor:
    description: str
    details: str


@dataclass
class RiskyCommit:
    commit: Commit
    risk_score: int
    risk_factors: List[RiskFactor] = field(default_factory=list)


@dataclass(frozen=True)
class RiskConfig:
    KEYWORDS: Tuple[str, ...] = (
        "password",
        "refactor",
        "security",
        "key",
        "secret",
        "credentials",
        "fixme",
        "todo",
    )
    LINES_CHANGED_THRESHOLD: int = 500
    FILES_CHANGED_THRESHOLD: int = 10


RISK_CONFIG = RiskConfig()
console = ConsoleSingleton.get_console()


def command(
    since: str = typer.Option(..., help="Start date in YYYY-MM-DD format"),
    until: str = typer.Option(None, help="End date in YYYY-MM-DD format"),
):
    """
    Identify risky commits in the repository in a given date range.
    """

    since_date, until_date = handle_since_until_arguments(since, until)
    risky_commits = _identify_risky_commits(since_date, until_date)

    if not risky_commits:
        console.print("[green]No risky commits found for this period.[/green]")
        return

    table = _generate_risky_commits_table(risky_commits)
    console.print(table)


def _identify_risky_commits(since: datetime, until: datetime) -> List[RiskyCommit]:
    all_commits = get_filtered_commits(
        since=since,
        until=until,
    )

    risky_commits = []

    for commit in all_commits:
        risk_score = 0
        risk_factors = []

        stats = commit.stats
        total_lines_changed = stats.total["insertions"] + stats.total["deletions"]
        files_changed = len(stats.files)

        risk_score += _assess_lines_changed(total_lines_changed, risk_factors)
        risk_score += _assess_files_changed(files_changed, risk_factors)
        risk_score += _assess_keywords(str(commit.message), risk_factors)

        # TODO: implement in the future
        # risk_score += _assess_first_time_files()

        if risk_score > 0:
            risky_commits.append(
                RiskyCommit(commit=commit, risk_score=risk_score, risk_factors=risk_factors)
            )

    return sorted(risky_commits, key=lambda c: c.risk_score, reverse=True)


def _assess_lines_changed(total_lines_changed: int, risk_factors: List[RiskFactor]) -> int:
    if total_lines_changed >= RISK_CONFIG.LINES_CHANGED_THRESHOLD:
        risk_factors.append(
            RiskFactor(
                description="Large number of lines changed",
                details=f"{total_lines_changed} lines changed",
            )
        )
        return 2
    return 0


def _assess_files_changed(files_changed: int, risk_factors: List[RiskFactor]) -> int:
    if files_changed >= RISK_CONFIG.FILES_CHANGED_THRESHOLD:
        risk_factors.append(
            RiskFactor(
                description="Many files modified",
                details=f"{files_changed} files changed",
            )
        )
        return 2
    return 0


def _assess_keywords(message: str, risk_factors: List[RiskFactor]) -> int:
    lower_msg = message.lower()
    score = 0
    for keyword in RISK_CONFIG.KEYWORDS:
        if keyword in lower_msg:
            risk_factors.append(
                RiskFactor(
                    description="Sensitive keyword in commit message",
                    details=f"Keyword '{keyword}' found in commit message",
                )
            )
            score += 3
    return score


def _generate_risky_commits_table(commits: List[RiskyCommit]) -> Table:
    table = Table(title="High Risk Commits")
    table.add_column("Commit", style="magenta")
    table.add_column("Author", style="cyan")
    table.add_column("Date", style="green")
    table.add_column("Risk Score", justify="right", style="red")
    table.add_column("Risk Factors", style="yellow")

    for risky_commit in commits:
        commit = risky_commit.commit
        factors_desc = "\n".join(
            f"- {rf.description}: {rf.details}" for rf in risky_commit.risk_factors
        )
        commit_summary = commit.message.strip().split("\n")[0][:50]

        table.add_row(
            commit.hexsha[:7] + f" ({commit_summary})",
            commit.author.name,
            datetime.fromtimestamp(commit.committed_date).strftime("%Y-%m-%d %H:%M"),
            str(risky_commit.risk_score),
            factors_desc,
        )

    return table
