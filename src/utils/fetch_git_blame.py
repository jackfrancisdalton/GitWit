from pathlib import Path
import re
from typing import Any, Dict
from git import List, Repo
from ..models.blame_line import BlameLine

class BlameFetchError(Exception):
    """Raised when git-blame for a file can’t be fetched or parsed."""

HEX_SHA = re.compile(r"^[0-9a-f]{7,40}$")

def fetch_file_gitblame(repo: Repo, file_path: Path) -> List[BlameLine]:
    try:
        raw_blame_info = repo.git.blame("--line-porcelain", str(file_path)).splitlines()
        blame_list = _parse_porcelain_blame(raw_blame_info)
    except Exception as e:
        raise BlameFetchError(f"failed to fetch or parse blame for {file_path} with error {e}") from e

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