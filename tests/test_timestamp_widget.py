"""Tests for timestamp widget functionality."""

from __future__ import annotations

import datetime

from streamlit_app.ui.views import _format_last_update_time


def test_format_last_update_time_never() -> None:
    """Test formatting when no sync has occurred."""
    result = _format_last_update_time(None)
    assert result == "Never"


def test_format_last_update_time_absolute() -> None:
    """Test formatting shows absolute timestamp."""
    test_time = datetime.datetime(2024, 1, 15, 14, 30, 45)
    result = _format_last_update_time(test_time)
    assert result == "2024-01-15 14:30:45"


def test_format_last_update_time_current() -> None:
    """Test formatting with current time."""
    now = datetime.datetime.now()
    result = _format_last_update_time(now)
    expected = now.strftime("%Y-%m-%d %H:%M:%S")
    assert result == expected


def test_format_last_update_time_different_formats() -> None:
    """Test various timestamp formats."""
    test_cases = [
        (datetime.datetime(2025, 12, 31, 23, 59, 59), "2025-12-31 23:59:59"),
        (datetime.datetime(2020, 1, 1, 0, 0, 0), "2020-01-01 00:00:00"),
        (datetime.datetime(2024, 6, 15, 12, 30, 15), "2024-06-15 12:30:15"),
    ]

    for test_time, expected in test_cases:
        result = _format_last_update_time(test_time)
        assert result == expected
