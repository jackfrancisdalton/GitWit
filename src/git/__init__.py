from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any

@dataclass
class Actor:
    name: str

@dataclass
class CommitStats:
    total: Dict[str, int]
    files: Dict[str, Dict[str, int]]

@dataclass
class Commit:
    hexsha: str
    author: Actor
    committed_datetime: datetime
    committed_date: int
    message: str
    stats: CommitStats

class Repo:
    pass
