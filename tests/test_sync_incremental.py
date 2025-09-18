from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import eth_abi
from eth_utils import event_abi_to_log_topic, to_checksum_address

from streamlit_app.core.sync import SyncResult, incremental_sync


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


def test_incremental_sync_with_overlap_confirmation_window() -> None:
    event_abi = _make_claim_event_abi()
    claimer = to_checksum_address("0x000000000000000000000000000000000000dEaD")
    amount = 10**6

    # Existing events up to block 200
    existing = [
        _mk_log(event_abi, 198, 0, claimer, amount),
        _mk_log(event_abi, 199, 0, claimer, amount),
        _mk_log(event_abi, 200, 0, claimer, amount),
    ]

    # New logs from 195..205 will be returned (overlap 5 blocks)
    new_logs: list[dict[str, Any]] = [
        _mk_log(event_abi, 201, 0, claimer, amount),
        _mk_log(event_abi, 202, 0, claimer, amount),
        _mk_log(event_abi, 205, 0, claimer, amount),
    ]

    mock_client = Mock()
    mock_client.fetch_logs_paginated = Mock(return_value=new_logs)  # type: ignore[attr-defined]

    res: SyncResult = incremental_sync(
        blockscout_client=mock_client,
        address=to_checksum_address("0x2222222222222222222222222222222222222222"),
        event_abi=event_abi,
        latest_block=210,
        confirmation_blocks=5,
        page_size=1000,
        decimals=6,
        existing_events=existing,
    )

    # Should contain existing + new (deduped) and update cursor to <= 205
    assert res.cursor.last_block == 205
    assert res.aggregates.claims_count == len(res.events)
    # No duplicates beyond tx_hash/log_index uniqueness
    keys = {(e["tx_hash"], e["log_index"]) for e in res.events}
    assert len(keys) == len(res.events)

