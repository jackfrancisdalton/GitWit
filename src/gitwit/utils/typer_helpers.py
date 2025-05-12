from datetime import datetime
from typing import Tuple
import typer
from gitwit.utils.date_utils import convert_to_datetime

def handle_since_until_arguments(
    since: str = typer.Option(..., help="Start date (YYYY-MM-DD)"),
    until: str = typer.Option(..., help="End date (YYYY-MM-DD)"),
) -> Tuple[datetime, datetime]:
    try:
        since_dt = convert_to_datetime(since)
        until_dt = convert_to_datetime(until)
    except ValueError:
        typer.secho("Invalid date format. Use YYYY-MM-DD.", fg="red")
        raise typer.Exit(1)
    if since_dt > until_dt:
        typer.secho("Start date cannot be after end date.", fg="red")
        raise typer.Exit(1)
    return since_dt, until_dt
