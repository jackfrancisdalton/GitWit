import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from gitwit.utils.git_helpers import (
    get_filtered_commits,
    fetch_file_paths_tracked_by_git,
    fetch_file_gitblame,
    BlameFetchError
)
from gitwit.models.blame_line import BlameLine
from git import Commit, Repo
from pathlib import Path

FIXED_NOW = datetime(2023, 1, 1, 12, 0, 0)

@pytest.fixture
def mock_repo():
    with patch('gitwit.utils.repo_singleton.RepoSingleton.get_repo') as mock_get_repo:
        mock_repo_instance = MagicMock(spec=Repo)
        mock_get_repo.return_value = mock_repo_instance
        yield mock_repo_instance

@pytest.mark.parametrize("authors, commit_author, expected_match", [
    (["jack"], "Jack Sparrow", True), # First name
    (["ja"], "Jane Doe", True),       # Substring prefix of first name
    (["ja"], "Raja", True),           # Substring in middle of first name
    (["ja"], "Michael", False),       # Substring not in name
    (["smith"], "Jane Smith", True),  # Last name match
    (["John Doe"], "John Doe", True), # Exact match (including caps)
    (["jOHn dOe"], "John Doe", True),     # CApitalisation mismatch
])
def test_get_filtered_commits__author_filter(mock_repo, authors, commit_author, expected_match):
    commit = MagicMock(spec=Commit)
    commit.author.name = commit_author
    mock_repo.iter_commits.return_value = [commit]

    since = FIXED_NOW - timedelta(days=1)
    until = FIXED_NOW

    results = list(get_filtered_commits(since, until, authors=authors))

    if expected_match:
        assert len(results) == 1
        assert results[0] == commit
    else:
        assert len(results) == 0

@pytest.mark.parametrize("directories, file_paths, expected_match", [
    (["src"], ["src/main.py", "README.md"], True),
    (["tests"], ["src/test.py", "tests/test_main.py"], True),
    (["docs"], ["src/main.py", "README.md"], False),
    (["src/subdir"], ["src/subdir/file.py"], True),
    (["src"], ["lib/file.py"], False),
])
def test_get_filtered_commits__directory_filter(mock_repo, directories, file_paths, expected_match):
    commit = MagicMock(spec=Commit)
    commit.stats.files = {f: {} for f in file_paths}
    mock_repo.iter_commits.return_value = [commit]

    since = FIXED_NOW - timedelta(days=1)
    until = FIXED_NOW

    results = list(get_filtered_commits(since, until, directories=directories))

    if expected_match:
        assert len(results) == 1
        assert results[0] == commit
    else:
        assert len(results) == 0

@pytest.mark.parametrize("pattern, directories, expected_result", [
    ("test", ["tests"], ["tests/test_main.py"]),
    ("main", ["src"], ["src/main.py"]),
    ("md", [], ["README.md"]),
    ("nonexistent", [], []),
])
def test_fetch_file_paths_tracked_by_git(mock_repo, pattern, directories, expected_result):
    mock_repo.git.ls_files.return_value = "src/main.py\ntests/test_main.py\nREADME.md"

    result = fetch_file_paths_tracked_by_git(pattern, directories)
    assert result == expected_result

def test_fetch_file_gitblame__success(mock_repo):
    mock_repo.git.blame.return_value = "\n".join([
        "abcdef1 1 2",                           
        "author John Doe",
        "author-mail <john@example.com>",
        "author-time 1609459200",
        "author-tz +0100",
        "committer Jane Doe",
        "committer-mail <jane@example.com>",
        "committer-time 1609459201",
        "committer-tz +0000",
        "summary initial import",
        "filename src/main.py",
        "\tline content in blame entry"
    ])

    result = fetch_file_gitblame(mock_repo, Path("src/main.py"))

    assert len(result) == 1
    assert isinstance(result[0], BlameLine)

    assert result[0].commit == "abcdef1"
    assert result[0].orig_lineno == 1
    assert result[0].final_lineno == 2
    assert result[0].num_lines == 1
    assert result[0].author == "John Doe"
    assert result[0].author_mail == "<john@example.com>"
    assert result[0].author_time == 1609459200
    assert result[0].author_tz == "+0100"
    assert result[0].committer == "Jane Doe"
    assert result[0].committer_mail == "<jane@example.com>"
    assert result[0].committer_time == 1609459201
    assert result[0].committer_tz == "+0000"
    assert result[0].summary == "initial import"
    assert result[0].filename == "src/main.py"
    assert result[0].content == "line content in blame entry"


def test_fetch_file_gitblame__error(mock_repo):
    mock_repo.git.blame.side_effect = Exception("git blame failed")

    with pytest.raises(BlameFetchError, match="failed to fetch or parse blame"):
        fetch_file_gitblame(mock_repo, Path("src/main.py"))
