import typer
from typing import List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
from rich.table import Table
from utils.console_singleton import ConsoleSingleton
from utils.date_utils import convert_to_datetime
from utils.human_readable_helper import humanise_timedelta
from utils.repo_helpers import get_filtered_commits

console = ConsoleSingleton.get_console()

@dataclass
class HotZone:
    path: str
    commits: int
    contributors: int
    last_change: datetime


@dataclass
class FileCommitEntry:
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
    since: str = typer.Option(..., "--since", "-s", help="Start date in YYYY-MM-DD format"),
    until: str = typer.Option(..., "--until", "-u", help="End date in YYYY-MM-DD format(defaults to now)"),
    directories: Optional[List[str]] = typer.Option(None, "--dir", "-d", help="Filter commits to these directory paths"),
    authors: Optional[List[str]] = typer.Option(None, "--author", "-a", help="Filter commits to these authors"),
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of hot zones to show"),
):
    since_datetime, until_datetime = _handle_date_arguments(since, until)
    entries = _collect_file_commit_entries(since_datetime, until_datetime, directories, authors)

    if not entries:
        return []

    file_tree_root_node = _generate_file_tree(entries)
    compressed_tree = _compress_node_tree(file_tree_root_node)
    hot_zones = _calculate_hot_zones(compressed_tree)

    if hot_zones:
        hot_zones.sort(key=lambda z: z.commits, reverse=True)
        hot_zones = hot_zones[:limit]
        table = _generate_table(hot_zones, since_datetime, until_datetime)
        console.print(table)
    else:
        console.print(f"[yellow]No activity between {since} and {until}.[/yellow]")


def _handle_date_arguments(since: str, until: str) -> tuple[datetime, datetime]:
    try:
        since_datetime = convert_to_datetime(since)
        until_datetime = convert_to_datetime(until)
    except ValueError:
        console.print("[red]Invalid date format. Use YYYY-MM-DD.[/red]")
        raise typer.Exit(1)

    if since_datetime > until_datetime:
        console.print("[red]Start date cannot be after end date.[/red]")
        raise typer.Exit(1)

    return since_datetime, until_datetime


def _collect_file_commit_entries(
    since: datetime,
    until: datetime,
    directories: Optional[List[str]],
    authors: Optional[List[str]]
) -> List[FileCommitEntry]:
    filtered = get_filtered_commits(
        since=since,
        until=until,
        directories=directories,
        authors=authors,
    )

    entries: List[FileCommitEntry] = []

    for commit in filtered:
        for path in commit.stats.files:
            entries.append(FileCommitEntry(
                commit.hexsha,
                path,
                commit.author.name,
                commit.committed_datetime.astimezone(timezone.utc),
            ))

    return entries


def _generate_file_tree(entries: List[FileCommitEntry]) -> Node:
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


def _generate_table(zones: List[HotZone], since: datetime, until: datetime) -> Table:
    table = Table(title=f"Hot Zones (from {since} to {until})")
    table.add_column("Directory", style="cyan")
    table.add_column("Commits", justify="right", style="green")
    table.add_column("Contributors", justify="right", style="magenta")
    table.add_column("Last Change", style="yellow")

    for z in zones:
        time_ago_string = humanise_timedelta(datetime.now(timezone.utc) - z.last_change)
        table.add_row(z.path, str(z.commits), str(z.contributors), time_ago_string)
    
    return table
