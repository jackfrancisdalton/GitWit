from utils.fetch_git_log_entries import fetch_git_log_entries

class DummyRepo:
    """Mocks Repo for git.log() calls."""
    def __init__(self, raw_log):
        self.git = self
        self._raw = raw_log

    def log(self, *args, **kwargs):
        return self._raw

def test_convert_git_log_to_log_blocks__single_file_and_multiple_file_commits():
    # Arrange
    raw = (
        "abcd1234\x002025-05-01T12:00:00+00:00\x00Alice\n"
        "file1.py\n"
        "file2.txt\n"
        "efgh5678\x002025-04-28T09:30:00+00:00\x00Bob\n"
        "src/main.py\n"
    )

    repo = DummyRepo(raw)

    # Act
    log_blocks = fetch_git_log_entries(repo)

    # Assert
    assert len(log_blocks) == 2

    assert log_blocks[0].commit_hash == "abcd1234"
    assert log_blocks[0].created_at_iso == "2025-05-01T12:00:00+00:00"
    assert log_blocks[0].author == "Alice"
    assert log_blocks[0].files == ["file1.py", "file2.txt"]

    assert log_blocks[1].commit_hash == "efgh5678"
    assert log_blocks[1].created_at_iso == "2025-04-28T09:30:00+00:00"
    assert log_blocks[1].author == "Bob"
    assert log_blocks[1].files == ["src/main.py"]

def test_convert_git_log_to_log_blocks__no_commits():
    # Arrange
    raw = ("")
    repo = DummyRepo(raw)

    # Act
    log_blocks = fetch_git_log_entries(repo)

    # Assert
    assert len(log_blocks) == 0