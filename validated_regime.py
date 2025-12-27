"""
Validated Market Regime Detection
Reconciled with trend metrics (ADX) and explicit horizon labels
"""

import pandas as pd
import numpy as np
from typing import Dict
from enum import Enum

from core_config import REGIME_CFG, INDICATOR_CFG
from validated_indicators import ValidatedIndicators


class RegimeType(Enum):
    """Market regime classifications"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    TRANSITIONING = "transitioning"


class ValidatedRegime:
    """
    Market regime detection with:
    - Explicit lookback windows
    - Reconciliation with ADX
    - Multiple horizon analysis
    - Rationale for classification
    """
    
    @staticmethod
    def classify_regime(
        df: pd.DataFrame,
        lookback: int = None,
        vol_window: int = None
    ) -> Dict:
        """
        Classify market regime with full explanation
        
        Args:
            df: DataFrame with Price, indicators
            lookback: Days for regime analysis
            vol_window: Rolling volatility window
            
        Returns:
            Dict with regime, confidence, metrics, and rationale
        """
        if lookback is None:
            lookback = REGIME_CFG.REGIME_LOOKBACK
        if vol_window is None:
            vol_window = REGIME_CFG.REGIME_VOL_WINDOW
        
        # Subset to lookback window
        recent_df = df.iloc[-min(lookback, len(df)):].copy()
        
        if len(recent_df) < vol_window:
            return {
                'regime': RegimeType.TRANSITIONING.value,
                'confidence': 0.3,
                'rationale': 'Insufficient data for regime classification',
                'lookback_days': len(recent_df)
            }
        
        # Calculate regime metrics
        # Handle MultiIndex columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            # Get canonical price column (Adj Close or Close)
            if 'Adj Close' in [col[0] if isinstance(col, tuple) else col for col in df.columns]:
                price_col = [col for col in df.columns if (isinstance(col, tuple) and col[0] == 'Adj Close') or col == 'Adj Close'][0]
            else:
                price_col = [col for col in df.columns if (isinstance(col, tuple) and col[0] == 'Close') or col == 'Close'][0]
            price_series = recent_df[price_col]
        else:
            # Use canonical Price column if available, otherwise Close
            if 'Price' in recent_df.columns:
                price_series = recent_df['Price']
            elif 'Adj Close' in recent_df.columns:
                price_series = recent_df['Adj Close']
            else:
                price_series = recent_df['Close']
        
        current_price = price_series.iloc[-1]
        
        # Moving averages
        sma_20 = ValidatedIndicators.sma(price_series, INDICATOR_CFG.SMA_SHORT).iloc[-1]
        sma_50 = ValidatedIndicators.sma(price_series, INDICATOR_CFG.SMA_LONG).iloc[-1]
        
        # Price position relative to SMAs
        price_vs_sma20 = (current_price - sma_20) / sma_20
        price_vs_sma50 = (current_price - sma_50) / sma_50
        sma_trend = (sma_20 - sma_50) / sma_50
        
        # Volatility (ANNUALIZED)
        returns = price_series.pct_change().dropna()
        vol_daily = returns.iloc[-vol_window:].std()
        vol_annualized = vol_daily * np.sqrt(252)
        
        # Internal assertion: verify thresholds are annualized scale (> 0.05)
        assert REGIME_CFG.VOL_LOW_THRESHOLD > 0.05, \
            "VOL_LOW_THRESHOLD must be annualized (> 0.05, typically 0.10-0.15)"
        assert REGIME_CFG.VOL_HIGH_THRESHOLD > REGIME_CFG.VOL_LOW_THRESHOLD, \
            "VOL_HIGH_THRESHOLD must exceed VOL_LOW_THRESHOLD"
        
        # ADX for trend strength
        if 'ADX' in recent_df.columns:
            adx_current = recent_df['ADX'].iloc[-1]
            plus_di = recent_df['Plus_DI'].iloc[-1]
            minus_di = recent_df['Minus_DI'].iloc[-1]
        else:
            # Calculate on the fly with fallback for missing OHLC columns
            high = recent_df['High'] if 'High' in recent_df.columns else price_series
            low = recent_df['Low'] if 'Low' in recent_df.columns else price_series
            close = recent_df['Close'] if 'Close' in recent_df.columns else price_series
            adx, plus_di, minus_di = ValidatedIndicators.adx(high, low, close)
            adx_current = adx.iloc[-1]
            plus_di = plus_di.iloc[-1]
            minus_di = minus_di.iloc[-1]
        
        # Classification logic with rationale
        rationale_parts = []
        
        # Check volatility first
        if vol_annualized > REGIME_CFG.VOL_HIGH_THRESHOLD:
            regime = RegimeType.VOLATILE
            confidence = 0.8
            rationale_parts.append(
                f"High volatility: {vol_annualized*100:.2f}% annualized "
                f"(threshold: {REGIME_CFG.VOL_HIGH_THRESHOLD*100:.1f}%)"
            )
        
        # Check for ranging market (low volatility + weak trend)
        elif (vol_annualized < REGIME_CFG.VOL_LOW_THRESHOLD and 
              abs(sma_trend) < REGIME_CFG.TREND_THRESHOLD and
              adx_current < REGIME_CFG.ADX_WEAK_TREND):
            regime = RegimeType.RANGING
            confidence = 0.75
            rationale_parts.append(
                f"Low volatility: {vol_annualized*100:.2f}% "
                f"(threshold: {REGIME_CFG.VOL_LOW_THRESHOLD*100:.1f}%)"
            )
            rationale_parts.append(
                f"Weak SMA trend: {sma_trend*100:.2f}% "
                f"(threshold: ±{REGIME_CFG.TREND_THRESHOLD*100:.1f}%)"
            )
            rationale_parts.append(
                f"ADX: {adx_current:.1f} indicates weak trend "
                f"(threshold: <{REGIME_CFG.ADX_WEAK_TREND})"
            )
        
        # Check for strong uptrend
        elif (price_vs_sma20 > REGIME_CFG.TREND_THRESHOLD and
              sma_trend > REGIME_CFG.TREND_THRESHOLD and
              adx_current > REGIME_CFG.ADX_STRONG_TREND and
              plus_di > minus_di):
            regime = RegimeType.TRENDING_UP
            confidence = 0.85
            rationale_parts.append(
                f"Price above SMA20: {price_vs_sma20*100:.2f}% "
                f"(threshold: >{REGIME_CFG.TREND_THRESHOLD*100:.1f}%)"
            )
            rationale_parts.append(
                f"SMA uptrend: {sma_trend*100:.2f}% "
                f"(threshold: >{REGIME_CFG.TREND_THRESHOLD*100:.1f}%)"
            )
            rationale_parts.append(
                f"ADX: {adx_current:.1f} indicates strong trend "
                f"(threshold: >{REGIME_CFG.ADX_STRONG_TREND})"
            )
            rationale_parts.append(
                f"+DI ({plus_di:.1f}) > -DI ({minus_di:.1f})"
            )
        
        # Check for strong downtrend
        elif (price_vs_sma20 < -REGIME_CFG.TREND_THRESHOLD and
              sma_trend < -REGIME_CFG.TREND_THRESHOLD and
              adx_current > REGIME_CFG.ADX_STRONG_TREND and
              minus_di > plus_di):
            regime = RegimeType.TRENDING_DOWN
            confidence = 0.85
            rationale_parts.append(
                f"Price below SMA20: {price_vs_sma20*100:.2f}% "
                f"(threshold: <-{REGIME_CFG.TREND_THRESHOLD*100:.1f}%)"
            )
            rationale_parts.append(
                f"SMA downtrend: {sma_trend*100:.2f}% "
                f"(threshold: <-{REGIME_CFG.TREND_THRESHOLD*100:.1f}%)"
            )
            rationale_parts.append(
                f"ADX: {adx_current:.1f} indicates strong trend "
                f"(threshold: >{REGIME_CFG.ADX_STRONG_TREND})"
            )
            rationale_parts.append(
                f"-DI ({minus_di:.1f}) > +DI ({plus_di:.1f})"
            )
        
        # Transitioning (default)
        else:
            regime = RegimeType.TRANSITIONING
            confidence = 0.5
            rationale_parts.append(
                "Mixed signals: no clear regime pattern"
            )
            rationale_parts.append(
                f"SMA trend: {sma_trend*100:.2f}%, "
                f"ADX: {adx_current:.1f}, "
                f"Vol: {vol_annualized*100:.2f}%"
            )
        
        return {
            'regime': regime.value,
            'confidence': confidence,
            'rationale': "; ".join(rationale_parts),
            'metrics': {
                'price_vs_sma20_pct': price_vs_sma20 * 100,
                'price_vs_sma50_pct': price_vs_sma50 * 100,
                'sma_trend_pct': sma_trend * 100,
                'volatility_daily_pct': vol_daily * 100,
                'volatility_annualized_pct': vol_annualized * 100,
                'adx': adx_current,
                'plus_di': plus_di,
                'minus_di': minus_di
            },
            'lookback_days': len(recent_df),
            'vol_window_days': vol_window,
            'analysis_window': {
                'start': recent_df.index[0],
                'end': recent_df.index[-1]
            }
        }
    
    @staticmethod
    def multi_horizon_regime(df: pd.DataFrame) -> Dict:
        """
        Analyze regime across multiple horizons
        
        Returns:
            Dict with short, medium, long-term regimes
        """
        horizons = {
            'short_term': 20,   # ~1 month
            'medium_term': 60,  # ~3 months
            'long_term': 120    # ~6 months
        }
        
        results = {}
        for label, lookback in horizons.items():
            if len(df) >= lookback:
                regime = ValidatedRegime.classify_regime(df, lookback=lookback)
                results[label] = {
                    'regime': regime['regime'],
                    'confidence': regime['confidence'],
                    'adx': regime['metrics']['adx'],
                    'volatility_pct': regime['metrics']['volatility_annualized_pct']
                }
            else:
                results[label] = {
                    'regime': 'insufficient_data',
                    'confidence': 0.0
                }
        
        return results
    
    @staticmethod
    def print_regime(regime_dict: Dict):
        """Print regime classification with full details"""
        print(f"\n{'='*80}")
        print("MARKET REGIME CLASSIFICATION")
        print(f"{'='*80}")
        
        window = regime_dict['analysis_window']
        print(f"Analysis Window:  {window['start'].date()} to {window['end'].date()}")
        print(f"Lookback Days:    {regime_dict['lookback_days']}")
        print(f"Vol Window Days:  {regime_dict['vol_window_days']}")
        
        print(f"\nRegime:           {regime_dict['regime'].upper().replace('_', ' ')}")
        print(f"Confidence:       {regime_dict['confidence']*100:.1f}%")
        
        print(f"\nRationale:")
        for line in regime_dict['rationale'].split("; "):
            print(f"  • {line}")
        
        print(f"\nKey Metrics:")
        metrics = regime_dict['metrics']
        print(f"  Price vs SMA20:   {metrics['price_vs_sma20_pct']:>6.2f}%")
        print(f"  Price vs SMA50:   {metrics['price_vs_sma50_pct']:>6.2f}%")
        print(f"  SMA Trend:        {metrics['sma_trend_pct']:>6.2f}%")
        print(f"  Volatility:       {metrics['volatility_annualized_pct']:>6.2f}% (annualized)")
        print(f"  ADX:              {metrics['adx']:>6.1f}")
        print(f"  +DI:              {metrics['plus_di']:>6.1f}")
        print(f"  -DI:              {metrics['minus_di']:>6.1f}")
        
        print(f"{'='*80}\n")


def compute_regime(df: pd.DataFrame, verbose: bool = True) -> Dict:
    """
    Convenience function to compute and optionally print regime
    """
    regime = ValidatedRegime.classify_regime(df)
    
    if verbose:
        ValidatedRegime.print_regime(regime)
    
    return regime
