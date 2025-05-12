import click
from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable)

def with_date_range() -> Callable[[F], F]:
    """
    Decorator that adds two Click options to a Typer command:
      --since / -s  parsed as YYYY-MM-DD → datetime
      --until / -u  parsed as YYYY-MM-DD → datetime
    """

    def _decorate(fn: F) -> F:
        # Note: order matters—decorate 'until' first so help shows since, then until.
        fn = click.option(
            "--until", "-u",
            "until",
            required=True,
            type=click.DateTime(formats=["%Y-%m-%d"]),
            help="End date (YYYY-MM-DD)",
        )(fn)  # type: ignore

        fn = click.option(
            "--since", "-s",
            "since",
            required=True,
            type=click.DateTime(formats=["%Y-%m-%d"]),
            help="Start date (YYYY-MM-DD)",
        )(fn)  # type: ignore

        return fn

    return _decorate