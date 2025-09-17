from __future__ import annotations

import importlib
import pytest


def test_app_imports_without_errors() -> None:
    pytest.importorskip("streamlit")
    module = importlib.import_module("streamlit_app.app")
    assert hasattr(module, "main")

