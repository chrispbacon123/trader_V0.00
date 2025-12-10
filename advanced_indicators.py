"""
Advanced Technical Indicators and Market Analysis
Includes institutional-grade indicators and pattern recognition
"""

import numpy as np
import pandas as pd
from typing import Tuple, List, Dict
from scipy import stats
from scipy.signal import find_peaks, argrelextrema

class AdvancedIndicators:
    """Collection of advanced technical indicators"""
    
    @staticmethod
    def ichimoku_cloud(df: pd.DataFrame, tenkan=9, kijun=26, senkou_b=52) -> pd.DataFrame:
        """Calculate Ichimoku Cloud indicator"""
        result = df.copy()
        
        # Tenkan-sen (Conversion Line)
        high_tenkan = result['high'].rolling(window=tenkan).max()
        low_tenkan = result['low'].rolling(window=tenkan).min()
        result['tenkan_sen'] = (high_tenkan + low_tenkan) / 2
        
        # Kijun-sen (Base Line)
        high_kijun = result['high'].rolling(window=kijun).max()
        low_kijun = result['low'].rolling(window=kijun).min()
        result['kijun_sen'] = (high_kijun + low_kijun) / 2
        
        # Senkou Span A (Leading Span A)
        result['senkou_span_a'] = ((result['tenkan_sen'] + result['kijun_sen']) / 2).shift(kijun)
        
        # Senkou Span B (Leading Span B)
        high_senkou = result['high'].rolling(window=senkou_b).max()
        low_senkou = result['low'].rolling(window=senkou_b).min()
        result['senkou_span_b'] = ((high_senkou + low_senkou) / 2).shift(kijun)
        
        # Chikou Span (Lagging Span)
        result['chikou_span'] = result['close'].shift(-kijun)
        
        return result
    
    @staticmethod
    def heikin_ashi(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Heikin Ashi candles"""
        result = df.copy()
        
        result['ha_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        result['ha_open'] = 0.0
        result['ha_open'].iloc[0] = (df['open'].iloc[0] + df['close'].iloc[0]) / 2
        
        for i in range(1, len(result)):
            result['ha_open'].iloc[i] = (result['ha_open'].iloc[i-1] + result['ha_close'].iloc[i-1]) / 2
        
        result['ha_high'] = result[['high', 'ha_open', 'ha_close']].max(axis=1)
        result['ha_low'] = result[['low', 'ha_open', 'ha_close']].min(axis=1)
        
        return result
    
    @staticmethod
    def keltner_channels(df: pd.DataFrame, period=20, atr_multiplier=2) -> pd.DataFrame:
        """Calculate Keltner Channels"""
        result = df.copy()
        
        # Middle line (EMA)
        result['keltner_mid'] = result['close'].ewm(span=period).mean()
        
        # ATR
        high_low = result['high'] - result['low']
        high_close = abs(result['high'] - result['close'].shift())
        low_close = abs(result['low'] - result['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        # Upper and lower bands
        result['keltner_upper'] = result['keltner_mid'] + (atr_multiplier * atr)
        result['keltner_lower'] = result['keltner_mid'] - (atr_multiplier * atr)
        
        return result
    
    @staticmethod
    def donchian_channels(df: pd.DataFrame, period=20) -> pd.DataFrame:
        """Calculate Donchian Channels"""
        result = df.copy()
        
        result['donchian_upper'] = result['high'].rolling(window=period).max()
        result['donchian_lower'] = result['low'].rolling(window=period).min()
        result['donchian_mid'] = (result['donchian_upper'] + result['donchian_lower']) / 2
        
        return result
    
    @staticmethod
    def vwap(df: pd.DataFrame) -> pd.Series:
        """Calculate Volume-Weighted Average Price"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        return (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
    
    @staticmethod
    def anchored_vwap(df: pd.DataFrame, anchor_date: str) -> pd.Series:
        """Calculate anchored VWAP from specific date"""
        df_subset = df[df.index >= anchor_date].copy()
        return AdvancedIndicators.vwap(df_subset)
    
    @staticmethod
    def supertrend(df: pd.DataFrame, period=10, multiplier=3) -> pd.DataFrame:
        """Calculate SuperTrend indicator"""
        result = df.copy()
        
        # Calculate ATR
        high_low = result['high'] - result['low']
        high_close = abs(result['high'] - result['close'].shift())
        low_close = abs(result['low'] - result['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        # Basic bands
        hl_avg = (result['high'] + result['low']) / 2
        upper_band = hl_avg + (multiplier * atr)
        lower_band = hl_avg - (multiplier * atr)
        
        # SuperTrend
        result['supertrend'] = 0.0
        result['supertrend_direction'] = 1
        
        for i in range(period, len(result)):
            if result['close'].iloc[i] > upper_band.iloc[i-1]:
                result['supertrend'].iloc[i] = lower_band.iloc[i]
                result['supertrend_direction'].iloc[i] = 1
            elif result['close'].iloc[i] < lower_band.iloc[i-1]:
                result['supertrend'].iloc[i] = upper_band.iloc[i]
                result['supertrend_direction'].iloc[i] = -1
            else:
                result['supertrend'].iloc[i] = result['supertrend'].iloc[i-1]
                result['supertrend_direction'].iloc[i] = result['supertrend_direction'].iloc[i-1]
        
        return result
    
    @staticmethod
    def elder_ray(df: pd.DataFrame, period=13) -> pd.DataFrame:
        """Calculate Elder Ray Index (Bull/Bear Power)"""
        result = df.copy()
        
        ema = result['close'].ewm(span=period).mean()
        result['bull_power'] = result['high'] - ema
        result['bear_power'] = result['low'] - ema
        
        return result
    
    @staticmethod
    def aroon(df: pd.DataFrame, period=25) -> pd.DataFrame:
        """Calculate Aroon indicator"""
        result = df.copy()
        
        result['aroon_up'] = df['high'].rolling(window=period).apply(
            lambda x: (period - x.argmax()) / period * 100, raw=True
        )
        result['aroon_down'] = df['low'].rolling(window=period).apply(
            lambda x: (period - x.argmin()) / period * 100, raw=True
        )
        result['aroon_oscillator'] = result['aroon_up'] - result['aroon_down']
        
        return result
    
    @staticmethod
    def stochastic_rsi(df: pd.DataFrame, period=14, smooth_k=3, smooth_d=3) -> pd.DataFrame:
        """Calculate Stochastic RSI"""
        result = df.copy()
        
        # Calculate RSI
        delta = result['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Stochastic of RSI
        rsi_min = rsi.rolling(window=period).min()
        rsi_max = rsi.rolling(window=period).max()
        stoch_rsi = (rsi - rsi_min) / (rsi_max - rsi_min) * 100
        
        result['stoch_rsi_k'] = stoch_rsi.rolling(window=smooth_k).mean()
        result['stoch_rsi_d'] = result['stoch_rsi_k'].rolling(window=smooth_d).mean()
        
        return result
    
    @staticmethod
    def williams_r(df: pd.DataFrame, period=14) -> pd.Series:
        """Calculate Williams %R"""
        highest_high = df['high'].rolling(window=period).max()
        lowest_low = df['low'].rolling(window=period).min()
        return -100 * (highest_high - df['close']) / (highest_high - lowest_low)
    
    @staticmethod
    def chaikin_money_flow(df: pd.DataFrame, period=20) -> pd.Series:
        """Calculate Chaikin Money Flow"""
        mfm = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
        mfv = mfm * df['volume']
        return mfv.rolling(window=period).sum() / df['volume'].rolling(window=period).sum()
    
    @staticmethod
    def on_balance_volume(df: pd.DataFrame) -> pd.Series:
        """Calculate On-Balance Volume"""
        obv = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
        return obv
    
    @staticmethod
    def accumulation_distribution(df: pd.DataFrame) -> pd.Series:
        """Calculate Accumulation/Distribution Line"""
        clv = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
        ad = (clv * df['volume']).cumsum()
        return ad
    
    @staticmethod
    def average_directional_index(df: pd.DataFrame, period=14) -> pd.DataFrame:
        """Calculate ADX, +DI, -DI"""
        result = df.copy()
        
        # True Range
        high_low = result['high'] - result['low']
        high_close = abs(result['high'] - result['close'].shift())
        low_close = abs(result['low'] - result['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        # Directional Movement
        up_move = result['high'] - result['high'].shift()
        down_move = result['low'].shift() - result['low']
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # Smoothed values
        atr = true_range.rolling(window=period).mean()
        plus_di = 100 * pd.Series(plus_dm).rolling(window=period).mean() / atr
        minus_di = 100 * pd.Series(minus_dm).rolling(window=period).mean() / atr
        
        # ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        result['plus_di'] = plus_di
        result['minus_di'] = minus_di
        result['adx'] = adx
        
        return result


class PatternRecognition:
    """Advanced pattern recognition algorithms"""
    
    @staticmethod
    def find_support_resistance(df: pd.DataFrame, window=20, threshold=0.02) -> Dict:
        """Identify support and resistance levels"""
        # Find local maxima and minima
        highs = df['high'].values
        lows = df['low'].values
        
        resistance_idx = argrelextrema(highs, np.greater, order=window)[0]
        support_idx = argrelextrema(lows, np.less, order=window)[0]
        
        resistance_levels = []
        support_levels = []
        
        # Cluster nearby levels
        for idx in resistance_idx:
            level = highs[idx]
            # Check if similar level exists
            similar = False
            for existing in resistance_levels:
                if abs(level - existing) / existing < threshold:
                    similar = True
                    break
            if not similar:
                resistance_levels.append(level)
        
        for idx in support_idx:
            level = lows[idx]
            similar = False
            for existing in support_levels:
                if abs(level - existing) / existing < threshold:
                    similar = True
                    break
            if not similar:
                support_levels.append(level)
        
        return {
            'resistance': sorted(resistance_levels, reverse=True)[:5],
            'support': sorted(support_levels, reverse=True)[:5]
        }
    
    @staticmethod
    def detect_trend(df: pd.DataFrame, period=20) -> str:
        """Detect current trend direction"""
        closes = df['close'].tail(period)
        
        # Linear regression
        x = np.arange(len(closes))
        slope, _, r_value, _, _ = stats.linregress(x, closes)
        
        # Determine trend
        if r_value ** 2 > 0.7:  # Strong linear relationship
            if slope > 0:
                return "STRONG_UPTREND"
            else:
                return "STRONG_DOWNTREND"
        elif r_value ** 2 > 0.4:
            if slope > 0:
                return "UPTREND"
            else:
                return "DOWNTREND"
        else:
            return "SIDEWAYS"
    
    @staticmethod
    def detect_divergence(df: pd.DataFrame, indicator: pd.Series, period=14) -> List[str]:
        """Detect bullish/bearish divergence"""
        divergences = []
        
        # Find recent peaks in price and indicator
        price_peaks_idx = argrelextrema(df['close'].values, np.greater, order=period)[0]
        indicator_peaks_idx = argrelextrema(indicator.values, np.greater, order=period)[0]
        
        # Check for bearish divergence (price higher high, indicator lower high)
        if len(price_peaks_idx) >= 2 and len(indicator_peaks_idx) >= 2:
            if (df['close'].iloc[price_peaks_idx[-1]] > df['close'].iloc[price_peaks_idx[-2]] and
                indicator.iloc[indicator_peaks_idx[-1]] < indicator.iloc[indicator_peaks_idx[-2]]):
                divergences.append("BEARISH_DIVERGENCE")
        
        # Find troughs
        price_troughs_idx = argrelextrema(df['close'].values, np.less, order=period)[0]
        indicator_troughs_idx = argrelextrema(indicator.values, np.less, order=period)[0]
        
        # Check for bullish divergence (price lower low, indicator higher low)
        if len(price_troughs_idx) >= 2 and len(indicator_troughs_idx) >= 2:
            if (df['close'].iloc[price_troughs_idx[-1]] < df['close'].iloc[price_troughs_idx[-2]] and
                indicator.iloc[indicator_troughs_idx[-1]] > indicator.iloc[indicator_troughs_idx[-2]]):
                divergences.append("BULLISH_DIVERGENCE")
        
        return divergences
    
    @staticmethod
    def detect_candlestick_patterns(df: pd.DataFrame) -> List[Dict]:
        """Detect common candlestick patterns"""
        patterns = []
        
        if len(df) < 3:
            return patterns
        
        # Get last few candles
        o = df['open'].values[-3:]
        h = df['high'].values[-3:]
        l = df['low'].values[-3:]
        c = df['close'].values[-3:]
        
        # Doji
        body = abs(c[-1] - o[-1])
        range_size = h[-1] - l[-1]
        if range_size > 0 and body / range_size < 0.1:
            patterns.append({'pattern': 'DOJI', 'signal': 'NEUTRAL'})
        
        # Hammer (bullish)
        lower_shadow = min(o[-1], c[-1]) - l[-1]
        upper_shadow = h[-1] - max(o[-1], c[-1])
        if lower_shadow > body * 2 and upper_shadow < body * 0.5:
            patterns.append({'pattern': 'HAMMER', 'signal': 'BULLISH'})
        
        # Shooting Star (bearish)
        if upper_shadow > body * 2 and lower_shadow < body * 0.5:
            patterns.append({'pattern': 'SHOOTING_STAR', 'signal': 'BEARISH'})
        
        # Engulfing patterns
        if len(o) >= 2:
            # Bullish engulfing
            if (c[-2] < o[-2] and c[-1] > o[-1] and 
                o[-1] < c[-2] and c[-1] > o[-2]):
                patterns.append({'pattern': 'BULLISH_ENGULFING', 'signal': 'BULLISH'})
            
            # Bearish engulfing
            if (c[-2] > o[-2] and c[-1] < o[-1] and 
                o[-1] > c[-2] and c[-1] < o[-2]):
                patterns.append({'pattern': 'BEARISH_ENGULFING', 'signal': 'BEARISH'})
        
        return patterns
    
    @staticmethod
    def detect_chart_patterns(df: pd.DataFrame, window=50) -> List[str]:
        """Detect chart patterns (head & shoulders, triangles, etc.)"""
        patterns = []
        
        if len(df) < window:
            return patterns
        
        recent = df.tail(window)
        closes = recent['close'].values
        
        # Simple pattern detection using peaks/troughs
        peaks_idx = argrelextrema(closes, np.greater, order=5)[0]
        troughs_idx = argrelextrema(closes, np.less, order=5)[0]
        
        # Head and shoulders (3 peaks with middle highest)
        if len(peaks_idx) >= 3:
            if (closes[peaks_idx[-2]] > closes[peaks_idx[-1]] and 
                closes[peaks_idx[-2]] > closes[peaks_idx[-3]]):
                patterns.append("HEAD_AND_SHOULDERS")
        
        # Double top
        if len(peaks_idx) >= 2:
            if abs(closes[peaks_idx[-1]] - closes[peaks_idx[-2]]) / closes[peaks_idx[-1]] < 0.02:
                patterns.append("DOUBLE_TOP")
        
        # Double bottom
        if len(troughs_idx) >= 2:
            if abs(closes[troughs_idx[-1]] - closes[troughs_idx[-2]]) / closes[troughs_idx[-1]] < 0.02:
                patterns.append("DOUBLE_BOTTOM")
        
        return patterns


class MarketRegime:
    """Market regime detection and classification"""
    
    @staticmethod
    def classify_volatility_regime(returns: pd.Series, threshold_low=0.01, threshold_high=0.03) -> str:
        """Classify volatility regime"""
        vol = returns.std() * np.sqrt(252)  # Annualized
        
        if vol < threshold_low:
            return "LOW_VOLATILITY"
        elif vol > threshold_high:
            return "HIGH_VOLATILITY"
        else:
            return "NORMAL_VOLATILITY"
    
    @staticmethod
    def detect_regime_change(returns: pd.Series, window=60) -> bool:
        """Detect if market regime has changed"""
        if len(returns) < window * 2:
            return False
        
        recent_vol = returns.tail(window).std()
        historical_vol = returns.iloc[-window*2:-window].std()
        
        # Significant change in volatility
        vol_ratio = recent_vol / historical_vol if historical_vol > 0 else 1
        
        return vol_ratio > 1.5 or vol_ratio < 0.67
