from __future__ import annotations

from typing import Any, List, Dict

from streamlit_app.core.abi import find_claim_events, load_abi_from_json


def test_find_claim_events_by_name_and_signature() -> None:
    abi: List[Dict[str, Any]] = [
        {
            "type": "event",
            "name": "Transfer",
            "inputs": [
                {"name": "from", "type": "address", "indexed": True},
                {"name": "to", "type": "address", "indexed": True},
                {"name": "value", "type": "uint256", "indexed": False},
            ],
            "anonymous": False,
        },
        {
            "type": "event",
            "name": "Claim",
            "inputs": [
                {"name": "account", "type": "address", "indexed": False},
                {"name": "amount", "type": "uint256", "indexed": False},
            ],
            "anonymous": False,
        },
        {
            "type": "event",
            "name": "AirdropClaim",
            "inputs": [
                {"name": "claimer", "type": "address", "indexed": False},
                {"name": "amount", "type": "uint256", "indexed": False},
                {"name": "salt", "type": "bytes32", "indexed": False},
            ],
            "anonymous": False,
        },
    ]

    events = find_claim_events(abi)
    names = sorted(e["name"] for e in events)
    assert names == ["AirdropClaim", "Claim"]


def test_load_abi_from_json_bytes() -> None:
    abi_json_bytes: bytes = (
        b"[{'type':'event','name':'Claim','inputs':[{'name':'a','type':'address','indexed':false},{'name':'amount','type':'uint256','indexed':false}], 'anonymous': false}]".replace(
            b"'", b'"'
        )
    )
    abi = load_abi_from_json(abi_json_bytes)
    assert isinstance(abi, list)
    assert len(abi) == 1
    assert abi[0]["name"] == "Claim"


