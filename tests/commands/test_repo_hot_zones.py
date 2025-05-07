import pytest
from datetime import datetime, timezone, timedelta

import commands.repo_hot_zones as hz
from commands.repo_hot_zones import (
    CommitData,
    _generate_commit_data,
    _generate_file_tree,
    _compress_node_tree,
    _calculate_hot_zones,
)
from models.git_log_entry import GitLogEntry

FIXED_NOW = datetime(2025, 5, 6, 0, 0, 0, tzinfo=timezone.utc)

class DummyEntry(GitLogEntry):
    """Allow instantiation of GitLogEntry for tests."""
    def __init__(self, commit_hash, created_at_iso, author, files):
        self.commit_hash = commit_hash
        self.created_at_iso = created_at_iso
        self.author = author
        self.files = files


@pytest.fixture(autouse=True)
def patch_fetch(monkeypatch):
    """Ensure no real git calls."""
    monkeypatch.setattr(hz, "get_filtered_commits", lambda since, until, directories, authors: [])


def make_iso(days_delta: int, hours: int = 0):
    dt = FIXED_NOW - timedelta(days=days_delta, hours=-hours)
    return dt.isoformat()


# ===== _generate_entries tests =====

def test_generate_entries__empty():
    since = FIXED_NOW - timedelta(days=5)
    until = FIXED_NOW
    entries = _generate_commit_data(since=since, until=until, directories=None, authors=None)

    assert entries == []

# ===== _generate_file_tree + compression + calculate tests =====

def test_file_tree__empty():
    # Arrange
    entries = []

    # Act
    root = _generate_file_tree(entries)
    comp = _compress_node_tree(root)
    zones = _calculate_hot_zones(comp)

    # Assert
    assert zones == []

def test_file_tree__basic_and_hot_zones():
    # Arrange
    entries = [
        CommitData("h1", "dir/a.txt", "A", FIXED_NOW),
        CommitData("h2", "dir/b.txt","B", FIXED_NOW),
        CommitData("h3", "dir/a.txt","B", FIXED_NOW),
        CommitData("h1", "test/test_a.txt", "A", FIXED_NOW),
    ]

    # Act
    root = _generate_file_tree(entries)
    comp = _compress_node_tree(root)
    zones = _calculate_hot_zones(comp)

    # Assert
    paths = sorted(z.path for z in zones)
    assert len(paths) == 2
    assert "/dir" in paths
    assert "/test" in paths

    dir_zone = next(z for z in zones if z.path == "/dir")
    assert dir_zone.commits == 3
    assert dir_zone.contributors == 2

    dir_zone = next(z for z in zones if z.path == "/test")
    assert dir_zone.commits == 1
    assert dir_zone.contributors == 1

def test_compress__chain_and_preserve_direct_commit():
    # Arrange 
    entries = [
        CommitData("h1", "a/b/file",  "X", FIXED_NOW),
        CommitData("h2", "a/b/c/file2","Y", FIXED_NOW),
    ]

    # Act 
    root = _generate_file_tree(entries)
    comp = _compress_node_tree(root)
    zones = _calculate_hot_zones(comp)
    
    # Assert
    paths = {z.path for z in zones}
    assert "/a/b" in paths
    assert "/a/b/c" in paths

def test_calculate_hot_zones__flat_tree():
    # Arrange
    root = hz.Node("")

    c1 = hz.Node("x")
    c1.commits = {"h1", "h2"}
    c1.authors = {"A"}
    c1.last_date = FIXED_NOW
    
    c2 = hz.Node("y")
    c2.commits = {"h3"}
    c2.authors = {"B","C"}
    c2.last_date = FIXED_NOW

    root.children["x"] = c1
    root.children["y"] = c2

    # Act
    zones = _calculate_hot_zones(root)

    # Assert
    zmap = {z.path: z for z in zones}
    assert zmap["/x"].commits == 2
    assert zmap["/x"].contributors == 1
    assert zmap["/y"].commits == 1
    assert zmap["/y"].contributors == 2
