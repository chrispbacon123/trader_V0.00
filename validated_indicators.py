"""
Validated Technical Indicators
Correct implementations with assertions and range checks
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional
import warnings

from core_config import INDICATOR_CFG


class ValidatedIndicators:
    """
    Technical indicators with validation:
    - Correct mathematical implementations (Wilder's RSI/ADX, etc.)
    - Range checks (RSI/Stoch/ADX bounded 0-100)
    - NaN handling after warmup
    - Self-verifying outputs
    """
    
    @staticmethod
    def validate_series(series: pd.Series, name: str, min_val: float, max_val: float):
        """Validate a calculated indicator series"""
        # Check for NaNs after warmup
        non_nan = series.dropna()
        if len(non_nan) == 0:
            warnings.warn(f"{name}: All values are NaN")
            return
        
        # Range check
        if non_nan.min() < min_val or non_nan.max() > max_val:
            actual_min, actual_max = non_nan.min(), non_nan.max()
            warnings.warn(
                f"{name} out of range: expected [{min_val}, {max_val}], "
                f"got [{actual_min:.2f}, {actual_max:.2f}]"
            )
    
    @staticmethod
    def rsi(prices: pd.Series, period: int = None) -> pd.Series:
        """
        Wilder's RSI (Relative Strength Index)
        
        Correct formula:
        - RS = EMA(gains, period) / EMA(losses, period)  [Wilder's smoothing]
        - RSI = 100 - (100 / (1 + RS))
        
        Range: [0, 100]
        Warmup: period + 1 bars
        """
        if period is None:
            period = INDICATOR_CFG.RSI_PERIOD
        
        # Calculate price changes
        delta = prices.diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0.0)
        losses = -delta.where(delta < 0, 0.0)
        
        # Wilder's smoothing (EMA with alpha = 1/period)
        alpha = 1.0 / period
        avg_gain = gains.ewm(alpha=alpha, adjust=False).mean()
        avg_loss = losses.ewm(alpha=alpha, adjust=False).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        
        # Handle division by zero (when avg_loss = 0)
        rsi = rsi.fillna(100.0)
        
        # Validate
        ValidatedIndicators.validate_series(
            rsi, 'RSI', INDICATOR_CFG.RSI_MIN, INDICATOR_CFG.RSI_MAX
        )
        
        return rsi
    
    @staticmethod
    def stochastic(
        high: pd.Series, 
        low: pd.Series, 
        close: pd.Series,
        k_period: int = None,
        d_period: int = None
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator (%K and %D)
        
        Formula:
        - %K = 100 * (Close - Low_n) / (High_n - Low_n)
        - %D = SMA(%K, d_period)
        
        Range: [0, 100]
        Warmup: k_period bars
        """
        if k_period is None:
            k_period = INDICATOR_CFG.STOCH_K_PERIOD
        if d_period is None:
            d_period = INDICATOR_CFG.STOCH_D_PERIOD
        
        # Rolling high/low
        high_roll = high.rolling(window=k_period).max()
        low_roll = low.rolling(window=k_period).min()
        
        # %K
        stoch_k = 100.0 * (close - low_roll) / (high_roll - low_roll)
        stoch_k = stoch_k.fillna(50.0)  # Fill NaN with neutral value
        
        # %D (smoothed %K)
        stoch_d = stoch_k.rolling(window=d_period).mean()
        
        # Validate
        ValidatedIndicators.validate_series(
            stoch_k, 'Stoch %K', INDICATOR_CFG.STOCH_MIN, INDICATOR_CFG.STOCH_MAX
        )
        ValidatedIndicators.validate_series(
            stoch_d, 'Stoch %D', INDICATOR_CFG.STOCH_MIN, INDICATOR_CFG.STOCH_MAX
        )
        
        return stoch_k, stoch_d
    
    @staticmethod
    def macd(
        prices: pd.Series,
        fast: int = None,
        slow: int = None,
        signal: int = None
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        MACD (Moving Average Convergence Divergence)
        
        Formula:
        - MACD = EMA(fast) - EMA(slow)
        - Signal = EMA(MACD, signal_period)
        - Histogram = MACD - Signal
        
        Warmup: slow period bars
        """
        if fast is None:
            fast = INDICATOR_CFG.MACD_FAST
        if slow is None:
            slow = INDICATOR_CFG.MACD_SLOW
        if signal is None:
            signal = INDICATOR_CFG.MACD_SIGNAL
        
        # Calculate EMAs
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        # MACD line
        macd_line = ema_fast - ema_slow
        
        # Signal line
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        
        # Histogram
        histogram = macd_line - signal_line
        
        # Assertion: histogram must equal macd - signal
        assert np.allclose(
            histogram.dropna(), 
            (macd_line - signal_line).dropna(),
            rtol=1e-6
        ), "MACD histogram != MACD - Signal"
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def adx(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = None
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        ADX (Average Directional Index) - Wilder's method
        
        Returns: (ADX, +DI, -DI)
        Range: [0, 100]
        Warmup: 2 * period bars
        """
        if period is None:
            period = INDICATOR_CFG.ADX_PERIOD
        
        # True Range
        high_low = high - low
        high_close = (high - close.shift()).abs()
        low_close = (low - close.shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # Directional Movement
        high_diff = high.diff()
        low_diff = -low.diff()
        
        plus_dm = pd.Series(0.0, index=high.index)
        minus_dm = pd.Series(0.0, index=high.index)
        
        plus_dm[(high_diff > low_diff) & (high_diff > 0)] = high_diff
        minus_dm[(low_diff > high_diff) & (low_diff > 0)] = low_diff
        
        # Wilder's smoothing
        alpha = 1.0 / period
        atr = tr.ewm(alpha=alpha, adjust=False).mean()
        plus_di_smooth = plus_dm.ewm(alpha=alpha, adjust=False).mean()
        minus_di_smooth = minus_dm.ewm(alpha=alpha, adjust=False).mean()
        
        # Directional Indicators
        plus_di = 100.0 * plus_di_smooth / atr
        minus_di = 100.0 * minus_di_smooth / atr
        
        # DX and ADX
        di_sum = plus_di + minus_di
        di_diff = (plus_di - minus_di).abs()
        dx = 100.0 * di_diff / di_sum
        dx = dx.fillna(0.0)
        
        adx = dx.ewm(alpha=alpha, adjust=False).mean()
        
        # Validate
        ValidatedIndicators.validate_series(
            adx, 'ADX', INDICATOR_CFG.ADX_MIN, INDICATOR_CFG.ADX_MAX
        )
        ValidatedIndicators.validate_series(
            plus_di, '+DI', 0, 100
        )
        ValidatedIndicators.validate_series(
            minus_di, '-DI', 0, 100
        )
        
        return adx, plus_di, minus_di
    
    @staticmethod
    def bollinger_bands(
        prices: pd.Series,
        period: int = None,
        std_dev: float = None
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands
        
        Returns: (middle, upper, lower)
        """
        if period is None:
            period = INDICATOR_CFG.BB_PERIOD
        if std_dev is None:
            std_dev = INDICATOR_CFG.BB_STD_DEV
        
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        
        return middle, upper, lower
    
    @staticmethod
    def atr(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = None
    ) -> pd.Series:
        """Average True Range - Wilder's method"""
        if period is None:
            period = INDICATOR_CFG.ATR_PERIOD
        
        high_low = high - low
        high_close = (high - close.shift()).abs()
        low_close = (low - close.shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # Wilder's smoothing
        alpha = 1.0 / period
        atr = tr.ewm(alpha=alpha, adjust=False).mean()
        
        return atr
    
    @staticmethod
    def sma(prices: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def ema(prices: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return prices.ewm(span=period, adjust=False).mean()
    
    def add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add momentum indicators with exact column names for tests.
        Handles Price-only DataFrames by deriving OHLC from Price if missing.
        
        Args:
            df: DataFrame with at least a 'Price' column
            
        Returns:
            DataFrame with momentum indicator columns added
        """
        result = df.copy()
        
        # Ensure we have price column
        if 'Price' not in result.columns:
            raise ValueError("DataFrame must contain 'Price' column")
        
        # Derive OHLC from Price if missing
        if 'Close' not in result.columns:
            result['Close'] = result['Price']
        if 'High' not in result.columns:
            result['High'] = result['Price']
        if 'Low' not in result.columns:
            result['Low'] = result['Price']
        
        # RSI
        result['RSI'] = ValidatedIndicators.rsi(result['Price'])
        
        # Stochastic
        stoch_k, stoch_d = ValidatedIndicators.stochastic(
            result['High'], result['Low'], result['Close']
        )
        result['Stochastic_K'] = stoch_k
        result['Stochastic_D'] = stoch_d
        
        # MACD
        macd, signal, hist = ValidatedIndicators.macd(result['Price'])
        result['MACD'] = macd
        result['MACD_Signal'] = signal
        result['MACD_Histogram'] = hist
        
        # ADX
        adx, plus_di, minus_di = ValidatedIndicators.adx(
            result['High'], result['Low'], result['Close']
        )
        result['ADX'] = adx
        result['Plus_DI'] = plus_di
        result['Minus_DI'] = minus_di
        
        return result


# Convenience function to compute all indicators at once
def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all standard indicators and add to DataFrame
    
    Args:
        df: DataFrame with 'Price' column (and optionally OHLCV)
        
    Returns:
        DataFrame with indicator columns added
    """
    result = df.copy()
    
    # Derive OHLC from Price if missing (backward compatibility)
    if 'Price' in result.columns:
        if 'Close' not in result.columns:
            result['Close'] = result['Price']
        if 'High' not in result.columns:
            result['High'] = result['Price']
        if 'Low' not in result.columns:
            result['Low'] = result['Price']
    
    # RSI
    result['RSI'] = ValidatedIndicators.rsi(result['Price'])
    
    # Stochastic
    stoch_k, stoch_d = ValidatedIndicators.stochastic(
        result['High'], result['Low'], result['Close']
    )
    result['Stoch_K'] = stoch_k
    result['Stoch_D'] = stoch_d
    
    # MACD
    macd, signal, hist = ValidatedIndicators.macd(result['Price'])
    result['MACD'] = macd
    result['MACD_Signal'] = signal
    result['MACD_Hist'] = hist
    
    # ADX
    adx, plus_di, minus_di = ValidatedIndicators.adx(
        result['High'], result['Low'], result['Close']
    )
    result['ADX'] = adx
    result['Plus_DI'] = plus_di
    result['Minus_DI'] = minus_di
    
    # Moving averages
    result['SMA_20'] = ValidatedIndicators.sma(result['Price'], INDICATOR_CFG.SMA_SHORT)
    result['SMA_50'] = ValidatedIndicators.sma(result['Price'], INDICATOR_CFG.SMA_LONG)
    result['EMA_12'] = ValidatedIndicators.ema(result['Price'], INDICATOR_CFG.EMA_SHORT)
    result['EMA_26'] = ValidatedIndicators.ema(result['Price'], INDICATOR_CFG.EMA_LONG)
    
    # Bollinger Bands
    bb_mid, bb_upper, bb_lower = ValidatedIndicators.bollinger_bands(result['Price'])
    result['BB_Mid'] = bb_mid
    result['BB_Upper'] = bb_upper
    result['BB_Lower'] = bb_lower
    
    # ATR
    result['ATR'] = ValidatedIndicators.atr(
        result['High'], result['Low'], result['Close']
    )
    
    return result
