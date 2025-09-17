from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any, cast


@dataclass
class AppState:
    chain: str = "sepolia"
    contract_address: str = ""
    from_block: int = 0
    page_size: int = 1000
    rate_limit_qps: float = 3.0
    poll_interval_ms: int = 5000
    confirmation_blocks: int = 6
    token_decimals: int = 18
    abi_events: list[dict[str, Any]] = field(default_factory=list)
    selected_event_names: list[str] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    last_block: int = 0
    live_running: bool = False
    trigger_initial_sync: bool = False
    last_sync_time: datetime.datetime | None = None


def ensure_session_state(st: Any) -> AppState:
    if "app_state" not in st.session_state:
        st.session_state.app_state = AppState()

    # Ensure backward compatibility for new fields
    app_state = cast(AppState, st.session_state.app_state)
    if not hasattr(app_state, 'token_decimals'):
        app_state.token_decimals = 18
    if not hasattr(app_state, 'last_sync_time'):
        app_state.last_sync_time = None

    return app_state


