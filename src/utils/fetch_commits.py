from datetime import datetime
from typing import Sequence
from git import Commit, Repo

def fetch_commits_in_date_range(since: datetime, until: datetime) -> Sequence[Commit]:
    """
    Fetch commits from the repository between two dates.
    """
    repo = Repo(".", search_parent_directories=True) # TODO: introduce a singleton pattern for providing the repo

    commits = repo.iter_commits(
        since=since.isoformat(),
        until=until.isoformat()
    )

    return list(commits)
