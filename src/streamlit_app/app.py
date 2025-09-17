from __future__ import annotations

import sys
from pathlib import Path
import streamlit as st
from streamlit.components.v1 import html as components_html
import asyncio

SRC_DIR = str(Path(__file__).resolve().parents[1])
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from streamlit_app.utils.secrets import load_secrets_from_dotenv
from streamlit_app.ui.sidebar import render_sidebar
from streamlit_app.ui.views import render_main
from streamlit_app.ui.state import ensure_session_state
from streamlit_app.config import resolve_network_config
from streamlit_app.datasources.blockscout import BlockscoutClient
from streamlit_app.datasources.rpc import RpcClient
from streamlit_app.core.abi import load_abi_from_json, find_all_events
from streamlit_app.core.app_logic import run_initial_sync, run_live_tick


def main() -> None:
    load_secrets_from_dotenv()
    st.set_page_config(page_title="Distributor Monitor", layout="wide")
    st.title("Distributor Monitor")
    render_sidebar()

    app = ensure_session_state(st)
    cfg = resolve_network_config(app.chain)

    # Upload ABI and select events
    abi_file = st.sidebar.file_uploader("Upload ABI.json", type=["json"])
    if abi_file is not None:
        abi = load_abi_from_json(abi_file.read())
        app.abi_events = find_all_events(abi)
        names = [e.get("name", "") for e in app.abi_events]
        # Default to claim-like events if available, otherwise show all
        claim_names = [name for name in names if "claim" in name.lower()]
        default_names = claim_names if claim_names else names[:1]  # At least one event
        app.selected_event_names = st.sidebar.multiselect("Events to monitor", options=names, default=default_names)

    # Async actions
    if app.contract_address and app.abi_events:
        selected_events = [e for e in app.abi_events if e.get("name") in app.selected_event_names]
        if selected_events:
            # For now, use the first selected event ABI
            event_abi = selected_events[0]

            # Clients
            blockscout = BlockscoutClient(base_url=cfg["blockscout_api"], api_key=None, rate_limit_qps=app.rate_limit_qps)
            rpc = RpcClient(base_url=cfg["ankr_rpc"])

            if app.trigger_initial_sync:
                try:
                    with st.spinner("Running initial sync..."):
                        st.info(f"Syncing from block {app.from_block} for contract {app.contract_address}")
                        res = asyncio.run(run_initial_sync(
                            blockscout_client=blockscout,
                            rpc_client=rpc,
                            address=app.contract_address,
                            event_abi=event_abi,
                            from_block=app.from_block,
                            page_size=app.page_size,
                            decimals=app.token_decimals,
                        ))
                        app.events = res.events
                        app.last_block = res.cursor.last_block
                        app.trigger_initial_sync = False
                        if not res.events:
                            st.warning(f"No events found from block {app.from_block}. Try a different block range or check the contract address.")
                        else:
                            st.success(f"Found {len(res.events)} events, last block: {res.cursor.last_block}")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Initial Sync failed: {exc}")
                    app.trigger_initial_sync = False

            if app.live_running:
                try:
                    with st.spinner("Live updating..."):
                        res2 = asyncio.run(run_live_tick(
                            blockscout_client=blockscout,
                            rpc_client=rpc,
                            address=app.contract_address,
                            event_abi=event_abi,
                            existing_events=app.events,
                            confirmation_blocks=app.confirmation_blocks,
                            page_size=app.page_size,
                            decimals=app.token_decimals,
                        ))
                        app.events = res2.events
                        app.last_block = res2.cursor.last_block
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Live update failed: {exc}")
                    app.live_running = False

            # Trigger browser auto-refresh using a lightweight meta refresh
            refresh_seconds = max(1, int(app.poll_interval_ms / 1000))
            components_html(
                f"<meta http-equiv='refresh' content='{refresh_seconds}'>",
                height=0,
            )

    render_main()


if __name__ == "__main__":
    main()


