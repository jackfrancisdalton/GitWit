import pytest
from datetime import datetime
from typer import Exit as TyperExit

import commands.who_is_the_expert as file_expert
from commands.who_is_the_expert import _compute_author_activity, _gather_blame_entries

class DummyBlame:
    def __init__(self, author, author_time, summary, num_lines):
        self.author = author
        self.author_time = author_time
        self.summary = summary
        self.num_lines = num_lines

@pytest.fixture
def tmp_file(tmp_path):
    p = tmp_path / "dummy.py"
    p.write_text("print('hello')")
    return p

@pytest.fixture
def tmp_dir(tmp_path):
    d = tmp_path / "test_dir"
    d.mkdir()
    f1 = d / "f1.py"
    f2 = d / "f2.py"
    f1.write_text("# file1")
    f2.write_text("# file2")
    return d

# --- Tests for the command function ---

def test_command_file_not_exists(tmp_path):
    missing = tmp_path / "noexist.py"
    with pytest.raises(TyperExit):
        file_expert.command(str(missing))


def test_command_fetch_error(tmp_file, monkeypatch):
    monkeypatch.setattr(
        file_expert,
        "fetch_file_gitblame",
        lambda repo, path: (_ for _ in ()).throw(Exception("Git blame failed"))
    )
    with pytest.raises(TyperExit):
        file_expert.command(str(tmp_file))


def test_command_empty(tmp_file, monkeypatch):
    monkeypatch.setattr(
        file_expert,
        "fetch_file_gitblame",
        lambda repo, path: []
    )
    with pytest.raises(TyperExit):
        file_expert.command(str(tmp_file))


def test_command_file_success(tmp_file, monkeypatch, capsys):
    # Single blame entry for file
    blame = DummyBlame("Alice", 100, "init commit", 4)
    monkeypatch.setattr(
        file_expert,
        "fetch_file_gitblame",
        lambda repo, path: [blame]
    )
    # Limit results to 1
    file_expert.command(str(tmp_file), num_results=1)
    captured = capsys.readouterr()
    assert "Alice" in captured.out
    assert "4" in captured.out
    assert str(tmp_file) in captured.out


def test_command_dir_success(tmp_dir, monkeypatch, capsys):
    # Simulate each file returning a single blame entry with author as filename
    def fake_blame(repo, path):
        name = path.name
        return [DummyBlame(name, 50, f"edit {name}", 1)]

    monkeypatch.setattr(
        file_expert,
        "fetch_file_gitblame",
        fake_blame
    )
    file_expert.command(str(tmp_dir), num_results=2)
    out = capsys.readouterr().out
    # Should include directory path in title
    assert str(tmp_dir) in out
    # Both files' authors (names) should appear
    assert "f1.py" in out
    assert "f2.py" in out

# --- Tests for helper functions ---

def test_gather_blame_entries_file(tmp_file, monkeypatch):
    bm = DummyBlame("A", 123, "msg", 2)
    def fake(repo, path):
        assert path == tmp_file
        return [bm]
    monkeypatch.setattr(
        file_expert,
        "fetch_file_gitblame",
        fake
    )
    repo = file_expert.Repo(".", search_parent_directories=True)
    entries = _gather_blame_entries(repo, tmp_file)
    assert entries == [bm]


def test_gather_blame_entries_dir(tmp_dir, monkeypatch):
    b1 = DummyBlame("X", 10, "m1", 1)
    b2 = DummyBlame("Y", 20, "m2", 2)
    def fake(repo, path):
        if path.name == "f1.py":
            return [b1]
        elif path.name == "f2.py":
            return [b2]
        return []

    monkeypatch.setattr(
        file_expert,
        "fetch_file_gitblame",
        fake
    )
    repo = file_expert.Repo(".", search_parent_directories=True)
    entries = _gather_blame_entries(repo, tmp_dir)

    assert b1 in entries
    assert b2 in entries


def test_compute_author_activity_empty():
    assert _compute_author_activity([]) == []


def test_compute_author_activity_aggregation():
    a1 = DummyBlame("Alice", 100, "start", 2)
    a2 = DummyBlame("Alice", 150, "later", 3)
    b = DummyBlame("Bob", 120, "fix", 1)
    result = _compute_author_activity([a1, a2, b])
    data = {d.author: d for d in result}

    alice = data["Alice"]
    assert alice.line_count == 5
    assert alice.last_commit_message == "later"
    assert alice.last_commit_date == datetime.fromtimestamp(150)

    bob = data["Bob"]
    assert bob.line_count == 1
    assert bob.last_commit_message == "fix"
    assert bob.last_commit_date == datetime.fromtimestamp(120)
