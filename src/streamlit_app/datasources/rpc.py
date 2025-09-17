from __future__ import annotations

import httpx


class RpcClient:
    def __init__(self, *, base_url: str) -> None:
        self._base_url = base_url
        self._client = httpx.Client(timeout=20.0)  # Synchronous client

    def close(self) -> None:
        self._client.close()

    def get_latest_block_number(self) -> int:
        """Get latest block number synchronously."""
        payload = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
        resp = self._client.post(self._base_url, json=payload)
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


