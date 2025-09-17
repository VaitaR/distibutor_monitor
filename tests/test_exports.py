from __future__ import annotations

from typing import Any, Dict, List

from streamlit_app.core.exports import build_snapshot, events_to_csv


def test_build_snapshot_and_csv() -> None:
    events: List[Dict[str, Any]] = [
        {
            "claimer": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "amount_raw": 1_000_000,
            "tx_hash": "0x01",
            "block_number": 10,
            "log_index": 0,
            "timestamp": 1000,
        },
        {
            "claimer": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "amount_raw": 2_000_000,
            "tx_hash": "0x02",
            "block_number": 12,
            "log_index": 0,
            "timestamp": 1200,
        },
    ]

    snapshot = build_snapshot(
        chain="sepolia",
        contract="0xcccccccccccccccccccccccccccccccccccccccc",
        events=events,
        decimals=6,
    )
    assert snapshot["chain"] == "sepolia"
    assert snapshot["contract"] == "0xcccccccccccccccccccccccccccccccccccccccc"
    assert snapshot["last_block"] == 12
    assert snapshot["claimed_by"] == {
        "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": "1",
        "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb": "2",
    }

    csv_text = events_to_csv(events)
    assert "claimer,amount_raw,tx_hash,block_number,log_index,timestamp" in csv_text.splitlines()[0]
    assert ",1_000_000,".replace("_", "") in csv_text


