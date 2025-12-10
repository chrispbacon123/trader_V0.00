#!/usr/bin/env python3
"""
Comprehensive test of all features
"""

from datetime import datetime, timedelta
from short_term_strategy import ShortTermStrategy
from simple_strategy import SimpleMeanReversionStrategy
from ml_strategy import MLTradingStrategy
from optimized_ml_strategy import OptimizedMLStrategy

print("=" * 80)
print("COMPREHENSIVE FEATURE TEST")
print("=" * 80)

tests_passed = 0
tests_failed = 0

# Test 1: Short-Term Strategy (2 weeks)
print("\n1. Short-Term Strategy (21 calendar days = ~14 trading days)...")
try:
    strategy = ShortTermStrategy('SPY')
    end = datetime.now()
    start = end - timedelta(days=21)
    data, trades, final, equity = strategy.backtest(start, end)
    print(f"   ✅ PASSED: {len(data)} trading days, {len(trades)} trades")
    tests_passed += 1
except Exception as e:
    print(f"   ❌ FAILED: {str(e)[:80]}")
    tests_failed += 1

# Test 2: Short-Term on different symbol
print("\n2. Short-Term Strategy on AAPL (30 calendar days)...")
try:
    strategy = ShortTermStrategy('AAPL')
    end = datetime.now()
    start = end - timedelta(days=30)
    data, trades, final, equity = strategy.backtest(start, end)
    print(f"   ✅ PASSED: {len(data)} trading days, {len(trades)} trades")
    tests_passed += 1
except Exception as e:
    print(f"   ❌ FAILED: {str(e)[:80]}")
    tests_failed += 1

# Test 3: Simple Strategy (45 calendar days = ~30 trading days)
print("\n3. Simple Mean Reversion (45 calendar days)...")
try:
    strategy = SimpleMeanReversionStrategy('SPY', lookback=10)
    end = datetime.now()
    start = end - timedelta(days=45)
    data, trades, final = strategy.backtest(start, end)
    print(f"   ✅ PASSED: {len(data)} trading days, {len(trades)} trades")
    tests_passed += 1
except Exception as e:
    print(f"   ❌ FAILED: {str(e)[:80]}")
    tests_failed += 1

# Test 4: ML Strategy (130 calendar days = ~90 trading days)
print("\n4. ML Strategy (130 calendar days, quiet mode)...")
try:
    strategy = MLTradingStrategy('SPY', lookback=30, prediction_horizon=3)
    end = datetime.now()
    start = end - timedelta(days=130)
    
    # Redirect output to suppress prints
    import sys
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    df, trades, final, equity = strategy.backtest(start, end)
    
    sys.stdout = old_stdout
    print(f"   ✅ PASSED: {len(trades)} trades")
    tests_passed += 1
except Exception as e:
    import sys
    sys.stdout = old_stdout
    print(f"   ❌ FAILED: {str(e)[:80]}")
    tests_failed += 1

# Test 5: Crypto
print("\n5. Short-Term on BTC-USD (30 calendar days)...")
try:
    strategy = ShortTermStrategy('BTC-USD')
    end = datetime.now()
    start = end - timedelta(days=30)
    data, trades, final, equity = strategy.backtest(start, end)
    print(f"   ✅ PASSED: {len(data)} trading days, {len(trades)} trades")
    tests_passed += 1
except Exception as e:
    print(f"   ❌ FAILED: {str(e)[:80]}")
    tests_failed += 1

# Test 6: ETF
print("\n6. Simple Strategy on QQQ (60 calendar days)...")
try:
    strategy = SimpleMeanReversionStrategy('QQQ', lookback=15)
    end = datetime.now()
    start = end - timedelta(days=60)
    data, trades, final = strategy.backtest(start, end)
    print(f"   ✅ PASSED: {len(data)} trading days, {len(trades)} trades")
    tests_passed += 1
except Exception as e:
    print(f"   ❌ FAILED: {str(e)[:80]}")
    tests_failed += 1

# Test 7: Different stock
print("\n7. Short-Term on TSLA (45 calendar days)...")
try:
    strategy = ShortTermStrategy('TSLA')
    end = datetime.now()
    start = end - timedelta(days=45)
    data, trades, final, equity = strategy.backtest(start, end)
    print(f"   ✅ PASSED: {len(data)} trading days, {len(trades)} trades")
    tests_passed += 1
except Exception as e:
    print(f"   ❌ FAILED: {str(e)[:80]}")
    tests_failed += 1

# Test 8: Optimized Strategy (longer period)
print("\n8. Optimized Ensemble (180 calendar days, 5 trials, quiet)...")
try:
    strategy = OptimizedMLStrategy('SPY', lookback=40, prediction_horizon=5)
    end = datetime.now()
    start = end - timedelta(days=180)
    
    import sys
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    df, trades, final, equity = strategy.backtest(start, end, optimize_params=True, n_trials=5)
    
    sys.stdout = old_stdout
    print(f"   ✅ PASSED: {len(trades)} trades")
    tests_passed += 1
except Exception as e:
    import sys
    sys.stdout = old_stdout
    print(f"   ❌ FAILED: {str(e)[:80]}")
    tests_failed += 1

# Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print(f"✅ Passed: {tests_passed}/8")
print(f"❌ Failed: {tests_failed}/8")
print()

if tests_failed == 0:
    print("🎉 ALL TESTS PASSED! System ready for production.")
else:
    print(f"⚠️  {tests_failed} test(s) failed. Review errors above.")

print("=" * 80)
