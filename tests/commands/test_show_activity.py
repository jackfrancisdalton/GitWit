import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta, timezone
from collections import Counter
from src.commands.show_activity import (
    _compute_file_statistics,
    _compute_author_activity_statistics,
)

@pytest.fixture
def commit_data():
    author1 = MagicMock()
    author1.name = "Alice"

    author2 = MagicMock()
    author2.name = "Bob"

    commit1 = MagicMock()
    commit1.committed_datetime = datetime.now(timezone.utc) - timedelta(days=2)
    commit1.author = author1
    commit1.stats.files = {"file1.py": {"lines": 10}}

    commit2 = MagicMock()
    commit2.committed_datetime = datetime.now(timezone.utc) - timedelta(days=1)
    commit2.author = author2
    commit2.stats.files = {"file2.py": {"lines": 5}}

    return {
        "commit1": commit1,
        "commit2": commit2,
    }

@pytest.mark.parametrize(
    "commit_keys, expected_commit_count, expected_lines, since_offset, until_offset",
    [
        (["commit1", "commit2"], 2, {"file1.py": 10, "file2.py": 5}, -5, 0),
        ([], 0, {}, -5, 0),
        (["commit1", "commit2"], 0, {}, -10, -8),
    ],
)
def test_compute_file_statistics_cases(commit_data, commit_keys, expected_commit_count, expected_lines, since_offset, until_offset):
    since_date = datetime.now(timezone.utc) + timedelta(days=since_offset)
    until_date = datetime.now(timezone.utc) + timedelta(days=until_offset)

    commits = [commit_data[key] for key in commit_keys]
    stats = _compute_file_statistics(commits, since_date, until_date)

    assert sum(file["commits"] for file in stats.values()) == expected_commit_count
    total_lines = sum(file["lines"] for file in stats.values())
    assert total_lines == sum(expected_lines.values())

@pytest.mark.parametrize(
    "commit_keys, expected_commit_count, expected_counter, since_offset, until_offset",
    [
        (["commit1", "commit2"], 2, Counter({"Alice": 1, "Bob": 1}), -5, 0),
        ([], 0, Counter(), -5, 0),
        (["commit1", "commit2"], 0, Counter(), -10, -8),
    ],
)
def test_compute_activity_summary_cases(commit_data, commit_keys, expected_commit_count, expected_counter, since_offset, until_offset):
    since_date = datetime.now(timezone.utc) + timedelta(days=since_offset)
    until_date = datetime.now(timezone.utc) + timedelta(days=until_offset)

    commits = [commit_data[key] for key in commit_keys]
    filtered_commits, author_counter = _compute_author_activity_statistics(commits, since_date, until_date)

    assert len(filtered_commits) == expected_commit_count
    assert author_counter == expected_counter


# TODO: figure outhow to test rich tables