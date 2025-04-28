from unittest.mock import MagicMock

from git import Repo

def generate_mock_repo() -> Repo:
    repo = MagicMock(spec=Repo)

    return repo
