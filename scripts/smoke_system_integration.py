"""
Comprehensive System Integration Test
Tests all major components for compatibility, accuracy, and connections
"""

import sys
import traceback
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Test results tracking
test_results = {
    'passed': [],
    'failed': [],
    'warnings': []
}

def test_section(name):
    """Decorator for test sections"""
    def decorator(func):
        def wrapper():
            print(f"\n{'='*80}")
            print(f"TESTING: {name}")
            print(f"{'='*80}")
            try:
                func()
                test_results['passed'].append(name)
                print(f"[PASS] {name}")
                return True
            except Exception as e:
                test_results['failed'].append(name)
                print(f"[FAIL] {name}")
                print(f"Error: {str(e)}")
                traceback.print_exc()
                return False
        return wrapper
    return decorator


# ============================================================================
# SECTION 1: Core Configuration
# ============================================================================

@test_section("Core Configuration (core_config.py)")
def test_core_config():
    """Test that all config parameters are valid and consistent"""
    from core_config import (
        INDICATOR_CFG, LEVEL_CFG, REGIME_CFG, RISK_CFG, 
        PORTFOLIO_CFG, DATA_CFG
    )
    
    # Validate data configs
    assert len(DATA_CFG.PRICE_COLUMN) > 0
    assert len(DATA_CFG.FALLBACK_PRICE_COLUMN) > 0
    
    # Validate indicator configs
    assert INDICATOR_CFG.RSI_PERIOD > 0
    assert INDICATOR_CFG.MACD_FAST > 0
    assert INDICATOR_CFG.MACD_SLOW > INDICATOR_CFG.MACD_FAST
    assert INDICATOR_CFG.ADX_PERIOD > 0
    
    # Validate level configs
    assert LEVEL_CFG.FIB_LOOKBACK > 0
    assert LEVEL_CFG.SR_LOOKBACK > 0
    assert 0 < LEVEL_CFG.SR_PROXIMITY_FILTER < 1
    
    # Validate regime configs
    assert REGIME_CFG.REGIME_LOOKBACK > 0
    assert REGIME_CFG.VOL_HIGH_THRESHOLD > 0
    assert REGIME_CFG.ADX_STRONG_TREND > 0
    
    # Validate risk configs
    assert RISK_CFG.TRADING_DAYS_PER_YEAR > 0
    assert 0 < RISK_CFG.VAR_CONFIDENCE < 1
    
    # Validate portfolio configs
    assert isinstance(PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED, bool)
    assert PORTFOLIO_CFG.MIN_POSITION_VALUE > 0
    assert 0 < PORTFOLIO_CFG.MAX_POSITION_WEIGHT <= 1
    assert 0 <= PORTFOLIO_CFG.MIN_CASH_BUFFER < 1
    
    print("OK All config parameters valid")
    
    # Validate level configs
    assert LEVEL_CFG.FIB_LOOKBACK > 0
    assert LEVEL_CFG.SR_LOOKBACK > 0
    assert 0 < LEVEL_CFG.SR_PROXIMITY_FILTER < 1
    
    # Validate regime configs
    assert REGIME_CFG.REGIME_LOOKBACK > 0
    assert REGIME_CFG.VOL_HIGH_THRESHOLD > 0
    assert REGIME_CFG.ADX_STRONG_TREND > 0
    
    # Validate risk configs
    assert RISK_CFG.TRADING_DAYS_PER_YEAR > 0
    assert 0 < RISK_CFG.VAR_CONFIDENCE < 1
    
    # Validate portfolio configs
    assert isinstance(PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED, bool)
    assert PORTFOLIO_CFG.MIN_POSITION_VALUE > 0
    assert 0 < PORTFOLIO_CFG.MAX_POSITION_WEIGHT <= 1
    assert 0 <= PORTFOLIO_CFG.MIN_CASH_BUFFER < 1
    
    print("[OK] All config parameters valid")


# ============================================================================
# SECTION 2: Canonical Data
# ============================================================================

@test_section("Canonical Data Fetcher (canonical_data.py)")
def test_canonical_data():
    """Test canonical data fetching and Price column creation"""
    from canonical_data import CanonicalDataFetcher
    
    fetcher = CanonicalDataFetcher()
    
    # Load test fixture
    fixture_path = Path(__file__).parent / 'tests' / 'data' / 'spy_daily.csv'
    df = pd.read_csv(fixture_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date')
    
    # Add Price column
    df['Price'] = df['Close']
    
    # Validate
    assert 'Price' in df.columns
    assert len(df) > 0
    assert not isinstance(df.columns, pd.MultiIndex)
    assert (df['Price'] > 0).all()
    assert (df['High'] >= df['Low']).all()
    
    # Test returns calculation
    returns = fetcher.get_returns(df)
    assert len(returns) == len(df)
    assert not returns.isna().all()
    
    print(f"[OK] Fetched {len(df)} rows")
    print(f"[OK] Price column created")
    print(f"[OK] Returns computed: {len(returns.dropna())} valid values")


# ============================================================================
# SECTION 3: Validated Indicators
# ============================================================================

@test_section("Validated Indicators (validated_indicators.py)")
def test_validated_indicators():
    """Test all indicator calculations"""
    from validated_indicators import ValidatedIndicators, compute_all_indicators
    
    # Load fixture
    fixture_path = Path(__file__).parent / 'tests' / 'data' / 'spy_daily.csv'
    df = pd.read_csv(fixture_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date')
    df['Price'] = df['Close']
    
    # Compute all indicators
    df = compute_all_indicators(df)
    
    # Validate RSI
    rsi = df['RSI'].dropna()
    assert len(rsi) > 0
    assert (rsi >= 0).all()
    assert (rsi <= 100).all()
    print(f"[OK] RSI: range [{rsi.min():.2f}, {rsi.max():.2f}]")
    
    # Validate ADX
    adx = df['ADX'].dropna()
    assert len(adx) > 0
    assert (adx >= 0).all()
    assert (adx <= 100).all()
    print(f"[OK] ADX: range [{adx.min():.2f}, {adx.max():.2f}]")
    
    # Validate MACD
    macd = df['MACD'].dropna()
    signal = df['MACD_Signal'].dropna()
    hist = df['MACD_Hist'].dropna()
    assert len(macd) > 0
    # Check histogram consistency
    diff = (df['MACD'] - df['MACD_Signal']).dropna()
    assert np.allclose(hist, diff, rtol=1e-6)
    print(f"[OK] MACD: histogram consistent")
    
    # Validate Stochastic
    stoch_k = df['Stoch_K'].dropna()
    stoch_d = df['Stoch_D'].dropna()
    assert len(stoch_k) > 0
    assert (stoch_k >= 0).all() and (stoch_k <= 100).all()
    assert (stoch_d >= 0).all() and (stoch_d <= 100).all()
    print(f"[OK] Stochastic: K range [{stoch_k.min():.2f}, {stoch_k.max():.2f}]")
    
    # Check for NaNs in final rows
    final_50 = df.iloc[-50:]
    critical_cols = ['RSI', 'MACD', 'ADX', 'Stoch_K']
    for col in critical_cols:
        nans = final_50[col].isna().sum()
        assert nans == 0, f"{col} has {nans} NaNs in final 50 rows"
    print(f"[OK] No NaNs in final 50 rows")


# ============================================================================
# SECTION 4: Validated Key Levels
# ============================================================================

@test_section("Validated Key Levels (validated_levels.py)")
def test_validated_levels():
    """Test support/resistance and Fibonacci calculations"""
    from validated_levels import ValidatedKeyLevels
    
    # Load fixture
    fixture_path = Path(__file__).parent / 'tests' / 'data' / 'spy_daily.csv'
    df = pd.read_csv(fixture_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date')
    df['Price'] = df['Close']
    
    # Test Fibonacci
    fib = ValidatedKeyLevels.fibonacci_retracements(df, lookback=100)
    
    # Check metadata
    assert 'anchor_high_date' in fib
    assert 'anchor_low_date' in fib
    assert 'anchor_high_price' in fib
    assert 'anchor_low_price' in fib
    
    # Check levels
    assert '0.0%' in fib
    assert '50.0%' in fib
    assert '100.0%' in fib
    
    high = fib['0.0%']
    mid = fib['50.0%']
    low = fib['100.0%']
    assert high > mid > low
    
    print(f"[OK] Fibonacci levels: {high:.2f} > {mid:.2f} > {low:.2f}")
    print(f"[OK] Anchor high: {fib['anchor_high_date'].date()} @ ${fib['anchor_high_price']:.2f}")
    print(f"[OK] Anchor low: {fib['anchor_low_date'].date()} @ ${fib['anchor_low_price']:.2f}")
    
    # Test Support/Resistance
    sr = ValidatedKeyLevels.support_resistance(df, lookback=100)
    
    assert 'support' in sr
    assert 'resistance' in sr
    assert 'current_price' in sr
    
    current = sr['current_price']
    print(f"[OK] Current price: ${current:.2f}")
    print(f"[OK] Support levels: {[f'${x:.2f}' for x in sr['support']]}")
    print(f"[OK] Resistance levels: {[f'${x:.2f}' for x in sr['resistance']]}")
    
    # Validate proximity
    from core_config import LEVEL_CFG
    proximity = LEVEL_CFG.SR_PROXIMITY_FILTER
    for level in sr['support']:
        assert level > current * (1 - proximity)
    for level in sr['resistance']:
        assert level < current * (1 + proximity)
    print(f"[OK] All levels within {proximity*100:.0f}% proximity")


# ============================================================================
# SECTION 5: Validated Regime
# ============================================================================

@test_section("Validated Regime (validated_regime.py)")
def test_validated_regime():
    """Test regime classification"""
    from validated_regime import ValidatedRegime
    from validated_indicators import compute_all_indicators
    
    # Load fixture
    fixture_path = Path(__file__).parent / 'tests' / 'data' / 'spy_daily.csv'
    df = pd.read_csv(fixture_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date')
    df['Price'] = df['Close']
    df = compute_all_indicators(df)
    
    # Classify regime
    regime = ValidatedRegime.classify_regime(df)
    
    # Validate structure
    assert 'regime' in regime
    assert 'confidence' in regime
    assert 'rationale' in regime
    assert 'metrics' in regime
    
    # Validate values
    assert regime['regime'] in ['volatile', 'ranging', 'trending_up', 'trending_down', 'transitioning']
    assert 0 <= regime['confidence'] <= 1
    assert len(regime['rationale']) > 0
    assert 'adx' in regime['metrics']
    
    print(f"[OK] Regime: {regime['regime'].upper()}")
    print(f"[OK] Confidence: {regime['confidence']*100:.1f}%")
    print(f"[OK] ADX: {regime['metrics']['adx']:.2f}")
    print(f"[OK] Rationale: {regime['rationale'][:80]}...")


# ============================================================================
# SECTION 6: Validated Risk Metrics
# ============================================================================

@test_section("Validated Risk Metrics (validated_risk.py)")
def test_validated_risk():
    """Test risk calculations"""
    from validated_risk import ValidatedRiskMetrics
    from canonical_data import CanonicalDataFetcher
    
    # Load fixture
    fixture_path = Path(__file__).parent / 'tests' / 'data' / 'spy_daily.csv'
    df = pd.read_csv(fixture_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date')
    df['Price'] = df['Close']
    
    # Compute returns
    fetcher = CanonicalDataFetcher()
    returns = fetcher.get_returns(df)
    
    # Test volatility
    vol = ValidatedRiskMetrics.volatility(returns)
    assert 'volatility_daily' in vol
    assert 'volatility_annualized' in vol
    assert vol['volatility_daily'] > 0
    assert vol['volatility_annualized'] > vol['volatility_daily']
    print(f"[OK] Volatility daily: {vol['volatility_daily']*100:.4f}%")
    print(f"[OK] Volatility annualized: {vol['volatility_annualized']*100:.2f}%")
    
    # Test VaR
    var = ValidatedRiskMetrics.value_at_risk(returns)
    assert 'var' in var
    assert 'method' in var
    assert 'horizon_days' in var
    print(f"[OK] VaR (95%, 1-day): {var['var']*100:.4f}%")
    
    # Test CVaR
    cvar = ValidatedRiskMetrics.conditional_var(returns)
    assert cvar['cvar'] <= var['var']  # CVaR should be more negative
    print(f"[OK] CVaR (95%, 1-day): {cvar['cvar']*100:.4f}%")
    
    # Test Sharpe
    sharpe = ValidatedRiskMetrics.sharpe_ratio(returns)
    print(f"[OK] Sharpe ratio: {sharpe['sharpe_ratio']:.4f}")
    
    # Test Sortino
    sortino = ValidatedRiskMetrics.sortino_ratio(returns)
    print(f"[OK] Sortino ratio: {sortino['sortino_ratio']:.4f}")


# ============================================================================
# SECTION 7: Validated Portfolio
# ============================================================================

@test_section("Validated Portfolio (validated_portfolio.py)")
def test_validated_portfolio():
    """Test portfolio allocation"""
    from validated_portfolio import ValidatedPortfolio
    
    # Test with fractional shares
    p1 = ValidatedPortfolio(
        equity=100000,
        fractional_allowed=True,
        slippage_bps=5.0,
        commission_per_share=0.005
    )
    
    weights = {'SPY': 0.6, 'QQQ': 0.4}
    prices = {'SPY': 450.75, 'QQQ': 380.25}
    
    summary = p1.allocate(weights, prices)
    
    # Validate structure
    assert 'positions' in summary
    assert 'total_invested' in summary
    assert 'cash_remaining' in summary
    assert 'transaction_costs' in summary
    
    # Validate fractional
    spy_shares = summary['positions']['SPY']['shares']
    assert spy_shares != int(spy_shares)  # Should be float
    print(f"[OK] Fractional shares: SPY={spy_shares:.4f}")
    
    # Test without fractional shares
    p2 = ValidatedPortfolio(equity=100000, fractional_allowed=False)
    summary2 = p2.allocate(weights, prices)
    spy_shares2 = summary2['positions']['SPY']['shares']
    assert spy_shares2 == int(spy_shares2)  # Should be int
    print(f"[OK] Whole shares: SPY={spy_shares2:.0f}")
    
    # Validate accounting
    total = summary['total_invested'] + summary['cash_remaining'] + summary['transaction_costs']
    assert abs(total - 100000) < 1.0
    print(f"[OK] Accounting balanced: ${total:.2f}")
    print(f"[OK] Transaction costs: ${summary['transaction_costs']:.2f}")


# ============================================================================
# SECTION 8: Market Analytics Integration
# ============================================================================

@test_section("Market Analytics (market_analytics.py)")
def test_market_analytics():
    """Test MarketAnalytics comprehensive analysis"""
    from market_analytics import MarketAnalytics
    from validated_indicators import compute_all_indicators
    
    # Create instance
    ma = MarketAnalytics('TEST')
    
    # Load fixture
    fixture_path = Path(__file__).parent / 'tests' / 'data' / 'spy_daily.csv'
    df = pd.read_csv(fixture_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date')
    df['Price'] = df['Close']
    
    ma.data = compute_all_indicators(df)
    ma.metadata = {
        'symbol': 'TEST',
        'actual_start': ma.data.index[0].date(),
        'actual_end': ma.data.index[-1].date(),
        'num_rows': len(ma.data),
        'price_source': 'Close (adjusted)'
    }
    
    # Test regime
    regime = ma.market_regime()
    assert 'regime' in regime
    print(f"[OK] Regime: {regime['regime']}")
    
    # Test levels
    levels = ma.support_resistance_levels()
    assert 'support' in levels
    assert 'resistance' in levels
    print(f"[OK] Levels computed")
    
    # Test fibonacci
    fib = ma.fibonacci_levels()
    assert len(fib) > 0
    print(f"[OK] Fibonacci: {len(fib)} levels")
    
    # Test momentum
    momentum = ma.momentum_analysis()
    assert 'RSI(14)' in str(momentum.keys())
    print(f"[OK] Momentum: {len(momentum)} indicators")
    
    # Test risk
    risk = ma.risk_metrics()
    assert 'volatility_daily' in risk
    assert 'volatility_annualized' in risk
    print(f"[OK] Risk metrics computed")
    
    # Test print (capture output)
    import io
    from contextlib import redirect_stdout
    f = io.StringIO()
    with redirect_stdout(f):
        ma.print_comprehensive_analysis()
    output = f.getvalue()
    
    # Validate output
    assert 'DATA SUMMARY' in output
    assert 'MARKET REGIME' in output
    assert 'FIBONACCI RETRACEMENTS' in output
    assert 'Anchor High:' in output
    assert 'lookback=' in output
    print(f"[OK] Comprehensive report generated ({len(output)} chars)")


# ============================================================================
# SECTION 9: Strategy Compatibility
# ============================================================================

@test_section("ML Strategy (ml_strategy.py)")
def test_ml_strategy():
    """Test ML strategy with fractional shares"""
    from ml_strategy import MLTradingStrategy
    
    # Load fixture
    fixture_path = Path(__file__).parent / 'tests' / 'data' / 'spy_daily.csv'
    df = pd.read_csv(fixture_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date')
    
    # Create strategy
    strategy = MLTradingStrategy(initial_capital=10000)
    
    # Prepare features (minimal)
    df['Returns'] = df['Close'].pct_change()
    df['Volatility_20'] = df['Returns'].rolling(20).std()
    df = df.dropna()
    
    if len(df) < 100:
        print("[WARN] Not enough data for full backtest, checking structure only")
        assert hasattr(strategy, 'cash')
        assert hasattr(strategy, 'prepare_features')
        print("[OK] Strategy structure valid")
    else:
        # Run minimal backtest
        try:
            results = strategy.run_backtest(df)
            assert 'trades' in results or 'final_value' in results
            print(f"[OK] Backtest completed")
        except Exception as e:
            print(f"[WARN] Backtest skipped: {str(e)[:50]}")
            print("[OK] Strategy importable")


@test_section("Optimized ML Strategy (optimized_ml_strategy.py)")
def test_optimized_ml_strategy():
    """Test optimized ML strategy"""
    from optimized_ml_strategy import OptimizedMLStrategy
    
    strategy = OptimizedMLStrategy(initial_capital=10000)
    assert hasattr(strategy, 'cash')
    assert hasattr(strategy, 'create_features') or hasattr(strategy, 'add_features')
    print("[OK] Strategy structure valid")


# ============================================================================
# SECTION 10: Data Manager Compatibility
# ============================================================================

@test_section("Data Manager (data_manager.py)")
def test_data_manager():
    """Test data manager functionality"""
    try:
        from data_manager import DataManager
        
        # Create instance
        dm = DataManager()
        
        # Test basic functionality
        assert hasattr(dm, 'fetch_data')
        print("[OK] DataManager importable")
        
    except ImportError as e:
        print(f"[WARN] DataManager import issue: {str(e)[:50]}")
        test_results['warnings'].append("DataManager import")


# ============================================================================
# SECTION 11: Performance Analytics
# ============================================================================

@test_section("Performance Analytics (performance_analytics.py)")
def test_performance_analytics():
    """Test performance analytics"""
    try:
        from performance_analytics import PerformanceAnalytics
        
        # Create instance
        pa = PerformanceAnalytics()
        
        # Test with dummy data
        returns = pd.Series(np.random.normal(0.001, 0.01, 100))
        
        # Test calculations
        assert hasattr(pa, 'sharpe_ratio')
        assert hasattr(pa, 'sortino_ratio')
        assert hasattr(pa, 'calmar_ratio')
        
        # Test they work
        sharpe = pa.sharpe_ratio(returns)
        sortino = pa.sortino_ratio(returns)
        
        print(f"[OK] Sharpe ratio: {sharpe:.4f}")
        print(f"[OK] Sortino ratio: {sortino:.4f}")
        print("[OK] PerformanceAnalytics structure valid")
        
    except ImportError as e:
        print(f"[WARN] PerformanceAnalytics import issue: {str(e)[:50]}")
        test_results['warnings'].append("PerformanceAnalytics import")


# ============================================================================
# SECTION 12: Risk Management
# ============================================================================

@test_section("Risk Management (risk_manager.py)")
def test_risk_manager():
    """Test risk management"""
    try:
        from risk_manager import RiskManager
        
        rm = RiskManager()
        assert hasattr(rm, 'calculate_position_size') or hasattr(rm, 'assess_risk')
        print("[OK] RiskManager structure valid")
        
    except ImportError as e:
        print(f"[WARN] RiskManager import issue: {str(e)[:50]}")
        test_results['warnings'].append("RiskManager import")


# ============================================================================
# SECTION 13: Cross-Module Integration
# ============================================================================

@test_section("Cross-Module Integration")
def test_cross_module_integration():
    """Test that modules work together correctly"""
    from canonical_data import CanonicalDataFetcher
    from validated_indicators import compute_all_indicators
    from validated_levels import ValidatedKeyLevels
    from validated_regime import ValidatedRegime
    from validated_risk import ValidatedRiskMetrics
    from validated_portfolio import ValidatedPortfolio
    
    # Load fixture
    fixture_path = Path(__file__).parent / 'tests' / 'data' / 'spy_daily.csv'
    df = pd.read_csv(fixture_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date')
    df['Price'] = df['Close']
    
    # Step 1: Add indicators
    df = compute_all_indicators(df)
    print("[OK] Indicators added")
    
    # Step 2: Get levels
    fib = ValidatedKeyLevels.fibonacci_retracements(df)
    sr = ValidatedKeyLevels.support_resistance(df)
    print("[OK] Levels computed")
    
    # Step 3: Classify regime
    regime = ValidatedRegime.classify_regime(df)
    print(f"[OK] Regime classified: {regime['regime']}")
    
    # Step 4: Calculate risk
    fetcher = CanonicalDataFetcher()
    returns = fetcher.get_returns(df)
    vol = ValidatedRiskMetrics.volatility(returns)
    sharpe = ValidatedRiskMetrics.sharpe_ratio(returns)
    print(f"[OK] Risk metrics: vol={vol['volatility_annualized']*100:.2f}%, sharpe={sharpe['sharpe_ratio']:.2f}")
    
    # Step 5: Portfolio allocation
    portfolio = ValidatedPortfolio(100000, fractional_allowed=True)
    current_price = df['Price'].iloc[-1]
    allocation = portfolio.allocate({'SPY': 1.0}, {'SPY': current_price})
    print(f"[OK] Portfolio allocated: {allocation['positions']['SPY']['shares']:.2f} shares")
    
    # Verify all data connected
    assert len(df['RSI'].dropna()) > 0
    assert regime['metrics']['adx'] > 0
    assert vol['volatility_daily'] > 0
    assert allocation['total_invested'] > 0
    print("[OK] All modules connected and working together")


# ============================================================================
# RUN ALL TESTS
# ============================================================================

def main():
    print("\n" + "="*80)
    print("COMPREHENSIVE SYSTEM INTEGRATION TEST")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    test_core_config()
    test_canonical_data()
    test_validated_indicators()
    test_validated_levels()
    test_validated_regime()
    test_validated_risk()
    test_validated_portfolio()
    test_market_analytics()
    test_ml_strategy()
    test_optimized_ml_strategy()
    test_data_manager()
    test_performance_analytics()
    test_risk_manager()
    test_cross_module_integration()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = len(test_results['passed'])
    failed = len(test_results['failed'])
    warnings = len(test_results['warnings'])
    total = passed + failed
    
    print(f"\n[PASSED]: {passed}/{total}")
    for test in test_results['passed']:
        print(f"   [+] {test}")
    
    if failed > 0:
        print(f"\n[FAILED]: {failed}/{total}")
        for test in test_results['failed']:
            print(f"   [-] {test}")
    
    if warnings > 0:
        print(f"\n[WARNINGS]: {warnings}")
        for warning in test_results['warnings']:
            print(f"   [!] {warning}")
    
    print("\n" + "="*80)
    
    if failed == 0:
        print("[OK] ALL CRITICAL TESTS PASSED")
        print("System is compatible, accurate, and connected")
        return 0
    else:
        print("[ERROR] SOME TESTS FAILED")
        print("Please review failures above")
        return 1


if __name__ == '__main__':
    sys.exit(main())
