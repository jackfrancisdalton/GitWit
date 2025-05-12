from git import Repo


class RepoSingleton:
    """Singleton Repo instance for consistent repository access."""

    _repo = None

    @classmethod
    def get_repo(cls) -> Repo:
        if cls._repo is None:
            cls._repo = Repo(".", search_parent_directories=True)

        return cls._repo
