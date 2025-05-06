import typer
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from git import Repo
from rich.table import Table
from utils.console_singleton import ConsoleSingleton
from utils.fetch_git_log_entries import fetch_git_log_entries

console = ConsoleSingleton.get_console()

# Assign a fixed UTC time at import time to avoid issues where microseconds during run time result in filtering errors
FIXED_NOW_UTC = datetime.now(timezone.utc)

@dataclass
class HotZone:
    path: str
    commits: int
    contributors: int
    last_change: datetime


@dataclass
class GitLogFileEntry:
    commit_hash: str
    path: str
    author: str
    date: datetime


class Node:
    # Slots assigned to the Node class to optimize memory usage
    __slots__ = ("name", "children", "commits", "direct_commits", "authors", "last_date")
    def __init__(self, name: str):
        self.name = name
        self.children: dict[str, Node] = {}
        self.commits: set[str] = set()
        self.direct_commits: set[str] = set()
        self.authors: set[str] = set()
        self.last_date: datetime = datetime.min.replace(tzinfo=timezone.utc)


def command(
    days: int = typer.Option(7, "--days", "-d", help="Number of days to look back for commits"),
    directories: Optional[List[str]] = typer.Option(
        None, "--dir", "-d", help="Filter commits to these directory paths"
    ),
    authors: Optional[List[str]] = typer.Option(
        None, "--author", "-a", help="Filter commits to these authors"
    ),
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of hot zones to show"),
):
    entries = _generate_entries(days, directories, authors)

    if not entries:
        return []

    file_tree_root_node = _generate_file_tree(entries)
    compressed_tree = _compress_node_tree(file_tree_root_node)
    hot_zones = _calculate_hot_zones(compressed_tree)

    if hot_zones:
        hot_zones.sort(key=lambda z: z.commits, reverse=True)
        hot_zones = hot_zones[:limit]
        table = _generate_table(hot_zones, days)
        console.print(table)
    else:
        console.print(f"[yellow]No activity in the last {days} days.[/yellow]")

# TODO: consider making this a re-usable function
def _generate_entries(
    days: int,
    directories: Optional[List[str]],
    authors: Optional[List[str]]
) -> List[GitLogFileEntry]:
    repo = Repo('.', search_parent_directories=True)
    cutoff = FIXED_NOW_UTC - timedelta(days=days)

    # Fetch git log entries
    git_log_entries = fetch_git_log_entries(repo)

    # normalize directory filters
    dirs = [d.rstrip("/") for d in directories] if directories else None

    def is_relevant_path(path: str) -> bool:
        if dirs is None:
            return True
        
        return any(path == d or path.startswith(f"{d}/") for d in dirs)

    def is_relevant_author(author: str) -> bool:
        if not authors:
            return True
        
        return any(a.lower() in author.lower() for a in authors)
    
    result: List[GitLogFileEntry] = []

    for log_entry in git_log_entries:
        log_entry_date = datetime.fromisoformat(log_entry.created_at_iso.rstrip("Z")).astimezone(timezone.utc)

        # Date Filter
        if log_entry_date < cutoff:
            continue

        # Author Filter
        if authors and not is_relevant_author(log_entry.author):
            continue

        # Path Filter
        matches = [p for p in log_entry.files if is_relevant_path(p)]
        if not matches:
            continue

        # TODO: review if this predicate is required
        if authors:
            # single entry per commit
            result.append(GitLogFileEntry(log_entry.commit_hash, matches[0], log_entry.author, log_entry_date))
        else:
            # one entry per file
            result.extend(
                GitLogFileEntry(log_entry.commit_hash, p, log_entry.author, log_entry_date)
                for p in matches
            )

    return result


def _generate_file_tree(entries: List[GitLogFileEntry]) -> Node:
    root = Node("")

    def add_entry(sha: str, path: str, author: str, date: datetime):
        parts = path.split("/")[:-1]
        node = root

        # aggregate at root
        node.commits.add(sha)
        node.authors.add(author)
        if date > node.last_date:
            node.last_date = date

        # traverse into subdirs
        for part in parts:
            if part not in node.children:
                node.children[part] = Node(part)

            node = node.children[part]
            node.commits.add(sha)
            node.authors.add(author)
            if date > node.last_date:
                node.last_date = date

        # record a direct commit on this directory
        node.direct_commits.add(sha)

    # 4. Iterate LogEntry instead of tuple
    for e in entries:
        add_entry(e.commit_hash, e.path, e.author, e.date)

    return root


def _compress_node_tree(root: Node) -> Node:
    def compress(node: Node):
        for child in list(node.children.values()):
            compress(child)

        not_root = node is not root
        has_no_direct_commits = not node.direct_commits
        has_one_child = len(node.children) == 1

        if not_root and has_no_direct_commits and has_one_child:
            child = next(iter(node.children.values()))
            node.name = f"{node.name}/{child.name}".lstrip("/")
            node.commits = child.commits
            node.direct_commits = child.direct_commits
            node.authors = child.authors
            node.last_date = child.last_date
            node.children = child.children

    compress(root)
    return root

def _calculate_hot_zones(root: Node) -> List[HotZone]:
    zones: List[HotZone] = []

    def gather(node: Node, prefix: str):
        for child in node.children.values():
            p = f"{prefix}/{child.name}" if prefix else f"/{child.name}"

            zones.append(HotZone(
                path=p,
                commits=len(child.commits),
                contributors=len(child.authors),
                last_change=child.last_date
            ))

            gather(child, p)

    gather(root, "")
    return zones


def _generate_table(zones: List[HotZone], days: int) -> Table:
    table = Table(title=f"Hot Zones (last {days} days)")
    table.add_column("Directory", style="cyan")
    table.add_column("Commits", justify="right", style="green")
    table.add_column("Contributors", justify="right", style="magenta")
    table.add_column("Last Change", style="yellow")

    for z in zones:
        delta = FIXED_NOW_UTC - z.last_change
        if delta < timedelta(hours=1):
            last = f"{int(delta.total_seconds() // 60)} min ago"
        elif delta < timedelta(days=1):
            last = f"{delta.seconds // 3600} hour(s) ago"
        else:
            last = f"{delta.days} day(s) ago"
        table.add_row(z.path, str(z.commits), str(z.contributors), last)
    return table
