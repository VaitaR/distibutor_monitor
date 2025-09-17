from __future__ import annotations

import os
from typing import TypedDict


class NetworkTemplate(TypedDict):
    chain_id: int
    blockscout_api: str
    etherscan_api: str
    ankr_rpc: str


NETWORKS: dict[str, NetworkTemplate] = {
    "mainnet": {
        "chain_id": 1,
        "blockscout_api": "https://eth.blockscout.com/api",
        "etherscan_api": "https://api.etherscan.io/api",
        "ankr_rpc": "https://rpc.ankr.com/eth/YOUR_API_KEY",
    },
    "sepolia": {
        "chain_id": 11155111,
        "blockscout_api": "https://eth-sepolia.blockscout.com/api",
        "etherscan_api": "https://api-sepolia.etherscan.io/api",
        "ankr_rpc": "https://rpc.ankr.com/eth_sepolia/YOUR_API_KEY",
    },
}

PAGE_SIZE_DEFAULT: int = 1000
API_QPS: int = 3
CACHE_TTL_SEC: int = 30


def _with_ankr_key(url_template: str) -> str:
    key = os.getenv("ANKR_API_KEY")
    if not key:
        return url_template
    if "<API_KEY>" in url_template:
        return url_template.replace("<API_KEY>", key)
    if "YOUR_API_KEY" in url_template:
        return url_template.replace("YOUR_API_KEY", key)
    return url_template


def _with_etherscan_key(url: str) -> str:
    key = os.getenv("ETHERSCAN_API_KEY")
    # Only append apikey when calling; here we keep base URL clean
    return url if not key else url


def resolve_network_config(name: str) -> NetworkTemplate:
    base: NetworkTemplate = NETWORKS[name]
    return NetworkTemplate(
        chain_id=base["chain_id"],
        blockscout_api=base["blockscout_api"],
        etherscan_api=_with_etherscan_key(base["etherscan_api"]),
        ankr_rpc=_with_ankr_key(base["ankr_rpc"]),
    )


