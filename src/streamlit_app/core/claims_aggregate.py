from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal, getcontext
from typing import Any

getcontext().prec = 78


@dataclass(frozen=True)
class ClaimsAggregate:
    total_claimed_raw: int
    total_claimed_adj: Decimal
    unique_claimers: int
    claims_count: int
    distribution_by_address: dict[str, Decimal]


def _to_decimal(value: int, decimals: int) -> Decimal:
    factor: Decimal = Decimal(10) ** decimals
    return Decimal(value) / factor


def deduplicate_events(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, int]] = set()
    out: list[dict[str, Any]] = []
    for e in events:
        key = (str(e.get("tx_hash", "")), int(e.get("log_index", 0)))
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def aggregate_claims(events: Iterable[dict[str, Any]], *, decimals: int) -> ClaimsAggregate:
    total_raw: int = 0
    dist: dict[str, Decimal] = {}
    claimers: set[str] = set()
    count: int = 0
    for e in events:
        claimer = str(e.get("claimer", "")).lower()
        amount_raw = int(e.get("amount_raw", 0))
        total_raw += amount_raw
        dist[claimer] = dist.get(claimer, Decimal(0)) + _to_decimal(amount_raw, decimals)
        claimers.add(claimer)
        count += 1

    return ClaimsAggregate(
        total_claimed_raw=total_raw,
        total_claimed_adj=_to_decimal(total_raw, decimals),
        unique_claimers=len(claimers),
        claims_count=count,
        distribution_by_address=dist,
    )


def build_cumulative_series(events: Iterable[dict[str, Any]], *, decimals: int) -> list[tuple[int, Decimal]]:
    # sort by timestamp, then block/log for stability
    items: list[dict[str, Any]] = sorted(
        list(events), key=lambda e: (int(e.get("timestamp", 0)), int(e.get("block_number", 0)), int(e.get("log_index", 0)))
    )
    cumulative: Decimal = Decimal(0)
    series: list[tuple[int, Decimal]] = []
    for e in items:
        cumulative += _to_decimal(int(e.get("amount_raw", 0)), decimals)
        series.append((int(e.get("timestamp", 0)), cumulative))
    return series


