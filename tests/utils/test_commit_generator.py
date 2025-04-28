import random
from datetime import datetime
from unittest.mock import MagicMock

from git import Commit

def generate_mock_commits(
    num_commits,
) -> list:
    users = ["user1", "user2", "user3"]
    commit_messages = [
        "Fix bug in payment processing",
        "Update README with new instructions",
        "Refactor user authentication logic",
        "Add unit tests for payment feature",
        "Improve performance of data processing",
    ]

    commits = []
    for _ in range(num_commits):
        commit = MagicMock(spec=Commit)
        commit.committed_datetime = datetime(2025, 4, 25)
        commit.author.name = random.choice(users)
        commit.message.strip.return_value = random.choice(commit_messages)

        commits.append(commit)

    return commits