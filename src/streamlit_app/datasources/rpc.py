from __future__ import annotations

import httpx


class RpcClient:
    def __init__(self, *, base_url: str) -> None:
        self._base_url = base_url
        self._client = httpx.AsyncClient(timeout=20.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def get_latest_block_number(self) -> int:
        payload = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
        resp = await self._client.post(self._base_url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        result = data.get("result")
        if isinstance(result, str) and result.startswith("0x"):
            return int(result, 16)
        # Fallback if numeric
        try:
            return int(result)
        except Exception:
            return 0


