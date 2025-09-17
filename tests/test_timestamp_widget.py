"""Tests for timestamp widget functionality."""

from __future__ import annotations

import datetime

from streamlit_app.ui.views import _format_last_update_time


def test_format_last_update_time_never() -> None:
    """Test formatting when no sync has occurred."""
    result = _format_last_update_time(None)
    assert result == "Never"


def test_format_last_update_time_seconds() -> None:
    """Test formatting for recent updates (seconds)."""
    now = datetime.datetime.now()
    recent = now - datetime.timedelta(seconds=30)
    result = _format_last_update_time(recent)
    assert "seconds ago" in result
    assert "30" in result


def test_format_last_update_time_minutes() -> None:
    """Test formatting for updates within the hour (minutes)."""
    now = datetime.datetime.now()
    recent = now - datetime.timedelta(minutes=15)
    result = _format_last_update_time(recent)
    assert "minutes ago" in result
    assert "15" in result


def test_format_last_update_time_hours() -> None:
    """Test formatting for updates within the day (hours)."""
    now = datetime.datetime.now()
    recent = now - datetime.timedelta(hours=3)
    result = _format_last_update_time(recent)
    assert "hours ago" in result
    assert "3" in result


def test_format_last_update_time_days() -> None:
    """Test formatting for old updates (full timestamp)."""
    old_time = datetime.datetime(2024, 1, 1, 12, 0, 0)
    result = _format_last_update_time(old_time)
    assert "2024-01-01 12:00:00" == result
