from __future__ import annotations

from typing import Any, Dict, Iterable, List, cast

from eth_abi.abi import decode as abi_decode
from eth_utils.abi import event_abi_to_log_topic
from eth_utils.address import to_checksum_address


def _topic0_hex(event_abi: Dict[str, Any]) -> str:
    return event_abi_to_log_topic(cast(Any, event_abi)).hex()


def _parse_int(value: Any) -> int:
    """Parse int from possibly hex or decimal string; return 0 on failure."""
    try:
        if isinstance(value, int):
            return value
        s: str = str(value).strip()
        if s.startswith("0x") or s.startswith("0X"):
            return int(s, 16)
        return int(s)
    except Exception:
        return 0


def decode_logs(events_abi: Iterable[Dict[str, Any]], logs: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Decode logs using provided event ABIs.

    Supports non-indexed parameters for the common Claim(address,uint256) shape.

    Returns a list of normalized event dicts with keys:
      - claimer, amount_raw, tx_hash, block_number, log_index, timestamp
    """
    abi_by_topic: Dict[str, Dict[str, Any]] = {}
    for e in events_abi:
        try:
            topic_hex = _topic0_hex(e)
            # Store both with and without 0x prefix for compatibility
            abi_by_topic[topic_hex] = e
            if topic_hex.startswith("0x"):
                abi_by_topic[topic_hex[2:]] = e
            else:
                abi_by_topic["0x" + topic_hex] = e
        except Exception:
            continue

    decoded: List[Dict[str, Any]] = []
    for log in logs:
        topics: List[str] = list(log.get("topics", []))
        if not topics:
            continue
        topic0 = topics[0]
        event_abi = abi_by_topic.get(topic0)
        if event_abi is None:
            # allow 0x prefix normalized
            event_abi = abi_by_topic.get(topic0.lower()) or abi_by_topic.get(topic0.upper())
        if event_abi is None:
            continue

        inputs: List[Dict[str, Any]] = list(event_abi.get("inputs", []))
        non_indexed_inputs = [i for i in inputs if not bool(i.get("indexed"))]
        indexed_inputs = [i for i in inputs if bool(i.get("indexed"))]
        
        non_indexed_types: List[str] = [i["type"] for i in non_indexed_inputs]

        data_hex: str = str(log.get("data", "0x"))
        if data_hex.startswith("0x"):
            data_hex = data_hex[2:]
        data_bytes = bytes.fromhex(data_hex) if data_hex else b""

        # Decode non-indexed data
        non_indexed_values: List[Any] = []
        if non_indexed_types:
            non_indexed_values = list(abi_decode(non_indexed_types, data_bytes))

        # Extract indexed values from topics (skip topic0)
        topics: List[str] = list(log.get("topics", []))
        indexed_values: List[Any] = []
        for i, indexed_input in enumerate(indexed_inputs):
            topic_index = i + 1  # Skip topic0
            if topic_index < len(topics) and topics[topic_index]:
                topic_hex = topics[topic_index]
                if topic_hex.startswith("0x"):
                    topic_hex = topic_hex[2:]
                topic_bytes = bytes.fromhex(topic_hex) if topic_hex else b""
                if indexed_input["type"] == "address":
                    # Address is padded to 32 bytes, take last 20
                    addr_bytes = topic_bytes[-20:] if len(topic_bytes) >= 20 else topic_bytes
                    indexed_values.append("0x" + addr_bytes.hex())
                elif indexed_input["type"].startswith("uint"):
                    # Decode as uint256, but cap at reasonable size to avoid overflow
                    val = int.from_bytes(topic_bytes, byteorder='big')
                    # Cap at 2^63-1 to avoid issues with pandas/arrow
                    indexed_values.append(min(val, 2**63 - 1))
                else:
                    indexed_values.append(topic_bytes)
            else:
                indexed_values.append(None)

        # Try to map common fields from both indexed and non-indexed
        claimer: str | None = None
        amount_raw: int | None = None
        
        # Check indexed parameters first
        for i, (inp, val) in enumerate(zip(indexed_inputs, indexed_values)):
            if val is None:
                continue
            typ = inp.get("type")
            name = inp.get("name", "").lower()
            if typ == "address" and claimer is None and ("user" in name or "account" in name or "claimer" in name):
                claimer = to_checksum_address(str(val))
            elif typ.startswith("uint") and amount_raw is None and "amount" in name:
                amount_raw = min(int(val), 2**63 - 1) if isinstance(val, int) else 0
        
        # Check non-indexed parameters
        for i, val in enumerate(non_indexed_values):
            inp = non_indexed_inputs[i] if i < len(non_indexed_inputs) else {}
            typ = inp.get("type")
            name = inp.get("name", "").lower()
            if typ == "address" and claimer is None and ("user" in name or "account" in name or "claimer" in name):
                claimer = to_checksum_address(str(val))
            elif typ.startswith("uint") and amount_raw is None and "amount" in name:
                amount_raw = min(int(val), 2**63 - 1) if isinstance(val, int) else 0

        decoded.append(
            {
                "claimer": claimer or "",
                "amount_raw": amount_raw if amount_raw is not None else 0,
                "tx_hash": str(log.get("transactionHash", "")),
                "block_number": _parse_int(log.get("blockNumber", 0)),
                "log_index": _parse_int(log.get("logIndex", 0)),
                "timestamp": _parse_int(log.get("timeStamp", 0)),
            }
        )

    return decoded


