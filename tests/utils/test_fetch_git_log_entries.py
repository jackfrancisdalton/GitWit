from git import Repo
import pytest
from unittest.mock import MagicMock, patch
from gitwit.utils.fetch_git_log_entries import fetch_git_log_entries_of_added_files
from gitwit.models.git_log_entry import GitLogEntry


@pytest.fixture
def mock_repo():
    with patch("gitwit.utils.repo_singleton.RepoSingleton.get_repo") as mock_get_repo:
        mock_repo_instance = MagicMock(spec=Repo)
        mock_get_repo.return_value = mock_repo_instance
        yield mock_repo_instance


def test_fetch_git_log_entries__commit_with_multiple_files(mock_repo):
    mock_repo.git.log.return_value = (
        "hash1\x002023-01-01T12:00:00Z\x00Rand al'Thor\n" "file1.txt\n" "file2.txt\n"
    )

    result = fetch_git_log_entries_of_added_files()

    assert len(result) == 1
    assert result[0] == GitLogEntry(
        commit_hash="hash1",
        created_at_iso="2023-01-01T12:00:00Z",
        author="Rand al'Thor",
        files=["file1.txt", "file2.txt"],
    )


def test_fetch_git_log_entries__multiple_commits(mock_repo):
    mock_repo.git.log.return_value = (
        "hash1\x002023-01-01T12:00:00Z\x00Moiraine Damodred\n"
        "file1.txt\n"
        "file2.txt\n"
        "hash2\x002023-01-02T13:00:00Z\x00al'Lan Mandragoran\n"
        "file3.txt\n"
    )

    result = fetch_git_log_entries_of_added_files()

    assert len(result) == 2
    assert result[0] == GitLogEntry(
        commit_hash="hash1",
        created_at_iso="2023-01-01T12:00:00Z",
        author="Moiraine Damodred",
        files=["file1.txt", "file2.txt"],
    )
    assert result[1] == GitLogEntry(
        commit_hash="hash2",
        created_at_iso="2023-01-02T13:00:00Z",
        author="al'Lan Mandragoran",
        files=["file3.txt"],
    )


def test_fetch_git_log__commit_with_no_files(mock_repo):
    mock_repo.git.log.return_value = "hash1\x002023-01-01T12:00:00Z\x00Mat Cauthon\n"

    result = fetch_git_log_entries_of_added_files()

    assert len(result) == 1
    assert result[0] == GitLogEntry(
        commit_hash="hash1",
        created_at_iso="2023-01-01T12:00:00Z",
        author="Mat Cauthon",
        files=[],
    )


def test_fetch_git_log_entries_of_added_files_no_commits(mock_repo):
    mock_repo.git.log.return_value = ""

    result = fetch_git_log_entries_of_added_files()

    assert result == []
