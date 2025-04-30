from dataclasses import dataclass


@dataclass
class BlameLine:
    commit: str
    orig_lineno: int
    final_lineno: int
    num_lines: int
    author: str
    author_mail: str
    author_time: int
    author_tz: str
    committer: str
    committer_mail: str
    committer_time: int
    committer_tz: str
    summary: str
    filename: str
    content: str