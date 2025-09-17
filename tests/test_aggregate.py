from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List

from streamlit_app.core.claims_aggregate import (
    aggregate_claims,
    deduplicate_events,
    build_cumulative_series,
)


def _mk_evt(claimer: str, amount_raw: int, block: int, ts: int, idx: int) -> Dict[str, Any]:
    return {
        "claimer": claimer,
        "amount_raw": amount_raw,
        "tx_hash": f"0x{block:064x}",
        "block_number": block,
        "log_index": idx,
        "timestamp": ts,
    }


def test_deduplicate_and_aggregate_and_cumulative() -> None:
    events: List[Dict[str, Any]] = [
        _mk_evt("0xAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAa", 1_000_000, 10, 1000, 0),
        _mk_evt("0xBbBbBbBbBbBbBbBbBbBbBbBbBbBbBbBbBbBbBbBb", 2_000_000, 11, 1100, 0),
        _mk_evt("0xAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAa", 500_000, 12, 1200, 0),
        # duplicate of first (same tx_hash, log_index)
        {
            "claimer": "0xAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAa",
            "amount_raw": 1_000_000,
            "tx_hash": f"0x{10:064x}",
            "block_number": 10,
            "log_index": 0,
            "timestamp": 1000,
        },
    ]

    deduped = deduplicate_events(events)
    assert len(deduped) == 3

    agg = aggregate_claims(deduped, decimals=6)
    assert agg.total_claimed_raw == 3_500_000
    assert agg.total_claimed_adj == Decimal("3.5")
    assert agg.unique_claimers == 2
    assert agg.claims_count == 3
    assert agg.distribution_by_address == {
        "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": Decimal("1.5"),
        "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb": Decimal("2"),
    }

    cum = build_cumulative_series(deduped, decimals=6)
    # Verify cumulative grows and last value equals total
    assert cum[-1][1] == Decimal("3.5")


