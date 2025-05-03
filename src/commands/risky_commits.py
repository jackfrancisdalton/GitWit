from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set
import typer
from git import Repo, Commit
from rich.table import Table
from utils.console_singleton import ConsoleSingleton


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
    period: str = typer.Option("week", help="Period to analyze: day, week, or month")
):
    period_mapping = {"day": 1, "week": 7, "month": 30}
    if period not in period_mapping:
        console.print(f"[red]Invalid period '{period}'. Choose 'day', 'week', or 'month'.[/red]")
        raise typer.Exit(1)

    since = datetime.now() - timedelta(days=period_mapping[period])
    repo = Repo(".", search_parent_directories=True)

    risky_commits = _identify_risky_commits(repo, since)

    if not risky_commits:
        console.print("[green]No risky commits found for this period.[/green]")
        return

    table = _generate_risky_commits_table(risky_commits)
    console.print(table)


def _generate_file_types_commited_by_author_dict(start_of_risk_assessment_period: datetime, repo: Repo) -> Dict[str, Set[str]]:
    # Initialize a dictionary to store file type prefixes seen by each author
    seen_prefixes_by_author: Dict[str, Set[str]] = {}

    # Iterate over all commits in the repository up to the specified date
    for old in repo.iter_commits(until=start_of_risk_assessment_period.isoformat()):
        # Get the parent commit of the current commit, if it exists
        parent = old.parents[0] if old.parents else None

        # Iterate over the differences (diffs) between the current commit and its parent
        for diff in old.diff(parent):
            # Check if the diff represents a new file and has a valid file path
            if diff.new_file and diff.b_path:
                # Extract the file type (suffix) or the file name if no suffix exists
                pref = Path(diff.b_path).suffix or Path(diff.b_path).name
                # Add the file type prefix to the set of seen prefixes for the commit's author
                seen_prefixes_by_author.setdefault(old.author.email, set()).add(pref)

    # Return the dictionary containing file type prefixes seen by each author
    return seen_prefixes_by_author


def _identify_risky_commits(repo: Repo, since: datetime) -> List[RiskyCommit]:

    # seen_prefixes_by_author = _generate_file_types_commited_by_author_dict(since, repo)
    commits_in_risk_period = list(repo.iter_commits(since=since.isoformat()))

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
        # risk_score += _assess_first_time_files(commit, seen_prefixes_by_author, risk_factors)

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


def _assess_first_time_files(
    commit: Commit,
    seen_prefixes_by_author: Dict[str, Set[str]],
    risk_factors: List[RiskFactor]
) -> int:
    author_id = commit.author.email
    seen = seen_prefixes_by_author.setdefault(author_id, set())

    parent = commit.parents[0] if commit.parents else None
    new_prefixes: Set[str] = set()

    for diff in commit.diff(parent):
        if not diff.new_file or not diff.b_path:
            continue

        pref = Path(diff.b_path).suffix or Path(diff.b_path).name

        if pref not in seen:
            new_prefixes.add(pref)
            seen.add(pref)

    for pref in new_prefixes:
        risk_factors.append(RiskFactor(
            description="First-time file type added",
            details=f"File type '{pref}'"
        ))

    return len(new_prefixes)


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