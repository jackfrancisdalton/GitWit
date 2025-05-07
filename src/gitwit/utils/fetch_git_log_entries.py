from typing import List, Optional

from gitwit.models.git_log_entry import GitLogEntry
from gitwit.utils.repo_singleton import RepoSingleton


# TODO: refactor this to be part of the git_fetch in git helpers
def fetch_git_log_entries_of_added_files() -> List[GitLogEntry]:
    repo = RepoSingleton.get_repo()

    raw = repo.git.log(
        '--diff-filter=A',
        '--format=%H%x00%aI%x00%an',
        '--name-only'
    )

    blocks: List[GitLogEntry] = []

    current_hash: Optional[str] = None
    current_iso_date: Optional[str] = None
    current_author: Optional[str] = None
    current_files: List[str] = []

    for line in raw.splitlines():
        if '\x00' in line:
            # flush the previous block if we had one
            if current_hash is not None:
                blocks.append(GitLogEntry(
                    commit_hash=current_hash,
                    created_at_iso=current_iso_date,
                    author=current_author,
                    files=current_files
                ))
            # parse new header
            commit_hash, iso_date, author = line.split('\x00')
            current_hash = commit_hash
            current_iso_date = iso_date
            current_author = author
            current_files = []
        else:
            path = line.strip()
            if path:
                current_files.append(path)

    # flush the final block
    if current_hash is not None:
        blocks.append(GitLogEntry(
            commit_hash=current_hash,
            created_at_iso=current_iso_date, 
            author=current_author,
            files=current_files
        ))

    return blocks