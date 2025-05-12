from datetime import datetime, timezone


def convert_to_datetime(date_str: str) -> datetime:
    """
    Convert an ISO‐8601 date or datetime string to a UTC datetime.
    Supports:
      - YYYY-MM-DD
      - YYYY-MM-DDTHH:MM:SS
      - YYYY-MM-DDTHH:MM:SSZ
      - YYYY-MM-DDTHH:MM:SS±HH:MM
    """
    # Normalize trailing 'Z' → '+00:00', so fromisoformat accepts it
    if date_str.endswith("Z"):
        date_str = date_str[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(date_str)
    except ValueError as exc:
        raise ValueError(
            "Invalid date format. Expected ISO-8601 like "
            "YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS, "
            "YYYY-MM-DDTHH:MM:SSZ, or YYYY-MM-DDTHH:MM:SS±HH:MM."
        ) from exc

    # If naive (no tzinfo), assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Convert any offset to UTC
    return dt.astimezone(timezone.utc)
