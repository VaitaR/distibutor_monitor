from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import eth_abi
import pytest
from eth_utils import event_abi_to_log_topic, to_checksum_address

from streamlit_app.core.sync import Cursor, SyncResult, initial_sync


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


def test_initial_sync_paginates_decodes_and_dedups() -> None:
    event_abi = _make_claim_event_abi()
    topic0 = event_abi_to_log_topic(event_abi).hex()
    claimer = to_checksum_address("0x000000000000000000000000000000000000dEaD")
    amount = 10**6

    def mk_log(block: int, idx: int) -> dict[str, Any]:
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

    page1: list[dict[str, Any]] = [mk_log(100, 0), mk_log(101, 0)]
    page2: list[dict[str, Any]] = [mk_log(102, 0)]

    mock_client = Mock()
    mock_client.fetch_logs_paginated = Mock(return_value=page1 + page2)  # type: ignore[attr-defined]

    result: SyncResult = initial_sync(
        blockscout_client=mock_client,
        address=to_checksum_address("0x2222222222222222222222222222222222222222"),
        event_abi=event_abi,
        from_block=0,
        to_block=99999999,
        page_size=1000,
        decimals=6,
    )

    assert isinstance(result.cursor, Cursor)
    assert result.cursor.last_block == 102
    assert result.aggregates.total_claimed_raw == 3 * amount
    assert result.aggregates.unique_claimers == 1
    # Idempotence: re-running should not double count
    result2: SyncResult = initial_sync(
        blockscout_client=mock_client,
        address=to_checksum_address("0x2222222222222222222222222222222222222222"),
        event_abi=event_abi,
        from_block=0,
        to_block=99999999,
        page_size=1000,
        decimals=6,
        existing_events=result.events,
    )
    assert result2.aggregates.total_claimed_raw == result.aggregates.total_claimed_raw


