from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, cast

from eth_utils.abi import event_abi_to_log_topic

from .claims_aggregate import ClaimsAggregate, aggregate_claims, deduplicate_events
from .decode import decode_logs


@dataclass
class Cursor:
    last_block: int


@dataclass
class SyncResult:
    events: list[dict[str, Any]]
    aggregates: ClaimsAggregate
    cursor: Cursor


async def initial_sync(
    *,
    blockscout_client: Any,
    address: str,
    event_abi: dict[str, Any],
    from_block: int,
    to_block: int,
    page_size: int,
    decimals: int,
    existing_events: Iterable[dict[str, Any]] | None = None,
) -> SyncResult:
    topic0_raw: str = event_abi_to_log_topic(cast(Any, event_abi)).hex()
    topic0: str = "0x" + topic0_raw if not topic0_raw.startswith("0x") else topic0_raw
    logs = await blockscout_client.fetch_logs_paginated(
        address=address,
        topic0=topic0,
        from_block=from_block,
        to_block=to_block,
        page_size=page_size,
    )
    decoded = decode_logs([event_abi], logs)
    merged: list[dict[str, Any]] = list(existing_events or []) + decoded
    deduped = deduplicate_events(merged)
    last_block = max((int(e.get("block_number", 0)) for e in deduped), default=0)
    aggregates = aggregate_claims(deduped, decimals=decimals)
    return SyncResult(events=deduped, aggregates=aggregates, cursor=Cursor(last_block=last_block))


async def incremental_sync(
    *,
    blockscout_client: Any,
    address: str,
    event_abi: dict[str, Any],
    latest_block: int,
    confirmation_blocks: int,
    page_size: int,
    decimals: int,
    existing_events: Iterable[dict[str, Any]],
) -> SyncResult:
    # Determine from_block with overlap window to guard against reorg
    existing_list: list[dict[str, Any]] = list(existing_events)
    last_block: int = max((int(e.get("block_number", 0)) for e in existing_list), default=0)
    from_block: int = max(0, last_block - confirmation_blocks)
    to_block: int = max(0, latest_block - confirmation_blocks) if confirmation_blocks > 0 else latest_block

    topic0_raw: str = event_abi_to_log_topic(cast(Any, event_abi)).hex()
    topic0: str = "0x" + topic0_raw if not topic0_raw.startswith("0x") else topic0_raw
    logs = await blockscout_client.fetch_logs_paginated(
        address=address,
        topic0=topic0,
        from_block=from_block,
        to_block=to_block,
        page_size=page_size,
    )
    decoded_new = decode_logs([event_abi], logs)

    # Normalize existing events: if items look like raw logs, decode them
    raw_logs: list[dict[str, Any]] = [e for e in existing_list if "tx_hash" not in e]
    already_norm: list[dict[str, Any]] = [e for e in existing_list if "tx_hash" in e]
    decoded_existing: list[dict[str, Any]] = []
    if raw_logs:
        decoded_existing = decode_logs([event_abi], raw_logs)

    merged: list[dict[str, Any]] = already_norm + decoded_existing + decoded_new
    deduped = deduplicate_events(merged)
    new_last_block = max((int(e.get("block_number", 0)) for e in deduped), default=last_block)
    aggregates = aggregate_claims(deduped, decimals=decimals)
    return SyncResult(events=deduped, aggregates=aggregates, cursor=Cursor(last_block=new_last_block))


