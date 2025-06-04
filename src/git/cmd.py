import subprocess
from pathlib import Path

class Git:
    def __init__(self, repo_path: Path | str = '.'):
        self.repo_path = Path(repo_path)

    def _run(self, *args: str) -> str:
        return subprocess.check_output(['git', *args], cwd=self.repo_path, text=True)

    def ls_files(self, *args: str) -> str:
        return self._run('ls-files', *args)

    def log(self, *args: str) -> str:
        return self._run('log', *args)

    def rev_list(self, *args: str) -> str:
        return self._run('rev-list', *args)

    def blame(self, *args: str) -> str:
        return self._run('blame', *args)
