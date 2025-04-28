from git import Commit
import pytest
from src.commands import show_activity
from typer import Exit
from rich.table import Table
from unittest.mock import patch

from tests.utils.commit_generator import generate_mock_commits
from tests.utils.repo_generator import generate_mock_repo

# ------------------------
# Tests for _validate_date_format
# ------------------------

def test_validate_date_format_valid():
    # Should not raise
    show_activity._validate_date_format("2025-04-01", "2025-04-27")

def test_validate_date_format_invalid():
    with pytest.raises(Exit):
        show_activity._validate_date_format("04-01-2025", "2025-04-27")


# ------------------------
# Tests for _generate_activity_table
# ------------------------

def test_generate_activity_table():
    number_of_commits = 5

    mock_commits = generate_mock_commits(number_of_commits)

    table = show_activity._generate_activity_table("2025-04-01", "2025-04-30", mock_commits)

    assert isinstance(table, Table)
    assert table.row_count == number_of_commits


def test_generate_activity_table_empty():
    mock_commits = []

    table = show_activity._generate_activity_table("2025-04-01", "2025-04-30", mock_commits)

    assert isinstance(table, Table)
    assert table.row_count == 0

# ------------------------
# Tests for _get_commits
# ------------------------
@patch("src.commands.show_activity.Repo")
def test_get_commits(mock_repo_class):
    number_of_commits = 5
    start = "2025-04-01"
    end = "2025-04-30"

    mock_repo = generate_mock_repo()
    commits = generate_mock_commits(
        number_of_commits,
        start,
        end
    )

    mock_repo.iter_commits.return_value = commits
    mock_repo_class.return_value = mock_repo 

    commits = show_activity._fetch_commits(start, end)

    assert len(commits) == number_of_commits
    assert all(isinstance(commit, Commit) for commit in commits)