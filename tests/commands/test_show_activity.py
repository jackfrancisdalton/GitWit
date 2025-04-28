from datetime import datetime
import pytest
from typer import Exit
from unittest.mock import patch
from src.commands.show_activity import command
from tests.mock_generators.commit_generator import generate_mock_commits

@pytest.fixture
def mock_convert_to_datetime():
    with patch("src.commands.show_activity.convert_to_datetime") as mock:
        yield mock

@pytest.fixture
def mock_fetch_commits_in_date_range():
    with patch("src.commands.show_activity.fetch_commits_in_date_range") as mock:
        yield mock

@pytest.fixture
def mock_console_print():
    with patch("src.commands.show_activity.console.print") as mock:
        yield mock

def test_no_commits_raises_exit_and_prints_warning(
    mock_convert_to_datetime,
    mock_fetch_commits_in_date_range,
    mock_console_print,
):
    # Arrange
    str_since = "2025-04-10"
    str_until = "2025-04-20"

    dt_since = datetime(2025, 4, 10)
    dt_until = datetime(2025, 4, 20)

    return_mapping = { str_since: dt_since, str_until: dt_until }
    mock_convert_to_datetime.side_effect = lambda s: return_mapping[s]

    mock_fetch_commits_in_date_range.return_value = []

    # Act & Assert: should exit after printing warning
    with pytest.raises(Exit):
        command(since=str_since, until=str_until)

    assert mock_convert_to_datetime.call_count == 2
    mock_fetch_commits_in_date_range.assert_called_once_with(dt_since, dt_until)
    mock_console_print.assert_called_once_with("[yellow]No commits found in this date range.[/yellow]")

def test_multiple_commits_prints_table_and_summary(
    mock_convert_to_datetime,
    mock_fetch_commits_in_date_range,
    mock_console_print,
):
    # Arrange
    str_since = "2025-04-10"
    str_until = "2025-04-20"

    dt_since = datetime(2025, 4, 10)
    dt_until = datetime(2025, 4, 20)

    return_mapping = { str_since: dt_since, str_until: dt_until,}
    mock_convert_to_datetime.side_effect = lambda s: return_mapping[s]

    commits = generate_mock_commits(2, start=str_since, end=str_until)
    commits[0].message = b"Fix critical bug\n" # force one message to be bytes to cover that edge case
    mock_fetch_commits_in_date_range.return_value = commits

    # Act
    command(since=str_since, until=str_until)

    # Assert
    assert mock_convert_to_datetime.call_count == 2
    mock_fetch_commits_in_date_range.assert_called_once_with(dt_since, dt_until)

    assert mock_console_print.call_count == 2  # Check for table and summary print out

    table_arg = mock_console_print.call_args_list[0][0][0]
    assert hasattr(table_arg, "title")
    assert table_arg.title == f"Commits from {str_since} to {str_until}"

    summary_arg = mock_console_print.call_args_list[1][0][0]
    assert summary_arg == f"\n[bold green]Summary:[/bold green] {len(commits)} commits."

def test_invalid_date_format_exits_and_prints_error(
    mock_convert_to_datetime,
    mock_fetch_commits_in_date_range,
    mock_console_print,
):
    # Arrange
    since_arg = "2025-04-10"
    until_arg = "2025-04-20"

    error_message = "Invalid date format"
    mock_convert_to_datetime.side_effect = ValueError(error_message)

    # Act & Assert
    with pytest.raises(Exit):
        command(since=since_arg, until=until_arg)

    mock_convert_to_datetime.assert_called_once_with(since_arg)
    mock_fetch_commits_in_date_range.assert_not_called()
    mock_console_print.assert_called_once_with(f"[red]Error: {error_message}[/red]")
