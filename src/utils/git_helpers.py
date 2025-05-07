from datetime import datetime
import os
from typing import List, Optional, Iterable
from git import Commit, Repo

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


def fetch_file_paths_tracked_by_git(repo: Repo, search_term: str, directories) -> List[str]:
    all_files = repo.git.ls_files().splitlines()
    matching_files = [f for f in all_files if search_term in os.path.basename(f)]

    if directories:
        dirs = [d.rstrip('/') + '/' for d in directories]
        matching_files = [f for f in matching_files if any(f.startswith(d) for d in dirs)]

    return matching_files