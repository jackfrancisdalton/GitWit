import pytest
from datetime import datetime

import gitwit.commands.latest_examples_of as latest
import gitwit.utils.repo_singleton as repo_singleton


class DummyRepo:
    """Mocks Repo for ls_files() calls."""

    def __init__(self, files):
        self.git = self
        self._files = files

    def ls_files(self):
        return "\n".join(self._files)


class DummyRepoLog:
    """Mocks Repo for git.log() calls."""

    def __init__(self, raw_log):
        self.git = self
        self._raw = raw_log

    def log(self, *args, **kwargs):
        return self._raw

    def ls_files(self):
        return ""


@pytest.fixture
def patch_repo_ls(monkeypatch):
    """Patch RepoSingleton.get_repo so ls_files returns our list."""

    def _patch(files):
        # 1) clear any cached real repo
        repo_singleton.RepoSingleton._repo = None
        # 2) patch get_repo to return our DummyRepo
        monkeypatch.setattr(
            repo_singleton.RepoSingleton,
            "get_repo",
            classmethod(lambda cls: DummyRepo(files)),
        )

    return _patch


@pytest.fixture
def patch_repo_log(monkeypatch):
    """Patch RepoSingleton.get_repo so git.log returns our raw log."""

    def _patch(raw_log):
        # 1) clear any cached real repo
        repo_singleton.RepoSingleton._repo = None
        # 2) patch get_repo to return our DummyRepoLog
        monkeypatch.setattr(
            repo_singleton.RepoSingleton,
            "get_repo",
            classmethod(lambda cls: DummyRepoLog(raw_log)),
        )

    return _patch


# =====================================================
# Tests for _hydrate_examples_and_filter_based_on_git_data
# =====================================================


def test_hydrate_examples_and_filter_based_on_git_data__no_filter(patch_repo_log):
    # Arrange
    raw = (
        "h1\x002025-05-02T11:00:00+00:00\x00Carol\n"
        "foo.py\n"
        "h2\x002025-05-03T12:30:00+00:00\x00Dave\n"
        "bar.py\n"
    )
    patch_repo_log(raw)

    # Act
    examples = latest._hydrate_examples_and_filter_based_on_git_data(
        ["foo.py", "bar.py"], None
    )

    # Assert
    assert len(examples) == 2

    assert examples[0].path == "foo.py"
    assert examples[0].author == "Carol"
    assert examples[0].created_at == datetime.fromisoformat("2025-05-02T11:00:00+00:00")

    assert examples[1].path == "bar.py"
    assert examples[1].author == "Dave"
    assert examples[1].created_at == datetime.fromisoformat("2025-05-03T12:30:00+00:00")


def test_hydrate_examples_and_filter_based_on_git_data__author_filter_with_exact_match(
    patch_repo_log,
):
    # Arrange
    raw = (
        "h1\x002025-05-02T11:00:00+00:00\x00Carol\n"
        "foo.py\n"
        "h2\x002025-05-03T12:30:00+00:00\x00Dave\n"
        "bar.py\n"
    )
    patch_repo_log(raw)

    # Act
    examples = latest._hydrate_examples_and_filter_based_on_git_data(
        ["foo.py", "bar.py"], ["Dave"]
    )

    # Assert
    assert len(examples) == 1
    assert examples[0].path == "bar.py"
    assert examples[0].author == "Dave"


def test_hydrate_examples_and_filter_based_on_git_data__author_filter_with_sub_string(
    patch_repo_log,
):
    # Arrange
    raw = (
        "h1\x002025-05-02T11:00:00+00:00\x00Jack\n"
        "foo.py\n"
        "h2\x002025-05-03T12:30:00+00:00\x00Jane\n"
        "bar.py\n"
        "h3\x002025-05-03T12:30:00+00:00\x00James\n"
        "zoo.py\n"
    )
    patch_repo_log(raw)

    # Act
    examples = latest._hydrate_examples_and_filter_based_on_git_data(
        ["foo.py", "bar.py", "zoo.py"], ["ja"]
    )

    # Assert
    assert len(examples) == 3

    assert examples[0].path == "foo.py"
    assert examples[0].author == "Jack"
    assert examples[0].created_at == datetime.fromisoformat("2025-05-02T11:00:00+00:00")

    assert examples[1].path == "bar.py"
    assert examples[1].author == "Jane"
    assert examples[1].created_at == datetime.fromisoformat("2025-05-03T12:30:00+00:00")

    assert examples[2].path == "zoo.py"
    assert examples[2].author == "James"
    assert examples[2].created_at == datetime.fromisoformat("2025-05-03T12:30:00+00:00")


# =====================================================
# Tests for _find_latest_examples_of_matching_files
# =====================================================


def test_find_latest_examples_no_matching_files(patch_repo_ls, patch_repo_log):
    # Arrange: ls_files returns no .py files
    files = ["foo.txt", "bar.js"]
    patch_repo_ls(files)
    # even if there is a log, it shouldn't matter
    raw = "h1\x002025-05-01T00:00:00+00:00\x00Alice\n" "foo.txt\n"
    patch_repo_log(raw)

    # Act
    examples = latest._find_latest_examples(".py", None, None, limit=5)

    # Assert
    assert examples == []


def test_find_latest_examples_no_log_entries(patch_repo_ls, patch_repo_log):
    # Arrange: we have .py files but git.log returns nothing
    files = ["a.py", "b.py"]
    patch_repo_ls(files)
    patch_repo_log("")  # empty log

    # Act
    examples = latest._find_latest_examples(".py", None, None, limit=5)

    # Assert
    assert examples == []


def test_find_latest_examples_limit_zero(patch_repo_ls, patch_repo_log):
    # Arrange
    files = ["x.py", "y.py"]
    patch_repo_ls(files)
    raw = (
        "h1\x002025-05-01T01:00:00+00:00\x00A\n"
        "x.py\n"
        "h2\x002025-05-02T02:00:00+00:00\x00B\n"
        "y.py\n"
    )
    patch_repo_log(raw)

    # Act
    examples = latest._find_latest_examples(".py", None, None, limit=0)

    # Assert
    assert examples == []


# TODO: fix tests

# def test_find_latest_examples_limit_exceeds_count(patch_repo_ls, patch_repo_log):
#     # Arrange
#     files = ["u.py", "v.py"]
#     patch_repo_ls(files)
#     raw = (
#         "h1\x002025-05-01T03:00:00+00:00\x00Alice\n"
#         "u.py\n"
#         "h2\x002025-05-02T04:00:00+00:00\x00Bob\n"
#         "v.py\n"
#     )
#     patch_repo_log(raw)

#     # Act: limit is larger than number of files
#     examples = latest._find_latest_examples(".py", None, None, limit=10)

#     # Assert: both files appear, in descending date order
#     assert [e.path for e in examples] == ["v.py", "u.py"]
#     assert examples[0].created_at > examples[1].created_at


# def test_find_latest_examples_author_filter_integration(patch_repo_ls, patch_repo_log):
#     # Arrange
#     files = ["m.py", "n.py", "o.py"]
#     patch_repo_ls(files)
#     raw = (
#         "h1\x002025-05-01T05:00:00+00:00\x00Carol\n"
#         "m.py\n"
#         "h2\x002025-05-02T06:00:00+00:00\x00Dave\n"
#         "n.py\n"
#         "h3\x002025-05-03T07:00:00+00:00\x00Eve\n"
#         "o.py\n"
#     )
#     patch_repo_log(raw)

#     # Act: only want files by “da” (case-insensitive substring)
#     examples = latest._find_latest_examples(".py", None, ["da"], limit=5)

#     # Assert: only n.py by Dave
#     assert len(examples) == 1
#     assert examples[0].path == "n.py"
#     assert examples[0].author.lower() == "dave"


# def test_find_latest_examples_directories_filter_integration(patch_repo_ls, patch_repo_log):
#     # Arrange
#     files = ["src/a.py", "src/sub/b.py", "lib/c.py", "d.py"]
#     patch_repo_ls(files)
#     raw = (
#         "h1\x002025-05-01T08:00:00+00:00\x00X\n"
#         "src/a.py\n"
#         "lib/c.py\n"
#         "h2\x002025-05-02T09:00:00+00:00\x00Y\n"
#         "src/sub/b.py\n"
#         "d.py\n"
#     )
#     patch_repo_log(raw)

#     # Act: only look under “src”
#     examples = latest._find_latest_examples(".py", ["src"], None, limit=10)

#     # Assert: should return b.py (May 2) then a.py (May 1)
#     paths = [e.path for e in examples]
#     assert paths == ["src/sub/b.py", "src/a.py"]
#     # ensure both are under src/
#     assert all(p.startswith("src/") for p in paths)


# def test_find_latest_examples_multiple_files_same_commit(patch_repo_ls, patch_repo_log):
#     # Arrange: one commit introduces two files at once
#     files = ["one.py", "two.py"]
#     patch_repo_ls(files)
#     raw = (
#         "h1\x002025-05-04T10:00:00+00:00\x00Zed\n"
#         "one.py\n"
#         "two.py\n"
#     )
#     patch_repo_log(raw)

#     # Act
#     examples = latest._find_latest_examples(".py", None, None, limit=10)

#     # Assert: both files returned, in the order they appeared in the commit
#     assert [e.path for e in examples] == ["one.py", "two.py"]
#     # and they share the same timestamp
#     times = {e.created_at for e in examples}
#     assert len(times) == 1
#     assert next(iter(times)) == datetime.fromisoformat("2025-05-04T10:00:00+00:00")
