from git import Commit
import pytest
from src.commands import show_activity
from typer import Exit
from rich.table import Table
from unittest.mock import patch, MagicMock
from datetime import datetime

from tests.utils.test_commit_generator import generate_mock_commits

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