import os
from typing import List
from git import Repo


def fetch_tracked_git_file_paths(repo: Repo, search_term: str, directories) -> List[str]:
    all_files = repo.git.ls_files().splitlines()
    matching_files = [f for f in all_files if search_term in os.path.basename(f)]

    if directories:
        dirs = [d.rstrip('/') + '/' for d in directories]
        matching_files = [f for f in matching_files if any(f.startswith(d) for d in dirs)]

    return matching_files