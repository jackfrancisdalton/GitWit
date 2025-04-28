import random
from datetime import datetime, timedelta
from typing import Optional
from unittest.mock import MagicMock

from git import Commit

def generate_mock_commits(
        num_commits,
        start: Optional[str] = None,
        end: Optional[str] = None
) -> list[Commit]:
    users = ["user1", "user2", "user3"]
    commit_messages = [
        "Fix bug in payment processing",
        "Update README with new instructions",
        "Refactor user authentication logic",
        "Add unit tests for payment feature",
        "Improve performance of data processing",
    ]

    [start_date, end_date] = _generate_date_range(start, end)

    commits = []
    for _ in range(num_commits):
        commit = MagicMock(spec=Commit)
        # Generate a random datetime within the specified range
        random_time = start_date + timedelta(
            seconds=random.randint(0, int((end_date - start_date).total_seconds()))
        )
        commit.committed_datetime = random_time
        commit.author.name = random.choice(users)
        commit.message.strip.return_value = random.choice(commit_messages)

        commits.append(commit)

    return commits


def _generate_date_range(start: Optional[str], end: Optional[str]) -> tuple[datetime, datetime]:
    if start is None:
        start_time_date = datetime.now() - timedelta(days=30)  # Default to 30 days ago
    else:
        start_time_date = datetime.strptime(start, "%Y-%m-%d")

    if end is None:
        end_time_date = datetime.now()  # Default to now
    else:
        end_time_date = datetime.strptime(end, "%Y-%m-%d")

    return (start_time_date, end_time_date)