from git import Actor, Commit
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from collections import Counter

from gitwit.commands.show_activity import (
    _compute_file_statistics,
    _compute_author_activity_statistics,
    FileStats,
    AuthorActivityStats,
)

FIXED_NOW = datetime(2023, 1, 1, 12, 0, 0)


@pytest.fixture
def commit_data():
    author1 = MagicMock(spec=Actor)
    author1.name = "Alice"
    author2 = MagicMock(spec=Actor)
    author2.name = "Bob"

    commit1 = MagicMock(spec=Commit)
    commit1.committed_datetime = FIXED_NOW - timedelta(days=2)
    commit1.author = author1
    commit1.stats.files = {"file1.py": {"lines": 10}}

    commit2 = MagicMock(spec=Commit)
    commit2.committed_datetime = FIXED_NOW - timedelta(days=1)
    commit2.author = author2
    commit2.stats.files = {"file2.py": {"lines": 5}}

    return {
        "commit1": commit1,
        "commit2": commit2,
    }


# ====================================================
# Tests for: _compute_file_statistics()
# ====================================================


@pytest.mark.parametrize(
    "commit_keys, expected_commit_count, expected_lines",
    [
        (["commit1", "commit2"], 2, {"file1.py": 10, "file2.py": 5}),
        ([], 0, {}),
        (["commit1"], 1, {"file1.py": 10}),
    ],
)
def test_compute_file_statistics_cases(
    commit_data, commit_keys, expected_commit_count, expected_lines
):
    # Arrange
    mock_commits = [commit_data[key] for key in commit_keys]

    # Act
    stats_list = _compute_file_statistics(mock_commits)

    # Assert
    # List of FileStats
    assert isinstance(stats_list, list)
    assert all(isinstance(fs, FileStats) for fs in stats_list)

    # Commit counts and total lines
    assert sum(fs.commits for fs in stats_list) == expected_commit_count
    assert sum(fs.lines for fs in stats_list) == sum(expected_lines.values())

    # Per-file lines mapping
    result_map = {fs.file: fs.lines for fs in stats_list}
    assert result_map == expected_lines


# ====================================================
# Tests for: _compute_author_activity_statistics()
# ====================================================


@pytest.mark.parametrize(
    "commit_keys, expected_commit_count, expected_counter",
    [
        (["commit1", "commit2"], 2, Counter({"Alice": 1, "Bob": 1})),
        ([], 0, Counter()),
        (["commit2"], 1, Counter({"Bob": 1})),
    ],
)
def test_compute_author_activity_statistics_cases(
    commit_data, commit_keys, expected_commit_count, expected_counter
):
    # Arrange
    mock_commits = [commit_data[key] for key in commit_keys]

    # Act
    stats = _compute_author_activity_statistics(mock_commits)

    # Assert

    # Return type
    assert isinstance(stats, AuthorActivityStats)

    # Basic counts
    assert stats.total_commits == expected_commit_count
    assert stats.num_authors == len(expected_counter)

    # Top contributor
    if expected_counter:
        top, count = expected_counter.most_common(1)[0]
    else:
        top, count = "", 0
    assert stats.top_contributor == top
    assert stats.top_contributor_commits == count

    # Total lines
    total_lines = sum(
        details.get("lines", 0)
        for commit in mock_commits
        for details in commit.stats.files.values()
    )
    assert stats.total_lines == total_lines

    # Last commit date
    if mock_commits:
        expected_last = max(c.committed_datetime for c in mock_commits).strftime("%Y-%m-%d")
    else:
        expected_last = "N/A"
    assert stats.last_commit_date == expected_last
