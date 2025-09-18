from __future__ import annotations

import streamlit as st

from pathlib import Path

from ..config import API_QPS, NETWORKS, PAGE_SIZE_DEFAULT
from ..core.abi import find_all_events, load_abi_from_json
from .state import ensure_session_state


def render_sidebar() -> None:
    app = ensure_session_state(st)
    with st.sidebar:
        st.header("Settings")
        app.chain = st.selectbox("Network", options=list(NETWORKS.keys()), index=list(NETWORKS.keys()).index(app.chain))

        # ABI upload first
        st.subheader("ABI")
        st.caption("Upload ABI.json or use the built-in distributor ABI by default")
        use_default_abi = st.checkbox("Use default distributor ABI (abi_distributor.json)", value=True)
        abi_file = st.file_uploader("Upload ABI.json", type=["json"], key="abi_upload")

        # Load ABI into session state (uploaded or default)
        loaded_abi: list[dict] | None = None
        if abi_file is not None:
            try:
                loaded_abi = load_abi_from_json(abi_file.read())
            except Exception:
                loaded_abi = None
        elif use_default_abi:
            try:
                default_path = Path(__file__).resolve().parents[2] / "abi_distributor.json"
                if default_path.exists():
                    loaded_abi = load_abi_from_json(default_path.read_bytes())
            except Exception:
                loaded_abi = None

        if loaded_abi is not None:
            app.abi_events = find_all_events(loaded_abi)
            names = [e.get("name", "") for e in app.abi_events]
            claim_names = [name for name in names if "claim" in name.lower()]
            default_names = claim_names if claim_names else names[:1]
            app.selected_event_names = st.multiselect(
                "Events to monitor",
                options=names,
                default=default_names,
                key="event_select",
            )

        st.divider()
        st.subheader("Contract")
        app.contract_address = st.text_input("Contract address", value=app.contract_address, placeholder="0x...")
        start = st.button("Initial Sync (Update)", use_container_width=True, key="btn_initial_sync")

        st.subheader("Parameters")
        cols = st.columns(2)
        with cols[0]:
            app.from_block = st.number_input("From block", min_value=0, step=1, value=app.from_block)
            app.page_size = st.number_input("Page size", min_value=1, step=1, value=app.page_size or PAGE_SIZE_DEFAULT)
            app.poll_interval_ms = st.number_input("Refresh interval (seconds)", min_value=5, step=1, value=int(app.poll_interval_ms/1000)) * 1000
        with cols[1]:
            app.confirmation_blocks = st.number_input("Confirmations", min_value=0, step=1, value=app.confirmation_blocks)
            app.rate_limit_qps = st.number_input("API QPS", min_value=0.0, step=0.5, value=float(app.rate_limit_qps or API_QPS))
            app.token_decimals = st.number_input("Token decimals", min_value=0, max_value=30, step=1, value=app.token_decimals)

        st.divider()
        # Test controls (replace standard live buttons)
        st.caption("Live controls (tests)")
        live_test_cols = st.columns(2)
        with live_test_cols[0]:
            start_live_test = st.button("Start Live (tests)", use_container_width=True, key="btn_start_live_tests")
        with live_test_cols[1]:
            stop_live_test = st.button("Stop Live (tests)", use_container_width=True, key="btn_stop_live_tests")

        reset = st.button("Reset", type="secondary", use_container_width=True)

        if reset:
            app.events = []
            app.last_block = 0
            app.live_running = False
            app.last_sync_time = None

        if start:
            app.trigger_initial_sync = True
        if start_live_test:
            app.live_running = True
            app.trigger_live_test = True
        if stop_live_test:
            app.live_running = False
            app.trigger_live_test = False


