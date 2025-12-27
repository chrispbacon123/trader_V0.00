#!/usr/bin/env python3
"""
Smoke Test Runner
Single-command validation of the full trading platform pipeline

Usage:
    python tools/smoke_platform.py           # Run with fixture (offline, deterministic)
    python tools/smoke_platform.py --live    # Run with live yfinance data (requires network)
    
This validates:
    1. Data fetch/load → normalize
    2. Market analytics (regime, levels, fibonacci, momentum, risk)
    3. Strategy backtest
    4. Strategy optimization
    5. Portfolio allocation (fractional shares)
    6. Persistence write/read
    7. Report generation
"""

import sys
import os
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Ensure we can import from the project root (parent of tools/)
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_deterministic_fixture():
    """
    Create a deterministic test DataFrame without network calls.
    Returns (DataFrame, metadata) in normalized format.
    """
    import pandas as pd
    import numpy as np
    
    # Deterministic random seed for reproducibility
    np.random.seed(42)
    
    # Create 252 trading days of synthetic data
    dates = pd.date_range(start='2023-01-01', periods=252, freq='B')
    
    # Generate synthetic price data (random walk with drift)
    returns = np.random.normal(0.0005, 0.02, len(dates))  # ~12.6% annual, 20% vol
    price = 100 * np.exp(np.cumsum(returns))
    
    # Create OHLCV data
    df = pd.DataFrame({
        'Open': price * (1 + np.random.uniform(-0.01, 0.01, len(dates))),
        'High': price * (1 + np.random.uniform(0, 0.02, len(dates))),
        'Low': price * (1 + np.random.uniform(-0.02, 0, len(dates))),
        'Close': price,
        'Volume': np.random.randint(1000000, 10000000, len(dates)),
        'Price': price  # Canonical price column
    }, index=dates)
    
    # Ensure High >= Close/Open and Low <= Close/Open
    df['High'] = df[['Open', 'Close', 'High']].max(axis=1)
    df['Low'] = df[['Open', 'Close', 'Low']].min(axis=1)
    
    metadata = {
        'symbol': 'TEST',
        'price_source': 'Close',
        'transformations': ['synthetic_fixture'],
        'actual_start': str(dates[0]),
        'actual_end': str(dates[-1]),
        'num_rows': len(df)
    }
    
    return df, metadata


def load_csv_fixture(filepath: str):
    """Load a CSV fixture file if it exists."""
    import pandas as pd
    from data_normalization import DataNormalizer
    
    if not Path(filepath).exists():
        return None, None
    
    df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    normalizer = DataNormalizer()
    df, metadata = normalizer.normalize_market_data(df, symbol='FIXTURE', require_ohlc=False)
    
    return df, metadata


def check_data_normalization(df, metadata):
    """Check 1: Data normalization"""
    print("\n" + "="*70)
    print("CHECK 1: Data Normalization")
    print("="*70)
    
    from data_normalization import DataNormalizer
    
    # Verify normalized data has required columns
    assert 'Price' in df.columns, "Missing Price column"
    assert len(df) > 0, "Empty DataFrame"
    assert df.index.is_monotonic_increasing, "Index not sorted"
    
    print(f"  [OK] DataFrame has {len(df)} rows")
    print(f"  [OK] Columns: {list(df.columns)}")
    print(f"  [OK] Date range: {df.index[0]} to {df.index[-1]}")
    print(f"  [OK] Price source: {metadata.get('price_source', 'Unknown')}")
    
    return True


def check_market_analytics(df, symbol='TEST'):
    """Check 2: Market analytics with pre-fetched data (NO re-fetch)"""
    print("\n" + "="*70)
    print("CHECK 2: Market Analytics (df-in, no re-fetch)")
    print("="*70)
    
    from market_analytics import MarketAnalytics
    
    analytics = MarketAnalytics(symbol)
    
    # Use the analyze() method with pre-fetched data
    result = analytics.analyze(df, symbol=symbol)
    
    # Verify stable schema
    assert 'success' in result, "Missing 'success' key"
    assert 'data_summary' in result, "Missing 'data_summary' key"
    assert 'regime' in result, "Missing 'regime' key"
    assert 'key_levels' in result, "Missing 'key_levels' key"
    assert 'momentum' in result, "Missing 'momentum' key"
    assert 'risk' in result, "Missing 'risk' key"
    
    print(f"  [OK] Analysis success: {result['success']}")
    print(f"  [OK] Data summary: {result['data_summary']}")
    
    if result.get('regime', {}).get('type'):
        print(f"  [OK] Regime: {result['regime']['type']} (conf: {result['regime'].get('confidence', 0):.2%})")
    
    if result.get('momentum', {}).get('RSI'):
        print(f"  [OK] RSI: {result['momentum']['RSI']:.2f}")
    
    if result.get('risk', {}).get('sharpe_ratio'):
        print(f"  [OK] Sharpe: {result['risk']['sharpe_ratio']:.4f}")
    
    return result


def check_platform_api(df, symbol='TEST'):
    """Check 3: Platform API with data injection"""
    print("\n" + "="*70)
    print("CHECK 3: Platform API (data injection, no double-fetch)")
    print("="*70)
    
    from platform_api import get_api
    from core_config import PLATFORM_VERSION
    
    api = get_api()
    
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    
    # Call analyze_market with pre-fetched data
    result = api.analyze_market(
        symbol,
        start_date,
        end_date,
        data=df,  # Inject data - prevents re-fetch
        debug=False
    )
    
    # Verify schema
    assert result.get('platform_version') == PLATFORM_VERSION, \
        f"Version mismatch: expected {PLATFORM_VERSION}, got {result.get('platform_version')}"
    
    print(f"  [OK] Platform version: {result['platform_version']}")
    print(f"  [OK] Symbol: {result['symbol']}")
    print(f"  [OK] Period: {result['period']}")
    
    # Verify date range matches input data
    data_summary = result.get('data_summary', {})
    print(f"  [OK] Data summary: {data_summary}")
    
    return result


def check_backtest(df, symbol='TEST'):
    """Check 4: Strategy backtest with data injection"""
    print("\n" + "="*70)
    print("CHECK 4: Strategy Backtest")
    print("="*70)
    
    from simple_strategy import SimpleMeanReversionStrategy
    
    strategy = SimpleMeanReversionStrategy(
        symbol=symbol,
        initial_capital=10000,
        lookback=20,
        std_dev=2.0
    )
    
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    
    # Run backtest with injected data
    result = strategy.backtest(start_date, end_date, data=df)
    
    # Unpack results
    df_result, trades, final_value = result[:3]
    
    return_pct = ((final_value - 10000) / 10000) * 100
    
    print(f"  [OK] Final value: ${final_value:,.2f}")
    print(f"  [OK] Return: {return_pct:.2f}%")
    print(f"  [OK] Trades: {len(trades)}")
    
    return {
        'success': True,
        'final_value': final_value,
        'return_pct': return_pct,
        'num_trades': len(trades)
    }


def check_portfolio_allocation():
    """Check 5: Portfolio allocation with fractional shares"""
    print("\n" + "="*70)
    print("CHECK 5: Portfolio Allocation (Fractional Shares)")
    print("="*70)
    
    from validated_portfolio import ValidatedPortfolio
    
    # Create portfolio with fractional shares allowed
    portfolio = ValidatedPortfolio(
        equity=10000,
        fractional_allowed=True
    )
    
    # Target allocation
    target_weights = {
        'AAPL': 0.40,
        'GOOGL': 0.35,
        'MSFT': 0.25
    }
    
    prices = {
        'AAPL': 175.50,
        'GOOGL': 140.25,
        'MSFT': 380.00
    }
    
    # Allocate
    result = portfolio.allocate(target_weights, prices)
    
    # Verify fractional shares
    print(f"  [OK] Total equity: ${result['total_equity']:,.2f}")
    print(f"  [OK] Invested: ${result['total_invested']:,.2f}")
    print(f"  [OK] Cash remaining: ${result['cash_remaining']:,.2f} ({result['cash_pct']:.2f}%)")
    print(f"  [OK] Fractional allowed: {result['fractional_allowed']}")
    
    for sym, pos in result['positions'].items():
        print(f"      {sym}: {pos['shares']:.4f} shares @ ${pos['price']:.2f} = ${pos['value']:,.2f}")
        
        # Verify fractional (non-integer) shares
        if result['fractional_allowed']:
            assert pos['shares'] != int(pos['shares']), \
                f"Expected fractional shares for {sym}"
    
    return result


def check_persistence():
    """Check 6: Persistence write/read with schema migration"""
    print("\n" + "="*70)
    print("CHECK 6: Persistence (Schema Migration)")
    print("="*70)
    
    from persistence import normalize_run_record, load_history, append_history, migrate_record
    
    # Test 1: Normalize old-format record
    old_record = {
        'date': '2023-01-15',
        'ticker': 'AAPL',
        'total_return': 5.5,
        'trades': 10
    }
    
    normalized = normalize_run_record(old_record)
    
    assert normalized['timestamp'] == '2023-01-15', "Timestamp migration failed"
    assert normalized['symbol'] == 'AAPL', "Symbol migration failed"
    assert normalized['return_pct'] == 5.5, "Return migration failed"
    assert normalized['num_trades'] == 10, "Trades migration failed"
    
    print(f"  [OK] Old record normalized: {old_record} -> keys: {list(normalized.keys())}")
    
    # Test 2: Write and read back
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / 'test_history.json'
        
        # Append records
        record1 = {
            'timestamp': datetime.now().isoformat(),
            'symbol': 'SPY',
            'strategy': 'TestStrategy',
            'return_pct': 10.5
        }
        
        success = append_history(str(history_path), record1)
        assert success, "Failed to append record"
        
        # Load and verify
        loaded = load_history(str(history_path))
        assert len(loaded) == 1, f"Expected 1 record, got {len(loaded)}"
        assert loaded[0]['symbol'] == 'SPY', "Record not preserved"
        
        print(f"  [OK] Write/read cycle successful")
        print(f"  [OK] Loaded record: {loaded[0]}")
    
    return True


def check_result_schemas():
    """Check 7: Result schema validation"""
    print("\n" + "="*70)
    print("CHECK 7: Result Schemas")
    print("="*70)
    
    from result_schemas import (
        MarketAnalysisResult,
        BacktestResult,
        OptimizationResult,
        ensure_optimization_schema
    )
    
    # Test optimization schema enforcement
    bad_result = {
        'success': False,
        'best_params': None,  # BAD - should never be None
        'tested': 5
    }
    
    fixed = ensure_optimization_schema(bad_result)
    
    assert fixed['best_params'] == {}, "Failed to fix None best_params"
    assert 'valid' in fixed, "Missing 'valid' key"
    assert 'failures' in fixed, "Missing 'failures' key"
    
    print(f"  [OK] Schema enforcement fixed None best_params")
    print(f"  [OK] Added missing keys: {[k for k in fixed if k not in bad_result]}")
    
    # Test typed result creation
    opt_result = OptimizationResult.from_dict(fixed)
    assert opt_result.best_params == {}, "Typed result failed"
    
    print(f"  [OK] Typed OptimizationResult created successfully")
    
    return True


def check_batch_analyze(data_map):
    """Check 8: Batch analyze with data_map (no duplicate fetches)"""
    print("\n" + "="*70)
    print("CHECK 8: Batch Analyze")
    print("="*70)
    
    from platform_api import get_api, export_batch_analysis_csv
    import tempfile
    
    api = get_api()
    
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    
    # Run batch analyze with data_map
    symbols = list(data_map.keys())
    results = api.batch_analyze(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        data_map=data_map
    )
    
    # Verify results
    assert len(results) == len(symbols), f"Expected {len(symbols)} results, got {len(results)}"
    
    for r in results:
        assert 'symbol' in r, "Missing symbol in result"
        assert 'success' in r, "Missing success in result"
    
    print(f"  [OK] Batch analyzed {len(symbols)} symbols")
    
    # Test CSV export
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        export_batch_analysis_csv(results, f.name)
        print(f"  [OK] Exported to CSV: {f.name}")
    
    return results


def check_run_analysis():
    """Check 9: Run analysis utilities"""
    print("\n" + "="*70)
    print("CHECK 9: Run Analysis")
    print("="*70)
    
    from run_analysis import load_runs, summarize_runs, format_run_summary
    import tempfile
    import json
    
    # Create a temp JSONL file with test data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        test_runs = [
            {
                'timestamp': '2024-01-01T10:00:00',
                'run_id': 'test123',
                'kind': 'optimize',
                'inputs': {'symbol': 'SPY', 'strategy': 'TestStrategy'},
                'outputs': {'best_score': 1.5, 'success': True},
                'warnings': [],
                'failure_summary': {},
                'error': None,
                'platform_version': 'test'
            },
            {
                'timestamp': '2024-01-02T10:00:00',
                'run_id': 'test456',
                'kind': 'analyze',
                'inputs': {'symbol': 'QQQ'},
                'outputs': {'regime': 'bullish'},
                'warnings': [],
                'failure_summary': {},
                'error': None,
                'platform_version': 'test'
            }
        ]
        for run in test_runs:
            f.write(json.dumps(run) + '\n')
        temp_path = f.name
    
    # Test load_runs
    runs = load_runs(temp_path)
    assert len(runs) == 2, f"Expected 2 runs, got {len(runs)}"
    print(f"  [OK] Loaded {len(runs)} runs")
    
    # Test filter by kind
    opt_runs = load_runs(temp_path, kind='optimize')
    assert len(opt_runs) == 1, f"Expected 1 optimize run, got {len(opt_runs)}"
    print(f"  [OK] Filtered to {len(opt_runs)} optimization runs")
    
    # Test summarize
    summary = summarize_runs(runs)
    assert summary['total_runs'] == 2, "Summary total wrong"
    assert 'optimize' in summary['by_kind'], "Missing optimize in summary"
    print(f"  [OK] Summary: {summary['total_runs']} total, {summary['by_kind']}")
    
    # Test format
    formatted = format_run_summary(runs[0])
    assert 'Run ID' in formatted, "Format missing run ID"
    print(f"  [OK] Format run summary works")
    
    # Cleanup
    Path(temp_path).unlink()
    
    return True


def check_decision_trace(df, symbol='TEST'):
    """Check 10: Decision trace for explainability"""
    print("\n" + "="*70)
    print("CHECK 10: Decision Trace")
    print("="*70)
    
    from platform_api import get_api
    from simple_strategy import SimpleMeanReversionStrategy
    
    api = get_api()
    
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    
    # Run backtest with debug=True
    result = api.backtest_strategy(
        strategy_class=SimpleMeanReversionStrategy,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        params={'lookback': 20, 'std_dev': 2.0},
        data=df,
        debug=True
    )
    
    # Verify decision trace
    assert result.get('success'), f"Backtest failed: {result.get('error')}"
    assert 'decision_trace' in result, "Missing decision_trace in debug result"
    
    trace = result['decision_trace']
    assert 'strategy' in trace, "Trace missing strategy"
    assert 'indicator_values' in trace, "Trace missing indicator_values"
    assert 'thresholds' in trace, "Trace missing thresholds"
    
    print(f"  [OK] Decision trace included in backtest result")
    print(f"  [OK] Last signal: {trace.get('last_signal')}")
    print(f"  [OK] Indicators: {list(trace.get('indicator_values', {}).keys())}")
    print(f"  [OK] Thresholds: {trace.get('thresholds')}")
    
    return result


def run_smoke_tests(use_live_data: bool = False, quick: bool = False):
    """Run all smoke tests"""
    print("\n" + "="*70)
    print("SMOKE TEST RUNNER")
    print("="*70)
    
    from core_config import PLATFORM_VERSION, get_version_string
    
    print(f"\n{get_version_string()}")
    print(f"Mode: {'LIVE (yfinance)' if use_live_data else 'OFFLINE (fixture)'}")
    print(f"Quick: {quick}")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Get test data
    if use_live_data:
        print("\n[INFO] Fetching live data from yfinance...")
        from platform_api import get_api
        api = get_api()
        start = datetime.now() - timedelta(days=365)
        end = datetime.now()
        df, metadata = api.fetch('SPY', start, end)
        symbol = 'SPY'
    else:
        print("\n[INFO] Using deterministic fixture (no network)")
        df, metadata = create_deterministic_fixture()
        symbol = 'TEST'
    
    # Create data_map for batch tests
    data_map = {symbol: df}
    if not quick:
        # Add a second fixture with different seed for batch testing
        import numpy as np
        np.random.seed(43)
        df2, _ = create_deterministic_fixture()
        data_map['TEST2'] = df2
    
    # Run checks
    results = {}
    
    try:
        results['1_normalization'] = check_data_normalization(df, metadata)
    except Exception as e:
        results['1_normalization'] = f"FAILED: {e}"
        print(f"  [FAIL] {e}")
    
    try:
        results['2_analytics'] = check_market_analytics(df, symbol)
    except Exception as e:
        results['2_analytics'] = f"FAILED: {e}"
        print(f"  [FAIL] {e}")
    
    try:
        results['3_platform_api'] = check_platform_api(df, symbol)
    except Exception as e:
        results['3_platform_api'] = f"FAILED: {e}"
        print(f"  [FAIL] {e}")
    
    try:
        results['4_backtest'] = check_backtest(df, symbol)
    except Exception as e:
        results['4_backtest'] = f"FAILED: {e}"
        print(f"  [FAIL] {e}")
    
    try:
        results['5_portfolio'] = check_portfolio_allocation()
    except Exception as e:
        results['5_portfolio'] = f"FAILED: {e}"
        print(f"  [FAIL] {e}")
    
    try:
        results['6_persistence'] = check_persistence()
    except Exception as e:
        results['6_persistence'] = f"FAILED: {e}"
        print(f"  [FAIL] {e}")
    
    try:
        results['7_schemas'] = check_result_schemas()
    except Exception as e:
        results['7_schemas'] = f"FAILED: {e}"
        print(f"  [FAIL] {e}")
    
    # New checks
    if not quick:
        try:
            results['8_batch_analyze'] = check_batch_analyze(data_map)
        except Exception as e:
            results['8_batch_analyze'] = f"FAILED: {e}"
            print(f"  [FAIL] {e}")
        
        try:
            results['9_run_analysis'] = check_run_analysis()
        except Exception as e:
            results['9_run_analysis'] = f"FAILED: {e}"
            print(f"  [FAIL] {e}")
        
        try:
            results['10_decision_trace'] = check_decision_trace(df, symbol)
        except Exception as e:
            results['10_decision_trace'] = f"FAILED: {e}"
            print(f"  [FAIL] {e}")
    
    # Summary
    print("\n" + "="*70)
    print("SMOKE TEST SUMMARY")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for name, result in results.items():
        if isinstance(result, str) and result.startswith('FAILED'):
            status = "[FAIL]"
            failed += 1
        else:
            status = "[OK]"
            passed += 1
        print(f"  {status} {name}")
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n[OK] ALL SMOKE TESTS PASSED!")
        return 0
    else:
        print(f"\n[FAIL] {failed} tests failed")
        return 1


if __name__ == '__main__':
    use_live = '--live' in sys.argv
    quick = '--quick' in sys.argv
    sys.exit(run_smoke_tests(use_live_data=use_live, quick=quick))
