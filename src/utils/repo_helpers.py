from datetime import datetime
from typing import Sequence, List, Optional, Iterable
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


def get_filtered_commits(
    since: datetime,
    until: datetime,
    directories: Optional[List[str]] = None,
    authors: Optional[List[str]] = None,
) -> Iterable[Commit]:
    """
    - Instantiates Repo()
    - Yields commits between since/until
    - Applies authors and directory filters
    """
    repo = Repo('.', search_parent_directories=True)
    
    for commit in repo.iter_commits(since=since.isoformat(), until=until.isoformat()):
        if authors and not any(a.lower() in commit.author.name.lower() for a in authors):
            continue

        if directories and not any(
           str(f).startswith(d.rstrip('/') + '/') for f in commit.stats.files for d in directories
        ):
            continue
        yield commit
