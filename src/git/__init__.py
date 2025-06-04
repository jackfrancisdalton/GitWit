from dataclasses import dataclass
from datetime import datetime
from typing import Dict

from .cmd import Git


@dataclass(slots=True)
class Actor:
    name: str


@dataclass(slots=True)
class CommitStats:
    total: Dict[str, int]
    files: Dict[str, Dict[str, int]]


@dataclass(slots=True)
class Commit:
    hexsha: str
    author: Actor
    committed_datetime: datetime
    committed_date: int
    message: str
    stats: CommitStats


class Repo:
    __slots__ = ("git",)

    def __init__(self, path: str = "."):
        self.git = Git(path)
