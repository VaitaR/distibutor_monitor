from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, cast


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
    abi_events: List[Dict[str, Any]] = field(default_factory=list)
    selected_event_names: List[str] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    last_block: int = 0
    live_running: bool = False
    trigger_initial_sync: bool = False


def ensure_session_state(st: Any) -> AppState:
    if "app_state" not in st.session_state:
        st.session_state.app_state = AppState()
    
    # Ensure backward compatibility for new fields
    app_state = cast(AppState, st.session_state.app_state)
    if not hasattr(app_state, 'token_decimals'):
        app_state.token_decimals = 18
    
    return app_state


