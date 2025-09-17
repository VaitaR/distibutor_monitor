from __future__ import annotations

import csv
import io
from collections.abc import Iterable
from typing import Any

from .claims_aggregate import aggregate_claims


def build_snapshot(*, chain: str, contract: str, events: Iterable[dict[str, Any]], decimals: int) -> dict[str, Any]:
    events_list: list[dict[str, Any]] = list(events)
    agg = aggregate_claims(events_list, decimals=decimals)
    last_block: int = max((int(e.get("block_number", 0)) for e in events_list), default=0)

    # Distribution with string amounts to preserve exact decimal text
    claimed_by: dict[str, str] = {addr: str(amount.normalize()) for addr, amount in agg.distribution_by_address.items()}

    return {
        "chain": chain,
        "contract": contract,
        "last_block": last_block,
        "claimed_by": claimed_by,
    }


def events_to_csv(events: Iterable[dict[str, Any]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["claimer", "amount_raw", "tx_hash", "block_number", "log_index", "timestamp"])
    for e in events:
        writer.writerow(
            [
                str(e.get("claimer", "")),
                int(e.get("amount_raw", 0)),
                str(e.get("tx_hash", "")),
                int(e.get("block_number", 0)),
                int(e.get("log_index", 0)),
                int(e.get("timestamp", 0)),
            ]
        )
    return buf.getvalue()


