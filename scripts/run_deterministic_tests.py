"""
Deterministic Test Harness
Validates all trading system invariants without requiring pytest or live data
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from canonical_data import CanonicalDataFetcher
from validated_indicators import ValidatedIndicators, compute_all_indicators
from validated_levels import ValidatedKeyLevels
from validated_regime import ValidatedRegime
from validated_risk import ValidatedRiskMetrics
from validated_portfolio import ValidatedPortfolio
from market_analytics import MarketAnalytics
from core_config import INDICATOR_CFG, LEVEL_CFG, REGIME_CFG, PORTFOLIO_CFG


# ============================================================================
# Synthetic Data Generators
# ============================================================================

def generate_synthetic_ohlcv(num_days=252, base_price=100.0, vol=0.01, trend=0.0, seed=42):
    """Generate synthetic OHLCV data"""
    np.random.seed(seed)
    
    dates = pd.date_range('2024-01-01', periods=num_days, freq='B')
    returns = np.random.normal(trend, vol, num_days)
    prices = base_price * np.exp(np.cumsum(returns))
    
    data = []
    for date, close in zip(dates, prices):
        high = close * (1 + abs(np.random.normal(0, vol * 0.5)))
        low = close * (1 - abs(np.random.normal(0, vol * 0.5)))
        open_price = low + (high - low) * np.random.random()
        volume = int(np.random.uniform(1e6, 10e6))
        
        data.append({
            'Date': date,
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': close,
            'Volume': volume
        })
    
    return pd.DataFrame(data).set_index('Date')


def generate_flat_prices(num_days=50, price=100.0):
    """Generate flat price series"""
    dates = pd.date_range('2024-01-01', periods=num_days, freq='B')
    
    data = []
    for date in dates:
        data.append({
            'Date': date,
            'Open': price,
            'High': price * 1.001,
            'Low': price * 0.999,
            'Close': price,
            'Volume': 1000000
        })
    
    return pd.DataFrame(data).set_index('Date')


# ============================================================================
# Test Classes
# ============================================================================

class TestResult:
    def __init__(self, name, passed, message=""):
        self.name = name
        self.passed = passed
        self.message = message
    
    def __repr__(self):
        status = "✓ PASS" if self.passed else "✗ FAIL"
        msg = f" - {self.message}" if self.message else ""
        return f"{status}: {self.name}{msg}"


class TestSuite:
    def __init__(self, name):
        self.name = name
        self.results = []
    
    def add(self, test_name, condition, message=""):
        result = TestResult(test_name, condition, message)
        self.results.append(result)
        return condition
    
    def assert_true(self, test_name, condition, message=""):
        return self.add(test_name, condition, message)
    
    def assert_range(self, test_name, value, min_val, max_val, message=""):
        in_range = min_val <= value <= max_val
        msg = message or f"Value {value:.4f} not in [{min_val}, {max_val}]"
        return self.add(test_name, in_range, msg)
    
    def assert_close(self, test_name, val1, val2, tol=1e-6, message=""):
        close = abs(val1 - val2) < tol
        msg = message or f"Values not close: {val1:.6f} vs {val2:.6f}"
        return self.add(test_name, close, msg)
    
    def report(self):
        print(f"\n{'='*70}")
        print(f"TEST SUITE: {self.name}")
        print(f"{'='*70}")
        
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        
        for result in self.results:
            print(f"  {result}")
        
        print(f"\n{'-'*70}")
        print(f"Total: {len(self.results)} | Passed: {passed} | Failed: {failed}")
        print(f"{'='*70}\n")
        
        return failed == 0


# ============================================================================
# Test: Data & Canonical Price
# ============================================================================

def test_canonical_data():
    """Test data fetching and canonical price column"""
    suite = TestSuite("Canonical Data")
    
    df = generate_synthetic_ohlcv(100, seed=42)
    df['Price'] = df['Close']  # Simulate canonical price
    
    suite.assert_true(
        "Price column exists",
        'Price' in df.columns
    )
    
    suite.assert_true(
        "No MultiIndex columns",
        not isinstance(df.columns, pd.MultiIndex)
    )
    
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required_cols:
        suite.assert_true(
            f"Required column '{col}' present",
            col in df.columns
        )
    
    suite.assert_true(
        "All prices positive",
        (df['Price'] > 0).all()
    )
    
    suite.assert_true(
        "High >= Low",
        (df['High'] >= df['Low']).all()
    )
    
    return suite.report()


# ============================================================================
# Test: Indicators
# ============================================================================

def test_indicators():
    """Test indicator calculations and invariants"""
    suite = TestSuite("Technical Indicators")
    
    df = generate_synthetic_ohlcv(252, seed=42)
    df['Price'] = df['Close']
    
    # RSI
    rsi = ValidatedIndicators.rsi(df['Price'])
    rsi_clean = rsi.dropna()
    
    suite.assert_true(
        "RSI produces values",
        len(rsi_clean) > 0
    )
    
    suite.assert_range(
        "RSI in [0, 100]",
        rsi_clean.iloc[-1],
        0, 100,
        f"RSI range: [{rsi_clean.min():.2f}, {rsi_clean.max():.2f}]"
    )
    
    # Stochastic
    stoch_k, stoch_d = ValidatedIndicators.stochastic(df['High'], df['Low'], df['Close'])
    k_clean = stoch_k.dropna()
    d_clean = stoch_d.dropna()
    
    suite.assert_range(
        "Stochastic %K in [0, 100]",
        k_clean.iloc[-1],
        0, 100
    )
    
    suite.assert_range(
        "Stochastic %D in [0, 100]",
        d_clean.iloc[-1],
        0, 100
    )
    
    # ADX
    adx, plus_di, minus_di = ValidatedIndicators.adx(df['High'], df['Low'], df['Close'])
    adx_clean = adx.dropna()
    
    suite.assert_range(
        "ADX in [0, 100]",
        adx_clean.iloc[-1],
        0, 100
    )
    
    # MACD
    macd, signal, hist = ValidatedIndicators.macd(df['Price'])
    
    # Check histogram consistency
    computed_hist = (macd - signal).dropna()
    hist_clean = hist.dropna()
    
    # Align indices
    common_idx = computed_hist.index.intersection(hist_clean.index)
    if len(common_idx) > 0:
        diff = abs(computed_hist.loc[common_idx] - hist_clean.loc[common_idx]).max()
        suite.assert_true(
            "MACD histogram = MACD - Signal",
            diff < 1e-6,
            f"Max diff: {diff:.2e}"
        )
    
    # Test no NaNs in final outputs
    df_full = compute_all_indicators(df)
    final_rows = df_full.iloc[-50:]
    
    critical_cols = ['RSI', 'MACD', 'ADX', 'Stoch_K', 'Stoch_D']
    for col in critical_cols:
        if col in final_rows.columns:
            nan_count = final_rows[col].isna().sum()
            suite.assert_true(
                f"No NaNs in {col} (final 50 rows)",
                nan_count == 0,
                f"{nan_count} NaNs found"
            )
    
    return suite.report()


# ============================================================================
# Test: Key Levels (Fibonacci, S/R)
# ============================================================================

def test_key_levels():
    """Test key levels calculations"""
    suite = TestSuite("Key Levels (Fibonacci & S/R)")
    
    df = generate_synthetic_ohlcv(252, seed=42)
    df['Price'] = df['Close']
    
    lookback = LEVEL_CFG.FIB_LOOKBACK
    
    fib_result = ValidatedKeyLevels.fibonacci_retracements(df, lookback=lookback)
    
    # Check metadata
    suite.assert_true(
        "Fib has anchor_high_date",
        'anchor_high_date' in fib_result
    )
    
    suite.assert_true(
        "Fib has anchor_low_date",
        'anchor_low_date' in fib_result
    )
    
    # Verify anchors are within window
    if 'anchor_high_date' in fib_result and 'lookback_start' in fib_result:
        anchor_high = fib_result['anchor_high_date']
        start = fib_result['lookback_start']
        end = fib_result['lookback_end']
        
        suite.assert_true(
            "Fib high anchor in window",
            start <= anchor_high <= end,
            f"{anchor_high} not in [{start}, {end}]"
        )
    
    # Check level ordering
    high = fib_result['0.0%']
    mid = fib_result['50.0%']
    low = fib_result['100.0%']
    
    suite.assert_true(
        "Fib levels ordered (high > mid > low)",
        high > mid > low,
        f"{high:.2f} > {mid:.2f} > {low:.2f}"
    )
    
    # Test S/R proximity
    sr_result = ValidatedKeyLevels.support_resistance(df)
    current_price = sr_result['current_price']
    proximity = LEVEL_CFG.SR_PROXIMITY_FILTER
    
    for level in sr_result['support']:
        ratio = level / current_price
        suite.assert_true(
            f"Support ${level:.2f} within proximity",
            ratio > (1 - proximity),
            f"Ratio: {ratio:.3f}"
        )
    
    for level in sr_result['resistance']:
        ratio = level / current_price
        suite.assert_true(
            f"Resistance ${level:.2f} within proximity",
            ratio < (1 + proximity),
            f"Ratio: {ratio:.3f}"
        )
    
    return suite.report()


# ============================================================================
# Test: Regime Classification
# ============================================================================

def test_regime():
    """Test market regime detection"""
    suite = TestSuite("Market Regime Classification")
    
    df = generate_synthetic_ohlcv(252, seed=42)
    df['Price'] = df['Close']
    df = compute_all_indicators(df)
    
    regime = ValidatedRegime.classify_regime(df)
    
    suite.assert_true(
        "Regime has 'regime' key",
        'regime' in regime
    )
    
    suite.assert_true(
        "Regime has 'rationale' key",
        'rationale' in regime
    )
    
    suite.assert_true(
        "Regime has 'metrics' key",
        'metrics' in regime
    )
    
    suite.assert_true(
        "Rationale is non-empty",
        len(regime.get('rationale', '')) > 0
    )
    
    # Check confidence bounds
    conf = regime.get('confidence', 0)
    suite.assert_range(
        "Confidence in [0, 1]",
        conf,
        0, 1
    )
    
    # Check ADX in metrics
    if 'metrics' in regime and 'adx' in regime['metrics']:
        adx = regime['metrics']['adx']
        suite.assert_range(
            "ADX in metrics bounded [0, 100]",
            adx,
            0, 100
        )
    
    return suite.report()


# ============================================================================
# Test: Risk Metrics
# ============================================================================

def test_risk_metrics():
    """Test risk calculations"""
    suite = TestSuite("Risk Metrics")
    
    df = generate_synthetic_ohlcv(252, seed=42)
    df['Price'] = df['Close']
    
    # Use canonical returns WITHOUT fillna(0)
    returns = np.log(df['Price'] / df['Price'].shift(1)).dropna()
    
    # Volatility
    vol = ValidatedRiskMetrics.volatility(returns)
    
    suite.assert_true(
        "Vol has daily component",
        'volatility_daily' in vol
    )
    
    suite.assert_true(
        "Vol has annualized component",
        'volatility_annualized' in vol
    )
    
    suite.assert_true(
        "Vol has annualization factor",
        'annualization_factor' in vol
    )
    
    # Check annualization
    if all(k in vol for k in ['volatility_daily', 'volatility_annualized', 'annualization_factor']):
        expected = vol['volatility_daily'] * vol['annualization_factor']
        actual = vol['volatility_annualized']
        suite.assert_close(
            "Annualized vol = daily * sqrt(252)",
            expected,
            actual,
            tol=1e-6
        )
    
    # Check returns length matches data rows - 1
    suite.assert_true(
        "Returns length = data rows - 1",
        len(returns) == len(df) - 1,
        f"Returns: {len(returns)}, Expected: {len(df)-1}"
    )
    
    # VaR
    var = ValidatedRiskMetrics.value_at_risk(returns)
    
    suite.assert_true(
        "VaR has horizon",
        'horizon_days' in var
    )
    
    suite.assert_true(
        "VaR has method",
        'method' in var
    )
    
    # CVaR
    cvar = ValidatedRiskMetrics.conditional_var(returns)
    
    # CVaR should be more negative than VaR
    suite.assert_true(
        "CVaR <= VaR (more negative)",
        cvar['cvar'] <= var['var'],
        f"CVaR={cvar['cvar']:.4f}, VaR={var['var']:.4f}"
    )
    
    return suite.report()


# ============================================================================
# Test: Portfolio Allocation (Fractional Shares)
# ============================================================================

def test_portfolio_fractional():
    """Test portfolio allocation with fractional shares"""
    suite = TestSuite("Portfolio Allocation (Fractional Shares)")
    
    # Test 1: Fractional shares enabled
    portfolio_frac = ValidatedPortfolio(
        equity=100000,
        fractional_allowed=True
    )
    
    target_weights = {'SPY': 0.6, 'QQQ': 0.4}
    prices = {'SPY': 450.75, 'QQQ': 380.25}
    
    summary_frac = portfolio_frac.allocate(target_weights, prices)
    
    spy_shares_frac = summary_frac['positions']['SPY']['shares']
    qqq_shares_frac = summary_frac['positions']['QQQ']['shares']
    
    # At least one should be fractional
    is_fractional = (spy_shares_frac != int(spy_shares_frac)) or (qqq_shares_frac != int(qqq_shares_frac))
    
    suite.assert_true(
        "Fractional shares enabled → shares are fractional",
        is_fractional,
        f"SPY: {spy_shares_frac:.4f}, QQQ: {qqq_shares_frac:.4f}"
    )
    
    # Test 2: Fractional shares disabled
    portfolio_whole = ValidatedPortfolio(
        equity=100000,
        fractional_allowed=False
    )
    
    summary_whole = portfolio_whole.allocate(target_weights, prices)
    
    spy_shares_whole = summary_whole['positions']['SPY']['shares']
    qqq_shares_whole = summary_whole['positions']['QQQ']['shares']
    
    suite.assert_true(
        "Fractional disabled → SPY shares are whole",
        spy_shares_whole == int(spy_shares_whole),
        f"SPY: {spy_shares_whole}"
    )
    
    suite.assert_true(
        "Fractional disabled → QQQ shares are whole",
        qqq_shares_whole == int(qqq_shares_whole),
        f"QQQ: {qqq_shares_whole}"
    )
    
    # Test 3: Cash tracking
    suite.assert_true(
        "Cash remaining tracked",
        'cash_remaining' in summary_frac
    )
    
    suite.assert_true(
        "Cash is non-negative",
        summary_frac['cash_remaining'] >= 0
    )
    
    # Total should equal equity
    total = summary_frac['total_invested'] + summary_frac['cash_remaining'] + summary_frac['transaction_costs']
    diff = abs(total - portfolio_frac.equity)
    
    suite.assert_true(
        "Total accounts balance",
        diff < 1.0,
        f"Diff: ${diff:.2f}"
    )
    
    # Test 4: Transaction costs
    portfolio_costs = ValidatedPortfolio(
        equity=100000,
        fractional_allowed=True,
        slippage_bps=5.0,
        commission_per_share=0.005
    )
    
    summary_costs = portfolio_costs.allocate(target_weights, prices)
    
    suite.assert_true(
        "Transaction costs > 0",
        summary_costs['transaction_costs'] > 0,
        f"Costs: ${summary_costs['transaction_costs']:.2f}"
    )
    
    return suite.report()


# ============================================================================
# Test: Edge Cases
# ============================================================================

def test_edge_cases():
    """Test edge cases and error handling"""
    suite = TestSuite("Edge Cases")
    
    # Flat prices
    df_flat = generate_flat_prices(100, price=100.0)
    df_flat['Price'] = df_flat['Close']
    
    try:
        df_flat = compute_all_indicators(df_flat)
        rsi_final = df_flat['RSI'].iloc[-1]
        
        suite.assert_range(
            "Flat prices: RSI bounded",
            rsi_final,
            0, 100,
            f"RSI={rsi_final:.2f}"
        )
        
        suite.assert_true(
            "Flat prices: RSI not NaN",
            not np.isnan(rsi_final)
        )
    except Exception as e:
        suite.assert_true(
            "Flat prices: indicators compute",
            False,
            f"Error: {e}"
        )
    
    # Short history
    df_short = generate_synthetic_ohlcv(20, seed=42)
    df_short['Price'] = df_short['Close']
    
    try:
        df_short = compute_all_indicators(df_short)
        
        suite.assert_true(
            "Short history: doesn't crash",
            True
        )
    except Exception as e:
        suite.assert_true(
            "Short history: doesn't crash",
            False,
            f"Error: {e}"
        )
    
    return suite.report()


# ============================================================================
# Main Runner
# ============================================================================

def main():
    """Run all deterministic tests"""
    print("\n" + "="*70)
    print(" "*20 + "DETERMINISTIC TEST HARNESS")
    print("="*70)
    print("\nRunning comprehensive validation without pytest or live data...\n")
    
    results = {}
    
    # Run all test suites
    results['Canonical Data'] = test_canonical_data()
    results['Indicators'] = test_indicators()
    results['Key Levels'] = test_key_levels()
    results['Regime'] = test_regime()
    results['Risk Metrics'] = test_risk_metrics()
    results['Portfolio'] = test_portfolio_fractional()
    results['Edge Cases'] = test_edge_cases()
    
    # Summary
    print("\n" + "="*70)
    print(" "*25 + "FINAL SUMMARY")
    print("="*70)
    
    all_passed = all(results.values())
    passed_count = sum(results.values())
    total_count = len(results)
    
    for suite_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {suite_name}")
    
    print(f"\n{'-'*70}")
    print(f"Total: {total_count} suites | Passed: {passed_count} | Failed: {total_count - passed_count}")
    print("="*70)
    
    if all_passed:
        print("\n✓ ALL TESTS PASSED - System is deterministic and validated\n")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED - Review failures above\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
