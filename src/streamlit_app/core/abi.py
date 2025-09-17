from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any


class AbiError(Exception):
    """Raised when ABI parsing or validation fails."""


def load_abi_from_json(data: bytes | str) -> list[dict[str, Any]]:
    """Load ABI from JSON bytes or string.

    Args:
        data: JSON content as bytes or string.

    Returns:
        Parsed ABI list.
    """
    text: str
    if isinstance(data, bytes):
        text = data.decode("utf-8")
    else:
        text = data

    parsed = json.loads(text)
    if not isinstance(parsed, list):
        raise AbiError("ABI root must be a list of entries")
    return parsed


def find_claim_events(abi: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Find events whose name contains the substring 'claim' (case-insensitive).

    Args:
        abi: Iterable of ABI entries.

    Returns:
        List of ABI event entries matching the predicate, sorted by name.
    """
    events: list[dict[str, Any]] = []
    for entry in abi:
        if not isinstance(entry, dict):
            continue
        if entry.get("type") != "event":
            continue
        name = str(entry.get("name", ""))
        if "claim" in name.lower():
            events.append(entry)
    return sorted(events, key=lambda e: str(e.get("name", "")))


def find_all_events(abi: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Find all events in the ABI.

    Args:
        abi: Iterable of ABI entries.

    Returns:
        List of all ABI event entries, sorted by name.
    """
    events: list[dict[str, Any]] = []
    for entry in abi:
        if not isinstance(entry, dict):
            continue
        if entry.get("type") != "event":
            continue
        events.append(entry)
    return sorted(events, key=lambda e: str(e.get("name", "")))


