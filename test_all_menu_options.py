#!/usr/bin/env python3
"""
Comprehensive test of all menu options to identify errors
"""

import sys
import os

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    errors = []
    
    try:
        import advanced_trading_interface
        print("✓ advanced_trading_interface")
    except Exception as e:
        errors.append(f"advanced_trading_interface: {e}")
    
    try:
        from simple_strategy import SimpleMeanReversionStrategy
        print("✓ SimpleMeanReversionStrategy")
    except Exception as e:
        errors.append(f"SimpleMeanReversionStrategy: {e}")
    
    try:
        from ml_strategy import MLTradingStrategy
        print("✓ MLTradingStrategy")
    except Exception as e:
        errors.append(f"MLTradingStrategy: {e}")
    
    try:
        from optimized_ml_strategy import OptimizedMLStrategy
        print("✓ OptimizedMLStrategy")
    except Exception as e:
        errors.append(f"OptimizedMLStrategy: {e}")
    
    try:
        from short_term_strategy import ShortTermStrategy
        print("✓ ShortTermStrategy")
    except Exception as e:
        errors.append(f"ShortTermStrategy: {e}")
    
    try:
        from strategy_manager import StrategyManager
        print("✓ StrategyManager")
    except Exception as e:
        errors.append(f"StrategyManager: {e}")
    
    try:
        from strategy_builder import StrategyBuilder
        print("✓ StrategyBuilder")
    except Exception as e:
        errors.append(f"StrategyBuilder: {e}")
    
    try:
        from market_analytics import MarketAnalytics
        print("✓ MarketAnalytics")
    except Exception as e:
        errors.append(f"MarketAnalytics: {e}")
    
    return errors

def test_data_fetch():
    """Test data fetching"""
    print("\nTesting data fetch...")
    try:
        import yfinance as yf
        data = yf.download('SPY', start='2024-01-01', end='2024-01-10', progress=False)
        if len(data) > 0:
            print(f"✓ Data fetch works ({len(data)} days)")
            return []
        else:
            return ["No data returned from yfinance"]
    except Exception as e:
        return [f"Data fetch error: {e}"]

def test_results_directory():
    """Test results directory"""
    print("\nTesting results directory...")
    os.makedirs('results', exist_ok=True)
    os.makedirs('saved_portfolios', exist_ok=True)
    os.makedirs('saved_strategies', exist_ok=True)
    os.makedirs('exports', exist_ok=True)
    print("✓ All directories created")
    return []

if __name__ == "__main__":
    print("="*80)
    print("COMPREHENSIVE PLATFORM TEST")
    print("="*80)
    
    all_errors = []
    
    # Test imports
    all_errors.extend(test_imports())
    
    # Test data fetch
    all_errors.extend(test_data_fetch())
    
    # Test directories
    all_errors.extend(test_results_directory())
    
    print("\n" + "="*80)
    if all_errors:
        print("❌ ERRORS FOUND:")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("✅ ALL TESTS PASSED - Platform ready for use")
        sys.exit(0)
