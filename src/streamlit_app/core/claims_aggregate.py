from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, getcontext
from typing import Any, Dict, Iterable, List, Tuple

getcontext().prec = 78


@dataclass(frozen=True)
class ClaimsAggregate:
    total_claimed_raw: int
    total_claimed_adj: Decimal
    unique_claimers: int
    claims_count: int
    distribution_by_address: Dict[str, Decimal]


def _to_decimal(value: int, decimals: int) -> Decimal:
    factor: Decimal = Decimal(10) ** decimals
    return Decimal(value) / factor


def deduplicate_events(events: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[Tuple[str, int]] = set()
    out: List[Dict[str, Any]] = []
    for e in events:
        key = (str(e.get("tx_hash", "")), int(e.get("log_index", 0)))
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def aggregate_claims(events: Iterable[Dict[str, Any]], *, decimals: int) -> ClaimsAggregate:
    total_raw: int = 0
    dist: Dict[str, Decimal] = {}
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


def build_cumulative_series(events: Iterable[Dict[str, Any]], *, decimals: int) -> List[Tuple[int, Decimal]]:
    # sort by timestamp, then block/log for stability
    items: List[Dict[str, Any]] = sorted(
        list(events), key=lambda e: (int(e.get("timestamp", 0)), int(e.get("block_number", 0)), int(e.get("log_index", 0)))
    )
    cumulative: Decimal = Decimal(0)
    series: List[Tuple[int, Decimal]] = []
    for e in items:
        cumulative += _to_decimal(int(e.get("amount_raw", 0)), decimals)
        series.append((int(e.get("timestamp", 0)), cumulative))
    return series


