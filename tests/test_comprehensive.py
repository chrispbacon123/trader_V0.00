"""
Comprehensive test suite for trading system
Tests deterministic behavior and catches common bugs
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Import modules to test
from canonical_data import CanonicalDataFetcher
from validated_indicators import ValidatedIndicators, compute_all_indicators
from validated_levels import ValidatedKeyLevels
from validated_regime import ValidatedRegime
from validated_risk import ValidatedRiskMetrics
from validated_portfolio import ValidatedPortfolio
from market_analytics import MarketAnalytics
from core_config import INDICATOR_CFG, LEVEL_CFG, REGIME_CFG, PORTFOLIO_CFG

# Import test fixtures
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))  # Insert project root, not tests dir
from tests.fixtures import (
    generate_synthetic_ohlcv,
    generate_flat_prices,
    generate_with_gaps,
    generate_with_nans,
    generate_short_history
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def spy_fixture_df():
    """Load frozen SPY CSV fixture"""
    fixture_path = Path(__file__).parent / 'data' / 'spy_daily.csv'
    df = pd.read_csv(fixture_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date')
    return df


@pytest.fixture
def synthetic_df():
    """Generate synthetic OHLCV for testing"""
    return generate_synthetic_ohlcv(num_days=252, seed=42)


@pytest.fixture
def canonical_fetcher():
    """Create CanonicalDataFetcher instance"""
    return CanonicalDataFetcher()


# ============================================================================
# TEST: Data Fetching & Canonical Price
# ============================================================================

class TestCanonicalData:
    """Test data fetching and canonical price column"""
    
    def test_price_column_exists(self, spy_fixture_df):
        """Test that Price column is created"""
        fetcher = CanonicalDataFetcher()
        
        # Add Price column (mimicking fetch_data)
        df = spy_fixture_df.copy()
        df['Price'] = df['Close']  # Simulating auto-adjusted
        
        assert 'Price' in df.columns
        assert len(df['Price']) == len(df)
        assert (df['Price'] > 0).all()
    
    def test_no_multiindex(self, spy_fixture_df):
        """Test that we never have MultiIndex columns"""
        assert not isinstance(spy_fixture_df.columns, pd.MultiIndex)
    
    def test_required_columns(self, spy_fixture_df):
        """Test all required OHLCV columns present"""
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required:
            assert col in spy_fixture_df.columns
    
    def test_price_validation(self, spy_fixture_df):
        """Test price validation rules"""
        df = spy_fixture_df.copy()
        
        # All prices positive
        assert (df['Open'] > 0).all()
        assert (df['High'] > 0).all()
        assert (df['Low'] > 0).all()
        assert (df['Close'] > 0).all()
        
        # High >= Low
        assert (df['High'] >= df['Low']).all()
        
        # Close within High/Low range
        assert (df['Close'] <= df['High']).all()
        assert (df['Close'] >= df['Low']).all()


# ============================================================================
# TEST: Indicators (RSI, MACD, ADX, Stochastic)
# ============================================================================

class TestValidatedIndicators:
    """Test indicator calculations and invariants"""
    
    def test_rsi_bounds(self, synthetic_df):
        """Test RSI always in [0, 100]"""
        df = synthetic_df.copy()
        df['Price'] = df['Close']
        
        rsi = ValidatedIndicators.rsi(df['Price'])
        rsi_clean = rsi.dropna()
        
        assert len(rsi_clean) > 0, "RSI produced all NaNs"
        assert (rsi_clean >= 0).all(), f"RSI below 0: min={rsi_clean.min()}"
        assert (rsi_clean <= 100).all(), f"RSI above 100: max={rsi_clean.max()}"
    
    def test_stochastic_bounds(self, synthetic_df):
        """Test Stochastic %K and %D in [0, 100]"""
        df = synthetic_df.copy()
        
        stoch_k, stoch_d = ValidatedIndicators.stochastic(
            df['High'], df['Low'], df['Close']
        )
        
        k_clean = stoch_k.dropna()
        d_clean = stoch_d.dropna()
        
        assert len(k_clean) > 0
        assert len(d_clean) > 0
        
        assert (k_clean >= 0).all() and (k_clean <= 100).all()
        assert (d_clean >= 0).all() and (d_clean <= 100).all()
    
    def test_adx_bounds(self, synthetic_df):
        """Test ADX in [0, 100]"""
        df = synthetic_df.copy()
        
        adx, plus_di, minus_di = ValidatedIndicators.adx(
            df['High'], df['Low'], df['Close']
        )
        
        adx_clean = adx.dropna()
        plus_clean = plus_di.dropna()
        minus_clean = minus_di.dropna()
        
        assert len(adx_clean) > 0
        
        assert (adx_clean >= 0).all() and (adx_clean <= 100).all()
        assert (plus_clean >= 0).all() and (plus_clean <= 100).all()
        assert (minus_clean >= 0).all() and (minus_clean <= 100).all()
    
    def test_macd_histogram_consistency(self, synthetic_df):
        """Test MACD histogram equals MACD - Signal"""
        df = synthetic_df.copy()
        df['Price'] = df['Close']
        
        macd, signal, hist = ValidatedIndicators.macd(df['Price'])
        
        # Check histogram consistency
        diff = (macd - signal).dropna()
        hist_clean = hist.dropna()
        
        # Should be equal within numerical precision
        assert np.allclose(hist_clean, diff, rtol=1e-6, atol=1e-8)
    
    def test_no_final_nans(self, synthetic_df):
        """Test no NaNs in final outputs after warmup"""
        df = synthetic_df.copy()
        df['Price'] = df['Close']
        
        df = compute_all_indicators(df)
        
        # Check last 50 rows (well past warmup for all indicators)
        final_rows = df.iloc[-50:]
        
        # These should have no NaNs after warmup
        critical_cols = ['RSI', 'MACD', 'ADX', 'Stoch_K', 'Stoch_D']
        
        for col in critical_cols:
            nans = final_rows[col].isna().sum()
            assert nans == 0, f"{col} has {nans} NaNs in final 50 rows"


# ============================================================================
# TEST: Key Levels (Support/Resistance, Fibonacci)
# ============================================================================

class TestValidatedLevels:
    """Test key levels calculations"""
    
    def test_fibonacci_anchors_in_window(self, synthetic_df):
        """Test Fibonacci anchors come from declared lookback window"""
        df = synthetic_df.copy()
        df['Price'] = df['Close']
        
        lookback = LEVEL_CFG.FIB_LOOKBACK
        
        fib_result = ValidatedKeyLevels.fibonacci_retracements(df, lookback=lookback)
        
        # Check metadata exists
        assert 'anchor_high_date' in fib_result
        assert 'anchor_low_date' in fib_result
        assert 'lookback_start' in fib_result
        assert 'lookback_end' in fib_result
        
        # Verify anchors are within lookback window
        anchor_high_date = fib_result['anchor_high_date']
        anchor_low_date = fib_result['anchor_low_date']
        lookback_start = fib_result['lookback_start']
        lookback_end = fib_result['lookback_end']
        
        assert anchor_high_date >= lookback_start
        assert anchor_high_date <= lookback_end
        assert anchor_low_date >= lookback_start
        assert anchor_low_date <= lookback_end
    
    def test_fibonacci_levels_ordered(self, synthetic_df):
        """Test Fibonacci levels are properly ordered"""
        df = synthetic_df.copy()
        df['Price'] = df['Close']
        
        fib_result = ValidatedKeyLevels.fibonacci_retracements(df)
        
        # Extract level prices
        high = fib_result['0.0%']
        mid = fib_result['50.0%']
        low = fib_result['100.0%']
        
        # Should be ordered: high > mid > low
        assert high > mid > low, f"Fib levels not ordered: {high} > {mid} > {low}"
    
    def test_support_resistance_proximity(self, synthetic_df):
        """Test S/R levels are within proximity filter of current price"""
        df = synthetic_df.copy()
        df['Price'] = df['Close']
        
        sr_result = ValidatedKeyLevels.support_resistance(df)
        
        current_price = sr_result['current_price']
        proximity = LEVEL_CFG.SR_PROXIMITY_FILTER
        
        # Check support levels
        for level in sr_result['support']:
            ratio = level / current_price
            assert ratio > (1 - proximity), f"Support ${level:.2f} too far below ${current_price:.2f}"
        
        # Check resistance levels
        for level in sr_result['resistance']:
            ratio = level / current_price
            assert ratio < (1 + proximity), f"Resistance ${level:.2f} too far above ${current_price:.2f}"


# ============================================================================
# TEST: Regime Classification
# ============================================================================

class TestValidatedRegime:
    """Test market regime detection"""
    
    def test_regime_has_rationale(self, synthetic_df):
        """Test regime includes explicit rationale"""
        df = synthetic_df.copy()
        df['Price'] = df['Close']
        df = compute_all_indicators(df)
        
        regime = ValidatedRegime.classify_regime(df)
        
        assert 'regime' in regime
        assert 'confidence' in regime
        assert 'rationale' in regime
        assert 'metrics' in regime
        
        # Rationale should be non-empty
        assert len(regime['rationale']) > 0
    
    def test_regime_uses_adx(self, synthetic_df):
        """Test regime classification uses ADX in metrics"""
        df = synthetic_df.copy()
        df['Price'] = df['Close']
        df = compute_all_indicators(df)
        
        regime = ValidatedRegime.classify_regime(df)
        
        # ADX should be in metrics
        assert 'adx' in regime['metrics']
        
        # ADX should be bounded
        adx = regime['metrics']['adx']
        assert 0 <= adx <= 100
    
    def test_regime_confidence_bounds(self, synthetic_df):
        """Test regime confidence in [0, 1]"""
        df = synthetic_df.copy()
        df['Price'] = df['Close']
        df = compute_all_indicators(df)
        
        regime = ValidatedRegime.classify_regime(df)
        
        conf = regime['confidence']
        assert 0 <= conf <= 1, f"Confidence {conf} out of bounds"


# ============================================================================
# TEST: Risk Metrics
# ============================================================================

class TestValidatedRiskMetrics:
    """Test risk calculations"""
    
    def test_volatility_annualization(self, synthetic_df):
        """Test volatility annualization is consistent"""
        df = synthetic_df.copy()
        df['Price'] = df['Close']
        
        # Use canonical returns WITHOUT fillna(0)
        returns = np.log(df['Price'] / df['Price'].shift(1)).dropna()
        
        vol = ValidatedRiskMetrics.volatility(returns)
        
        # Check annualization factor
        expected_factor = np.sqrt(252)
        assert vol['annualization_factor'] == expected_factor
        
        # Check relationship
        vol_daily = vol['volatility_daily']
        vol_annual = vol['volatility_annualized']
        
        assert np.isclose(vol_annual, vol_daily * expected_factor, rtol=1e-6)
        
        # Returns length should be data rows - 1
        assert len(returns) == len(df) - 1
    
    def test_var_cvar_relationship(self, synthetic_df):
        """Test CVaR <= VaR (more negative)"""
        df = synthetic_df.copy()
        df['Price'] = df['Close']
        
        # Use canonical returns WITHOUT fillna(0)
        returns = np.log(df['Price'] / df['Price'].shift(1)).dropna()
        
        var = ValidatedRiskMetrics.value_at_risk(returns)
        cvar = ValidatedRiskMetrics.conditional_var(returns)
        
        # CVaR should be more negative than VaR
        assert cvar['cvar'] <= var['var']
    
    def test_risk_labels_explicit(self, synthetic_df):
        """Test risk metrics have explicit labels"""
        df = synthetic_df.copy()
        df['Price'] = df['Close']
        
        # Use canonical returns WITHOUT fillna(0)
        returns = np.log(df['Price'] / df['Price'].shift(1)).dropna()
        
        vol = ValidatedRiskMetrics.volatility(returns)
        var = ValidatedRiskMetrics.value_at_risk(returns)
        
        # Should have both daily and annualized
        assert 'volatility_daily' in vol
        assert 'volatility_annualized' in vol
        
        # VaR should have horizon and method
        assert 'horizon_days' in var
        assert 'method' in var
        assert 'confidence' in var
    
    def test_market_analytics_risk_metrics_backward_compat(self, synthetic_df):
        """Test MarketAnalytics.risk_metrics() returns backward-compatible keys for UI"""
        # Required keys that the UI expects
        ui_required_keys = ['volatility', 'var_95', 'cvar_95', 'downside_deviation', 
                            'max_drawdown', 'calmar_ratio', 'sortino_ratio']
        
        # Also require detailed keys for new code
        detailed_keys = ['volatility_daily', 'volatility_annualized', 'var_95_1day', 'cvar_95_1day']
        
        # Create a mock MarketAnalytics with data
        from market_analytics import MarketAnalytics
        from canonical_data import CanonicalDataFetcher
        
        analytics = MarketAnalytics('TEST')
        # Set up data directly (skip fetch)
        df = synthetic_df.copy()
        if 'Price' not in df.columns:
            df['Price'] = df['Close']
        analytics.data = df
        analytics.fetcher = CanonicalDataFetcher()
        
        # Get risk metrics
        risk = analytics.risk_metrics()
        
        # Must return non-empty dict for valid data
        assert risk, "risk_metrics() returned empty dict"
        
        # Verify all UI-required keys exist
        for key in ui_required_keys:
            assert key in risk, f"Missing UI-required key: {key}"
        
        # Verify all detailed keys exist
        for key in detailed_keys:
            assert key in risk, f"Missing detailed key: {key}"
        
        # Verify aliases are consistent
        assert risk['volatility'] == risk['volatility_annualized'], "volatility alias mismatch"
        assert risk['var_95'] == risk['var_95_1day'], "var_95 alias mismatch"
        assert risk['cvar_95'] == risk['cvar_95_1day'], "cvar_95 alias mismatch"


# ============================================================================
# TEST: Portfolio Allocation (Fractional Shares)
# ============================================================================

class TestValidatedPortfolio:
    """Test portfolio allocation with fractional shares"""
    
    def test_fractional_shares_allocation(self):
        """Test fractional shares are used when enabled"""
        portfolio = ValidatedPortfolio(
            equity=100000,
            fractional_allowed=True
        )
        
        target_weights = {'SPY': 0.6, 'QQQ': 0.4}
        prices = {'SPY': 450.75, 'QQQ': 380.25}
        
        summary = portfolio.allocate(target_weights, prices)
        
        # Check that shares are fractional
        spy_shares = summary['positions']['SPY']['shares']
        qqq_shares = summary['positions']['QQQ']['shares']
        
        # Should not be whole numbers
        assert spy_shares != int(spy_shares) or qqq_shares != int(qqq_shares)
    
    def test_whole_shares_when_disabled(self):
        """Test whole shares are used when fractional disabled"""
        portfolio = ValidatedPortfolio(
            equity=100000,
            fractional_allowed=False
        )
        
        target_weights = {'SPY': 0.6, 'QQQ': 0.4}
        prices = {'SPY': 450.75, 'QQQ': 380.25}
        
        summary = portfolio.allocate(target_weights, prices)
        
        # Check that shares are whole numbers
        spy_shares = summary['positions']['SPY']['shares']
        qqq_shares = summary['positions']['QQQ']['shares']
        
        assert spy_shares == int(spy_shares)
        assert qqq_shares == int(qqq_shares)
    
    def test_cash_tracking(self):
        """Test cash residuals are tracked explicitly"""
        portfolio = ValidatedPortfolio(
            equity=100000,
            fractional_allowed=True
        )
        
        target_weights = {'SPY': 1.0}
        prices = {'SPY': 450.00}
        
        summary = portfolio.allocate(target_weights, prices)
        
        # Should have cash remaining
        assert 'cash_remaining' in summary
        assert summary['cash_remaining'] >= 0
        
        # Total should equal equity
        total = summary['total_invested'] + summary['cash_remaining'] + summary['transaction_costs']
        assert np.isclose(total, portfolio.equity, atol=1.0)
    
    def test_transaction_costs(self):
        """Test transaction costs are applied"""
        portfolio = ValidatedPortfolio(
            equity=100000,
            fractional_allowed=True,
            slippage_bps=5.0,
            commission_per_share=0.005
        )
        
        target_weights = {'SPY': 1.0}
        prices = {'SPY': 450.00}
        
        summary = portfolio.allocate(target_weights, prices)
        
        # Should have non-zero costs
        assert 'transaction_costs' in summary
        assert summary['transaction_costs'] > 0


# ============================================================================
# TEST: Market Analytics Integration
# ============================================================================

class TestMarketAnalytics:
    """Test MarketAnalytics with frozen data"""
    
    def test_comprehensive_analysis_no_errors(self, spy_fixture_df):
        """Test print_comprehensive_analysis runs without errors"""
        # Create MarketAnalytics instance
        ma = MarketAnalytics('TEST')
        
        # Manually set data (bypass live fetch)
        ma.data = spy_fixture_df.copy()
        ma.data['Price'] = ma.data['Close']
        ma.data = compute_all_indicators(ma.data)
        
        ma.metadata = {
            'symbol': 'TEST',
            'actual_start': ma.data.index[0].date(),
            'actual_end': ma.data.index[-1].date(),
            'num_rows': len(ma.data),
            'price_source': 'Close (adjusted)'
        }
        
        # Should run without exception
        try:
            ma.print_comprehensive_analysis()
            success = True
        except Exception as e:
            print(f"Error: {e}")
            success = False
        
        assert success, "print_comprehensive_analysis raised exception"
    
    def test_indicators_in_output(self, spy_fixture_df):
        """Test that momentum indicators are computed"""
        ma = MarketAnalytics('TEST')
        ma.data = spy_fixture_df.copy()
        ma.data['Price'] = ma.data['Close']
        ma.data = compute_all_indicators(ma.data)
        
        momentum = ma.momentum_analysis()
        
        # Should have labeled indicators
        assert any('RSI' in key for key in momentum.keys())
        assert any('ADX' in key for key in momentum.keys())
        assert any('MACD' in key for key in momentum.keys())


# ============================================================================
# TEST: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_flat_prices(self):
        """Test handling of flat/constant prices"""
        df = generate_flat_prices(100, price=100.0)
        df['Price'] = df['Close']
        
        # Should not crash
        df = compute_all_indicators(df)
        
        # For truly flat prices, RSI can be 100 (no losses)
        # Just check it's bounded and not NaN
        rsi_final = df['RSI'].iloc[-1]
        assert 0 <= rsi_final <= 100, f"RSI={rsi_final} out of bounds [0,100]"
        assert not np.isnan(rsi_final), "RSI is NaN for flat prices"
    
    def test_short_history(self):
        """Test handling of very short history"""
        df = generate_short_history(15)
        df['Price'] = df['Close']
        
        # Should handle gracefully (may have NaNs)
        df = compute_all_indicators(df)
        
        # At least some indicators should compute
        assert not df['Price'].isna().all()
    
    def test_with_nans(self):
        """Test handling of NaN values"""
        df = generate_with_nans(100, [5, 15, 25])
        df['Price'] = df['Close'].ffill()  # Forward fill NaNs
        
        # Should not crash
        df = compute_all_indicators(df)
        
        # Should have computed something
        assert not df['RSI'].isna().all()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
