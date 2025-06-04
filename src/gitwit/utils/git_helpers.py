from dataclasses import dataclass
from datetime import datetime
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Iterable

from git import Actor, Commit, CommitStats
from gitwit.models.blame_line import BlameLine
from gitwit.utils.repo_singleton import RepoSingleton


def _run_git(*args: str) -> str:
    repo = RepoSingleton.get_repo()
    return repo.git._run(*args)


def count_commits(since: datetime, until: datetime) -> int:
    out = _run_git(
        "rev-list",
        "--count",
        f"--since={since.isoformat()}",
        f"--until={until.isoformat()}",
    )
    return int(out.strip() or 0)


def get_filtered_commits(
    since: datetime,
    until: datetime,
    directories: Optional[List[str]] = None,
    authors: Optional[List[str]] = None,
) -> Iterable[Commit]:
    fmt = "%H%x00%an%x00%aI%x00%B%x00"
    raw = _run_git(
        "log",
        f"--since={since.isoformat()}",
        f"--until={until.isoformat()}",
        "--numstat",
        "-z",
        f"--pretty=format:{fmt}",
    )
    parts = raw.split("\x00")
    i = 0
    while i < len(parts) - 1:
        sha = parts[i]
        if not sha:
            break
        author_name = parts[i + 1]
        iso_date = parts[i + 2]
        message = parts[i + 3]
        i += 4
        numstat_block = parts[i]
        i += 1  # skip block
        i += 1  # skip delimiter
        files: Dict[str, Dict[str, int]] = {}
        if numstat_block:
            for line in numstat_block.splitlines():
                if not line.strip():
                    continue
                ins, del_, path = line.split("\t")
                ins = 0 if ins == "-" else int(ins)
                del_ = 0 if del_ == "-" else int(del_)
                files[path] = {
                    "insertions": ins,
                    "deletions": del_,
                    "lines": ins + del_,
                }
        if authors and not any(a.lower() in author_name.lower() for a in authors):
            continue
        if directories and not any(
            p.startswith(d.rstrip("/") + "/") for p in files for d in directories
        ):
            continue
        total_insertions = sum(f["insertions"] for f in files.values())
        total_deletions = sum(f["deletions"] for f in files.values())
        stats = CommitStats(
            total={"insertions": total_insertions, "deletions": total_deletions},
            files=files,
        )
        dt = datetime.fromisoformat(iso_date)
        yield Commit(
            hexsha=sha,
            author=Actor(name=author_name),
            committed_datetime=dt,
            committed_date=int(dt.timestamp()),
            message=message,
            stats=stats,
        )


def fetch_file_paths_tracked_by_git(search_term: str, directories) -> List[str]:
    all_files = _run_git("ls-files").splitlines()
    matching_files = [f for f in all_files if search_term in os.path.basename(f)]
    if directories:
        dirs = [d.rstrip("/") + "/" for d in directories]
        matching_files = [f for f in matching_files if any(f.startswith(d) for d in dirs)]
    return matching_files


class BlameFetchError(Exception):
    """Raised when git-blame for a file can’t be fetched or parsed."""


HEX_SHA = re.compile(r"^[0-9a-f]{7,40}$")


def fetch_file_gitblame(file_path: Path) -> List[BlameLine]:
    try:
        raw_blame_info = _run_git("blame", "--line-porcelain", str(file_path)).splitlines()
        blame_list = _parse_porcelain_blame(raw_blame_info)
    except Exception:
        raise BlameFetchError("failed to fetch or parse blame")
    return blame_list


def _parse_porcelain_blame(blame_lines_str: List[str]) -> List[BlameLine]:
    blame_lines: List[BlameLine] = []
    current: Dict[str, Any] = {}
    for raw in blame_lines_str:
        raw = raw.rstrip("\r\n")
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
        if raw.startswith("\t"):
            current["content"] = raw[1:]
            blame_lines.append(BlameLine(**current))
            current = {}
            continue
        if " " in raw:
            key, val = raw.split(" ", 1)
            key = key.replace("-", "_")
            if key in ("author_time", "committer_time"):
                val = int(val)
            current[key] = val
            continue
    return blame_lines
