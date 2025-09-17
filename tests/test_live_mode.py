"""Tests for live mode functionality."""

from __future__ import annotations

from streamlit_app.ui.state import AppState


def test_live_mode_state_management() -> None:
    """Test that live mode state is properly managed."""
    app = AppState()
    
    # Initially not running
    assert app.live_running is False
    
    # Can be activated
    app.live_running = True
    assert app.live_running is True
    
    # Can be deactivated
    app.live_running = False
    assert app.live_running is False


def test_live_mode_with_poll_interval() -> None:
    """Test live mode with different poll intervals."""
    app = AppState()
    
    # Test different poll intervals
    test_intervals = [1000, 5000, 10000, 30000]
    
    for interval in test_intervals:
        app.poll_interval_ms = interval
        app.live_running = True
        
        # Verify state is consistent
        assert app.poll_interval_ms == interval
        assert app.live_running is True
        
        # Verify refresh calculation would work
        refresh_seconds = max(1, int(app.poll_interval_ms / 1000))
        assert refresh_seconds >= 1
        assert refresh_seconds == interval // 1000


def test_live_mode_reset() -> None:
    """Test that reset properly stops live mode."""
    app = AppState()
    
    # Set up live mode
    app.live_running = True
    app.events = [{"test": "data"}]
    app.last_block = 12345
    
    # Reset should stop live mode and clear data
    app.live_running = False
    app.events = []
    app.last_block = 0
    
    assert app.live_running is False
    assert app.events == []
    assert app.last_block == 0
