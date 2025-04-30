import pytest
from datetime import datetime
from typer import Exit as TyperExit

import src.commands.who_is_the_expert as file_expert
from src.commands.who_is_the_expert import _compute_author_activity_data

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

def test_compute_author_activity_data_file_not_exists(tmp_path):
    missing = tmp_path / "noexist.py"
    with pytest.raises(TyperExit):
        _compute_author_activity_data(missing)

def test_compute_author_activity_data_fetch_error(tmp_file, monkeypatch):
    monkeypatch.setattr(
        file_expert,
        "fetch_file_gitblame",
        lambda repo, path: (_ for _ in ()).throw(Exception("File Does not Exist"))
    )
    with pytest.raises(TyperExit):
        _compute_author_activity_data(tmp_file)

def test_compute_author_activity_data_empty(tmp_file, monkeypatch):
    monkeypatch.setattr(file_expert, "fetch_file_gitblame", lambda repo, path: [])
    result = _compute_author_activity_data(tmp_file)
    assert result == []

def test_compute_author_activity_data_present(tmp_file, monkeypatch):
    alice1 = DummyBlame("Alice", 100, "init", 3)
    alice2 = DummyBlame("Alice", 200, "update", 2)
    bob    = DummyBlame("Bob", 150, "fix", 5)

    monkeypatch.setattr(
        file_expert,
        "fetch_file_gitblame",
        lambda repo, path: [alice1, alice2, bob]
    )
    result = _compute_author_activity_data(tmp_file)

    data_map = {d.author: d for d in result}
    assert set(data_map) == {"Alice", "Bob"}

    a = data_map["Alice"]
    assert a.line_count == 5
    assert a.last_commit_message == "update"
    assert a.last_commit_date == datetime.fromtimestamp(200)

    b = data_map["Bob"]
    assert b.line_count == 5
    assert b.last_commit_message == "fix"
    assert b.last_commit_date == datetime.fromtimestamp(150)
