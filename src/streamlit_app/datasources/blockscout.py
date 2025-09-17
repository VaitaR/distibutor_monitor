from __future__ import annotations

import asyncio
from typing import Any

import httpx


def _parse_int(value: Any) -> int:
    """Parse Blockscout/Etherscan numeric field which may be int, decimal str, or hex str.

    Returns 0 on failure.
    """
    try:
        if isinstance(value, int):
            return value
        s: str = str(value).strip()
        if s.startswith("0x") or s.startswith("0X"):
            return int(s, 16)
        return int(s)
    except Exception:
        return 0


class BlockscoutClient:
    def __init__(self, *, base_url: str, api_key: str | None, rate_limit_qps: float) -> None:
        self._base_url: str = base_url.rstrip("/")
        self._api_key: str | None = api_key
        self._qps: float = rate_limit_qps
        self._client: httpx.AsyncClient = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def _throttle(self) -> None:
        if self._qps <= 0:
            return
        await asyncio.sleep(1.0 / self._qps)

    async def _get_logs_page(
        self,
        *,
        address: str,
        topic0: str,
        from_block: int,
        to_block: int,
        page: int,
        offset: int,
    ) -> list[dict[str, Any]]:
        params = {
            "module": "logs",
            "action": "getLogs",
            "address": address,
            "fromBlock": str(from_block),
            "toBlock": str(to_block),
            "page": str(page),
            "offset": str(offset),
            "sort": "asc",
        }
        # Only add topic0 if it's not empty
        if topic0:
            params["topic0"] = topic0
        if self._api_key:
            params["apikey"] = self._api_key

        await self._throttle()
        resp = await self._client.get(f"{self._base_url}", params=params)
        resp.raise_for_status()
        data = resp.json()
        result = data.get("result")
        if not isinstance(result, list):
            return []
        # Normalize field types
        out: list[dict[str, Any]] = []
        for item in result:
            out.append(
                {
                    "address": item.get("address"),
                    "topics": item.get("topics", []),
                    "data": item.get("data", "0x"),
                    "blockNumber": _parse_int(item.get("blockNumber", 0)),
                    "transactionHash": item.get("transactionHash"),
                    "logIndex": _parse_int(item.get("logIndex", 0)),
                    "timeStamp": _parse_int(item.get("timeStamp", 0)),
                }
            )
        return out

    async def fetch_logs_paginated(
        self,
        *,
        address: str,
        topic0: str,
        from_block: int,
        to_block: int,
        page_size: int,
        start_page: int = 1,
    ) -> list[dict[str, Any]]:
        page = start_page
        collected: list[dict[str, Any]] = []
        seen: set[tuple[str, int]] = set()
        max_pages: int = 10000
        pages_scanned: int = 0
        while True:
            pages_scanned += 1
            if pages_scanned > max_pages:
                break
            logs = await self._get_logs_page(
                address=address,
                topic0=topic0,
                from_block=from_block,
                to_block=to_block,
                page=page,
                offset=page_size,
            )
            if not logs:
                break
            added_this_page: int = 0
            for item in logs:
                tx_hash: str = str(item.get("transactionHash", ""))
                log_index: int = _parse_int(item.get("logIndex", 0))
                key = (tx_hash, log_index)
                if key in seen:
                    continue
                seen.add(key)
                collected.append(item)
                added_this_page += 1
            # If no new items were added, pages likely repeat -> stop to avoid infinite loop
            if added_this_page == 0:
                break
            page += 1
        return collected


