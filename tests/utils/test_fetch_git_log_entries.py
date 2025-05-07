import pytest
from unittest.mock import MagicMock, patch
from gitwit.utils.fetch_git_log_entries import fetch_git_log_entries_of_added_files
from gitwit.models.git_log_entry import GitLogEntry
from gitwit.utils.repo_singleton import RepoSingleton

@pytest.fixture
def mock_repo():
    with patch('gitwit.utils.repo_singleton.RepoSingleton.get_repo') as mock_get_repo:
        mock_repo_instance = MagicMock()
        mock_get_repo.return_value = mock_repo_instance
        yield mock_repo_instance


def test_fetch_git_log_entries_of_added_files_single_commit(mock_repo):
    mock_repo.git.log.return_value = (
        "abc123\x002023-01-01T12:00:00Z\x00John Doe\n"
        "file1.txt\n"
        "file2.txt\n"
    )

    result = fetch_git_log_entries_of_added_files()

    assert len(result) == 1
    assert result[0] == GitLogEntry(
        commit_hash="abc123",
        created_at_iso="2023-01-01T12:00:00Z",
        author="John Doe",
        files=["file1.txt", "file2.txt"]
    )


def test_fetch_git_log_entries_of_added_files_multiple_commits(mock_repo):
    mock_repo.git.log.return_value = (
        "abc123\x002023-01-01T12:00:00Z\x00John Doe\n"
        "file1.txt\n"
        "file2.txt\n"
        "def456\x002023-01-02T13:00:00Z\x00Jane Smith\n"
        "file3.txt\n"
    )

    result = fetch_git_log_entries_of_added_files()

    assert len(result) == 2
    assert result[0] == GitLogEntry(
        commit_hash="abc123",
        created_at_iso="2023-01-01T12:00:00Z",
        author="John Doe",
        files=["file1.txt", "file2.txt"]
    )
    assert result[1] == GitLogEntry(
        commit_hash="def456",
        created_at_iso="2023-01-02T13:00:00Z",
        author="Jane Smith",
        files=["file3.txt"]
    )


def test_fetch_git_log_entries_of_added_files_no_commits(mock_repo):
    mock_repo.git.log.return_value = ""

    result = fetch_git_log_entries_of_added_files()

    assert result == []


def test_fetch_git_log_entries_of_added_files_commit_with_no_files(mock_repo):
    mock_repo.git.log.return_value = (
        "abc123\x002023-01-01T12:00:00Z\x00John Doe\n"
    )

    result = fetch_git_log_entries_of_added_files()

    assert len(result) == 1
    assert result[0] == GitLogEntry(
        commit_hash="abc123",
        created_at_iso="2023-01-01T12:00:00Z",
        author="John Doe",
        files=[]
    )