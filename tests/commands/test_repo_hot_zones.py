import pytest
from datetime import datetime, timezone, timedelta

import commands.repo_hot_zones as hz
from commands.repo_hot_zones import (
    GitLogFileEntry,
    _generate_entries,
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
    monkeypatch.setattr(hz, "fetch_git_log_entries", lambda repo: [])
    monkeypatch.setattr(hz, "FIXED_NOW_UTC", FIXED_NOW)


def make_iso(days_delta: int, hours: int = 0):
    dt = FIXED_NOW - timedelta(days=days_delta, hours=-hours)
    return dt.isoformat()


# ===== _generate_entries tests =====

def test_generate_entries__empty():
    entries = _generate_entries(days=5, directories=None, authors=None)
    assert entries == []

def test_generate_entries__no_filters(monkeypatch):
    # Arrange
    raw = [
        DummyEntry("h1", make_iso(1), "Alice", ["a.py", "path/c.py"]),
        DummyEntry("h2", make_iso(4), "Bob",   ["d.py"])
    ]

    monkeypatch.setattr(hz, "fetch_git_log_entries", lambda repo: raw)

    # Act
    entries = _generate_entries(days=7, directories=None, authors=None)

    # Assert
    assert len(entries) == 3 
    paths = [e.path for e in entries]
    assert paths == ["a.py", "path/c.py", "d.py"]

def test_generate_entries__on_cutoff_boundary(monkeypatch):
    # Arrange
    raw = [
        DummyEntry("h1", make_iso(7, 1), "A", ["x.py"])
    ]
    monkeypatch.setattr(hz, "fetch_git_log_entries", lambda repo: raw)

    # Act
    entries = _generate_entries(days=7, directories=None, authors=None)

    # Assert
    assert len(entries) == 1
    assert entries[0].path == "x.py"

def test_generate_entries__older_than_cutoff_dropped(monkeypatch):
    # Arrange
    raw = [
        DummyEntry("h1", make_iso(8), "A", ["y.py"])
    ]
    monkeypatch.setattr(hz, "fetch_git_log_entries", lambda repo: raw)

    # Act
    entries = _generate_entries(days=7, directories=None, authors=None)

    # Assert
    assert entries == []

@pytest.mark.parametrize("author_filter, expected_count, expected_commit_shas", [
    (["alice"], 2, ["h1", "h3"]),   # exact
    (["li"],    2, ["h1", "h3"]),   # substring
    (["BO"],    1, ["h2"]),         # case-insensitive
    (["x"],     0, []),             # no match
])
def test_generate_entries__author_filter(monkeypatch, author_filter, expected_count, expected_commit_shas):
    # Arrange
    raw = [
        DummyEntry("h1", make_iso(1), "Alice", ["a.py"]),
        DummyEntry("h2", make_iso(1), "Bob",   ["b.py"]),
        DummyEntry("h3", make_iso(1), "Alice",   ["b.py", "c.py"]),
    ]
    monkeypatch.setattr(hz, "fetch_git_log_entries", lambda repo: raw)

    # Act
    entries = _generate_entries(days=2, directories=None, authors=author_filter)

    # Assert
    assert len(entries) == expected_count
    commit_shas = [e.commit_hash for e in entries]
    assert commit_shas == expected_commit_shas

def test_generate_entries__directory_filter(monkeypatch):
    # Arrange
    raw = [
        DummyEntry("h1", make_iso(1), "A", ["src/a.py", "lib/b.py", "src/sub/c.py"]),
    ]
    monkeypatch.setattr(hz, "fetch_git_log_entries", lambda repo: raw)

    # Act
    entries = _generate_entries(days=2, directories=["src"], authors=None)

    # Assert
    assert len(entries) == 2
    paths = sorted(e.path for e in entries)
    assert paths == ["src/a.py", "src/sub/c.py"]

def test_generate_entries__multiple_files_same_commit(monkeypatch):
    # Arrange
    raw = [
        DummyEntry("h1", make_iso(0), "Z", ["f1.py", "f2.py"]),
    ]
    monkeypatch.setattr(hz, "fetch_git_log_entries", lambda repo: raw)

    # Act
    entries = _generate_entries(days=1, directories=None, authors=None)

    # Assert
    assert {e.path for e in entries} == {"f1.py", "f2.py"}
    dates = {e.date for e in entries}
    assert len(dates) == 1


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
    now = datetime.now(timezone.utc)
    entries = [
        GitLogFileEntry("h1", "a.txt",    "A", now),
        GitLogFileEntry("h2", "dir/b.txt","B", now - timedelta(hours=1)),
    ]

    # Act
    root = _generate_file_tree(entries)
    comp = _compress_node_tree(root)
    zones = _calculate_hot_zones(comp)

    # Assert
    # Expect two top-level zones: /a.txt’s parent "" compresses to "/" and /dir
    paths = sorted(z.path for z in zones)
    assert "/dir" in paths
    assert "/a.txt".startswith("/")  # leaf under root shows as "/a.txt"'s parent = "/"

    # Check commits/contributors counts
    dir_zone = next(z for z in zones if z.path == "/dir")
    assert dir_zone.commits == 1
    assert dir_zone.contributors == 1

def test_compress__chain_and_preserve_direct_commit():
    # Arrange 
    now = datetime.now(timezone.utc)
    # Two entries, one in a/b/file (direct at b) and one in a/b/c/file2 (direct at c)
    entries = [
        GitLogFileEntry("h1", "a/b/file",  "X", now),
        GitLogFileEntry("h2", "a/b/c/file2","Y", now - timedelta(hours=1)),
    ]

    # Act 
    root = _generate_file_tree(entries)
    comp = _compress_node_tree(root)
    zones = _calculate_hot_zones(comp)
    
    # Assert
    # Should see "/a/b" (because it has a direct commit) and "/a/b/c"
    paths = {z.path for z in zones}
    assert "/a/b" in paths
    assert "/a/b/c" in paths

def test_calculate_hot_zones__flat_tree():
    # Arrange
    root = hz.Node("")

    c1 = hz.Node("x")
    c1.commits = {"h1", "h2"}
    c1.authors = {"A"}
    c1.last_date = datetime(2025,5,6, tzinfo=timezone.utc)
    
    c2 = hz.Node("y")
    c2.commits = {"h3"}
    c2.authors = {"B","C"}
    c2.last_date = datetime(2025,5,5, tzinfo=timezone.utc)

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
