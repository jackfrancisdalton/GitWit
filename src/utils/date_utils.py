from datetime import datetime

def convert_to_datetime(date_str: str) -> datetime:
    """
    Convert a date string to a datetime object.
    Supports formats: YYYY-MM-DD and YYYY-MM-DDTHH:MM:SS.
    """
    try:
        if "T" in date_str:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("Invalid date format. Expected YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS.") from exc