import typer
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from git import Repo
from rich.table import Table
from utils.console_singleton import ConsoleSingleton

console = ConsoleSingleton.get_console()

@dataclass
class HotZone:
    path: str
    commits: int
    contributors: int
    last_change: datetime


class Node:
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
    """
    Show the most active areas (hot zones) of the code base.
    """

    entries = _generate_entries(days, directories, authors)

    if not entries:
        return []

    file_tree_root_node = _generate_file_tree(entries)
    hot_zones = _calculate_hot_zones(file_tree_root_node)
    hot_zones.sort(key=lambda z: z.commits, reverse=True)
    hot_zones = hot_zones[:limit]

    if hot_zones:
        table = _generate_table(hot_zones, days)
        console.print(table)
    else:
        console.print(f"[yellow]No activity in the last {days} days.[/yellow]")



def _generate_file_tree(entries: List[tuple[str, str, str, datetime]]) -> Node:
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

    for sha, path, author, date in entries:
        add_entry(sha, path, author, date)

    return root

def _calculate_hot_zones(root: Node) -> List[HotZone]:

    # compress chains of single-child nodes with no direct commits
    def compress(node: Node):
        # If node has children then traverse further
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

    # flatten into list
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


# TODO: this can likley be converted to a shared implementation in utils
def _generate_entries(days: int, directories: Optional[List[str]], authors: Optional[List[str]]) -> List[tuple[str, str, str, datetime]]:
    repo = Repo('.', search_parent_directories=True)
    raw = repo.git.log(
        f"--since={days} days ago",
        "--pretty=format:%H%x01%aI%x01%an",
        "--date=iso",
        "--name-only"
    )

    entries: List[tuple[str, str, str, datetime]] = []
    current_commit: Optional[tuple[str, str, datetime]] = None

    for line in raw.splitlines():
        # If no entry skip it
        if not line.strip():
            continue

        # If it's a log header
        if "\x01" in line:
            sha, datestr, author = line.split("\x01")
            try:
                date = datetime.fromisoformat(datestr)
            except ValueError:
                # handle timestamps without timezone
                date = datetime.fromisoformat(datestr.rstrip('Z'))
            date = date.astimezone(timezone.utc)
            current_commit = (sha, author, date)

        # it's a file path under the header or an empty line
        else:
            path = line.strip()

            if not current_commit:
                continue
            sha, author, date = current_commit

            # filter by directories
            if directories:
                normalized_dirs = [d.strip("/") for d in directories]
                if not any(path == nd or path.startswith(f"{nd}/") for nd in normalized_dirs):
                    continue

            # filter by authors
            if authors and not any(a.lower() in author.lower() for a in authors):
                continue

            entries.append((sha, path, author, date))
    
    return entries

def _generate_table(zones: List[HotZone], days: int) -> Table:
    table = Table(title=f"Hot Zones (last {days} days)")
    table.add_column("Directory", style="cyan")
    table.add_column("Commits", justify="right", style="green")
    table.add_column("Contributors", justify="right", style="magenta")
    table.add_column("Last Change", style="yellow")

    now = datetime.now(timezone.utc)
    for z in zones:
        delta = now - z.last_change
        if delta < timedelta(hours=1):
            last = f"{int(delta.total_seconds() // 60)} min ago"
        elif delta < timedelta(days=1):
            last = f"{delta.seconds // 3600} hour(s) ago"
        else:
            last = f"{delta.days} day(s) ago"
        table.add_row(z.path, str(z.commits), str(z.contributors), last)
    return table
