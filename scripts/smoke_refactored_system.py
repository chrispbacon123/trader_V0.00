"""
Comprehensive Test Suite
Validates all refactored components
"""

import sys
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

def test_data_fetching():
    """Test canonical data fetcher"""
    print("\n" + "="*80)
    print("TEST 1: Data Fetching")
    print("="*80)
    
    from canonical_data import FETCHER
    
    # Test single symbol fetch
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    df, metadata = FETCHER.fetch_data('SPY', start_date, end_date)
    
    # Validate
    assert 'Price' in df.columns, "Missing Price column"
    assert metadata['symbol'] == 'SPY', "Wrong symbol in metadata"
    assert metadata['price_source'] in ['Adj Close', 'Close', 'Close (adjusted)'], "Invalid price source"
    assert len(df) > 200, f"Insufficient data: {len(df)} rows"
    assert (df['Price'] > 0).all(), "Negative prices detected"
    
    print(f"OK Fetched {len(df)} rows for SPY")
    print(f"OK Price source: {metadata['price_source']}")
    print(f"OK Date range: {metadata['actual_start']} to {metadata['actual_end']}")
    print(f"OK Current price: ${df['Price'].iloc[-1]:.2f}")
    
    # Test returns calculation
    returns = FETCHER.get_returns(df)
    assert len(returns) == len(df), "Returns length mismatch"
    assert returns.iloc[0] == 0.0, "First return should be 0"
    assert not np.isinf(returns).any(), "Infinite returns detected"
    
    print(f"OK Returns calculated: mean={returns.mean()*100:.4f}%, std={returns.std()*100:.4f}%")
    
    print("OK Data fetching tests PASSED\n")
    return True


def test_indicators():
    """Test validated indicators"""
    print("\n" + "="*80)
    print("TEST 2: Technical Indicators")
    print("="*80)
    
    from canonical_data import FETCHER
    from validated_indicators import ValidatedIndicators, compute_all_indicators
    
    # Get test data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    df, _ = FETCHER.fetch_data('SPY', start_date, end_date)
    
    # Test RSI
    rsi = ValidatedIndicators.rsi(df['Price'])
    assert (rsi.dropna() >= 0).all() and (rsi.dropna() <= 100).all(), "RSI out of range"
    print(f"OK RSI: current={rsi.iloc[-1]:.2f}, range=[{rsi.min():.2f}, {rsi.max():.2f}]")
    
    # Test Stochastic
    stoch_k, stoch_d = ValidatedIndicators.stochastic(df['High'], df['Low'], df['Close'])
    assert (stoch_k.dropna() >= 0).all() and (stoch_k.dropna() <= 100).all(), "Stoch %K out of range"
    assert (stoch_d.dropna() >= 0).all() and (stoch_d.dropna() <= 100).all(), "Stoch %D out of range"
    print(f"OK Stochastic: %K={stoch_k.iloc[-1]:.2f}, %D={stoch_d.iloc[-1]:.2f}")
    
    # Test MACD
    macd, signal, hist = ValidatedIndicators.macd(df['Price'])
    assert np.allclose(hist.dropna(), (macd - signal).dropna(), rtol=1e-6), "MACD histogram != MACD - Signal"
    print(f"OK MACD: line={macd.iloc[-1]:.2f}, signal={signal.iloc[-1]:.2f}, hist={hist.iloc[-1]:.2f}")
    
    # Test ADX
    adx, plus_di, minus_di = ValidatedIndicators.adx(df['High'], df['Low'], df['Close'])
    assert (adx.dropna() >= 0).all() and (adx.dropna() <= 100).all(), "ADX out of range"
    print(f"OK ADX: {adx.iloc[-1]:.2f}, +DI={plus_di.iloc[-1]:.2f}, -DI={minus_di.iloc[-1]:.2f}")
    
    # Test full computation
    df_with_ind = compute_all_indicators(df)
    required_indicators = ['RSI', 'MACD', 'ADX', 'Stoch_K', 'SMA_20', 'BB_Mid', 'ATR']
    for ind in required_indicators:
        assert ind in df_with_ind.columns, f"Missing indicator: {ind}"
    
    print(f"OK All {len(required_indicators)} indicators computed")
    print("OK Indicator tests PASSED\n")
    return True


def test_key_levels():
    """Test support/resistance and Fibonacci"""
    print("\n" + "="*80)
    print("TEST 3: Key Levels")
    print("="*80)
    
    from canonical_data import FETCHER
    from validated_indicators import compute_all_indicators
    from validated_levels import ValidatedKeyLevels
    
    # Get test data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    df, _ = FETCHER.fetch_data('SPY', start_date, end_date)
    df = compute_all_indicators(df)
    
    # Test support/resistance
    sr = ValidatedKeyLevels.support_resistance(df)
    current_price = sr['current_price']
    
    assert 'support' in sr and len(sr['support']) > 0, "No support levels found"
    assert 'resistance' in sr and len(sr['resistance']) > 0, "No resistance levels found"
    
    # Validate proximity
    for level in sr['support']:
        ratio = level / current_price
        assert 0.8 <= ratio <= 1.2, f"Support ${level:.2f} too far from current ${current_price:.2f}"
    
    for level in sr['resistance']:
        ratio = level / current_price
        assert 0.8 <= ratio <= 1.2, f"Resistance ${level:.2f} too far from current ${current_price:.2f}"
    
    print(f"OK Support/Resistance validated for price ${current_price:.2f}")
    print(f"  Support: {[f'${x:.2f}' for x in sr['support'][:3]]}")
    print(f"  Resistance: {[f'${x:.2f}' for x in sr['resistance'][:3]]}")
    
    # Test Fibonacci
    fib = ValidatedKeyLevels.fibonacci_retracements(df)
    assert 'anchor_high_price' in fib, "Missing Fibonacci anchors"
    assert fib['0.0%'] > fib['50.0%'] > fib['100.0%'], "Fibonacci levels not ordered"
    
    print(f"OK Fibonacci validated:")
    print(f"  High: ${fib['anchor_high_price']:.2f} on {fib['anchor_high_date'].date()}")
    print(f"  Low:  ${fib['anchor_low_price']:.2f} on {fib['anchor_low_date'].date()}")
    print(f"  50% level: ${fib['50.0%']:.2f}")
    
    print("OK Key levels tests PASSED\n")
    return True


def test_regime_classification():
    """Test market regime detection"""
    print("\n" + "="*80)
    print("TEST 4: Market Regime")
    print("="*80)
    
    from canonical_data import FETCHER
    from validated_indicators import compute_all_indicators
    from validated_regime import ValidatedRegime
    
    # Get test data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    df, _ = FETCHER.fetch_data('SPY', start_date, end_date)
    df = compute_all_indicators(df)
    
    # Test regime
    regime = ValidatedRegime.classify_regime(df)
    
    assert 'regime' in regime, "Missing regime classification"
    assert 'confidence' in regime, "Missing confidence"
    assert 0 <= regime['confidence'] <= 1, "Confidence out of range"
    assert 'rationale' in regime, "Missing rationale"
    assert 'metrics' in regime, "Missing metrics"
    
    # Validate ADX reconciliation
    assert 'adx' in regime['metrics'], "Missing ADX in regime metrics"
    assert 0 <= regime['metrics']['adx'] <= 100, "ADX out of range"
    
    print(f"OK Regime: {regime['regime'].upper()}")
    print(f"OK Confidence: {regime['confidence']*100:.1f}%")
    print(f"OK Rationale: {regime['rationale'][:100]}...")
    print(f"OK ADX: {regime['metrics']['adx']:.2f}")
    print(f"OK Volatility: {regime['metrics']['volatility_annualized_pct']:.2f}%")
    
    print("OK Regime classification tests PASSED\n")
    return True


def test_risk_metrics():
    """Test risk calculations"""
    print("\n" + "="*80)
    print("TEST 5: Risk Metrics")
    print("="*80)
    
    from canonical_data import FETCHER
    from validated_risk import ValidatedRiskMetrics
    
    # Get test data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    df, _ = FETCHER.fetch_data('SPY', start_date, end_date)
    returns = FETCHER.get_returns(df)
    
    # Test volatility
    vol = ValidatedRiskMetrics.volatility(returns)
    assert 'volatility_daily' in vol and 'volatility_annualized' in vol, "Missing volatility metrics"
    assert vol['volatility_annualized'] > vol['volatility_daily'], "Annualized should be > daily"
    assert vol['annualization_factor'] == np.sqrt(252), "Wrong annualization factor"
    
    print(f"OK Volatility: daily={vol['volatility_daily_pct']:.4f}%, annual={vol['volatility_annualized_pct']:.2f}%")
    
    # Test VaR
    var = ValidatedRiskMetrics.value_at_risk(returns)
    assert 'var' in var and var['var'] < 0, "VaR should be negative"
    assert var['confidence'] == 0.95, "Default confidence should be 95%"
    assert var['horizon_days'] == 1, "Default horizon should be 1 day"
    
    print(f"OK VaR: {var['var_pct']:.4f}% ({var['method']}, {var['confidence_pct']:.0f}%, {var['horizon_days']}-day)")
    
    # Test CVaR
    cvar = ValidatedRiskMetrics.conditional_var(returns)
    assert cvar['cvar'] <= var['var'], "CVaR should be <= VaR"
    
    print(f"OK CVaR: {cvar['cvar_pct']:.4f}%")
    
    # Test Sharpe
    sharpe = ValidatedRiskMetrics.sharpe_ratio(returns)
    assert 'sharpe_ratio' in sharpe, "Missing Sharpe ratio"
    assert sharpe['method'] == 'annualized', "Sharpe should be annualized"
    
    print(f"OK Sharpe: {sharpe['sharpe_ratio']:.4f} (annualized)")
    
    # Test Sortino
    sortino = ValidatedRiskMetrics.sortino_ratio(returns)
    assert sortino['method'] == 'annualized', "Sortino should be annualized"
    
    print(f"OK Sortino: {sortino['sortino_ratio']:.4f} (annualized)")
    
    # Test drawdown
    mdd = ValidatedRiskMetrics.max_drawdown_analysis(returns)
    assert mdd['max_drawdown'] <= 0, "Max drawdown should be negative"
    assert 'recovery_days' in mdd, "Missing recovery days"
    
    print(f"OK Max Drawdown: {mdd['max_drawdown_pct']:.2f}%, Recovery: {mdd['recovery_days']} days")
    
    print("OK Risk metrics tests PASSED\n")
    return True


def test_portfolio_allocation():
    """Test portfolio allocation with fractional shares"""
    print("\n" + "="*80)
    print("TEST 6: Portfolio Allocation")
    print("="*80)
    
    from validated_portfolio import ValidatedPortfolio
    
    # Test allocation
    portfolio = ValidatedPortfolio(equity=100000, fractional_allowed=True)
    
    target_weights = {
        'SPY': 0.40,
        'QQQ': 0.30,
        'IWM': 0.20,
        'TLT': 0.10
    }
    
    prices = {
        'SPY': 450.00,
        'QQQ': 380.00,
        'IWM': 190.00,
        'TLT': 95.00
    }
    
    summary = portfolio.allocate(target_weights, prices)
    
    assert 'total_invested' in summary, "Missing investment total"
    assert 'cash_remaining' in summary, "Missing cash"
    assert summary['num_positions'] == 4, "Should have 4 positions"
    
    # Validate weights sum close to 1
    total_weight = sum(pos['weight_pct'] for pos in summary['positions'].values()) / 100
    assert 0.95 <= total_weight <= 1.05, f"Weights sum to {total_weight}, should be ~1.0"
    
    print(f"OK Allocated ${summary['total_invested']:,.2f} across {summary['num_positions']} positions")
    print(f"OK Cash remaining: ${summary['cash_remaining']:,.2f}")
    print(f"OK Transaction costs: ${summary['transaction_costs']:,.2f}")
    
    # Test fractional vs integer shares
    portfolio_int = ValidatedPortfolio(equity=100000, fractional_allowed=False)
    summary_int = portfolio_int.allocate(target_weights, prices)
    
    assert summary_int['total_invested'] <= summary['total_invested'], "Integer should invest less"
    
    print(f"OK Fractional shares work correctly")
    
    print("OK Portfolio allocation tests PASSED\n")
    return True


def test_master_analyzer():
    """Test master integration"""
    print("\n" + "="*80)
    print("TEST 7: Master Analyzer Integration")
    print("="*80)
    
    from master_analyzer import TradingAnalyzer
    
    analyzer = TradingAnalyzer()
    
    # Test full analysis
    results = analyzer.quick_analysis('SPY', days=252, verbose=False)
    
    # Validate structure
    required_keys = ['symbol', 'metadata', 'data', 'returns', 'indicators', 'levels', 'regime', 'risk']
    for key in required_keys:
        assert key in results, f"Missing key: {key}"
    
    print(f"OK Full analysis completed for {results['symbol']}")
    print(f"OK Data points: {len(results['data'])}")
    print(f"OK Regime: {results['regime']['regime']}")
    print(f"OK Sharpe: {results['risk']['sharpe_ratio']['sharpe_ratio']:.4f}")
    
    # Test comparison
    comparison = analyzer.compare_symbols(['SPY', 'QQQ'], days=252, verbose=False)
    
    assert 'comparison_table' in comparison, "Missing comparison table"
    assert len(comparison['comparison_table']) == 2, "Should compare 2 symbols"
    
    print(f"OK Symbol comparison works")
    
    print("OK Master analyzer tests PASSED\n")
    return True


def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST SUITE")
    print("Validating End-to-End Refactored System")
    print("="*80)
    
    tests = [
        ("Data Fetching", test_data_fetching),
        ("Indicators", test_indicators),
        ("Key Levels", test_key_levels),
        ("Regime Classification", test_regime_classification),
        ("Risk Metrics", test_risk_metrics),
        ("Portfolio Allocation", test_portfolio_allocation),
        ("Master Analyzer", test_master_analyzer)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\nX TEST FAILED: {name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print("TEST SUITE SUMMARY")
    print("="*80)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed:      {passed}")
    print(f"Failed:      {failed}")
    
    if failed == 0:
        print("\nALL TESTS PASSED! System is validated and ready to use.")
        return 0
    else:
        print(f"\n{failed} test(s) failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
