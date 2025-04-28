from git import Commit
import pytest
from src.commands import show_activity
from typer import Exit
from rich.table import Table
from unittest.mock import patch, MagicMock
from datetime import datetime

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
    fake_commit = MagicMock(spec=Commit)
    fake_commit.committed_datetime = datetime(2025, 4, 25)
    fake_commit.author.name = "jack_smith"
    fake_commit.message.strip.return_value = "Add payment feature"

    commits = [fake_commit]

    table = show_activity._generate_activity_table("2025-04-01", "2025-04-30", commits)

    assert isinstance(table, Table)
    assert table.row_count == 1