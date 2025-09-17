from __future__ import annotations

import os
from typing import Optional

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None  # type: ignore[assignment]


def load_secrets_from_dotenv() -> None:
    """Load environment variables from a .env file if python-dotenv is installed."""
    if load_dotenv is not None:
        load_dotenv(override=False)


def get_ankr_api_key() -> Optional[str]:
    return os.getenv("ANKR_API_KEY")


def get_etherscan_api_key() -> Optional[str]:
    return os.getenv("ETHERSCAN_API_KEY")
