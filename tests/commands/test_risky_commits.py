from git import Commit
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from gitwit.commands.risky_commits import (
    _identify_risky_commits,
    _assess_lines_changed,
    _assess_files_changed,
    _assess_keywords,
)


FIXED_NOW = datetime(2023, 1, 1, 12, 0, 0)


# TODO: consider moving to a tests util file
def create_commit(insertions, deletions, files, message):
    commit_mock = MagicMock(spec=Commit)
    commit_mock.stats.total = {"insertions": insertions, "deletions": deletions}
    commit_mock.stats.files = {f"file{i}.py": {} for i in range(files)}
    commit_mock.message = message
    commit_mock.hexsha = "abcdef1234567890"
    commit_mock.author.name = "John Doe"
    commit_mock.committed_date = FIXED_NOW.timestamp()
    return commit_mock


@pytest.mark.parametrize(
    "commit_mock,expected_score,expected_factors",
    [
        # No risk factors
        (create_commit(499, 0, 9, "Normal commit"), 0, []),
        # Just below risky number of lines
        (create_commit(499, 0, 9, "Normal commit"), 0, []),
        # Just above risky number of lines
        (
            create_commit(500, 0, 9, "Normal commit"),
            2,
            ["Large number of lines changed"],
        ),
        # Just below risky number of files
        (create_commit(0, 0, 9, "Normal commit"), 0, []),
        # Just above risky number of files
        (create_commit(0, 0, 10, "Normal commit"), 2, ["Many files modified"]),
        # Sensitive keyword in message
        (
            create_commit(0, 0, 1, "Refactor password logic"),
            6,
            ["Sensitive keyword in commit message"] * 2,
        ),
        # Combination: risky lines and sensitive keyword
        (
            create_commit(500, 0, 1, "Security improvements"),
            5,
            ["Large number of lines changed", "Sensitive keyword in commit message"],
        ),
        # Combination: risky files and sensitive keyword
        (
            create_commit(0, 0, 10, "Fixme: update credentials"),
            8,
            [
                "Many files modified",
                "Sensitive keyword in commit message",
                "Sensitive keyword in commit message",
            ],
        ),
        # All risk factors combined
        (
            create_commit(501, 0, 11, "Todo: Refactor security logic"),
            13,
            [
                "Large number of lines changed",
                "Many files modified",
                "Sensitive keyword in commit message",
                "Sensitive keyword in commit message",
                "Sensitive keyword in commit message",
            ],
        ),
    ],
)
@patch("gitwit.commands.risky_commits.get_filtered_commits")
def test_identify_risky_commits(
    mock_filtered_commits, commit_mock, expected_score, expected_factors
):
    since = FIXED_NOW - timedelta(days=1)
    until = FIXED_NOW + timedelta(days=1)

    mock_filtered_commits.return_value = [commit_mock]

    risky_commits = _identify_risky_commits(since, until)

    if expected_score == 0:
        assert len(risky_commits) == 0
        return

    assert len(risky_commits) == 1
    risky_commit = risky_commits[0]

    assert risky_commit.commit == commit_mock
    assert risky_commit.risk_score == expected_score
    assert len(risky_commit.risk_factors) == len(expected_factors)

    factor_descriptions = [factor.description for factor in risky_commit.risk_factors]
    for expected_description in expected_factors:
        assert expected_description in factor_descriptions


@pytest.mark.parametrize(
    "lines_changed, expected_score",
    [
        (499, 0),
        (500, 2),
        (501, 2),
    ],
)
def test_assess_lines_changed(lines_changed, expected_score):
    factors = []
    score = _assess_lines_changed(lines_changed, factors)

    assert score == expected_score
    if expected_score:
        assert len(factors) == 1
        assert factors[0].description == "Large number of lines changed"
    else:
        assert not factors


@pytest.mark.parametrize(
    "files_changed, expected_score",
    [
        (9, 0),
        (10, 2),
        (11, 2),
    ],
)
def test_assess_files_changed(files_changed, expected_score):
    factors = []
    score = _assess_files_changed(files_changed, factors)
    assert score == expected_score
    if expected_score:
        assert len(factors) == 1
        assert factors[0].description == "Many files modified"
    else:
        assert not factors


@pytest.mark.parametrize(
    "message, expected_score, expected_keywords",
    [
        ("Fix security issue", 3, ["security"]),
        ("Refactor and update documentation", 3, ["refactor"]),
        ("Minor typo fixes", 0, []),
        ("Add todo and fixme comments", 6, ["fixme", "todo"]),
    ],
)
def test_assess_keywords(message, expected_score, expected_keywords):
    factors = []
    score = _assess_keywords(message, factors)
    assert score == expected_score
    assert len(factors) == len(expected_keywords)
    for keyword in expected_keywords:
        assert any(keyword in factor.details for factor in factors)
