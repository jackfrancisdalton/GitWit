import pytest
from datetime import datetime, timedelta
from typer import Exit as TyperExit

import commands.risky_commits as risk_commits
from commands.risky_commits import _identify_risky_commits


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
        monkeypatch.setattr(risk_commits, "Repo", lambda *_args, **_kwargs: RepoMock(commits))

    return mock_repo


@pytest.mark.parametrize("insertions,deletions,expected_score", [
    (499, 0, 0),
    (500, 0, 2),
    (501, 0, 2)
])
def test_lines_changed_threshold(repo_mock, insertions, deletions, expected_score):
    # Arrange
    commit = DummyCommit(
        hexsha="abc1234",
        author_name="Dev",
        committed_date=datetime.now().timestamp(),
        message="Regular update",
        stats=DummyStats(insertions, deletions, ["app.py"])
    )
    repo_mock([commit])
    since = datetime.now() - timedelta(days=7)
    repo = risk_commits.Repo(".")

    # Act
    results = _identify_risky_commits(repo, since)

    # Assert
    if expected_score == 0:
        assert len(results) == 0
    else:
        assert len(results) == 1
        assert results[0].risk_score == expected_score
        assert results[0].risk_factors[0].description == "Large number of lines changed"


@pytest.mark.parametrize("files_changed,expected_score", [
    (9, 0),
    (10, 2),
    (11, 2)
])
def test_files_changed_threshold(repo_mock, files_changed, expected_score):
    # Arrange
    files = [f"file_{i}.py" for i in range(files_changed)]
    commit = DummyCommit(
        hexsha="def5678",
        author_name="Dev",
        committed_date=datetime.now().timestamp(),
        message="Regular update",
        stats=DummyStats(10, 5, files)
    )

    repo_mock([commit])
    since = datetime.now() - timedelta(days=7)
    repo = risk_commits.Repo(".")
    
    # Act
    results = _identify_risky_commits(repo, since)

    # Assert
    if expected_score == 0:
        assert len(results) == 0
    else:
        assert len(results) == 1
        assert results[0].risk_score == expected_score
        assert results[0].risk_factors[0].description == "Many files modified"


@pytest.mark.parametrize("message,expected_score,keyword", [
    ("This commit contains password reset logic", 3, "password"),
    ("Regular update", 0, None)
])
def test_keyword_in_message(repo_mock, message, expected_score, keyword):
    # Arrange
    commit = DummyCommit(
        hexsha="ghi9012",
        author_name="Dev",
        committed_date=datetime.now().timestamp(),
        message=message,
        stats=DummyStats(10, 5, ["app.py"])
    )

    repo_mock([commit])
    since = datetime.now() - timedelta(days=7)
    repo = risk_commits.Repo(".")

    # Act
    results = _identify_risky_commits(repo, since)

    # Assert
    if expected_score == 0:
        assert len(results) == 0
    else:
        assert len(results) == 1
        assert results[0].risk_score == expected_score
        assert any(keyword in factor.details for factor in results[0].risk_factors)

def test_command_invalid_period():
    with pytest.raises(TyperExit):
        risk_commits.command("year")


def test_command_no_risky_commits(repo_mock, capsys):
    # Arrange
    repo_mock([])
    risk_commits.command("week")

    # Act
    captured = capsys.readouterr()

    # Assert
    assert "No risky commits found" in captured.out


# TODO: test cases for first-time file type commits
# @pytest.mark.parametrize("commits_data,expected_risks_per_commit", [
#     (
#         [
#             {"author": "Alice", "files": ["file.js"], "message": "Initial commit", "days_ago": 10},
#             {"author": "Bob", "files": ["file.js"], "message": "Added new files", "days_ago": 0}
#         ],
#         [[], ["First-time file type commit by author"]]
#     ),
#     (
#         [
#             {"author": "Alice", "files": ["file.js"], "message": "Initial commit", "days_ago": 10},
#             {"author": "Bob", "files": ["file.config.js"], "message": "Added new files", "days_ago": 0}
#         ],
#         [[], ["First-time file type commit by author"]]
#     ),
#     (
#         [
#             {"author": "Alice", "files": ["file.js"], "message": "Initial commit", "days_ago": 10},
#             {"author": "Alice", "files": ["file.js"], "message": "Added new files", "days_ago": 0}
#         ],
#         [[], []]
#     ),
#     (
#         [
#             {"author": "Alice", "files": ["file.js"], "message": "Initial commit", "days_ago": 10},
#             {"author": "Alice", "files": ["file.config.js"], "message": "Added new files", "days_ago": 0}
#         ],
#         [[], ["First-time file type commit by author"]]
#     ),
#     (
#         [
#             {"author": "Alice", "files": [], "message": "Initial commit", "days_ago": 10},
#             {"author": "Bob", "files": ["file.py"], "message": "Added new files", "days_ago": 0}
#         ],
#         [[], ["First-time file type commit by author"]]
#     ),
#     (
#         [
#             {"author": "Alice", "files": ["file.py"], "message": "Initial commit", "days_ago": 10},
#             {"author": "Alice", "files": ["file.js"], "message": "Added new files", "days_ago": 0}
#         ],
#         [[], ["First-time file type commit by author"]]
#     )
# ])
