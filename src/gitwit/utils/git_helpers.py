from datetime import datetime
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Iterable
from git import Commit, Repo

from gitwit.models.blame_line import BlameLine
from gitwit.utils.repo_singleton import RepoSingleton


def count_commits(since: datetime, until: datetime) -> int:
    repo = RepoSingleton.get_repo()
    return int(
        repo.git.rev_list(
            "--count", f"--since={since.isoformat()}", f"--until={until.isoformat()}"
        )
    )


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
    repo = RepoSingleton.get_repo()

    for commit in repo.iter_commits(since=since.isoformat(), until=until.isoformat()):
        if authors and not any(
            a.lower() in commit.author.name.lower() for a in authors
        ):
            continue

        if directories and not any(
            str(f).startswith(d.rstrip("/") + "/")
            for f in commit.stats.files
            for d in directories
        ):
            continue
        yield commit


# TODO WIP: improve efficiency of this function by doing filtering in git instead of in python
# def get_filtered_commits(
#     since: datetime,
#     until: datetime,
#     directories: Optional[List[str]] = None,
#     authors: Optional[List[str]] = None,
# ) -> Iterable[Commit]:
#     """
#     - Instantiates Repo()
#     - Yields commits between since/until
#     - Applies authors and directory filters
#     """
#     repo = RepoSingleton.get_repo()

#     kwargs = {
#         "since": since.isoformat(),
#         "until": until.isoformat(),
#     }

#     if authors:
#         # build a case-insensitive regex that matches any of the names as substrings
#         pattern = "(?i)(" + "|".join(re.escape(a) for a in authors) + ")"
#         kwargs["author"] = pattern

#     # if directories:
#     #     kwargs["paths"] = directories

#     return repo.iter_commits(**kwargs)


def fetch_file_paths_tracked_by_git(search_term: str, directories) -> List[str]:
    repo = RepoSingleton.get_repo()

    all_files = repo.git.ls_files().splitlines()
    matching_files = [f for f in all_files if search_term in os.path.basename(f)]

    if directories:
        dirs = [d.rstrip("/") + "/" for d in directories]
        matching_files = [
            f for f in matching_files if any(f.startswith(d) for d in dirs)
        ]

    return matching_files


class BlameFetchError(Exception):
    """Raised when git-blame for a file can’t be fetched or parsed."""


HEX_SHA = re.compile(r"^[0-9a-f]{7,40}$")


def fetch_file_gitblame(repo: Repo, file_path: Path) -> List[BlameLine]:
    repo = RepoSingleton.get_repo()

    try:
        raw_blame_info = repo.git.blame("--line-porcelain", str(file_path)).splitlines()
        blame_list = _parse_porcelain_blame(raw_blame_info)
    except Exception:
        raise BlameFetchError("failed to fetch or parse blame")

    return blame_list


def _parse_porcelain_blame(blame_lines_str: List[str]) -> List[BlameLine]:
    blame_lines: List[BlameLine] = []
    current: Dict[str, Any] = {}

    for raw in blame_lines_str:
        raw = raw.rstrip("\r\n")

        # --- 1) Is this a header? ---
        parts = raw.split()

        if len(parts) >= 3 and HEX_SHA.match(parts[0]):
            sha = parts[0]
            orig = int(parts[1])
            final = int(parts[2])
            count = int(parts[3]) if len(parts) >= 4 else 1
            current = {
                "commit": sha,
                "orig_lineno": orig,
                "final_lineno": final,
                "num_lines": count,
            }
            continue

        # --- 2) Is this the content line? ---
        if raw.startswith("\t"):
            current["content"] = raw[1:]
            blame_lines.append(BlameLine(**current))
            current = {}
            continue

        # --- 3) Otherwise it must be a key/value line ---
        if " " in raw:
            key, val = raw.split(" ", 1)
            key = key.replace("-", "_")
            if key in ("author_time", "committer_time"):
                val = int(val)

            current[key] = val
            continue

    return blame_lines
