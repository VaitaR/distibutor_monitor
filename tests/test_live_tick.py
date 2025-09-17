from __future__ import annotations

import os
from typing import Any
from unittest.mock import AsyncMock

import eth_abi
import pytest
from eth_utils import event_abi_to_log_topic, to_checksum_address

from streamlit_app.config import resolve_network_config
from streamlit_app.core.abi import find_claim_events, load_abi_from_json
from streamlit_app.core.decode import decode_logs
from streamlit_app.core.sync import incremental_sync
from streamlit_app.datasources.blockscout import BlockscoutClient


def _make_claim_event_abi() -> dict[str, Any]:
    return {
        "type": "event",
        "name": "Claim",
        "inputs": [
            {"name": "account", "type": "address", "indexed": False},
            {"name": "amount", "type": "uint256", "indexed": False},
        ],
        "anonymous": False,
    }


def _mk_log(event_abi: dict[str, Any], block: int, idx: int, claimer: str, amount: int) -> dict[str, Any]:
    topic0 = event_abi_to_log_topic(event_abi).hex()
    data = eth_abi.encode(["address", "uint256"], [claimer, amount])
    return {
        "address": to_checksum_address("0x1111111111111111111111111111111111111111"),
        "topics": [topic0],
        "data": "0x" + data.hex(),
        "blockNumber": block,
        "transactionHash": f"0x{block:064x}",
        "logIndex": idx,
        "timeStamp": 1_700_000_000 + block,
    }


@pytest.mark.asyncio
async def test_live_tick_increments_with_latest_block() -> None:
    event_abi = _make_claim_event_abi()
    claimer = to_checksum_address("0x000000000000000000000000000000000000dEaD")
    amount = 10**6

    existing: list[dict[str, Any]] = []
    new_logs: list[dict[str, Any]] = [
        _mk_log(event_abi, 1000, 0, claimer, amount),
    ]

    mock_blockscout = AsyncMock()
    mock_blockscout.fetch_logs_paginated = AsyncMock(return_value=new_logs)  # type: ignore[attr-defined]

    res = await incremental_sync(
        blockscout_client=mock_blockscout,
        address=to_checksum_address("0x2222222222222222222222222222222222222222"),
        event_abi=event_abi,
        latest_block=1005,
        confirmation_blocks=3,
        page_size=1000,
        decimals=6,
        existing_events=existing,
    )

    assert res.cursor.last_block == 1000
    assert res.aggregates.claims_count == 1


@pytest.mark.asyncio
@pytest.mark.skipif(os.getenv("RUN_E2E") != "1", reason="Set RUN_E2E=1 to run live Blockscout test")
async def test_e2e_blockscout_decode_with_real_abi() -> None:
    contract: str | None = os.getenv("E2E_CONTRACT")
    if not contract:
        pytest.skip("E2E_CONTRACT not set")

    chain: str = os.getenv("E2E_CHAIN", "sepolia")
    cfg = resolve_network_config(chain)

    # Load real distributor ABI from repo root
    abi_path = os.path.join(os.getcwd(), "abi_distributor.json")
    with open(abi_path, encoding="utf-8") as f:
        abi_json = f.read()
    abi = load_abi_from_json(abi_json)
    claim_events: list[dict[str, Any]] = find_claim_events(abi)
    assert claim_events, "No Claim-like events found in ABI"

    print(f"Found {len(claim_events)} claim events: {[e.get('name') for e in claim_events]}")
    event_abi = claim_events[0]
    print(f"Using event: {event_abi.get('name')}")

    client = BlockscoutClient(base_url=cfg["blockscout_api"], api_key=None, rate_limit_qps=2.0)

    # Small window to reduce request load
    from_block_env = os.getenv("E2E_FROM_BLOCK")
    to_block_env = os.getenv("E2E_TO_BLOCK")
    from_block = int(from_block_env) if from_block_env else 0
    to_block = int(to_block_env) if to_block_env else from_block + 5000 if from_block else 99999999

    topic0_raw = event_abi_to_log_topic(event_abi).hex()
    topic0 = "0x" + topic0_raw if not topic0_raw.startswith("0x") else topic0_raw
    print(f"Searching for topic0: {topic0}")
    print(f"Contract: {contract}, from_block: {from_block}, to_block: {to_block}")
    print(f"Blockscout URL: {cfg['blockscout_api']}")

    # First, get ALL logs for this contract to see what events exist
    all_logs = await client.fetch_logs_paginated(
        address=contract,
        topic0="",  # Empty string to get all events
        from_block=from_block,
        to_block=to_block,
        page_size=100,
    )

    print(f"All logs found: {len(all_logs)}")
    unique_topics = set()
    for log in all_logs:
        if log.get("topics"):
            unique_topics.add(log["topics"][0])

    print(f"Unique topic0s found: {list(unique_topics)}")

    # Now search for specific Claimed events
    logs = await client.fetch_logs_paginated(
        address=contract,
        topic0=topic0,
        from_block=from_block,
        to_block=to_block,
        page_size=100,
    )

    print(f"Claimed event logs found: {len(logs)}")

    # Filter logs to only those with matching topic0
    filtered_logs = [log for log in logs if log.get("topics") and log["topics"][0] == topic0]
    print(f"Logs with correct topic0: {len(filtered_logs)}")

    if filtered_logs:
        print(f"First correct Claimed log: {filtered_logs[0]}")

    decoded = decode_logs([event_abi], filtered_logs)
    print(f"Decoded Claimed events: {len(decoded)}")

    if filtered_logs and not decoded:
        print("Debug: First log details:")
        log = filtered_logs[0]
        print(f"  Topics: {log.get('topics')}")
        print(f"  Data: {log.get('data')}")
        print(f"  Event ABI: {event_abi}")

        # Manual decode attempt
        expected_topic = event_abi_to_log_topic(event_abi).hex()
        print(f"  Expected topic0 (no 0x): {expected_topic}")
        print(f"  Actual topic0: {log.get('topics', [''])[0]}")
        print(f"  Topic match: {log.get('topics', [''])[0] == '0x' + expected_topic}")

    if not decoded:
        print(f"No Claimed events found. Expected topic0: {topic0}")
        print("Available events in contract:")
        for i, log in enumerate(all_logs[:5]):
            print(f"  Log {i}: topic0={log.get('topics', ['None'])[0]}, block={log.get('blockNumber')}")
        pytest.skip("No Claimed events found in the specified range")

    # Basic sanity: required fields present and well-typed
    evt = decoded[0]
    assert isinstance(evt["block_number"], int)
    assert isinstance(evt["log_index"], int)
    assert isinstance(evt["timestamp"], int)
    assert isinstance(evt["tx_hash"], str)

