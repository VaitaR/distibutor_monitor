from __future__ import annotations

import asyncio
import datetime
import sys
from pathlib import Path

import streamlit as st

# Add src directory to Python path for imports
SRC_DIR = str(Path(__file__).resolve().parents[1])
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from streamlit_app.config import resolve_network_config
from streamlit_app.core.abi import find_all_events, load_abi_from_json
from streamlit_app.core.app_logic import run_initial_sync, run_live_tick
from streamlit_app.datasources.blockscout import BlockscoutClient
from streamlit_app.datasources.rpc import RpcClient
from streamlit_app.ui.sidebar import render_sidebar
from streamlit_app.ui.state import ensure_session_state
from streamlit_app.ui.views import render_main
from streamlit_app.utils.secrets import load_secrets_from_dotenv


# Cache heavy resources (connections, clients)
@st.cache_resource
def get_clients(chain: str) -> tuple[BlockscoutClient, RpcClient]:
    """Get cached Blockscout and RPC clients."""
    network_config = resolve_network_config(chain)
    blockscout = BlockscoutClient(
        base_url=network_config["blockscout_api"],
        api_key=None,
        rate_limit_qps=3.0,  # Will be overridden by user setting
    )
    rpc = RpcClient(base_url=network_config["ankr_rpc"])
    return blockscout, rpc


def main() -> None:
    load_secrets_from_dotenv()
    st.set_page_config(page_title="Distributor Monitor", layout="wide")
    st.title("Distributor Monitor")
    render_sidebar()

    app = ensure_session_state(st)

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

            # Clients (cached for better performance)
            blockscout, rpc = get_clients(app.chain)
            # Update rate limit from user settings
            blockscout._qps = app.rate_limit_qps

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
                        app.last_sync_time = datetime.datetime.now()
                        app.trigger_initial_sync = False
                        if not res.events:
                            st.warning(f"No events found from block {app.from_block}. Try a different block range or check the contract address.")
                        else:
                            st.success(f"Found {len(res.events)} events, last block: {res.cursor.last_block}")
                except Exception as exc:
                    st.error(f"Initial Sync failed: {exc}")
                    app.trigger_initial_sync = False

            # Native Streamlit auto-refresh approach (much simpler and more reliable)
            if app.live_running:
                try:
                    current_time = datetime.datetime.now()
                    st.info(f"🔄 Live mode active - updating at {current_time.strftime('%H:%M:%S')}")

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
                        app.last_sync_time = current_time

                        refresh_seconds = max(1, int(app.poll_interval_ms / 1000))
                        st.success(f"✅ Live update completed - next update in {refresh_seconds}s")

                    # Native Streamlit auto-refresh: sleep + rerun
                    import time
                    time.sleep(refresh_seconds)
                    st.rerun()

                except Exception as exc:
                    st.error(f"Live update failed: {exc}")
                    app.live_running = False

    render_main()


if __name__ == "__main__":
    main()


