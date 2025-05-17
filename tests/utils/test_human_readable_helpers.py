import pytest
from datetime import timedelta
from gitwit.utils.human_readable_helpers import humanise_timedelta


@pytest.mark.parametrize(
    "delta, expected",
    [
        (timedelta(seconds=59), "59 sec ago"),  # seconds
        (timedelta(minutes=1), "1 min ago"),  # minium minutes
        (timedelta(minutes=59, seconds=59), "59 min ago"),  # maximum minutes
        (timedelta(hours=1), "1 hour(s) ago"),  # minimum hours
        (timedelta(hours=23, minutes=59), "23 hour(s) ago"),  # maximum hours
        (timedelta(days=1), "1 day(s) ago"),  # minimum days
        (timedelta(days=40000), "40000 day(s) ago"),  # high days value to test limits
    ],
)
def test_humanise_timedelta(delta, expected):
    assert humanise_timedelta(delta) == expected
