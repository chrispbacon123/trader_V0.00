"""
V0.11 Platform API Integration Tests
Tests that platform_api provides stable, JSON-serializable responses
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


def test_platform_api_fetch():
    """Test platform_api.fetch returns normalized data"""
    from platform_api import get_api
    
    api = get_api()
    
    # Create synthetic test data
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    test_df = pd.DataFrame({
        'Close': np.linspace(100, 110, 100),
        'High': np.linspace(101, 111, 100),
        'Low': np.linspace(99, 109, 100),
        'Volume': np.full(100, 1000)
    }, index=dates)
    
    # Mock data fetching
    with patch.object(api.data_manager, 'fetch_data', return_value=test_df):
        df, metadata = api.fetch(
            'TEST',
            datetime.now() - timedelta(days=100),
            datetime.now()
        )
    
    # Verify result
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert 'Price' in df.columns, "Normalized df must have Price column"
    assert isinstance(metadata, dict)
    
    print("[OK] platform_api.fetch() returns normalized data")


def test_platform_api_analyze_market_stable_schema():
    """Test analyze_market returns stable JSON-serializable schema"""
    from platform_api import get_api
    
    api = get_api()
    
    # Create synthetic test data
    dates = pd.date_range(end=datetime.now(), periods=200, freq='D')
    test_df = pd.DataFrame({
        'Price': np.linspace(100, 120, 200) + np.random.randn(200) * 2,
        'Close': np.linspace(100, 120, 200) + np.random.randn(200) * 2,
        'High': np.linspace(101, 121, 200) + np.random.randn(200) * 2,
        'Low': np.linspace(99, 119, 200) + np.random.randn(200) * 2,
        'Volume': np.random.randint(1000, 10000, 200)
    }, index=dates)
    
    # Mock data fetching
    with patch.object(api.data_manager, 'fetch_data', return_value=test_df):
        result = api.analyze_market(
            'TEST',
            datetime.now() - timedelta(days=200),
            datetime.now()
        )
    
    # Verify stable schema
    required_keys = ['success', 'symbol', 'period', 'metadata', 'warnings']
    for key in required_keys:
        assert key in result, f"Missing required key: {key}"
    
    # Verify JSON-serializable
    import json
    try:
        json_str = json.dumps(result, default=str)
        assert len(json_str) > 0
        print("[OK] platform_api.analyze_market() returns JSON-serializable schema")
    except Exception as e:
        pytest.fail(f"Result is not JSON-serializable: {e}")


def test_platform_api_analyze_market_with_debug():
    """Test analyze_market debug parameter"""
    from platform_api import get_api
    import io
    import sys
    
    api = get_api()
    
    # Create test data
    dates = pd.date_range(end=datetime.now(), periods=50, freq='D')
    test_df = pd.DataFrame({
        'Price': np.linspace(100, 110, 50),
        'Close': np.linspace(100, 110, 50),
        'High': np.linspace(101, 111, 50),
        'Low': np.linspace(99, 109, 50),
        'Volume': np.full(50, 1000)
    }, index=dates)
    
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = captured = io.StringIO()
    
    try:
        with patch.object(api.data_manager, 'fetch_data', return_value=test_df):
            result = api.analyze_market(
                'TEST',
                datetime.now() - timedelta(days=50),
                datetime.now(),
                debug=True
            )
        
        output = captured.getvalue()
        
        # Verify debug output exists
        assert '[DEBUG]' in output, "Debug mode should produce [DEBUG] output"
        print(f"[OK] platform_api.analyze_market(debug=True) produces debug output")
        
    finally:
        sys.stdout = old_stdout


def test_platform_api_optimize_strategy_stable_schema():
    """Test optimize_strategy returns stable schema even when all combos fail"""
    from platform_api import get_api
    from strategy_optimizer import StrategyOptimizer
    
    api = get_api()
    
    # Create a failing strategy for testing
    class FailingStrategy:
        def __init__(self, symbol, initial_capital, **params):
            self.symbol = symbol
            self.initial_capital = initial_capital
        
        def backtest(self, start_date, end_date, data=None):
            raise ValueError("Test failure")
    
    # Mock the optimizer to return stable schema
    mock_results = {
        'success': False,
        'best_params': {},
        'best_score': None,
        'tested': 4,
        'valid': 0,
        'failures': 4,
        'skipped': 0,
        'error': 'All combos failed',
        'warnings': [],
        'failure_summary': {'strategy_exception': 4},
        'example_failures': ['Test failure'] * 4,
        'top_results': [],
        'all_results': []
    }
    
    with patch.object(StrategyOptimizer, 'grid_search', return_value=mock_results):
        result = api.optimize_strategy(
            FailingStrategy,
            {'param1': [1, 2]},
            'TEST',
            datetime.now() - timedelta(days=100),
            datetime.now()
        )
    
    # Verify stable schema
    required_keys = [
        'success', 'best_params', 'best_score', 'tested', 'valid',
        'failures', 'skipped', 'platform_version', 'optimization_date'
    ]
    for key in required_keys:
        assert key in result, f"Missing required key: {key}"
    
    # Verify best_params is never None
    assert isinstance(result['best_params'], dict), \
        "best_params must be dict, never None"
    
    print("[OK] platform_api.optimize_strategy() returns stable schema")


def test_platform_api_optimize_mode_parameter():
    """Test optimize_strategy mode parameter"""
    from platform_api import get_api
    from strategy_optimizer import StrategyOptimizer
    
    api = get_api()
    
    class DummyStrategy:
        def __init__(self, symbol, initial_capital, **params):
            pass
        
        def backtest(self, start_date, end_date, data=None):
            return pd.DataFrame(), [], 10000
    
    mock_results = {
        'success': True,
        'best_params': {'param1': 1},
        'best_score': 0.5,
        'tested': 2,
        'valid': 2,
        'failures': 0,
        'skipped': 0,
        'error': None,
        'warnings': [],
        'failure_summary': {},
        'example_failures': [],
        'top_results': [],
        'all_results': []
    }
    
    # Test grid mode (default)
    with patch.object(StrategyOptimizer, 'grid_search', return_value=mock_results) as mock_grid:
        result = api.optimize_strategy(
            DummyStrategy,
            {'param1': [1, 2]},
            'TEST',
            datetime.now() - timedelta(days=100),
            datetime.now(),
            mode='grid'
        )
        assert mock_grid.called
        assert result['success']
    
    print("[OK] platform_api.optimize_strategy() supports mode parameter")


if __name__ == '__main__':
    print("="*70)
    print("V0.11 PLATFORM API INTEGRATION TESTS")
    print("="*70)
    
    test_platform_api_fetch()
    print()
    test_platform_api_analyze_market_stable_schema()
    print()
    test_platform_api_analyze_market_with_debug()
    print()
    test_platform_api_optimize_strategy_stable_schema()
    print()
    test_platform_api_optimize_mode_parameter()
    
    print("\n" + "="*70)
    print("[OK] ALL V0.11 PLATFORM API TESTS PASSED")
    print("="*70)
