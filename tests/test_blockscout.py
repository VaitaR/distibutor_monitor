from __future__ import annotations

from typing import Any
from unittest.mock import Mock

from streamlit_app.datasources.blockscout import BlockscoutClient


def test_blockscout_pagination_mocked() -> None:
    client = BlockscoutClient(
        base_url="https://example/api",
        api_key=None,
        rate_limit_qps=100.0,
    )

    page1: list[dict[str, Any]] = [
        {
            "address": "0x1",
            "topics": ["0xabc"],
            "data": "0x",
            "blockNumber": 1,
            "transactionHash": "0x11",
            "logIndex": 0,
            "timeStamp": 1000,
        }
    ]
    page2: list[dict[str, Any]] = [
        {
            "address": "0x1",
            "topics": ["0xabc"],
            "data": "0x",
            "blockNumber": 2,
            "transactionHash": "0x12",
            "logIndex": 0,
            "timeStamp": 1001,
        }
    ]

    # Monkeypatch the internal page fetcher
    client._get_logs_page = Mock(side_effect=[page1, page2, []])  # type: ignore[attr-defined]

    logs = client.fetch_logs_paginated(
        address="0x1111111111111111111111111111111111111111",
        topic0="0xabc",
        from_block=0,
        to_block=100,
        page_size=1,
    )

    assert [log_item["transactionHash"] for log_item in logs] == ["0x11", "0x12"]


def test_blockscout_normalizes_hex_fields() -> None:
    client = BlockscoutClient(
        base_url="https://example/api",
        api_key=None,
        rate_limit_qps=0.0,
    )

    class FakeResp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {
                "result": [
                    {
                        "address": "0x1",
                        "topics": ["0xabc"],
                        "data": "0x",
                        "blockNumber": "0x2",
                        "transactionHash": "0x12",
                        "logIndex": "0x0",
                        "timeStamp": "0x3e9",
                    }
                ]
            }

    # Monkeypatch HTTP get to return hex-like payload
    client._client.get = Mock(return_value=FakeResp())  # type: ignore[attr-defined]

    logs = client._get_logs_page(
        address="0x1111111111111111111111111111111111111111",
        topic0="0xabc",
        from_block=0,
        to_block=100,
        page=1,
        offset=1000,
    )

    assert len(logs) == 1
    item = logs[0]
    assert item["blockNumber"] == 2
    assert item["logIndex"] == 0
    assert item["timeStamp"] == 1001


