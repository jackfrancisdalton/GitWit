from dataclasses import dataclass
from typing import List


@dataclass
class GitLogEntry:
    commit_hash: str
    created_at_iso: str
    author: str
    files: List[str]