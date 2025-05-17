import pytest
from datetime import datetime

import gitwit.commands.latest_examples_of as latest
import gitwit.utils.repo_singleton as repo_singleton


@pytest.fixture
def patch_repo_ls(monkeypatch):
    """Patch RepoSingleton.get_repo so ls_files returns our list only."""

    def _patch(files):
        # clear cached real repo
        repo_singleton.RepoSingleton._repo = None

        class DummyRepo:
            def __init__(self, files):
                self.git = self
                self._files = files

            def ls_files(self):
                return "\n".join(self._files)

            def log(self, *args, **kwargs):
                return ""  # no log

        dummy = DummyRepo(files)
        monkeypatch.setattr(
            repo_singleton.RepoSingleton, "get_repo", classmethod(lambda cls: dummy)
        )

    return _patch


@pytest.fixture
def patch_repo_log(monkeypatch):
    """Patch RepoSingleton.get_repo so git.log returns our raw log only."""

    def _patch(raw_log):
        repo_singleton.RepoSingleton._repo = None

        class DummyRepoLog:
            def __init__(self, raw):
                self.git = self
                self._raw = raw

            def log(self, *args, **kwargs):
                return self._raw

            def ls_files(self):
                return ""  # no files

        dummy = DummyRepoLog(raw_log)
        monkeypatch.setattr(
            repo_singleton.RepoSingleton, "get_repo", classmethod(lambda cls: dummy)
        )

    return _patch


@pytest.fixture
def patch_both(monkeypatch):
    """Patch RepoSingleton.get_repo so ls_files and git.log both return specified values."""

    def _patch(files, raw_log):
        repo_singleton.RepoSingleton._repo = None

        class CombinedRepo:
            def __init__(self, files, raw):
                self.git = self
                self._files = files
                self._raw = raw

            def ls_files(self):
                return "\n".join(self._files)

            def log(self, *args, **kwargs):
                return self._raw

        combined = CombinedRepo(files, raw_log)
        monkeypatch.setattr(
            repo_singleton.RepoSingleton, "get_repo", classmethod(lambda cls: combined)
        )

    return _patch


# =====================================================
# Tests for _hydrate_examples_and_filter_based_on_git_data
# =====================================================


def test_hydrate_examples_and_filter_based_on_git_data__no_filter(patch_repo_log):
    raw = (
        "h1\x002025-05-02T11:00:00+00:00\x00Carol\n"
        "foo.py\n"
        "h2\x002025-05-03T12:30:00+00:00\x00Dave\n"
        "bar.py\n"
    )
    patch_repo_log(raw)

    examples = latest._hydrate_examples_and_filter_based_on_git_data(["foo.py", "bar.py"], None)

    assert len(examples) == 2
    assert examples[0].path == "foo.py"
    assert examples[0].author == "Carol"
    assert examples[0].created_at == datetime.fromisoformat("2025-05-02T11:00:00+00:00")
    assert examples[1].path == "bar.py"
    assert examples[1].author == "Dave"
    assert examples[1].created_at == datetime.fromisoformat("2025-05-03T12:30:00+00:00")


def test_hydrate_examples_and_filter_based_on_git_data__author_filter_exact_match(
    patch_repo_log,
):
    raw = (
        "h1\x002025-05-02T11:00:00+00:00\x00Carol\n"
        "foo.py\n"
        "h2\x002025-05-03T12:30:00+00:00\x00Dave\n"
        "bar.py\n"
    )
    patch_repo_log(raw)

    examples = latest._hydrate_examples_and_filter_based_on_git_data(["foo.py", "bar.py"], ["Dave"])

    assert len(examples) == 1
    assert examples[0].path == "bar.py"
    assert examples[0].author == "Dave"


def test_hydrate_examples_and_filter_based_on_git_data__author_filter_substring(
    patch_repo_log,
):
    raw = (
        "h1\x002025-05-02T11:00:00+00:00\x00Jack\n"
        "foo.py\n"
        "h2\x002025-05-03T12:30:00+00:00\x00Jane\n"
        "bar.py\n"
        "h3\x002025-05-03T12:30:00+00:00\x00James\n"
        "zoo.py\n"
    )
    patch_repo_log(raw)

    examples = latest._hydrate_examples_and_filter_based_on_git_data(
        ["foo.py", "bar.py", "zoo.py"], ["ja"]
    )

    assert len(examples) == 3
    assert [e.path for e in examples] == ["foo.py", "bar.py", "zoo.py"]


# =====================================================
# Tests for _find_latest_examples using patch_both
# =====================================================


def test_find_latest_examples_no_matching_files(patch_both):
    files = ["foo.txt", "bar.js"]
    raw = "h1\x002025-05-01T00:00:00+00:00\x00Alice\n" "foo.txt\n"
    patch_both(files, raw)

    examples = latest._find_latest_examples(".py", None, None, limit=5)
    assert examples == []


def test_find_latest_examples_no_log_entries(patch_both):
    files = ["a.py", "b.py"]
    patch_both(files, "")

    examples = latest._find_latest_examples(".py", None, None, limit=5)
    assert examples == []


def test_find_latest_examples_limit_zero(patch_both):
    files = ["x.py", "y.py"]
    raw = (
        "h1\x002025-05-01T01:00:00+00:00\x00A\n"
        "x.py\n"
        "h2\x002025-05-02T02:00:00+00:00\x00B\n"
        "y.py\n"
    )
    patch_both(files, raw)

    examples = latest._find_latest_examples(".py", None, None, limit=0)
    assert examples == []


def test_find_latest_examples_limit_exceeds_count(patch_both):
    files = ["u.py", "v.py"]
    raw = (
        "h1\x002025-05-01T03:00:00+00:00\x00Alice\n"
        "u.py\n"
        "h2\x002025-05-02T04:00:00+00:00\x00Bob\n"
        "v.py\n"
    )
    patch_both(files, raw)

    examples = latest._find_latest_examples(".py", None, None, limit=10)
    assert [e.path for e in examples] == ["v.py", "u.py"]
    assert examples[0].created_at > examples[1].created_at


def test_find_latest_examples_limit_one(patch_both):
    files = ["a.py", "b.py", "c.py"]
    raw = (
        "h1\x002025-05-01T01:00:00+00:00\x00A\n"
        "a.py\n"
        "h2\x002025-05-02T02:00:00+00:00\x00B\n"
        "b.py\n"
        "h3\x002025-05-03T03:00:00+00:00\x00C\n"
        "c.py\n"
    )
    patch_both(files, raw)

    examples = latest._find_latest_examples(".py", None, None, limit=1)
    assert len(examples) == 1
    assert examples[0].path == "c.py"


def test_find_latest_examples_author_filter_integration(patch_both):
    files = ["m.py", "n.py", "o.py"]
    raw = (
        "h1\x002025-05-01T05:00:00+00:00\x00Carol\n"
        "m.py\n"
        "h2\x002025-05-02T06:00:00+00:00\x00Dave\n"
        "n.py\n"
        "h3\x002025-05-03T07:00:00+00:00\x00Eve\n"
        "o.py\n"
    )
    patch_both(files, raw)

    examples = latest._find_latest_examples(".py", None, ["da"], limit=5)
    assert len(examples) == 1
    assert examples[0].path == "n.py"
    assert examples[0].author.lower() == "dave"


def test_find_latest_examples_directories_filter_integration(patch_both):
    files = ["src/a.py", "src/sub/b.py", "lib/c.py", "d.py"]
    raw = (
        "h1\x002025-05-01T08:00:00+00:00\x00X\n"
        "src/a.py\n"
        "lib/c.py\n"
        "h2\x002025-05-02T09:00:00+00:00\x00Y\n"
        "src/sub/b.py\n"
        "d.py\n"
    )
    patch_both(files, raw)

    examples = latest._find_latest_examples(".py", ["src"], None, limit=10)
    paths = [e.path for e in examples]
    assert paths == ["src/sub/b.py", "src/a.py"]
    assert all(p.startswith("src/") for p in paths)


def test_find_latest_examples_multiple_files_same_commit(patch_both):
    files = ["one.py", "two.py"]
    raw = "h1\x002025-05-04T10:00:00+00:00\x00Zed\n" "one.py\n" "two.py\n"
    patch_both(files, raw)

    examples = latest._find_latest_examples(".py", None, None, limit=10)
    assert [e.path for e in examples] == ["one.py", "two.py"]
    times = {e.created_at for e in examples}
    assert len(times) == 1
    assert next(iter(times)) == datetime.fromisoformat("2025-05-04T10:00:00+00:00")
