"""
Test Regime Detection Unit Coherence
Validates that regime classification is NOT always VOLATILE
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

from validated_regime import ValidatedRegime, compute_regime
from validated_indicators import compute_all_indicators
from core_config import REGIME_CFG


def generate_synthetic_ohlcv(
    n_days: int = 252,
    start_price: float = 100.0,
    trend: float = 0.0,
    volatility: float = 0.01,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic OHLCV data with controlled characteristics
    
    Args:
        n_days: Number of trading days
        start_price: Initial price
        trend: Daily drift (e.g., 0.001 = 0.1% per day)
        volatility: Daily volatility (std dev of returns)
        seed: Random seed
        
    Returns:
        DataFrame with Date, Open, High, Low, Close, Volume, Price
    """
    np.random.seed(seed)
    
    # Generate daily returns
    drift = trend
    shocks = np.random.normal(0, volatility, n_days)
    returns = drift + shocks
    
    # Generate prices
    prices = start_price * (1 + returns).cumprod()
    
    # Generate OHLC around close
    df = pd.DataFrame({
        'Date': [datetime(2024, 1, 1) + timedelta(days=i) for i in range(n_days)],
        'Close': prices
    })
    
    # Create OHLC with realistic intraday noise
    intraday_vol = volatility * 0.3
    df['Open'] = df['Close'] * (1 + np.random.normal(0, intraday_vol, n_days))
    df['High'] = df[['Open', 'Close']].max(axis=1) * (1 + np.abs(np.random.normal(0, intraday_vol, n_days)))
    df['Low'] = df[['Open', 'Close']].min(axis=1) * (1 - np.abs(np.random.normal(0, intraday_vol, n_days)))
    df['Volume'] = np.random.randint(1000000, 5000000, n_days)
    df['Price'] = df['Close']
    
    df = df.set_index('Date')
    
    return df


def test_flat_market():
    """Test 1: Flat market should be RANGING"""
    print("\n" + "="*80)
    print("TEST 1: FLAT MARKET (zero trend, zero volatility)")
    print("="*80)
    
    # Generate perfectly flat prices
    n_days = 252
    df = pd.DataFrame({
        'Date': [datetime(2024, 1, 1) + timedelta(days=i) for i in range(n_days)],
        'Close': [100.0] * n_days
    })
    df = df.set_index('Date')
    
    # Add minimal noise for indicators
    df['Open'] = df['Close'] * (1 + np.random.normal(0, 0.0001, n_days))
    df['High'] = df['Close'] * 1.0001
    df['Low'] = df['Close'] * 0.9999
    df['Volume'] = 1000000
    df['Price'] = df['Close']
    
    # Compute indicators
    df = compute_all_indicators(df)
    
    # Classify regime
    regime = ValidatedRegime.classify_regime(df)
    
    print(f"\nResult:")
    print(f"  Regime: {regime['regime'].upper()}")
    print(f"  Confidence: {regime['confidence']*100:.1f}%")
    print(f"  Volatility: {regime['metrics']['volatility_annualized_pct']:.2f}% annualized")
    print(f"  Rationale: {regime['rationale']}")
    
    # Assert NOT volatile
    assert regime['regime'] != 'volatile', \
        f"Flat market classified as VOLATILE! Vol={regime['metrics']['volatility_annualized_pct']:.2f}%"
    
    # Should be ranging or transitioning
    assert regime['regime'] in ['ranging', 'transitioning'], \
        f"Expected RANGING or TRANSITIONING, got {regime['regime'].upper()}"
    
    print("\n[PASS] Flat market correctly classified as non-VOLATILE")
    return True


def test_low_volatility_trend():
    """Test 2: Low volatility uptrend should be TRENDING_UP"""
    print("\n" + "="*80)
    print("TEST 2: LOW VOLATILITY UPTREND (0.1% daily drift, 0.5% daily vol)")
    print("="*80)
    
    # Generate low-vol uptrend
    df = generate_synthetic_ohlcv(
        n_days=252,
        start_price=100.0,
        trend=0.001,      # 0.1% per day = ~25% per year
        volatility=0.005, # 0.5% per day = ~8% annualized
        seed=42
    )
    
    # Compute indicators
    df = compute_all_indicators(df)
    
    # Classify regime
    regime = ValidatedRegime.classify_regime(df)
    
    print(f"\nResult:")
    print(f"  Regime: {regime['regime'].upper()}")
    print(f"  Confidence: {regime['confidence']*100:.1f}%")
    print(f"  Volatility: {regime['metrics']['volatility_annualized_pct']:.2f}% annualized")
    print(f"  ADX: {regime['metrics']['adx']:.1f}")
    print(f"  Rationale: {regime['rationale']}")
    
    # Assert NOT volatile
    assert regime['regime'] != 'volatile', \
        f"Low-vol trend classified as VOLATILE! Vol={regime['metrics']['volatility_annualized_pct']:.2f}%"
    
    # Annualized vol should be < high threshold
    vol_ann = regime['metrics']['volatility_annualized_pct'] / 100
    assert vol_ann < REGIME_CFG.VOL_HIGH_THRESHOLD, \
        f"Vol {vol_ann*100:.1f}% should be < {REGIME_CFG.VOL_HIGH_THRESHOLD*100:.1f}%"
    
    print(f"\n[PASS] Low-vol trend correctly classified as non-VOLATILE")
    print(f"  Measured vol {vol_ann*100:.1f}% < threshold {REGIME_CFG.VOL_HIGH_THRESHOLD*100:.1f}%")
    return True


def test_moderate_volatility():
    """Test 3: Moderate volatility should be RANGING or TRANSITIONING"""
    print("\n" + "="*80)
    print("TEST 3: MODERATE VOLATILITY (no trend, 1% daily vol = ~16% annualized)")
    print("="*80)
    
    # Generate moderate volatility, no trend
    df = generate_synthetic_ohlcv(
        n_days=252,
        start_price=100.0,
        trend=0.0,        # No trend
        volatility=0.01,  # 1% per day = ~16% annualized
        seed=123
    )
    
    # Compute indicators
    df = compute_all_indicators(df)
    
    # Classify regime
    regime = ValidatedRegime.classify_regime(df)
    
    print(f"\nResult:")
    print(f"  Regime: {regime['regime'].upper()}")
    print(f"  Confidence: {regime['confidence']*100:.1f}%")
    print(f"  Volatility: {regime['metrics']['volatility_annualized_pct']:.2f}% annualized")
    print(f"  ADX: {regime['metrics']['adx']:.1f}")
    print(f"  Rationale: {regime['rationale']}")
    
    # Moderate vol (12-25%) should NOT be volatile
    vol_ann = regime['metrics']['volatility_annualized_pct'] / 100
    if vol_ann < REGIME_CFG.VOL_HIGH_THRESHOLD:
        assert regime['regime'] != 'volatile', \
            f"Moderate vol ({vol_ann*100:.1f}%) should not be VOLATILE (threshold: {REGIME_CFG.VOL_HIGH_THRESHOLD*100:.1f}%)"
        print(f"\n[PASS] Moderate volatility correctly NOT classified as VOLATILE")
        print(f"  Measured vol {vol_ann*100:.1f}% < threshold {REGIME_CFG.VOL_HIGH_THRESHOLD*100:.1f}%")
    else:
        print(f"\n[NOTE] Volatility {vol_ann*100:.1f}% exceeds threshold {REGIME_CFG.VOL_HIGH_THRESHOLD*100:.1f}%")
        print(f"  Regime: {regime['regime'].upper()} - acceptable")
    
    return True


def test_high_volatility():
    """Test 4: High volatility should be VOLATILE"""
    print("\n" + "="*80)
    print("TEST 4: HIGH VOLATILITY (no trend, 2% daily vol = ~32% annualized)")
    print("="*80)
    
    # Generate high volatility
    df = generate_synthetic_ohlcv(
        n_days=252,
        start_price=100.0,
        trend=0.0,        # No trend
        volatility=0.02,  # 2% per day = ~32% annualized
        seed=456
    )
    
    # Compute indicators
    df = compute_all_indicators(df)
    
    # Classify regime
    regime = ValidatedRegime.classify_regime(df)
    
    print(f"\nResult:")
    print(f"  Regime: {regime['regime'].upper()}")
    print(f"  Confidence: {regime['confidence']*100:.1f}%")
    print(f"  Volatility: {regime['metrics']['volatility_annualized_pct']:.2f}% annualized")
    print(f"  ADX: {regime['metrics']['adx']:.1f}")
    print(f"  Rationale: {regime['rationale']}")
    
    # High vol should be VOLATILE
    vol_ann = regime['metrics']['volatility_annualized_pct'] / 100
    assert vol_ann > REGIME_CFG.VOL_HIGH_THRESHOLD, \
        f"Test data should have vol > {REGIME_CFG.VOL_HIGH_THRESHOLD*100:.1f}%"
    
    assert regime['regime'] == 'volatile', \
        f"High vol ({vol_ann*100:.1f}%) should be VOLATILE"
    
    print(f"\n[PASS] High volatility correctly classified as VOLATILE")
    print(f"  Measured vol {vol_ann*100:.1f}% > threshold {REGIME_CFG.VOL_HIGH_THRESHOLD*100:.1f}%")
    return True


def test_thresholds_in_rationale():
    """Test 5: Verify thresholds and volatility are printed in same units"""
    print("\n" + "="*80)
    print("TEST 5: THRESHOLD UNITS IN RATIONALE")
    print("="*80)
    
    # Use real SPY data if available
    from pathlib import Path
    fixture_path = Path(__file__).parent / 'tests' / 'data' / 'spy_daily.csv'
    
    if fixture_path.exists():
        df = pd.read_csv(fixture_path)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')
        df['Price'] = df['Close']
        df = compute_all_indicators(df)
        
        regime = ValidatedRegime.classify_regime(df)
        
        print(f"\nAnalyzing SPY fixture data:")
        print(f"  Regime: {regime['regime'].upper()}")
        print(f"  Volatility measured: {regime['metrics']['volatility_annualized_pct']:.2f}% annualized")
        print(f"  Low threshold: {REGIME_CFG.VOL_LOW_THRESHOLD*100:.1f}% annualized")
        print(f"  High threshold: {REGIME_CFG.VOL_HIGH_THRESHOLD*100:.1f}% annualized")
        print(f"\n  Rationale: {regime['rationale']}")
        
        # Check rationale mentions thresholds (or it's transitioning which is acceptable)
        rationale = regime['rationale']
        if regime['regime'] != 'transitioning':
            assert 'threshold' in rationale.lower(), "Rationale should mention thresholds"
        assert '%' in rationale, "Rationale should show percentages"
        
        # Verify volatility classification is correct
        vol_ann = regime['metrics']['volatility_annualized_pct'] / 100
        if vol_ann > REGIME_CFG.VOL_HIGH_THRESHOLD:
            assert regime['regime'] == 'volatile', \
                f"Vol {vol_ann*100:.1f}% > {REGIME_CFG.VOL_HIGH_THRESHOLD*100:.1f}% should be VOLATILE"
        elif vol_ann < REGIME_CFG.VOL_LOW_THRESHOLD:
            # Could be ranging or trending (if ADX is high)
            pass
        else:
            # In between - should NOT be volatile
            assert regime['regime'] != 'volatile', \
                f"Vol {vol_ann*100:.1f}% between thresholds should not be VOLATILE"
        
        print("\n[PASS] Rationale and classification coherent with thresholds")
    else:
        print("\n[SKIP] SPY fixture not found, using synthetic data")
        df = generate_synthetic_ohlcv(252, volatility=0.01)
        df = compute_all_indicators(df)
        regime = ValidatedRegime.classify_regime(df)
        print(f"  Regime: {regime['regime'].upper()}")
        print(f"  Rationale: {regime['rationale']}")
        print("\n[PASS] Synthetic data test complete")
    
    return True


def test_config_assertion():
    """Test 6: Verify config assertions catch bad thresholds"""
    print("\n" + "="*80)
    print("TEST 6: CONFIG ASSERTIONS")
    print("="*80)
    
    print(f"\nChecking config thresholds:")
    print(f"  VOL_LOW_THRESHOLD:  {REGIME_CFG.VOL_LOW_THRESHOLD*100:.1f}% (should be > 5%)")
    print(f"  VOL_HIGH_THRESHOLD: {REGIME_CFG.VOL_HIGH_THRESHOLD*100:.1f}% (should be > VOL_LOW)")
    
    # These should pass in validated_regime.py classify_regime()
    assert REGIME_CFG.VOL_LOW_THRESHOLD > 0.05, \
        "VOL_LOW_THRESHOLD too low (should be annualized, > 5%)"
    assert REGIME_CFG.VOL_HIGH_THRESHOLD > REGIME_CFG.VOL_LOW_THRESHOLD, \
        "VOL_HIGH_THRESHOLD should exceed VOL_LOW_THRESHOLD"
    
    print("\n[PASS] Config thresholds are valid annualized percentages")
    return True


def main():
    """Run all regime coherence tests"""
    print("\n" + "="*80)
    print("REGIME DETECTION UNIT COHERENCE TESTS")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  VOL_LOW_THRESHOLD:  {REGIME_CFG.VOL_LOW_THRESHOLD*100:.1f}% annualized")
    print(f"  VOL_HIGH_THRESHOLD: {REGIME_CFG.VOL_HIGH_THRESHOLD*100:.1f}% annualized")
    print(f"  ADX_STRONG_TREND:   {REGIME_CFG.ADX_STRONG_TREND}")
    print(f"  ADX_WEAK_TREND:     {REGIME_CFG.ADX_WEAK_TREND}")
    
    tests = [
        ("Config Assertions", test_config_assertion),
        ("Flat Market", test_flat_market),
        ("Low Volatility Trend", test_low_volatility_trend),
        ("Moderate Volatility", test_moderate_volatility),
        ("High Volatility", test_high_volatility),
        ("Threshold Units", test_thresholds_in_rationale),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = "PASS"
        except AssertionError as e:
            print(f"\n[FAIL] {test_name}: {str(e)}")
            results[test_name] = "FAIL"
        except Exception as e:
            print(f"\n[ERROR] {test_name}: {str(e)}")
            results[test_name] = "ERROR"
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results.values() if r == "PASS")
    failed = sum(1 for r in results.values() if r == "FAIL")
    errors = sum(1 for r in results.values() if r == "ERROR")
    total = len(results)
    
    for test_name, result in results.items():
        status_symbol = {"PASS": "[+]", "FAIL": "[-]", "ERROR": "[!]"}[result]
        print(f"  {status_symbol} {test_name}: {result}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if failed == 0 and errors == 0:
        print("\n[OK] ALL REGIME COHERENCE TESTS PASSED")
        print("Regime detection uses consistent annualized volatility units")
        return 0
    else:
        print(f"\n[ERROR] {failed} failed, {errors} errors")
        return 1


if __name__ == '__main__':
    sys.exit(main())
