
from utils.fetch_tracked_git_file_paths import fetch_tracked_git_file_paths

class DummyRepo:
    """Mocks Repo for ls_files() calls."""
    def __init__(self, files):
        self.git = self
        self._files = files

    def ls_files(self):
        return "\n".join(self._files)

def test_get_list_of_matching_files__without_dirs():
    # Arrange
    files = [
        "app.py",
        "test_app.py",
        "README.md",
        "src/controller.py",
        "src/controller.pyi",
        "src/utils/helper.txt",
    ]
    repo = DummyRepo(files)

    # Act
    result = fetch_tracked_git_file_paths(repo, ".py", None)

    # Assert
    assert result == ["app.py", "test_app.py", "src/controller.py", "src/controller.pyi"]

def test_get_list_of_matching_files__with_dirs():
    # Arrange
    files = [
        "app.py",
        "test_app.py",
        "lib/app.py",
        "lib/test_lib.py",
        "lib/other.js",
        "other/app.py",
    ]

    repo = DummyRepo(files)

    # Act
    result = fetch_tracked_git_file_paths(repo, ".py", ["lib"])

    # Assert
    assert result == ["lib/app.py", "lib/test_lib.py"]


def test_get_list_of_matching_files__no_matches():
    # Arrange
    files = [
        "app.js",
        "app.go"
    ]
    repo = DummyRepo(files)

    # Act
    result = fetch_tracked_git_file_paths(repo, ".py", None)

    # Assert
    assert len(result) == 0