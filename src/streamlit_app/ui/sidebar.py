from __future__ import annotations

import streamlit as st

from ..config import API_QPS, NETWORKS, PAGE_SIZE_DEFAULT
from .state import ensure_session_state


def render_sidebar() -> None:
    app = ensure_session_state(st)
    with st.sidebar:
        st.header("Settings")
        app.chain = st.selectbox("Network", options=list(NETWORKS.keys()), index=list(NETWORKS.keys()).index(app.chain))
        app.contract_address = st.text_input("Contract address", value=app.contract_address, placeholder="0x...")
        cols = st.columns(2)
        with cols[0]:
            app.from_block = st.number_input("From block", min_value=0, step=1, value=app.from_block)
        with cols[1]:
            app.confirmation_blocks = st.number_input("Confirmations", min_value=0, step=1, value=app.confirmation_blocks)

        app.page_size = st.number_input("Page size", min_value=1, step=1, value=app.page_size or PAGE_SIZE_DEFAULT)
        app.rate_limit_qps = st.number_input("API QPS", min_value=0.0, step=0.5, value=float(app.rate_limit_qps or API_QPS))
        app.poll_interval_ms = st.number_input("Poll interval (ms)", min_value=500, step=500, value=app.poll_interval_ms)
        app.token_decimals = st.number_input("Token decimals", min_value=0, max_value=30, step=1, value=app.token_decimals, help="Number of decimal places for the token (18 for most ERC20 tokens)")

        st.divider()
        start = st.button("Initial Sync", use_container_width=True)

        # Live mode buttons with visual indication
        if app.live_running:
            start_live = st.button("🔴 Live Mode ON", use_container_width=True, type="primary")
            stop_live = st.button("Stop Live", use_container_width=True)
        else:
            start_live = st.button("Start Live", use_container_width=True)
            stop_live = st.button("Stop Live", use_container_width=True, disabled=True)

        reset = st.button("Reset", type="secondary", use_container_width=True)

        if reset:
            app.events = []
            app.last_block = 0
            app.live_running = False
            app.next_live_update = None

        if start:
            app.trigger_initial_sync = True
        if start_live:
            app.live_running = True
            app.next_live_update = None  # Reset timer when starting
        if stop_live:
            app.live_running = False
            app.next_live_update = None  # Clear timer when stopping


