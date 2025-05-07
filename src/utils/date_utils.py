from datetime import datetime, timezone

def convert_to_datetime(date_str: str) -> datetime:
    """
    Convert a date string to a datetime object in UTC. We want to ensure that we handle all dates in a common timezone (UTC).
    Supports formats: YYYY-MM-DD and YYYY-MM-DDTHH:MM:SS.
    """
    try:
        if "T" in date_str:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError("Invalid date format. Expected YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS.") from exc