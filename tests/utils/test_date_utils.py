from datetime import datetime, timezone
import pytest
from gitwit.utils.date_utils import convert_to_datetime


@pytest.mark.parametrize(
    "date_str, expected",
    [
        (
            "2023-10-01", # Date only
            datetime(2023, 10, 1, tzinfo=timezone.utc)
        ),  
        (
            "2023-10-01T12:00:00", # Date and time
            datetime(2023, 10, 1, 12, 0, tzinfo=timezone.utc),
        ),
        (
            "2023-10-01T12:00:00Z", # Date and time with Zulu time
            datetime(2023, 10, 1, 12, 0, tzinfo=timezone.utc),
        ),
        (
            "2023-10-01T12:00:00+02:00",  # Date and time with timezone offset
            datetime(2023, 10, 1, 10, 0, tzinfo=timezone.utc),
        ),
    ],
)
def test_convert_to_datetime__valid_cases(date_str, expected):
    # Act
    result = convert_to_datetime(date_str)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "date_str",
    [
        "2023-13-01",                 # Invalid month
        "2023-10-32",                 # Invalid day
        "2023-10-01T25:00:00",        # Invalid hour
        "2023-10-01T12:60:00",        # Invalid minute
        "2023-10-01T12:00:60",        # Invalid second
        "2023-10-01T12:00:00+25:00",  # Invalid timezone offset
        "not-a-date",                 # Completely invalid format
        "",                           # Empty string
    ],
)
def test_convert_to_datetime__invalid_cases(date_str):
    # Act & Assert
    with pytest.raises(ValueError, match="Invalid date format"):
        convert_to_datetime(date_str)
