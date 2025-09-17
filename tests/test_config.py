from __future__ import annotations

from typing import Any

from streamlit_app.config import resolve_network_config


def test_resolve_network_config_inserts_ankr_key_from_env(monkeypatch: Any) -> None:
    monkeypatch.setenv("ANKR_API_KEY", "TESTKEY")
    cfg = resolve_network_config("sepolia")
    assert cfg["ankr_rpc"].endswith("/TESTKEY")


def test_resolve_network_config_etherscan_optional(monkeypatch: Any) -> None:
    monkeypatch.delenv("ETHERSCAN_API_KEY", raising=False)
    cfg = resolve_network_config("mainnet")
    # Etherscan URL should remain unchanged if no key
    assert "apikey=" not in cfg["etherscan_api"]


