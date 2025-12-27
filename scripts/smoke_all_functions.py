#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test script to verify all features work correctly
"""

import sys
import os
import traceback
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def test_imports():
    """Test all required imports"""
    print("Testing imports...")
    try:
        import yfinance as yf
        import pandas as pd
        import numpy as np
        import json
        from simple_strategy import SimpleMeanReversionStrategy
        from ml_strategy import MLTradingStrategy
        from optimized_ml_strategy import OptimizedMLStrategy
        from short_term_strategy import ShortTermStrategy
        from enhanced_utils import validate_symbol, download_data_with_retry
        from strategy_manager import StrategyManager
        from advanced_settings import AdvancedSettingsManager
        from market_analytics import MarketAnalytics
        from strategy_optimizer import StrategyOptimizer
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_data_download():
    """Test data download"""
    print("\nTesting data download...")
    try:
        from enhanced_utils import download_data_with_retry
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        df = download_data_with_retry('SPY', start_date, end_date)
        if df is not None and len(df) > 30:
            print(f"✅ Data download successful: {len(df)} days of data")
            return True
        else:
            print(f"❌ Insufficient data: {len(df) if df is not None else 0} days")
            return False
    except Exception as e:
        print(f"❌ Data download error: {e}")
        traceback.print_exc()
        return False

def test_simple_strategy():
    """Test simple strategy"""
    print("\nTesting Simple Mean Reversion Strategy...")
    try:
        from simple_strategy import SimpleMeanReversionStrategy
        strategy = SimpleMeanReversionStrategy('SPY')
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        df, trades, final_value, equity = strategy.backtest(start_date, end_date)
        print(f"✅ Simple strategy works: Final value ${final_value:,.2f}, {len(trades)} trades")
        return True
    except Exception as e:
        print(f"❌ Simple strategy error: {e}")
        traceback.print_exc()
        return False

def test_ml_strategy():
    """Test ML strategy"""
    print("\nTesting ML Trading Strategy...")
    try:
        from ml_strategy import MLTradingStrategy
        strategy = MLTradingStrategy('SPY')
        end_date = datetime.now()
        start_date = end_date - timedelta(days=120)  # ML needs more data
        df, trades, final_value, equity = strategy.backtest(start_date, end_date)
        print(f"✅ ML strategy works: Final value ${final_value:,.2f}, {len(trades)} trades")
        return True
    except Exception as e:
        print(f"❌ ML strategy error: {e}")
        traceback.print_exc()
        return False

def test_portfolio_creation():
    """Test portfolio creation"""
    print("\nTesting Portfolio Management...")
    try:
        from advanced_trading_interface import Portfolio
        portfolio = Portfolio("Test Portfolio", initial_capital=100000)
        portfolio.strategy_allocations = {
            'SPY': {'allocation': 0.5, 'strategy': 'simple'},
            'QQQ': {'allocation': 0.5, 'strategy': 'simple'}
        }
        print(f"✅ Portfolio creation works: {portfolio.name}")
        return True
    except Exception as e:
        print(f"❌ Portfolio error: {e}")
        traceback.print_exc()
        return False

def test_strategy_manager():
    """Test strategy manager"""
    print("\nTesting Strategy Manager...")
    try:
        from strategy_manager import StrategyManager, StrategyConfig
        manager = StrategyManager()
        
        # Create test config
        config = StrategyConfig(
            name="Test Strategy",
            strategy_type="simple",
            symbol="SPY",
            parameters={"short_window": 10, "long_window": 30}
        )
        
        # Save and load
        manager.save_strategy(config)
        loaded = manager.load_strategy("Test Strategy")
        
        if loaded and loaded.name == "Test Strategy":
            print("✅ Strategy Manager works")
            return True
        else:
            print("❌ Strategy Manager: Load failed")
            return False
    except Exception as e:
        print(f"❌ Strategy Manager error: {e}")
        traceback.print_exc()
        return False

def test_market_analytics():
    """Test market analytics"""
    print("\nTesting Market Analytics...")
    try:
        from market_analytics import MarketAnalytics
        from enhanced_utils import download_data_with_retry
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        df = download_data_with_retry('SPY', start_date, end_date)
        
        analytics = MarketAnalytics()
        regime = analytics.detect_market_regime(df)
        
        print(f"✅ Market Analytics works: Regime = {regime}")
        return True
    except Exception as e:
        print(f"❌ Market Analytics error: {e}")
        traceback.print_exc()
        return False

def test_json_operations():
    """Test JSON file operations"""
    print("\nTesting JSON operations...")
    try:
        from enhanced_utils import safe_json_load, safe_json_save
        import os
        
        test_file = 'test_data.json'
        test_data = {'test': 'data', 'number': 123}
        
        # Test save
        safe_json_save(test_file, test_data)
        
        # Test load
        loaded = safe_json_load(test_file)
        
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
        
        if loaded == test_data:
            print("✅ JSON operations work")
            return True
        else:
            print("❌ JSON operations: Data mismatch")
            return False
    except Exception as e:
        print(f"❌ JSON operations error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("="*70)
    print("COMPREHENSIVE SYSTEM TEST")
    print("="*70)
    
    tests = [
        ("Imports", test_imports),
        ("Data Download", test_data_download),
        ("Simple Strategy", test_simple_strategy),
        ("ML Strategy", test_ml_strategy),
        ("Portfolio Management", test_portfolio_creation),
        ("Strategy Manager", test_strategy_manager),
        ("Market Analytics", test_market_analytics),
        ("JSON Operations", test_json_operations),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is fully functional.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
