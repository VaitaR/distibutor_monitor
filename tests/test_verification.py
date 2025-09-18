"""Tests for CSV verification functionality."""

from __future__ import annotations

import io
from unittest.mock import MagicMock

import pandas as pd

from streamlit_app.ui.state import AppState


def test_verification_data_structure():
    """Test that verification data is stored correctly."""
    app_state = AppState()

    # Simulate CSV data
    csv_data = """address,wave1_bard_wei,wave2_bard_wei
0x1234567890123456789012345678901234567890,1000000000000000000,2000000000000000000
0xABCDEF1234567890123456789012345678901234,500000000000000000,1500000000000000000"""

    df = pd.read_csv(io.StringIO(csv_data))

    # Process verification data like in sidebar.py
    verification_data = {}
    for _, row in df.iterrows():
        addr = str(row['address']).lower()
        wave1 = int(row['wave1_bard_wei']) if pd.notna(row['wave1_bard_wei']) else 0
        wave2 = int(row['wave2_bard_wei']) if pd.notna(row['wave2_bard_wei']) else 0
        verification_data[addr] = {
            'wave1_bard_wei': wave1,
            'wave2_bard_wei': wave2
        }

    app_state.verification_data = verification_data

    # Test data structure
    assert len(app_state.verification_data) == 2
    assert '0x1234567890123456789012345678901234567890' in app_state.verification_data
    assert app_state.verification_data['0x1234567890123456789012345678901234567890']['wave1_bard_wei'] == 1000000000000000000
    assert app_state.verification_data['0x1234567890123456789012345678901234567890']['wave2_bard_wei'] == 2000000000000000000


def test_verification_check_logic():
    """Test the verification check logic."""
    # Mock app state with verification data
    verification_data = {
        '0x1234567890123456789012345678901234567890': {
            'wave1_bard_wei': 1000000000000000000,
            'wave2_bard_wei': 2000000000000000000
        }
    }

    # Mock row data
    def create_mock_row(claimer: str, amount_raw: int):
        row = MagicMock()
        row.get.side_effect = lambda key, default=None: {
            'claimer': claimer,
            'amount_raw': amount_raw
        }.get(key, default)
        return row

    # Test matching wave1
    row1 = create_mock_row('0x1234567890123456789012345678901234567890', 1000000000000000000)

    # Simulate check_verification function from views.py
    def check_verification(row, verification_data):
        if not verification_data:
            return ""

        claimer = str(row.get('claimer', '')).lower()
        amount_raw = int(row.get('amount_raw', 0))

        if claimer in verification_data:
            expected_wave1 = verification_data[claimer]['wave1_bard_wei']
            expected_wave2 = verification_data[claimer]['wave2_bard_wei']

            # Check if amount matches either wave1 or wave2
            if amount_raw == expected_wave1 or amount_raw == expected_wave2:
                return "✅"
            else:
                return "❌"
        else:
            return "❌"  # Address not in verification data

    # Test cases
    result1 = check_verification(row1, verification_data)
    assert result1 == "✅"

    # Test matching wave2
    row2 = create_mock_row('0x1234567890123456789012345678901234567890', 2000000000000000000)
    result2 = check_verification(row2, verification_data)
    assert result2 == "✅"

    # Test non-matching amount
    row3 = create_mock_row('0x1234567890123456789012345678901234567890', 3000000000000000000)
    result3 = check_verification(row3, verification_data)
    assert result3 == "❌"

    # Test unknown address
    row4 = create_mock_row('0xunknown', 1000000000000000000)
    result4 = check_verification(row4, verification_data)
    assert result4 == "❌"

    # Test empty verification data
    result5 = check_verification(row1, {})
    assert result5 == ""


def test_duplicate_claim_detection():
    """Test detection of duplicate claims from same address."""
    verification_data = {
        '0x1234567890123456789012345678901234567890': {
            'wave1_bard_wei': 1000000000000000000,
            'wave2_bard_wei': 2000000000000000000
        }
    }

    # Mock row data
    def create_mock_row(claimer: str, amount_raw: int):
        row = MagicMock()
        row.get.side_effect = lambda key, default=None: {
            'claimer': claimer,
            'amount_raw': amount_raw
        }.get(key, default)
        return row

    # Simulate check_verification function with duplicate detection
    claim_count_by_address: dict[str, int] = {}

    def check_verification_with_duplicates(row, verification_data):
        if not verification_data:
            return ""

        claimer = str(row.get('claimer', '')).lower()
        amount_raw = int(row.get('amount_raw', 0))

        if claimer in verification_data:
            expected_wave1 = verification_data[claimer]['wave1_bard_wei']
            expected_wave2 = verification_data[claimer]['wave2_bard_wei']

            # Check if amount matches either wave1 or wave2
            if amount_raw == expected_wave1 or amount_raw == expected_wave2:
                # Track how many times this address has matched
                claim_count_by_address[claimer] = claim_count_by_address.get(claimer, 0) + 1

                if claim_count_by_address[claimer] == 1:
                    return "✅"  # First match
                else:
                    return "⚠️"  # Duplicate match (suspicious)
            else:
                return "❌"  # Amount doesn't match
        else:
            return "❌"  # Not in verification CSV

    # Test first claim - should get ✅
    row1 = create_mock_row('0x1234567890123456789012345678901234567890', 1000000000000000000)
    result1 = check_verification_with_duplicates(row1, verification_data)
    assert result1 == "✅"

    # Test second claim from same address - should get ⚠️
    row2 = create_mock_row('0x1234567890123456789012345678901234567890', 2000000000000000000)
    result2 = check_verification_with_duplicates(row2, verification_data)
    assert result2 == "⚠️"

    # Test third claim from same address - should still get ⚠️
    row3 = create_mock_row('0x1234567890123456789012345678901234567890', 1000000000000000000)
    result3 = check_verification_with_duplicates(row3, verification_data)
    assert result3 == "⚠️"

    # Test unknown address - should get ❌
    row4 = create_mock_row('0xunknown', 1000000000000000000)
    result4 = check_verification_with_duplicates(row4, verification_data)
    assert result4 == "❌"


def test_csv_column_validation():
    """Test CSV column validation."""
    required_cols = ['address', 'wave1_bard_wei', 'wave2_bard_wei']

    # Valid CSV
    valid_csv = """address,wave1_bard_wei,wave2_bard_wei
0x1234,1000,2000"""
    df_valid = pd.read_csv(io.StringIO(valid_csv))
    assert all(col in df_valid.columns for col in required_cols)

    # Invalid CSV - missing column
    invalid_csv = """address,wave1_bard_wei
0x1234,1000"""
    df_invalid = pd.read_csv(io.StringIO(invalid_csv))
    assert not all(col in df_invalid.columns for col in required_cols)
