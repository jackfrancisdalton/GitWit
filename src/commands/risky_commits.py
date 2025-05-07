from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import typer
from git import Repo, Commit
from rich.table import Table
from utils.console_singleton import ConsoleSingleton
from utils.date_utils import convert_to_datetime


@dataclass
class RiskFactor:
    description: str
    details: str


@dataclass
class RiskyCommit:
    commit: Commit
    risk_score: int
    risk_factors: List[RiskFactor] = field(default_factory=list)


console = ConsoleSingleton.get_console()

KEYWORDS = ["password", "refactor", "security", "key", "secret", "credentials", "fixme", "todo"]
LINES_CHANGED_THRESHOLD = 500
FILES_CHANGED_THRESHOLD = 10


def command(
    since: str = typer.Option(..., help="Start date in YYYY-MM-DD format"),
    until: str = typer.Option(None, help="End date in YYYY-MM-DD format")
):
    try:
        since_date = convert_to_datetime(since)
        until_date = convert_to_datetime(until)
    except ValueError:
        console.print(f"[red]Invalid date format provided. Use 'YYYY-MM-DD'.[/red]")
        raise typer.Exit(1)

    repo = Repo(".", search_parent_directories=True)
    risky_commits = _identify_risky_commits(repo, since_date, until_date)

    if not risky_commits:
        console.print("[green]No risky commits found for this period.[/green]")
        return

    table = _generate_risky_commits_table(risky_commits)
    console.print(table)


def _identify_risky_commits(repo: Repo, since: datetime, until: datetime) -> List[RiskyCommit]:
    commits_in_risk_period = list(
        repo.iter_commits(
            since=since.isoformat(), 
            until=until.isoformat()
        )
    )

    risky_commits = []

    for commit in commits_in_risk_period:
        risk_score = 0
        risk_factors = []

        stats = commit.stats
        total_lines_changed = stats.total['insertions'] + stats.total['deletions']
        files_changed = len(stats.files)

        risk_score += _assess_lines_changed(total_lines_changed, risk_factors)
        risk_score += _assess_files_changed(files_changed, risk_factors)
        risk_score += _assess_keywords(str(commit.message), risk_factors)
        # risk_score += _assess_first_time_files(commit, seen_prefixes_by_author, risk_factors) TODO: implement in the future

        if risk_score > 0:
            risky_commits.append(RiskyCommit(commit=commit, risk_score=risk_score, risk_factors=risk_factors))

    return sorted(risky_commits, key=lambda c: c.risk_score, reverse=True)


def _assess_lines_changed(total_lines_changed: int, risk_factors: List[RiskFactor]) -> int:
    if total_lines_changed >= LINES_CHANGED_THRESHOLD:
        risk_factors.append(RiskFactor(
            description="Large number of lines changed",
            details=f"{total_lines_changed} lines changed"
        ))
        return 2
    return 0


def _assess_files_changed(files_changed: int, risk_factors: List[RiskFactor]) -> int:
    if files_changed >= FILES_CHANGED_THRESHOLD:
        risk_factors.append(RiskFactor(
            description="Many files modified",
            details=f"{files_changed} files changed"
        ))
        return 2
    return 0


def _assess_keywords(message: str, risk_factors: List[RiskFactor]) -> int:
    lower_msg = message.lower()
    score = 0
    for keyword in KEYWORDS:
        if keyword in lower_msg:
            risk_factors.append(RiskFactor(
                description="Sensitive keyword in commit message",
                details=f"Keyword '{keyword}' found in commit message"
            ))
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
        factors_desc = "\n".join(f"- {rf.description}: {rf.details}" for rf in risky_commit.risk_factors)
        commit_summary = commit.message.strip().split("\n")[0][:50]

        table.add_row(
            commit.hexsha[:7] + f" ({commit_summary})",
            commit.author.name,
            datetime.fromtimestamp(commit.committed_date).strftime("%Y-%m-%d %H:%M"),
            str(risky_commit.risk_score),
            factors_desc
        )

    return table