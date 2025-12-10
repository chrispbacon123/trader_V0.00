#!/usr/bin/env python3
"""
Comprehensive System Test
Tests all features systematically
"""

import sys
sys.path.insert(0, '/Users/jonathanbrooks/lean-trading')

from datetime import datetime, timedelta
from simple_strategy import SimpleMeanReversionStrategy
from ml_strategy import MLTradingStrategy
from short_term_strategy import ShortTermStrategy
from optimized_ml_strategy import OptimizedMLStrategy

def test_strategy(strategy_class, name, symbol='SPY', days=365):
    """Test a single strategy"""
    print(f"\n{'='*60}")
    print(f"Testing {name}")
    print('='*60)
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        strategy = strategy_class(symbol=symbol)
        strategy.cash = 100000
        
        print(f"Running backtest on {symbol} for {days} days...")
        result = strategy.backtest(start_date, end_date)
        
        # Validate return format
        if not isinstance(result, tuple):
            print(f"❌ {name}: backtest didn't return tuple")
            return False
        
        if len(result) != 4:
            print(f"❌ {name}: backtest returned {len(result)} values, expected 4")
            return False
        
        data, trades, final_value, equity = result
        
        # Validate return values
        if trades is None or not isinstance(trades, list):
            print(f"❌ {name}: trades is not a list")
            return False
        
        if not isinstance(final_value, (int, float)):
            print(f"❌ {name}: final_value is not numeric")
            return False
        
        if equity is None or not isinstance(equity, list):
            print(f"❌ {name}: equity is not a list")
            return False
        
        # Print results
        return_pct = ((final_value - 100000) / 100000) * 100
        print(f"✅ {name} passed all checks")
        print(f"   Trades: {len(trades)}")
        print(f"   Final Value: ${final_value:,.2f}")
        print(f"   Return: {return_pct:.2f}%")
        return True
        
    except Exception as e:
        print(f"❌ {name} failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive tests"""
    print("\n" + "="*60)
    print("COMPREHENSIVE SYSTEM TEST")
    print("="*60)
    
    tests = [
        (SimpleMeanReversionStrategy, "Simple Strategy", 'SPY', 180),
        (MLTradingStrategy, "ML Strategy", 'SPY', 365),
        (ShortTermStrategy, "Short-Term Strategy", 'SPY', 90),
        (OptimizedMLStrategy, "Optimized ML Strategy", 'SPY', 365),
    ]
    
    results = {}
    for strategy_class, name, symbol, days in tests:
        results[name] = test_strategy(strategy_class, name, symbol, days)
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:30} {status}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return all(results.values())

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
