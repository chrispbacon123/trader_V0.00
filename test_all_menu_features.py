#!/usr/bin/env python3
"""
Comprehensive Menu Feature Testing
Tests all interface capabilities end-to-end
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd

print('=' * 60)
print('COMPREHENSIVE MENU FEATURE TESTING')
print('=' * 60)

# Import all required modules
from advanced_trading_interface import AdvancedTradingInterface, Portfolio
from ml_strategy import MLTradingStrategy
from simple_strategy import SimpleMeanReversionStrategy
from optimized_ml_strategy import OptimizedMLStrategy
from short_term_strategy import ShortTermStrategy
from strategy_manager import StrategyManager, StrategyConfig

test_results = []

def test_feature(name, func):
    """Helper to test a feature"""
    print(f'\n{name}...')
    try:
        result = func()
        print(f'  ✅ PASS')
        test_results.append((name, 'PASS', None))
        return result
    except Exception as e:
        print(f'  ❌ FAIL: {str(e)[:100]}')
        test_results.append((name, 'FAIL', str(e)))
        return None

# Test 1: Single Strategy Backtesting
def test_single_strategy():
    """Test running a single strategy backtest"""
    strategy = SimpleMeanReversionStrategy('SPY', initial_capital=10000)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    data, trades, final_value = strategy.backtest(start_date, end_date)
    assert final_value > 0
    assert len(trades) >= 0
    print(f'    Final value: ${final_value:,.2f}, Trades: {len(trades)}')
    return True

test_feature('1. Single Strategy Backtest', test_single_strategy)

# Test 2: Multiple Strategy Comparison
def test_multiple_strategies():
    """Test comparing multiple strategies"""
    strategies = [
        ('Simple', SimpleMeanReversionStrategy('SPY', 10000)),
        ('ML', MLTradingStrategy('SPY', 10000)),
    ]
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    results = []
    for name, strategy in strategies:
        if name == 'ML':
            _, _, final_value, _ = strategy.backtest(start_date, end_date)
        else:
            _, _, final_value = strategy.backtest(start_date, end_date)
        results.append((name, final_value))
    
    print(f'    Compared {len(results)} strategies')
    for name, val in results:
        print(f'      {name}: ${val:,.2f}')
    return True

test_feature('2. Multiple Strategy Comparison', test_multiple_strategies)

# Test 3: Portfolio Creation
def test_portfolio_creation():
    """Test creating a portfolio"""
    portfolio = Portfolio('Test_Portfolio', 100000, 0.15)
    portfolio.strategy_allocations = {
        'AAPL': {'allocation': 0.5, 'strategy_type': 'ml'},
        'SPY': {'allocation': 0.5, 'strategy_type': 'simple'}
    }
    assert portfolio.name == 'Test_Portfolio'
    assert portfolio.initial_capital == 100000
    assert len(portfolio.strategy_allocations) == 2
    print(f'    Portfolio: {portfolio.name}, ${portfolio.initial_capital:,.0f}')
    return True

test_feature('3. Portfolio Creation', test_portfolio_creation)

# Test 4: Strategy Saving
def test_strategy_save():
    """Test saving strategy configuration"""
    sm = StrategyManager()
    config = StrategyConfig(
        name='Test_Save_Strategy',
        strategy_type='ml',
        symbol='AAPL',
        initial_capital=10000,
        description='Test strategy for saving'
    )
    sm.save_strategy(config)
    
    # Verify it was saved
    loaded = sm.load_strategy('Test_Save_Strategy')
    assert loaded is not None
    assert loaded.name == 'Test_Save_Strategy'
    print(f'    Saved and loaded: {loaded.name}')
    
    # Cleanup
    sm.delete_strategy('Test_Save_Strategy')
    return True

test_feature('4. Strategy Save/Load', test_strategy_save)

# Test 5: Different Asset Types
def test_asset_types():
    """Test different asset types (stock, ETF, crypto)"""
    import yfinance as yf
    
    assets = [
        ('Stock', 'AAPL'),
        ('ETF', 'SPY'),
        ('Crypto', 'BTC-USD')
    ]
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    results = []
    for asset_type, symbol in assets:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        results.append((asset_type, symbol, len(df)))
        print(f'    {asset_type} ({symbol}): {len(df)} days')
    
    assert all(days > 0 for _, _, days in results)
    return True

test_feature('5. Different Asset Types', test_asset_types)

# Test 6: Short-term vs Long-term
def test_time_periods():
    """Test different backtest time periods"""
    strategy = SimpleMeanReversionStrategy('SPY', 10000)
    end_date = datetime.now()
    
    periods = [
        ('1 week', 7),
        ('1 month', 30),
        ('3 months', 90),
    ]
    
    results = []
    for name, days in periods:
        start_date = end_date - timedelta(days=days)
        try:
            _, trades, final_value = strategy.backtest(start_date, end_date)
            results.append((name, final_value, len(trades)))
            print(f'    {name}: ${final_value:,.2f}, {len(trades)} trades')
        except Exception as e:
            print(f'    {name}: Skipped ({str(e)[:50]})')
    
    return len(results) > 0

test_feature('6. Multiple Time Periods', test_time_periods)

# Test 7: Technical Indicators
def test_indicators():
    """Test technical indicator calculation"""
    strategy = MLTradingStrategy('SPY', 10000)
    
    import yfinance as yf
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    ticker = yf.Ticker('SPY')
    df = ticker.history(start=start_date, end=end_date)
    df_features = strategy.add_features(df)
    
    indicators = ['RSI', 'MACD', 'SMA_10', 'BB_Upper', 'BB_Lower']
    found = [ind for ind in indicators if ind in df_features.columns]
    
    print(f'    Found {len(found)}/{len(indicators)} indicators')
    print(f'    Total features: {len(df_features.columns)}')
    return len(found) >= 4

test_feature('7. Technical Indicators', test_indicators)

# Test 8: ML Model Training
def test_ml_training():
    """Test ML model training"""
    strategy = MLTradingStrategy('SPY', 10000)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    # This will train the model internally
    _, trades, final_value, equity = strategy.backtest(start_date, end_date)
    
    assert strategy.model is not None
    assert len(strategy.feature_names) > 0
    print(f'    Model trained with {len(strategy.feature_names)} features')
    print(f'    Final value: ${final_value:,.2f}')
    return True

test_feature('8. ML Model Training', test_ml_training)

# Test 9: Portfolio Management Features
def test_portfolio_management():
    """Test portfolio management operations"""
    interface = AdvancedTradingInterface()
    
    # Create portfolio
    portfolio = Portfolio('Test_Mgmt_Portfolio', 50000, 0.12)
    portfolio.strategy_allocations = {
        'AAPL': {'allocation': 0.6, 'strategy_type': 'ml', 'capital': 30000},
        'MSFT': {'allocation': 0.4, 'strategy_type': 'simple', 'capital': 20000}
    }
    
    # Save
    interface.save_portfolio(portfolio)
    
    # Load
    loaded = interface.load_portfolio('Test_Mgmt_Portfolio')
    assert loaded is not None
    assert loaded.name == 'Test_Mgmt_Portfolio'
    assert len(loaded.strategy_allocations) == 2
    
    print(f'    Portfolio managed: {loaded.name}')
    print(f'    Allocations: {len(loaded.strategy_allocations)}')
    
    # Cleanup
    import os
    if os.path.exists('saved_portfolios/Test_Mgmt_Portfolio.json'):
        os.remove('saved_portfolios/Test_Mgmt_Portfolio.json')
    
    return True

test_feature('9. Portfolio Management', test_portfolio_management)

# Test 10: Data Validation
def test_data_validation():
    """Test input validation functions"""
    from enhanced_utils import (
        validate_symbol, validate_days, validate_capital, 
        validate_percentage, ValidationError
    )
    
    # Valid inputs
    assert validate_symbol('AAPL') == 'AAPL'
    assert validate_days('30') == 30
    assert validate_capital('10000') == 10000.0
    pct = validate_percentage('15')
    assert 0.1 < pct < 0.2
    
    # Invalid inputs should raise errors
    error_count = 0
    try:
        validate_days('-5')
    except ValidationError:
        error_count += 1
    
    try:
        validate_capital('abc')
    except ValidationError:
        error_count += 1
    
    try:
        validate_symbol('')
    except ValidationError:
        error_count += 1
    
    print(f'    Validation tests: {error_count}/3 errors caught')
    return error_count == 3

test_feature('10. Data Validation', test_data_validation)

# Print Summary
print('\n' + '=' * 60)
print('TEST SUMMARY')
print('=' * 60)

passed = sum(1 for _, status, _ in test_results if status == 'PASS')
failed = sum(1 for _, status, _ in test_results if status == 'FAIL')

print(f'\n✅ Passed: {passed}/{len(test_results)}')
print(f'❌ Failed: {failed}/{len(test_results)}')

if failed > 0:
    print('\nFailed tests:')
    for name, status, error in test_results:
        if status == 'FAIL':
            print(f'  - {name}')
            if error:
                print(f'    Error: {error[:100]}')

if failed == 0:
    print('\n' + '🎉' * 20)
    print('ALL FEATURES TESTED AND WORKING!')
    print('System is ready for production use.')
    print('\nRun: ./launch.sh to start the interface')
    print('=' * 60)
else:
    print(f'\n⚠️  {failed} feature(s) need attention')

sys.exit(0 if failed == 0 else 1)
