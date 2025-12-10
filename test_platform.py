#!/usr/bin/env python3
"""
Platform Testing and Error Detection Script
Tests all features systematically and reports errors
"""

import sys
import traceback
from datetime import datetime, timedelta

def test_imports():
    """Test all module imports"""
    print("\n" + "="*60)
    print("TESTING MODULE IMPORTS")
    print("="*60)
    
    modules = [
        ('pandas', 'pd'),
        ('numpy', 'np'),
        ('yfinance', 'yf'),
        ('sklearn', 'sklearn'),
        ('xgboost', 'xgb'),
        ('lightgbm', 'lgb'),
        ('ta', 'ta'),
        ('matplotlib.pyplot', 'plt'),
        ('seaborn', 'sns'),
    ]
    
    for module_name, alias in modules:
        try:
            exec(f"import {module_name} as {alias}")
            print(f"✅ {module_name}")
        except Exception as e:
            print(f"❌ {module_name}: {e}")
            return False
    
    return True

def test_strategy_files():
    """Test strategy file imports"""
    print("\n" + "="*60)
    print("TESTING STRATEGY FILES")
    print("="*60)
    
    strategies = [
        'simple_strategy',
        'ml_strategy',
        'optimized_ml_strategy',
        'short_term_strategy'
    ]
    
    for strategy in strategies:
        try:
            __import__(strategy)
            print(f"✅ {strategy}.py")
        except Exception as e:
            print(f"❌ {strategy}.py: {e}")
            traceback.print_exc()
            return False
    
    return True

def test_utility_files():
    """Test utility file imports"""
    print("\n" + "="*60)
    print("TESTING UTILITY FILES")
    print("="*60)
    
    utilities = [
        'enhanced_utils',
        'unified_backtest_engine',
        'strategy_manager',
        'advanced_settings',
        'market_analytics',
        'strategy_optimizer',
        'strategy_builder'
    ]
    
    for util in utilities:
        try:
            __import__(util)
            print(f"✅ {util}.py")
        except Exception as e:
            print(f"❌ {util}.py: {e}")
            if "--verbose" in sys.argv:
                traceback.print_exc()
            return False
    
    return True

def test_main_interface():
    """Test main interface initialization"""
    print("\n" + "="*60)
    print("TESTING MAIN INTERFACE")
    print("="*60)
    
    try:
        from advanced_trading_interface import AdvancedTradingInterface
        print("✅ Interface import successful")
        
        # Try to initialize (this might be slow)
        print("Initializing interface...")
        interface = AdvancedTradingInterface()
        print("✅ Interface initialization successful")
        return True
    except Exception as e:
        print(f"❌ Interface initialization failed: {e}")
        if "--verbose" in sys.argv:
            traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print(" TRADING PLATFORM COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Module Imports", test_imports),
        ("Strategy Files", test_strategy_files),
        ("Utility Files", test_utility_files),
        ("Main Interface", test_main_interface),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            if "--verbose" in sys.argv:
                traceback.print_exc()
            results[test_name] = False
    
    # Summary
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    print("\n" + "="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED - Please review errors above")
    print("="*70)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
