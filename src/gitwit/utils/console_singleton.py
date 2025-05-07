from rich.console import Console

class ConsoleSingleton:
    """Singleton Console instance for consistent output formatting."""

    _console = None

    @classmethod
    def get_console(cls) -> Console:
        if cls._console is None:
            cls._console = Console()
        return cls._console