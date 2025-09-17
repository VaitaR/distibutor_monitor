from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .sync import SyncResult, incremental_sync, initial_sync


def run_initial_sync(
    *,
    blockscout_client: Any,
    rpc_client: Any,
    address: str,
    event_abi: dict[str, Any],
    from_block: int,
    page_size: int,
    decimals: int,
) -> SyncResult:
    """Synchronous initial sync."""
    latest_block: int = rpc_client.get_latest_block_number()  # Remove await
    if latest_block <= 0:
        # Fallback if RPC is not configured/available. Use a very high block number
        # so Blockscout effectively treats it as latest.
        latest_block = 999_999_999
    return initial_sync(  # Remove await
        blockscout_client=blockscout_client,
        address=address,
        event_abi=event_abi,
        from_block=from_block,
        to_block=latest_block,
        page_size=page_size,
        decimals=decimals,
    )


def run_live_tick(
    *,
    blockscout_client: Any,
    rpc_client: Any,
    address: str,
    event_abi: dict[str, Any],
    existing_events: Iterable[dict[str, Any]],
    confirmation_blocks: int,
    page_size: int,
    decimals: int,
) -> SyncResult:
    """Synchronous live tick."""
    latest_block: int = rpc_client.get_latest_block_number()  # Remove await
    if latest_block <= 0:
        # If we cannot get latest, do a no-op tick to avoid clearing data
        from .claims_aggregate import aggregate_claims
        from .sync import Cursor

        events_list = list(existing_events)
        aggregates = aggregate_claims(events_list, decimals=decimals)
        last_block = max((int(e.get("block_number", 0)) for e in events_list), default=0)
        return SyncResult(events=events_list, aggregates=aggregates, cursor=Cursor(last_block=last_block))
    return incremental_sync(  # Remove await
        blockscout_client=blockscout_client,
        address=address,
        event_abi=event_abi,
        latest_block=latest_block,
        confirmation_blocks=confirmation_blocks,
        page_size=page_size,
        decimals=decimals,
        existing_events=existing_events,
    )


