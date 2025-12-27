"""
V0.11 Persistence/History Schema Stability Tests
Tests for LINE ITEM 4: schema normalization prevents KeyError crashes
"""

import pytest
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import tempfile


def test_normalize_run_record_required_keys():
    """Test that normalize_run_record ensures all required keys exist"""
    from persistence import normalize_run_record
    
    # Minimal record
    record = {}
    normalized = normalize_run_record(record)
    
    # Verify required keys
    required_keys = ['timestamp', 'symbol', 'strategy', 'return_pct']
    for key in required_keys:
        assert key in normalized, f"Missing required key: {key}"
    
    # Verify defaults
    assert normalized['symbol'] == 'UNKNOWN'
    assert normalized['strategy'] == 'Unknown Strategy'
    assert normalized['return_pct'] == 0.0
    
    print("[OK] normalize_run_record ensures all required keys exist")


def test_normalize_run_record_old_keys():
    """Test that old key names are mapped to new schema"""
    from persistence import normalize_run_record
    
    # Old format record
    old_record = {
        'date': '2025-01-01T00:00:00',
        'ticker': 'AAPL',
        'strategy_name': 'Old Strategy',
        'total_return': 15.5,
        'trades': 10,
        'max_dd': -5.2
    }
    
    normalized = normalize_run_record(old_record)
    
    # Verify mapping
    assert normalized['timestamp'] == '2025-01-01T00:00:00'
    assert normalized['symbol'] == 'AAPL'
    assert normalized['strategy'] == 'Old Strategy'
    assert normalized['return_pct'] == 15.5
    assert normalized['num_trades'] == 10
    assert normalized['max_drawdown'] == -5.2
    
    print("[OK] normalize_run_record maps old keys to new schema")


def test_normalize_run_record_preserves_extra_fields():
    """Test that extra fields are preserved"""
    from persistence import normalize_run_record
    
    record = {
        'symbol': 'SPY',
        'strategy': 'Test',
        'return_pct': 10.0,
        'custom_field': 'custom_value',
        'extra_metric': 42
    }
    
    normalized = normalize_run_record(record)
    
    # Verify custom fields preserved
    assert normalized['custom_field'] == 'custom_value'
    assert normalized['extra_metric'] == 42
    
    print("[OK] normalize_run_record preserves extra fields")


def test_load_history_handles_missing_file():
    """Test that load_history returns empty list for missing file"""
    from persistence import load_history
    
    # Non-existent file
    history = load_history('/nonexistent/path/history.json')
    
    assert isinstance(history, list)
    assert len(history) == 0
    
    print("[OK] load_history handles missing file gracefully")


def test_load_history_normalizes_all_records():
    """Test that load_history normalizes all records"""
    from persistence import load_history
    
    # Create temp file with mixed format records
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        records = [
            {'symbol': 'AAPL', 'strategy': 'Test1', 'return_pct': 5.0},
            {'ticker': 'MSFT', 'strategy_name': 'Test2', 'total_return': 10.0},
            {}  # Empty record
        ]
        json.dump(records, f)
        temp_path = f.name
    
    try:
        history = load_history(temp_path)
        
        # Verify all normalized
        assert len(history) == 3
        for record in history:
            assert 'timestamp' in record
            assert 'symbol' in record
            assert 'strategy' in record
            assert 'return_pct' in record
        
        # Verify specific mappings
        assert history[0]['symbol'] == 'AAPL'
        assert history[1]['symbol'] == 'MSFT'
        assert history[1]['return_pct'] == 10.0
        assert history[2]['symbol'] == 'UNKNOWN'
        
        print("[OK] load_history normalizes all records")
        
    finally:
        os.unlink(temp_path)


def test_load_history_handles_dict_format():
    """Test that load_history handles old dict-of-lists format"""
    from persistence import load_history
    
    # Create temp file with old dict format
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        old_format = {
            'strategy1': [
                {'symbol': 'AAPL', 'return': 5.0}
            ],
            'strategy2': [
                {'symbol': 'MSFT', 'return': 10.0}
            ]
        }
        json.dump(old_format, f)
        temp_path = f.name
    
    try:
        history = load_history(temp_path)
        
        # Should flatten and normalize
        assert len(history) == 2
        assert all('timestamp' in r for r in history)
        
        print("[OK] load_history handles dict-of-lists format")
        
    finally:
        os.unlink(temp_path)


def test_load_history_handles_corrupt_json():
    """Test that load_history handles corrupt JSON gracefully"""
    from persistence import load_history
    
    # Create temp file with invalid JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        temp_path = f.name
    
    try:
        history = load_history(temp_path)
        
        # Should return empty list, not crash
        assert isinstance(history, list)
        assert len(history) == 0
        
        print("[OK] load_history handles corrupt JSON gracefully")
        
    finally:
        os.unlink(temp_path)


def test_append_history():
    """Test that append_history normalizes and appends records"""
    from persistence import append_history, load_history
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        initial_records = [{'symbol': 'AAPL', 'strategy': 'Test', 'return_pct': 5.0}]
        json.dump(initial_records, f)
        temp_path = f.name
    
    try:
        # Append new record (with old keys)
        new_record = {
            'ticker': 'MSFT',
            'strategy_name': 'New Strategy',
            'total_return': 10.0
        }
        
        success = append_history(temp_path, new_record)
        assert success
        
        # Load and verify
        history = load_history(temp_path)
        assert len(history) == 2
        
        # Verify normalization
        assert history[1]['symbol'] == 'MSFT'
        assert history[1]['strategy'] == 'New Strategy'
        assert history[1]['return_pct'] == 10.0
        
        print("[OK] append_history normalizes and appends records")
        
    finally:
        os.unlink(temp_path)


def test_safe_get():
    """Test safe_get helper function"""
    from persistence import safe_get
    
    record = {'key1': 'value1', 'key2': None}
    
    # Existing key
    assert safe_get(record, 'key1') == 'value1'
    
    # Missing key with default
    assert safe_get(record, 'missing', 'default') == 'default'
    
    # None value
    assert safe_get(record, 'key2') is None
    assert safe_get(record, 'key2', 'default') is None  # Returns None, not default
    
    print("[OK] safe_get provides safe access with defaults")


def test_format_history_summary():
    """Test format_history_summary creates readable output"""
    from persistence import format_history_summary
    
    records = [
        {'symbol': 'AAPL', 'strategy': 'Test1', 'return_pct': 5.0, 'timestamp': '2025-01-01T00:00:00'},
        {'symbol': 'MSFT', 'strategy': 'Test1', 'return_pct': 10.0, 'timestamp': '2025-01-02T00:00:00'},
        {'symbol': 'GOOGL', 'strategy': 'Test2', 'return_pct': -2.0, 'timestamp': '2025-01-03T00:00:00'}
    ]
    
    summary = format_history_summary(records)
    
    # Should contain key information
    assert 'Test1' in summary
    assert 'Test2' in summary
    assert 'Average Return' in summary
    assert 'Best Return' in summary
    assert 'Worst Return' in summary
    
    # Empty records
    empty_summary = format_history_summary([])
    assert 'No history records' in empty_summary
    
    print("[OK] format_history_summary creates readable output")


def test_no_keyerror_on_normalized_records():
    """Integration test: normalized records never cause KeyError"""
    from persistence import normalize_run_record
    
    # Simulate various malformed records
    malformed_records = [
        {},  # Empty
        {'some': 'field'},  # Missing all required
        {'timestamp': '2025-01-01'},  # Partial
        None,  # Intentionally bad (will be caught)
    ]
    
    for i, record in enumerate(malformed_records):
        if record is None:
            continue
        
        normalized = normalize_run_record(record)
        
        # These accesses should NEVER KeyError
        try:
            _ = normalized['timestamp']
            _ = normalized['symbol']
            _ = normalized['strategy']
            _ = normalized['return_pct']
        except KeyError as e:
            pytest.fail(f"KeyError on normalized record {i}: {e}")
    
    print("[OK] Normalized records never cause KeyError on required keys")


if __name__ == '__main__':
    print("="*70)
    print("V0.11 PERSISTENCE/HISTORY SCHEMA STABILITY TESTS (LINE ITEM 4)")
    print("="*70)
    
    test_normalize_run_record_required_keys()
    print()
    test_normalize_run_record_old_keys()
    print()
    test_normalize_run_record_preserves_extra_fields()
    print()
    test_load_history_handles_missing_file()
    print()
    test_load_history_normalizes_all_records()
    print()
    test_load_history_handles_dict_format()
    print()
    test_load_history_handles_corrupt_json()
    print()
    test_append_history()
    print()
    test_safe_get()
    print()
    test_format_history_summary()
    print()
    test_no_keyerror_on_normalized_records()
    
    print("\n" + "="*70)
    print("[OK] ALL LINE ITEM 4 TESTS PASSED")
    print("="*70)
