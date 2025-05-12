from datetime import datetime
import pytest
from typer import Exit

from gitwit.utils.typer_helpers import handle_since_until_arguments


@pytest.mark.parametrize(
    "since, until, expected_exception",
    [
        ("2023-01-01", "2023-01-02", None),
        ("2023-01-02", "2023-01-01", Exit),
        ("2023-01-01", "invalid-date", Exit),
        ("invalid-date", "2023-01-01", Exit),
    ],
)
def test_handle_since_until_arguments(since, until, expected_exception):
    if expected_exception:
        with pytest.raises(expected_exception):
            handle_since_until_arguments(since, until)
    else:
        since_date, until_date = handle_since_until_arguments(since, until)
        assert isinstance(since_date, datetime)
        assert isinstance(until_date, datetime)