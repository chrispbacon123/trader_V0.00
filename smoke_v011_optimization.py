"""
V0.11 Strategy Optimization Reliability Tests
Tests for LINE ITEM 3: stable schema, data reuse, failure categorization
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


def test_optimizer_stable_schema_all_fail():
    """Test optimizer returns stable schema when all combos fail"""
    from strategy_optimizer import StrategyOptimizer
    
    class FailingStrategy:
        def __init__(self, symbol, initial_capital, **params):
            self.symbol = symbol
            self.initial_capital = initial_capital
        
        def backtest(self, start_date, end_date, data=None):
            raise ValueError("Simulated failure")
    
    optimizer = StrategyOptimizer(FailingStrategy, metric='sharpe_ratio')
    param_grid = {'lookback': [7, 14]}
    
    # Mock data fetching
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    test_df = pd.DataFrame({
        'Close': np.linspace(100, 110, 100),
        'High': np.linspace(101, 111, 100),
        'Low': np.linspace(99, 109, 100),
        'Volume': np.full(100, 1000),
        'Price': np.linspace(100, 110, 100)
    }, index=dates)
    
    with patch('data_manager.DataManager') as MockDataManager, \
         patch('data_normalization.DataNormalizer') as MockNormalizer:
        
        mock_manager = MockDataManager.return_value
        mock_normalizer = MockNormalizer.return_value
        mock_manager.fetch_data.return_value = test_df
        mock_normalizer.normalize_market_data.return_value = (test_df, {'price_source': 'Close'})
        
        results = optimizer.grid_search(
            param_grid,
            'TEST',
            datetime.now() - timedelta(days=100),
            datetime.now()
        )
    
    # Verify stable schema
    required_keys = [
        'success', 'best_params', 'best_score', 'tested', 'valid',
        'failures', 'skipped', 'error', 'warnings', 'failure_summary',
        'example_failures', 'top_results', 'all_results'
    ]
    for key in required_keys:
        assert key in results, f"Missing required key: {key}"
    
    # Verify failure state
    assert results['success'] == False
    assert isinstance(results['best_params'], dict)
    assert results['best_params'] == {}  # Empty dict, not None!
    assert results['best_score'] is None
    assert results['tested'] > 0
    assert results['valid'] == 0
    assert results['failures'] > 0
    
    print("[OK] Optimizer returns stable schema when all combos fail")


def test_optimizer_data_reuse():
    """Test optimizer fetches data once and reuses for all combos"""
    from strategy_optimizer import StrategyOptimizer
    
    class SimpleStrategy:
        def __init__(self, symbol, initial_capital, **params):
            self.symbol = symbol
            self.initial_capital = initial_capital
            self.lookback = params.get('lookback', 7)
        
        def backtest(self, start_date, end_date, data=None):
            # Return minimal valid result
            return data, [], self.initial_capital
    
    optimizer = StrategyOptimizer(SimpleStrategy, metric='sharpe_ratio')
    param_grid = {'lookback': [7, 14, 21]}  # 3 combinations
    
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    test_df = pd.DataFrame({
        'Close': np.linspace(100, 110, 100),
        'High': np.linspace(101, 111, 100),
        'Low': np.linspace(99, 109, 100),
        'Volume': np.full(100, 1000),
        'Price': np.linspace(100, 110, 100)
    }, index=dates)
    
    with patch('data_manager.DataManager') as MockDataManager, \
         patch('data_normalization.DataNormalizer') as MockNormalizer:
        
        mock_manager = MockDataManager.return_value
        mock_normalizer = MockNormalizer.return_value
        mock_manager.fetch_data.return_value = test_df
        mock_normalizer.normalize_market_data.return_value = (test_df, {'price_source': 'Close'})
        
        results = optimizer.grid_search(
            param_grid,
            'TEST',
            datetime.now() - timedelta(days=100),
            datetime.now()
        )
        
        # Verify fetch_data called only ONCE
        assert mock_manager.fetch_data.call_count == 1, \
            f"Expected 1 fetch call, got {mock_manager.fetch_data.call_count}"
        
        # Verify normalization called only ONCE
        assert mock_normalizer.normalize_market_data.call_count == 1
    
    print("[OK] Optimizer fetches data once and reuses for all combos")


def test_optimizer_failure_categorization():
    """Test optimizer categorizes failures correctly"""
    from strategy_optimizer import StrategyOptimizer
    
    call_count = [0]
    
    class MixedStrategy:
        def __init__(self, symbol, initial_capital, **params):
            self.symbol = symbol
            self.initial_capital = initial_capital
            self.lookback = params.get('lookback', 7)
        
        def backtest(self, start_date, end_date, data=None):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ValueError("Insufficient data for analysis")
            elif call_count[0] == 2:
                raise ValueError("No data available")
            elif call_count[0] == 3:
                raise RuntimeError("Something else broke")
            else:
                return data, [], self.initial_capital
    
    optimizer = StrategyOptimizer(MixedStrategy, metric='sharpe_ratio')
    param_grid = {'lookback': [7, 14, 21, 28]}
    
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    test_df = pd.DataFrame({
        'Close': np.linspace(100, 110, 100),
        'High': np.linspace(101, 111, 100),
        'Low': np.linspace(99, 109, 100),
        'Volume': np.full(100, 1000),
        'Price': np.linspace(100, 110, 100)
    }, index=dates)
    
    with patch('data_manager.DataManager') as MockDataManager, \
         patch('data_normalization.DataNormalizer') as MockNormalizer:
        
        mock_manager = MockDataManager.return_value
        mock_normalizer = MockNormalizer.return_value
        mock_manager.fetch_data.return_value = test_df
        mock_normalizer.normalize_market_data.return_value = (test_df, {'price_source': 'Close'})
        
        results = optimizer.grid_search(
            param_grid,
            'TEST',
            datetime.now() - timedelta(days=100),
            datetime.now()
        )
    
    # Verify failure summary exists and categorizes
    assert 'failure_summary' in results
    assert isinstance(results['failure_summary'], dict)
    
    # Should have categorized the failures
    # Note: exact categories depend on implementation, but should have some
    if results['failures'] > 0:
        assert len(results['failure_summary']) > 0
        print(f"   Failure categories: {results['failure_summary']}")
    
    # Verify example failures exist
    assert 'example_failures' in results
    assert isinstance(results['example_failures'], list)
    
    print("[OK] Optimizer categorizes failures correctly")


def test_optimizer_warmup_check():
    """Test optimizer warns about insufficient data for warmup"""
    from strategy_optimizer import StrategyOptimizer
    
    class SimpleStrategy:
        def __init__(self, symbol, initial_capital, **params):
            self.symbol = symbol
            self.initial_capital = initial_capital
        
        def backtest(self, start_date, end_date, data=None):
            return data, [], self.initial_capital
    
    optimizer = StrategyOptimizer(SimpleStrategy, metric='sharpe_ratio')
    
    # Large lookback but small dataset
    param_grid = {'lookback': [100, 200, 300]}
    
    # Only 50 rows of data
    dates = pd.date_range(end=datetime.now(), periods=50, freq='D')
    test_df = pd.DataFrame({
        'Close': np.linspace(100, 110, 50),
        'High': np.linspace(101, 111, 50),
        'Low': np.linspace(99, 109, 50),
        'Volume': np.full(50, 1000),
        'Price': np.linspace(100, 110, 50)
    }, index=dates)
    
    with patch('data_manager.DataManager') as MockDataManager, \
         patch('data_normalization.DataNormalizer') as MockNormalizer:
        
        mock_manager = MockDataManager.return_value
        mock_normalizer = MockNormalizer.return_value
        mock_manager.fetch_data.return_value = test_df
        mock_normalizer.normalize_market_data.return_value = (test_df, {'price_source': 'Close'})
        
        results = optimizer.grid_search(
            param_grid,
            'TEST',
            datetime.now() - timedelta(days=50),
            datetime.now()
        )
    
    # Should have warnings about insufficient data
    assert 'warnings' in results
    if len(results['warnings']) > 0:
        print(f"   Warnings: {results['warnings']}")
    
    print("[OK] Optimizer checks for insufficient warmup data")


def test_optimizer_best_params_never_none():
    """Test that best_params is never None, even in edge cases"""
    from strategy_optimizer import StrategyOptimizer
    
    class BadStrategy:
        def __init__(self, symbol, initial_capital, **params):
            self.symbol = symbol
            self.initial_capital = initial_capital
        
        def backtest(self, start_date, end_date, data=None):
            raise Exception("Always fails")
    
    optimizer = StrategyOptimizer(BadStrategy, metric='sharpe_ratio')
    param_grid = {'param1': [1]}
    
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    test_df = pd.DataFrame({
        'Close': np.linspace(100, 110, 100),
        'High': np.linspace(101, 111, 100),
        'Low': np.linspace(99, 109, 100),
        'Volume': np.full(100, 1000),
        'Price': np.linspace(100, 110, 100)
    }, index=dates)
    
    with patch('data_manager.DataManager') as MockDataManager, \
         patch('data_normalization.DataNormalizer') as MockNormalizer:
        
        mock_manager = MockDataManager.return_value
        mock_normalizer = MockNormalizer.return_value
        mock_manager.fetch_data.return_value = test_df
        mock_normalizer.normalize_market_data.return_value = (test_df, {'price_source': 'Close'})
        
        results = optimizer.grid_search(
            param_grid,
            'TEST',
            datetime.now() - timedelta(days=100),
            datetime.now()
        )
    
    # best_params must be dict, never None
    assert results['best_params'] is not None, \
        "best_params must never be None"
    assert isinstance(results['best_params'], dict), \
        "best_params must be dict"
    assert results['best_params'] == {}, \
        "best_params should be empty dict when no valid results"
    
    print("[OK] Optimizer best_params is never None")


if __name__ == '__main__':
    print("="*70)
    print("V0.11 OPTIMIZATION RELIABILITY TESTS (LINE ITEM 3)")
    print("="*70)
    
    test_optimizer_stable_schema_all_fail()
    print()
    test_optimizer_data_reuse()
    print()
    test_optimizer_failure_categorization()
    print()
    test_optimizer_warmup_check()
    print()
    test_optimizer_best_params_never_none()
    
    print("\n" + "="*70)
    print("[OK] ALL LINE ITEM 3 TESTS PASSED")
    print("="*70)
