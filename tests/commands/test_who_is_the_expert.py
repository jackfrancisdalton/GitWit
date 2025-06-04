import pytest
from datetime import datetime
from pathlib import Path
from git.cmd import Git
from typer import Exit as TyperExit

import gitwit.commands.who_is_the_expert as file_expert
from gitwit.commands.who_is_the_expert import (
    _compute_author_activity,
    _gather_blame_entries,
)


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


# ====================================================
# Tests for: command()
# ====================================================


def test_command_file_not_exists(tmp_path):
    missing = tmp_path / "noexist.py"
    with pytest.raises(TyperExit):
        file_expert.command(str(missing))


def test_command_fetch_error(tmp_file, monkeypatch):
    monkeypatch.setattr(
        file_expert,
        "fetch_file_gitblame",
        lambda path: (_ for _ in ()).throw(Exception("Git blame failed")),
    )
    with pytest.raises(TyperExit):
        file_expert.command(str(tmp_file))


def test_command_empty(tmp_file, monkeypatch):
    monkeypatch.setattr(file_expert, "fetch_file_gitblame", lambda path: [])
    with pytest.raises(TyperExit):
        file_expert.command(str(tmp_file))


def test_command_file_success(tmp_file, monkeypatch, capsys):
    # Single blame entry for file
    blame = DummyBlame("Alice", 100, "init commit", 4)
    monkeypatch.setattr(file_expert, "fetch_file_gitblame", lambda path: [blame])
    # Limit results to 1
    file_expert.command(str(tmp_file), num_results=1)
    captured = capsys.readouterr()
    assert "Alice" in captured.out
    assert "4" in captured.out
    assert str(tmp_file) in captured.out


def test_command_dir_success(tmp_dir, monkeypatch, capsys):
    # Monkeypatch git ls-files to return our test files
    monkeypatch.setattr(
        Git,
        "ls_files",
        lambda self, path: "\n".join(
            [
                str(Path(path) / "f1.py"),
                str(Path(path) / "f2.py"),
            ]
        ),
        raising=False,
    )

    # Simulate each file returning a single blame entry with author as filename
    def fake_blame(path):
        name = Path(path).name
        return [DummyBlame(name, 50, f"edit {name}", 1)]

    monkeypatch.setattr(file_expert, "fetch_file_gitblame", fake_blame)
    file_expert.command(str(tmp_dir), num_results=2)
    out = capsys.readouterr().out
    # Should include directory path in title
    assert str(tmp_dir) in out
    # Both files' authors (names) should appear
    assert "f1.py" in out
    assert "f2.py" in out


# ====================================================
# Tests for: _gather_blame_entries()
# ====================================================


def test_gather_blame_entries__file(tmp_file, monkeypatch):
    # Arrange
    bm = DummyBlame("A", 123, "msg", 2)

    def fake(path):
        assert Path(path) == tmp_file
        return [bm]

    monkeypatch.setattr(file_expert, "fetch_file_gitblame", fake)
    entries = _gather_blame_entries(tmp_file)

    # Assert
    assert entries == [bm]


def test_gather_blame_entries__dir(tmp_dir, monkeypatch):
    # Monkeypatch git ls-files to return our test files
    monkeypatch.setattr(
        Git,
        "ls_files",
        lambda self, path: "\n".join(
            [
                str(Path(path) / "f1.py"),
                str(Path(path) / "f2.py"),
            ]
        ),
        raising=False,
    )
    # Arrange
    b1 = DummyBlame("X", 10, "m1", 1)
    b2 = DummyBlame("Y", 20, "m2", 2)

    def fake(path):
        name = Path(path).name
        if name == "f1.py":
            return [b1]
        elif name == "f2.py":
            return [b2]
        return []

    monkeypatch.setattr(file_expert, "fetch_file_gitblame", fake)
    entries = _gather_blame_entries(tmp_dir)

    # Assert
    assert len(entries) == 2
    assert b1 in entries
    assert b2 in entries


# ====================================================
# Tests for: _compute_author_activity()
# ====================================================


def test_compute_author_activity__empty():
    assert _compute_author_activity([]) == []


def test_compute_author_activity__aggregation():
    # Arrange
    a1 = DummyBlame("Alice", 100, "start", 2)
    a2 = DummyBlame("Alice", 150, "later", 3)
    b = DummyBlame("Bob", 120, "fix", 1)

    # Act
    result = _compute_author_activity([a1, a2, b])

    # Assert
    assert len(result) == 2
    data = {d.author: d for d in result}

    alice = data["Alice"]
    assert alice.line_count == 5
    assert alice.last_commit_message == "later"
    assert alice.last_commit_date == datetime.fromtimestamp(150)

    bob = data["Bob"]
    assert bob.line_count == 1
    assert bob.last_commit_message == "fix"
    assert bob.last_commit_date == datetime.fromtimestamp(120)
