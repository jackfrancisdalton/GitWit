from datetime import datetime, timedelta

import pytest

import commands.team_activity as team_activity


class DummyCommit:
    def __init__(self, hexsha, author_name, committed_date, message, stats):
        self.hexsha = hexsha
        self.author = DummyAuthor(author_name)
        self.committed_date = committed_date
        self.message = message
        self.stats = stats

class DummyAuthor:
    def __init__(self, name):
        self.name = name

class DummyStats:
    def __init__(self, insertions, deletions, files):
        self.total = {'insertions': insertions, 'deletions': deletions}
        self.files = files


@pytest.fixture
def repo_mock(monkeypatch):
    class RepoMock:
        def __init__(self, commits):
            self._commits = commits

        def iter_commits(self, since=None, author=None):
            since_ts = datetime.fromisoformat(since).timestamp() if since else 0
            filtered_commits = [
                c for c in self._commits
                if c.committed_date >= since_ts and (author is None or c.author.name == author)
            ]
            return iter(filtered_commits)

    def mock_repo(commits):
        monkeypatch.setattr(team_activity, "Repo", lambda *_args, **_kwargs: RepoMock(commits))

    return mock_repo

def test_fetch_developer_activities__no_commits(repo_mock):
    # Arrange
    repo_mock([])
    since = datetime.now() - timedelta(days=7)
    repo = team_activity.Repo(".")

    # Act
    results = team_activity._fetch_developer_activities(repo, since)

    # Assert
    assert len(results) == 0

def test_fetch_developer_activities__commit_out_of_range(repo_mock):
    # Arrange
    commit_outside_of_date_range = DummyCommit(
        hexsha="def5678",
        author_name="Dev2",
        committed_date=(datetime.now() - timedelta(days=7) ).timestamp(),
        message="Update file",
        stats=DummyStats(20, 10, ["file4.py"])
    )

    repo_mock([commit_outside_of_date_range])
    since = datetime.now() - timedelta(days=7)
    repo = team_activity.Repo(".")

    # Act
    results = team_activity._fetch_developer_activities(repo, since)

    # Assert
    assert len(results) == 0
    
def test_fetch_developer_activities__valid_commits(repo_mock):
    # Arrange
    simple_commit = DummyCommit(
        hexsha="abc1234",
        author_name="Dev1",
        committed_date=datetime.now().timestamp(),
        message="Initial commit",
        stats=DummyStats(10, 5, ["file1.py"])
    )
    commit_with_multiple_files = DummyCommit(
        hexsha="def5678",
        author_name="Dev2",
        committed_date=datetime.now().timestamp(),
        message="Update file",
        stats=DummyStats(20, 10, ["file8.py", "file2.py", "file3.py"])
    )

    repo_mock([
        simple_commit,
        commit_with_multiple_files,
    ])
    since = datetime.now() - timedelta(days=7)
    repo = team_activity.Repo(".")

    # Act
    results = team_activity._fetch_developer_activities(repo, since)

    # Assert
    assert len(results) == 2

    assert results[0].developer == "Dev1"
    assert results[0].lines_added == 10
    assert results[0].lines_deleted == 5
    assert results[0].prs_merged == 0
    assert results[0].reviews_done == 0
    assert results[0].files_touched == 1

    assert results[1].developer == "Dev2"
    assert results[1].lines_added == 20
    assert results[1].lines_deleted == 10
    assert results[1].prs_merged == 0
    assert results[1].reviews_done == 0
    assert results[1].files_touched == 3


def test_fetch_developer_activities__valid_commits_from_same_author(repo_mock):
    # Arrange
    simple_commit = DummyCommit(
        hexsha="abc1234",
        author_name="Dev1",
        committed_date=datetime.now().timestamp(),
        message="Initial commit",
        stats=DummyStats(10, 5, ["file1.py"])
    )
    commit_with_multiple_files = DummyCommit(
        hexsha="def5678",
        author_name="Dev1",
        committed_date=datetime.now().timestamp(),
        message="Update file",
        stats=DummyStats(20, 10, ["file4.py", "file2.py", "file3.py"])
    )

    repo_mock([
        simple_commit,
        commit_with_multiple_files
    ])
    since = datetime.now() - timedelta(days=7)
    repo = team_activity.Repo(".")

    # Act
    results = team_activity._fetch_developer_activities(repo, since)

    # Assert
    assert len(results) == 1

    assert results[0].developer == "Dev1"
    assert results[0].lines_added == 10 + 20
    assert results[0].lines_deleted == 5 + 10
    assert results[0].prs_merged == 0
    assert results[0].reviews_done == 0
    assert results[0].files_touched == 1 + 3


def test_fetch_developer_activities__valid_commits_on_the_same_file(repo_mock):
    # Arrange
    simple_commit = DummyCommit(
        hexsha="abc1234",
        author_name="Dev1",
        committed_date=datetime.now().timestamp(),
        message="Initial commit",
        stats=DummyStats(10, 5, ["file1.py"])
    )
    commit_on_the_same_file = DummyCommit(
        hexsha="def5678",
        author_name="Dev1",
        committed_date=datetime.now().timestamp(),
        message="Update file",
        stats=DummyStats(20, 10, ["file1.py", "file2.py"])
    )
    commit_from_different_author_on_same_file = DummyCommit(
        hexsha="def5678",
        author_name="Dev2",
        committed_date=datetime.now().timestamp(),
        message="Update file",
        stats=DummyStats(5, 7, ["file1.py"])
    )

    repo_mock([
        simple_commit,
        commit_on_the_same_file,
        commit_from_different_author_on_same_file
    ])
    since = datetime.now() - timedelta(days=7)
    repo = team_activity.Repo(".")

    # Act
    results = team_activity._fetch_developer_activities(repo, since)

    # Assert
    assert len(results) == 2

    assert results[0].developer == "Dev1"
    assert results[0].lines_added == 10 + 20
    assert results[0].lines_deleted == 5 + 10
    assert results[0].prs_merged == 0
    assert results[0].reviews_done == 0
    assert results[0].files_touched == 1 + 1

    assert results[1].developer == "Dev2"
    assert results[1].lines_added == 5
    assert results[1].lines_deleted == 7
    assert results[1].prs_merged == 0
    assert results[1].reviews_done == 0
    assert results[1].files_touched == 1