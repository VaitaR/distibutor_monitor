from __future__ import annotations

from typing import Any, Dict

import eth_abi
from eth_utils import event_abi_to_log_topic, to_checksum_address

from streamlit_app.core.decode import decode_logs


def test_decode_claim_log_nonindexed() -> None:
    event_abi: Dict[str, Any] = {
        "type": "event",
        "name": "Claim",
        "inputs": [
            {"name": "account", "type": "address", "indexed": False},
            {"name": "amount", "type": "uint256", "indexed": False},
        ],
        "anonymous": False,
    }

    topic0 = event_abi_to_log_topic(event_abi).hex()
    claimer = to_checksum_address("0x000000000000000000000000000000000000dEaD")
    amount = 123_456_789
    data_bytes = eth_abi.encode(["address", "uint256"], [claimer, amount])
    log: Dict[str, Any] = {
        "address": to_checksum_address("0x1111111111111111111111111111111111111111"),
        "topics": [topic0],
        "data": "0x" + data_bytes.hex(),
        "blockNumber": 100,
        "transactionHash": "0x" + "ab" * 32,
        "logIndex": 0,
        "timeStamp": 1_700_000_000,
    }

    decoded = decode_logs([event_abi], [log])
    assert len(decoded) == 1
    evt = decoded[0]
    assert evt["claimer"] == claimer
    assert evt["amount_raw"] == amount
    assert evt["tx_hash"] == log["transactionHash"]
    assert evt["block_number"] == 100
    assert evt["log_index"] == 0
    assert evt["timestamp"] == 1_700_000_000


def test_decode_hex_numeric_fields() -> None:
    event_abi: Dict[str, Any] = {
        "type": "event",
        "name": "Claim",
        "inputs": [
            {"name": "account", "type": "address", "indexed": False},
            {"name": "amount", "type": "uint256", "indexed": False},
        ],
        "anonymous": False,
    }
    topic0 = event_abi_to_log_topic(event_abi).hex()
    claimer = to_checksum_address("0x000000000000000000000000000000000000dEaD")
    amount = 1
    data_bytes = eth_abi.encode(["address", "uint256"], [claimer, amount])

    log_hex: Dict[str, Any] = {
        "address": to_checksum_address("0x1111111111111111111111111111111111111111"),
        "topics": [topic0],
        "data": "0x" + data_bytes.hex(),
        "blockNumber": "0x8ca325",
        "transactionHash": "0x" + "cd" * 32,
        "logIndex": "0x0",
        "timeStamp": "0x65c8edd0",
    }

    decoded = decode_logs([event_abi], [log_hex])
    assert len(decoded) == 1
    evt = decoded[0]
    assert evt["block_number"] == int("0x8ca325", 16)
    assert evt["log_index"] == 0
    assert evt["timestamp"] == int("0x65c8edd0", 16)


