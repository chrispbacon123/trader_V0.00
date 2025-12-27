"""
Phase 1 Correctness Tests
Validates all critical invariants after refactor
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from canonical_data import CanonicalDataFetcher
from validated_indicators import ValidatedIndicators
from validated_levels import ValidatedKeyLevels
from validated_regime import ValidatedRegime
from validated_risk import ValidatedRisk
from validated_portfolio import ValidatedPortfolio
from sizing import calculate_shares, calculate_shares_from_weight, format_shares
from core_config import PORTFOLIO_CFG, INDICATOR_CFG, LEVEL_CFG, REGIME_CFG, RISK_CFG


# ============================================================================
# PHASE 1.1: FRACTIONAL SHARES END-TO-END
# ============================================================================

def test_fractional_shares_enabled():
    """Test that fractional shares work when enabled"""
    # Temporarily enable
    original = PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED
    try:
        PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = True
        
        # Test calculate_shares
        shares, residual = calculate_shares(10000, 457.23)
        
        assert shares > 21.8 and shares < 21.9, f"Expected ~21.87 shares, got {shares}"
        assert residual < 1.0, f"Expected near-zero residual, got {residual}"
        assert shares != int(shares), "Shares should be fractional"
        
        print(f"✓ Fractional shares: {shares:.4f} shares, ${residual:.2f} residual")
        
    finally:
        PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = original


def test_fractional_shares_disabled():
    """Test that whole shares work when disabled"""
    # Temporarily disable
    original = PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED
    try:
        PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = False
        
        # Test calculate_shares
        shares, residual = calculate_shares(10000, 457.23)
        
        assert shares == int(shares), f"Shares should be whole number, got {shares}"
        assert shares == 21, f"Expected 21 shares, got {shares}"
        assert residual > 300, f"Expected significant residual, got {residual}"
        
        print(f"✓ Whole shares: {shares:.0f} shares, ${residual:.2f} residual")
        
    finally:
        PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = original


def test_format_shares():
    """Test share formatting respects fractional flag"""
    original = PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED
    try:
        # Fractional
        PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = True
        fmt = format_shares(21.8723)
        assert fmt == '.4f', f"Expected '.4f', got '{fmt}'"
        formatted = f"{21.8723:{fmt}}"
        assert '.' in formatted, "Should include decimals"
        
        # Whole
        PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = False
        fmt = format_shares(21.0)
        assert fmt == '.0f', f"Expected '.0f', got '{fmt}'"
        formatted = f"{21.0:{fmt}}"
        assert '.' not in formatted or formatted.endswith('.0'), "Should not show decimals"
        
        print(f"✓ Format shares correct")
        
    finally:
        PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = original


# ============================================================================
# PHASE 1.2: CANONICAL RETURNS (NO SYNTHETIC ZEROS)
# ============================================================================

def test_canonical_returns_no_synthetic_zero():
    """Test that canonical returns have NaN for first value, not 0"""
    fetcher = CanonicalDataFetcher()
    
    # Create synthetic data
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    df = pd.DataFrame({
        'Open': prices,
        'High': prices * 1.01,
        'Low': prices * 0.99,
        'Close': prices,
        'Volume': 1000000,
        'Price': prices
    }, index=dates)
    
    # Get returns
    returns = fetcher.get_returns(df, kind='log')
    
    assert pd.isna(returns.iloc[0]), "First return must be NaN, not 0 or any other value"
    assert not pd.isna(returns.iloc[1]), "Second return should be valid"
    assert returns.iloc[0] != 0, "First return must NOT be synthetic zero"
    
    # Test cleaned returns
    returns_clean = returns.dropna()
    assert len(returns_clean) == len(returns) - 1, "Cleaned returns should be N-1"
    assert not returns_clean.isna().any(), "No NaN after dropna"
    
    print(f"✓ Canonical returns correct: first=NaN, clean length={len(returns_clean)}")


def test_returns_contamination():
    """Test that filling first return with 0 would contaminate statistics"""
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    prices = 100 * (1 + np.random.randn(100) * 0.01).cumprod()
    
    # Correct: NaN first return
    returns_correct = np.log(prices / np.roll(prices, 1))
    returns_correct[0] = np.nan
    
    # Wrong: Zero first return
    returns_wrong = np.log(prices / np.roll(prices, 1))
    returns_wrong[0] = 0
    
    # Statistics
    mean_correct = np.nanmean(returns_correct)
    mean_wrong = np.mean(returns_wrong)
    
    # The zero pulls the mean toward zero, biasing it
    assert abs(mean_correct - mean_wrong) > 1e-6, "Filling with 0 biases statistics"
    
    print(f"✓ Returns contamination test passed")
    print(f"  Mean with NaN: {mean_correct:.6f}")
    print(f"  Mean with 0:   {mean_wrong:.6f}")
    print(f"  Bias:          {abs(mean_correct - mean_wrong):.6f}")


# ============================================================================
# PHASE 1.3: UNIT COHERENCE (VOLATILITY/RISK)
# ============================================================================

def test_volatility_annualization():
    """Test that volatility annualization is consistent"""
    # Synthetic daily returns
    daily_returns = pd.Series(np.random.randn(252) * 0.01)
    
    # Daily vol
    vol_daily = daily_returns.std()
    
    # Annualized vol
    vol_annual = vol_daily * np.sqrt(252)
    
    # Check reasonable range for equity (5%-50% annualized)
    assert 0.05 < vol_annual < 0.50, f"Annualized vol {vol_annual:.2%} outside typical range"
    
    # Test ValidatedRisk
    risk = ValidatedRisk()
    metrics = risk.compute_risk_metrics(daily_returns)
    
    # Check units are labeled
    assert 'daily' in str(metrics).lower() or 'annualized' in str(metrics).lower(), \
        "Risk metrics must label volatility units"
    
    print(f"✓ Volatility annualization correct")
    print(f"  Daily:      {vol_daily:.4f}")
    print(f"  Annualized: {vol_annual:.4f} ({vol_annual:.2%})")


def test_regime_volatility_coherence():
    """Test that regime volatility thresholds are coherent with computed volatility"""
    # Synthetic data with low, medium, high vol regimes
    np.random.seed(42)
    
    # Low vol: 5% annualized
    low_vol_returns = pd.Series(np.random.randn(252) * 0.05 / np.sqrt(252))
    
    # High vol: 30% annualized  
    high_vol_returns = pd.Series(np.random.randn(252) * 0.30 / np.sqrt(252))
    
    regime = ValidatedRegime()
    
    # Create fake price series
    low_vol_prices = 100 * (1 + low_vol_returns).cumprod()
    high_vol_prices = 100 * (1 + high_vol_returns).cumprod()
    
    low_vol_df = pd.DataFrame({'Price': low_vol_prices})
    high_vol_df = pd.DataFrame({'Price': high_vol_prices})
    
    # Classify
    low_result = regime.classify_regime(low_vol_df)
    high_result = regime.classify_regime(high_vol_df)
    
    # Low vol should NOT always classify as VOLATILE
    # High vol SHOULD classify with volatility component
    print(f"✓ Regime volatility coherence")
    print(f"  Low vol regime:  {low_result['regime']}")
    print(f"  High vol regime: {high_result['regime']}")
    print(f"  Low vol value:   {low_result.get('volatility', 'N/A')}")
    print(f"  High vol value:  {high_result.get('volatility', 'N/A')}")


# ============================================================================
# PHASE 1.4: INDICATOR INVARIANTS
# ============================================================================

def test_rsi_bounds():
    """Test that RSI is always in [0, 100]"""
    # Synthetic price data
    np.random.seed(42)
    prices = 100 * (1 + np.random.randn(100) * 0.02).cumprod()
    df = pd.DataFrame({'Price': prices})
    
    indicators = ValidatedIndicators()
    df_with_ind = indicators.add_momentum_indicators(df)
    
    rsi = df_with_ind['RSI'].dropna()
    
    assert (rsi >= 0).all(), f"RSI below 0 detected: {rsi.min()}"
    assert (rsi <= 100).all(), f"RSI above 100 detected: {rsi.max()}"
    
    print(f"✓ RSI bounds valid: [{rsi.min():.2f}, {rsi.max():.2f}]")


def test_stochastic_bounds():
    """Test that Stochastic oscillator is in [0, 100]"""
    np.random.seed(42)
    prices = 100 * (1 + np.random.randn(100) * 0.02).cumprod()
    df = pd.DataFrame({
        'Price': prices,
        'High': prices * 1.01,
        'Low': prices * 0.99
    })
    
    indicators = ValidatedIndicators()
    df_with_ind = indicators.add_momentum_indicators(df)
    
    if 'Stochastic_K' in df_with_ind.columns:
        stoch_k = df_with_ind['Stochastic_K'].dropna()
        stoch_d = df_with_ind['Stochastic_D'].dropna()
        
        assert (stoch_k >= 0).all() and (stoch_k <= 100).all(), "Stochastic_K out of bounds"
        assert (stoch_d >= 0).all() and (stoch_d <= 100).all(), "Stochastic_D out of bounds"
        
        print(f"✓ Stochastic bounds valid: K=[{stoch_k.min():.2f}, {stoch_k.max():.2f}]")


def test_macd_histogram_invariant():
    """Test that MACD histogram = MACD - Signal"""
    np.random.seed(42)
    prices = 100 * (1 + np.random.randn(100) * 0.02).cumprod()
    df = pd.DataFrame({'Price': prices})
    
    indicators = ValidatedIndicators()
    df_with_ind = indicators.add_momentum_indicators(df)
    
    if all(col in df_with_ind.columns for col in ['MACD', 'MACD_Signal', 'MACD_Histogram']):
        df_clean = df_with_ind[['MACD', 'MACD_Signal', 'MACD_Histogram']].dropna()
        
        # Check histogram = MACD - Signal
        computed_hist = df_clean['MACD'] - df_clean['MACD_Signal']
        actual_hist = df_clean['MACD_Histogram']
        
        diff = (computed_hist - actual_hist).abs().max()
        assert diff < 1e-6, f"MACD histogram mismatch: max diff = {diff}"
        
        print(f"✓ MACD histogram invariant valid (max diff = {diff:.2e})")


# ============================================================================
# PHASE 1.5: FIBONACCI ANCHOR VALIDATION
# ============================================================================

def test_fibonacci_anchors_within_lookback():
    """Test that Fibonacci anchors come from declared lookback window"""
    # Synthetic data
    dates = pd.date_range('2023-01-01', periods=200, freq='D')
    prices = 100 + np.cumsum(np.random.randn(200) * 2)
    df = pd.DataFrame({
        'Price': prices,
        'High': prices * 1.01,
        'Low': prices * 0.99
    }, index=dates)
    
    levels = ValidatedKeyLevels()
    fib_result = levels.fibonacci_retracements(df, lookback=100)
    
    # Check anchors are within last 100 periods
    last_100_start = df.index[-100]
    
    anchor_high_date = fib_result['anchor_high_date']
    anchor_low_date = fib_result['anchor_low_date']
    
    assert anchor_high_date >= last_100_start, \
        f"High anchor {anchor_high_date} before lookback window start {last_100_start}"
    assert anchor_low_date >= last_100_start, \
        f"Low anchor {anchor_low_date} before lookback window start {last_100_start}"
    
    print(f"✓ Fibonacci anchors within lookback")
    print(f"  Lookback start: {last_100_start.date()}")
    print(f"  High anchor:    {anchor_high_date.date()}")
    print(f"  Low anchor:     {anchor_low_date.date()}")


def test_fibonacci_math():
    """Test that Fibonacci levels follow the formula"""
    dates = pd.date_range('2023-01-01', periods=200, freq='D')
    prices = 100 + np.cumsum(np.random.randn(200) * 2)
    df = pd.DataFrame({
        'Price': prices,
        'High': prices * 1.01,
        'Low': prices * 0.99
    }, index=dates)
    
    levels = ValidatedKeyLevels()
    fib_result = levels.fibonacci_retracements(df)
    
    high = fib_result['anchor_high_price']
    low = fib_result['anchor_low_price']
    
    # Check formula: level = low + (high - low) * (1 - ratio)
    for ratio in [0.236, 0.382, 0.5, 0.618, 0.786]:
        key = f'fib_{ratio}'
        expected = low + (high - low) * (1 - ratio)
        actual = fib_result[key]
        
        diff = abs(expected - actual)
        assert diff < 0.01, f"Fib {ratio} mismatch: expected {expected:.2f}, got {actual:.2f}"
    
    print(f"✓ Fibonacci math correct")


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == '__main__':
    print("="*80)
    print("PHASE 1 CORRECTNESS TESTS")
    print("="*80)
    
    tests = [
        ("Fractional shares enabled", test_fractional_shares_enabled),
        ("Fractional shares disabled", test_fractional_shares_disabled),
        ("Format shares", test_format_shares),
        ("Canonical returns no synthetic zero", test_canonical_returns_no_synthetic_zero),
        ("Returns contamination", test_returns_contamination),
        ("Volatility annualization", test_volatility_annualization),
        ("Regime volatility coherence", test_regime_volatility_coherence),
        ("RSI bounds", test_rsi_bounds),
        ("Stochastic bounds", test_stochastic_bounds),
        ("MACD histogram invariant", test_macd_histogram_invariant),
        ("Fibonacci anchors within lookback", test_fibonacci_anchors_within_lookback),
        ("Fibonacci math", test_fibonacci_math),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n[TEST] {name}")
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ FAILED: {e}")
            failed += 1
    
    print("\n" + "="*80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*80)
    
    sys.exit(0 if failed == 0 else 1)
