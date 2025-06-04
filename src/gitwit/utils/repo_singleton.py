import subprocess
from pathlib import Path
from git.cmd import Git


class RepoCLI:
    """Lightweight wrapper around git CLI used in this project."""

    def __init__(self, path: Path):
        self.path = path
        self.git = Git(path)


class RepoSingleton:
    """Singleton RepoCLI instance for consistent repository access."""

    _repo: RepoCLI | None = None

    @classmethod
    def get_repo(cls) -> RepoCLI:
        if cls._repo is None:
            root = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], text=True
            ).strip()
            cls._repo = RepoCLI(Path(root))
        return cls._repo
