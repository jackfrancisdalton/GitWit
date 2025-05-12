import subprocess
from datetime import datetime, timezone
from typing import List, Optional, Iterable, Tuple
from dataclasses import dataclass

@dataclass
class CommitStats:
    insertions: int
    deletions: int
    files_changed: int

@dataclass
class Commit:
    hash: str
    author: str
    date: datetime
    message: str
    stats: CommitStats

@dataclass
class BlameLine:
    commit: str
    author: str
    author_time: str
    content: str

def run_git_command(args: List[str]) -> str:
    result = subprocess.run(['git'] + args, capture_output=True, text=True, check=True)
    return result.stdout

def get_filtered_commits(
    since: datetime,
    until: datetime,
    directories: Optional[List[str]] = None,
    authors: Optional[List[str]] = None
) -> Iterable[Commit]:
    command = [
        "log",
        "--since", since.isoformat(),
        "--until", until.isoformat(),
        "--pretty=format:%H%x01%an%x01%ai%x01%s",
        "--shortstat"
    ]

    if authors:
        author_pattern = '|'.join(authors)
        command += ["--author", author_pattern]

    if directories:
        command += ["--"] + directories

    output = run_git_command(command)
    lines = output.splitlines()

    for i in range(0, len(lines), 2):
        commit_info = lines[i].split('\x01')
        commit_hash, author, date_str, message = commit_info
        date = datetime.fromisoformat(date_str).astimezone(timezone.utc)

        if i+1 < len(lines) and lines[i+1]:
            stats_line = lines[i+1]
            insertions, deletions, files_changed = parse_shortstat(stats_line)
        else:
            insertions = deletions = files_changed = 0

        yield Commit(
            hash=commit_hash,
            author=author,
            date=date,
            message=message,
            stats=CommitStats(insertions, deletions, files_changed)
        )

def parse_shortstat(line: str) -> Tuple[int, int, int]:
    insertions = deletions = files_changed = 0
    parts = line.split(',')
    for part in parts:
        part = part.strip()
        if 'file changed' in part or 'files changed' in part:
            files_changed = int(part.split()[0])
        elif 'insertion' in part:
            insertions = int(part.split()[0])
        elif 'deletion' in part:
            deletions = int(part.split()[0])
    return insertions, deletions, files_changed

def fetch_file_paths_tracked_by_git(search_term: str, directories: Optional[List[str]]) -> List[str]:
    command = ["ls-files"] + (directories if directories else [])
    output = run_git_command(command)
    return [line for line in output.splitlines() if search_term in line]

def fetch_file_gitblame(file_path: str) -> List[BlameLine]:
    command = ["blame", "--line-porcelain", file_path]
    output = run_git_command(command)
    return parse_blame_porcelain(output)

def parse_blame_porcelain(output: str) -> List[BlameLine]:
    blame_lines = []
    current_line_data = {}
    for line in output.splitlines():
        if line.startswith('\t'):
            current_line_data['content'] = line[1:]
            blame_lines.append(BlameLine(**current_line_data))
            current_line_data = {}
        else:
            key, _, value = line.partition(' ')
            key = key.replace('-', '_')
            current_line_data[key] = value
    return blame_lines


# from datetime import datetime
# import os
# from pathlib import Path
# import re
# from typing import Any, Dict, List, Optional, Iterable
# from git import Commit, Repo

# from gitwit.models.blame_line import BlameLine
# from gitwit.utils.repo_singleton import RepoSingleton


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

#     for commit in repo.iter_commits(since=since.isoformat(), until=until.isoformat()):
#         if authors and not any(a.lower() in commit.author.name.lower() for a in authors):
#             continue

#         if directories and not any(
#             str(f).startswith(d.rstrip("/") + "/") for f in commit.stats.files for d in directoriesf
#         ):
#             continue
#         yield commit


# # TODO WIP: improve efficiency of this function by doing filtering in git instead of in python
# # def get_filtered_commits(
# #     since: datetime,
# #     until: datetime,
# #     directories: Optional[List[str]] = None,
# #     authors: Optional[List[str]] = None,
# # ) -> Iterable[Commit]:
# #     """
# #     - Instantiates Repo()
# #     - Yields commits between since/until
# #     - Applies authors and directory filters
# #     """
# #     repo = RepoSingleton.get_repo()

# #     kwargs = {
# #         "since": since.isoformat(),
# #         "until": until.isoformat(),
# #     }

# #     if authors:
# #         # build a case-insensitive regex that matches any of the names as substrings
# #         pattern = "(?i)(" + "|".join(re.escape(a) for a in authors) + ")"
# #         kwargs["author"] = pattern

# #     # if directories:
# #     #     kwargs["paths"] = directories

# #     return repo.iter_commits(**kwargs)


# def fetch_file_paths_tracked_by_git(search_term: str, directories) -> List[str]:
#     repo = RepoSingleton.get_repo()

#     all_files = repo.git.ls_files().splitlines()
#     matching_files = [f for f in all_files if search_term in os.path.basename(f)]

#     if directories:
#         dirs = [d.rstrip("/") + "/" for d in directories]
#         matching_files = [f for f in matching_files if any(f.startswith(d) for d in dirs)]

#     return matching_files


# class BlameFetchError(Exception):
#     """Raised when git-blame for a file can’t be fetched or parsed."""


# HEX_SHA = re.compile(r"^[0-9a-f]{7,40}$")


# def fetch_file_gitblame(repo: Repo, file_path: Path) -> List[BlameLine]:
#     repo = RepoSingleton.get_repo()

#     try:
#         raw_blame_info = repo.git.blame("--line-porcelain", str(file_path)).splitlines()
#         blame_list = _parse_porcelain_blame(raw_blame_info)
#     except Exception as e:
#         raise BlameFetchError(
#             f"failed to fetch or parse blame for {file_path} with error {e}"
#         ) from e

#     return blame_list


# def _parse_porcelain_blame(blame_lines_str: List[str]) -> List[BlameLine]:
#     blame_lines: List[BlameLine] = []
#     current: Dict[str, Any] = {}

#     for raw in blame_lines_str:
#         raw = raw.rstrip("\r\n")

#         # --- 1) Is this a header? ---
#         parts = raw.split()

#         if len(parts) >= 3 and HEX_SHA.match(parts[0]):
#             sha = parts[0]
#             orig = int(parts[1])
#             final = int(parts[2])
#             count = int(parts[3]) if len(parts) >= 4 else 1
#             current = {
#                 "commit": sha,
#                 "orig_lineno": orig,
#                 "final_lineno": final,
#                 "num_lines": count,
#             }
#             continue

#         # --- 2) Is this the content line? ---
#         if raw.startswith("\t"):
#             current["content"] = raw[1:]
#             blame_lines.append(BlameLine(**current))
#             current = {}
#             continue

#         # --- 3) Otherwise it must be a key/value line ---
#         if " " in raw:
#             key, val = raw.split(" ", 1)
#             key = key.replace("-", "_")
#             if key in ("author_time", "committer_time"):
#                 val = int(val)
#             current[key] = val
#             continue

#     return blame_lines
