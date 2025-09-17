from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .sync import SyncResult, incremental_sync, initial_sync


async def run_initial_sync(
    *,
    blockscout_client: Any,
    rpc_client: Any,
    address: str,
    event_abi: dict[str, Any],
    from_block: int,
    page_size: int,
    decimals: int,
) -> SyncResult:
    latest_block: int = await rpc_client.get_latest_block_number()
    if latest_block <= 0:
        # Fallback if RPC is not configured/available. Use a very high block number
        # so Blockscout effectively treats it as latest.
        latest_block = 999_999_999
    return await initial_sync(
        blockscout_client=blockscout_client,
        address=address,
        event_abi=event_abi,
        from_block=from_block,
        to_block=latest_block,
        page_size=page_size,
        decimals=decimals,
    )


async def run_live_tick(
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
    latest_block: int = await rpc_client.get_latest_block_number()
    if latest_block <= 0:
        # If we cannot get latest, do a no-op tick to avoid clearing data
        return SyncResult(events=list(existing_events), aggregates=(await initial_sync(  # type: ignore[no-any-return]
            blockscout_client=blockscout_client,
            address=address,
            event_abi=event_abi,
            from_block=0,
            to_block=0,
            page_size=page_size,
            decimals=decimals,
        )).aggregates, cursor=(await initial_sync(
            blockscout_client=blockscout_client,
            address=address,
            event_abi=event_abi,
            from_block=0,
            to_block=0,
            page_size=page_size,
            decimals=decimals,
        )).cursor)  # type: ignore[no-any-return]
    return await incremental_sync(
        blockscout_client=blockscout_client,
        address=address,
        event_abi=event_abi,
        latest_block=latest_block,
        confirmation_blocks=confirmation_blocks,
        page_size=page_size,
        decimals=decimals,
        existing_events=existing_events,
    )


