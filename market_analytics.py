"""
Advanced Market Analytics and Indicators
Comprehensive technical analysis, market regime detection, and correlation analysis
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class MarketAnalytics:
    """Advanced market analysis tools"""
    
    def __init__(self, symbol: str = None):
        self.symbol = symbol
        self.data = None
        
    def fetch_data(self, period: str = '1y'):
        """Fetch market data"""
        self.data = yf.download(self.symbol, period=period, progress=False)
        if isinstance(self.data.columns, pd.MultiIndex):
            self.data.columns = self.data.columns.droplevel(1)
        return self.data
    
    def detect_market_regime(self, data: pd.DataFrame = None) -> Dict:
        """
        Detect current market regime from provided data or self.data
        Returns: trending_up, trending_down, ranging, volatile
        """
        df = data if data is not None else self.data
        if df is None or len(df) < 50:
            return {'regime': 'unknown', 'confidence': 0}
        
        return self._analyze_regime(df)
    
    def market_regime(self) -> Dict:
        """
        Detect current market regime using self.data
        Returns: trending_up, trending_down, ranging, volatile
        """
        if self.data is None or len(self.data) < 50:
            return {'regime': 'unknown', 'confidence': 0}
        
        return self._analyze_regime(self.data)
    
    def _analyze_regime(self, df: pd.DataFrame) -> Dict:
        df = df.copy()
        
        # Calculate indicators
        df['SMA_20'] = df['Close'].rolling(20).mean()
        df['SMA_50'] = df['Close'].rolling(50).mean()
        df['Returns'] = df['Close'].pct_change()
        df['Volatility'] = df['Returns'].rolling(20).std()
        
        # Get recent data
        recent = df.iloc[-20:]
        current_price = df['Close'].iloc[-1]
        sma_20 = df['SMA_20'].iloc[-1]
        sma_50 = df['SMA_50'].iloc[-1]
        volatility = recent['Volatility'].mean()
        
        # Trend detection
        price_vs_sma20 = (current_price - sma_20) / sma_20
        price_vs_sma50 = (current_price - sma_50) / sma_50
        sma_trend = (sma_20 - sma_50) / sma_50
        
        # Determine regime
        if abs(sma_trend) < 0.02 and volatility < 0.015:
            regime = 'ranging'
            confidence = 0.7
        elif volatility > 0.03:
            regime = 'volatile'
            confidence = 0.8
        elif price_vs_sma20 > 0.03 and sma_trend > 0.02:
            regime = 'trending_up'
            confidence = 0.85
        elif price_vs_sma20 < -0.03 and sma_trend < -0.02:
            regime = 'trending_down'
            confidence = 0.85
        else:
            regime = 'transitioning'
            confidence = 0.5
        
        return {
            'regime': regime,
            'confidence': confidence,
            'volatility': volatility,
            'trend_strength': abs(sma_trend),
            'price_vs_sma20': price_vs_sma20,
            'price_vs_sma50': price_vs_sma50
        }
    
    def support_resistance_levels(self, window: int = 20, num_levels: int = 3) -> Dict[str, List[float]]:
        """Find key support and resistance levels"""
        if self.data is None or len(self.data) < window:
            return {'support': [], 'resistance': []}
        
        df = self.data.copy()
        
        # Find local minima (support) and maxima (resistance)
        support_levels = []
        resistance_levels = []
        
        for i in range(window, len(df) - window):
            # Check if local minimum
            if df['Low'].iloc[i] == df['Low'].iloc[i-window:i+window].min():
                support_levels.append(df['Low'].iloc[i])
            
            # Check if local maximum
            if df['High'].iloc[i] == df['High'].iloc[i-window:i+window].max():
                resistance_levels.append(df['High'].iloc[i])
        
        # Cluster nearby levels
        support_levels = self._cluster_levels(support_levels, num_levels)
        resistance_levels = self._cluster_levels(resistance_levels, num_levels)
        
        return {
            'support': sorted(support_levels)[:num_levels],
            'resistance': sorted(resistance_levels, reverse=True)[:num_levels]
        }
    
    def _cluster_levels(self, levels: List[float], num_clusters: int) -> List[float]:
        """Cluster nearby price levels"""
        if len(levels) == 0:
            return []
        
        levels = sorted(levels)
        if len(levels) <= num_clusters:
            return levels
        
        # Simple clustering by grouping nearby levels
        clustered = []
        current_cluster = [levels[0]]
        threshold = np.std(levels) * 0.5
        
        for level in levels[1:]:
            if level - current_cluster[-1] < threshold:
                current_cluster.append(level)
            else:
                clustered.append(np.mean(current_cluster))
                current_cluster = [level]
        
        if current_cluster:
            clustered.append(np.mean(current_cluster))
        
        return clustered
    
    def fibonacci_levels(self, lookback: int = 100) -> Dict[str, float]:
        """Calculate Fibonacci retracement levels"""
        if self.data is None or len(self.data) < lookback:
            return {}
        
        recent_data = self.data.iloc[-lookback:]
        high = recent_data['High'].max()
        low = recent_data['Low'].min()
        diff = high - low
        
        levels = {
            '0.0': high,
            '23.6': high - 0.236 * diff,
            '38.2': high - 0.382 * diff,
            '50.0': high - 0.5 * diff,
            '61.8': high - 0.618 * diff,
            '78.6': high - 0.786 * diff,
            '100.0': low
        }
        
        return levels
    
    def volume_profile(self, bins: int = 20) -> pd.DataFrame:
        """Calculate volume profile"""
        if self.data is None:
            return pd.DataFrame()
        
        df = self.data.copy()
        
        # Create price bins
        price_range = df['High'].max() - df['Low'].min()
        bin_size = price_range / bins
        
        # Calculate volume at each price level
        df['Price_Bin'] = ((df['Close'] - df['Low'].min()) / bin_size).astype(int)
        volume_profile = df.groupby('Price_Bin').agg({
            'Volume': 'sum',
            'Close': 'mean'
        }).sort_values('Volume', ascending=False)
        
        volume_profile.columns = ['Total_Volume', 'Avg_Price']
        
        return volume_profile.head(10)
    
    def momentum_analysis(self) -> Dict[str, float]:
        """Comprehensive momentum indicators"""
        if self.data is None or len(self.data) < 50:
            return {}
        
        df = self.data.copy()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Stochastic
        low_14 = df['Low'].rolling(window=14).min()
        high_14 = df['High'].rolling(window=14).max()
        stoch_k = 100 * (df['Close'] - low_14) / (high_14 - low_14)
        stoch_d = stoch_k.rolling(window=3).mean()
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        
        # ADX (Average Directional Index)
        high_diff = df['High'].diff()
        low_diff = -df['Low'].diff()
        
        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
        
        tr = pd.concat([
            df['High'] - df['Low'],
            abs(df['High'] - df['Close'].shift()),
            abs(df['Low'] - df['Close'].shift())
        ], axis=1).max(axis=1)
        
        atr = tr.rolling(window=14).mean()
        plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=14).mean()
        
        return {
            'RSI': rsi.iloc[-1],
            'Stochastic_K': stoch_k.iloc[-1],
            'Stochastic_D': stoch_d.iloc[-1],
            'MACD': macd.iloc[-1],
            'MACD_Signal': macd_signal.iloc[-1],
            'MACD_Histogram': (macd - macd_signal).iloc[-1],
            'ADX': adx.iloc[-1],
            'Plus_DI': plus_di.iloc[-1],
            'Minus_DI': minus_di.iloc[-1]
        }
    
    def correlation_matrix(self, symbols: List[str], period: str = '3mo') -> pd.DataFrame:
        """Calculate correlation matrix for multiple symbols"""
        data_dict = {}
        
        for symbol in symbols:
            try:
                df = yf.download(symbol, period=period, progress=False)
                if not df.empty:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.droplevel(1)
                    data_dict[symbol] = df['Close'].pct_change()
            except:
                continue
        
        if len(data_dict) < 2:
            return pd.DataFrame()
        
        # Combine data
        combined = pd.DataFrame(data_dict).dropna()
        
        # Calculate correlation
        corr_matrix = combined.corr()
        
        return corr_matrix
    
    def risk_metrics(self) -> Dict[str, float]:
        """Calculate comprehensive risk metrics"""
        if self.data is None or len(self.data) < 30:
            return {}
        
        df = self.data.copy()
        returns = df['Close'].pct_change().dropna()
        
        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(252)
        
        # Downside deviation
        downside_returns = returns[returns < 0]
        downside_dev = downside_returns.std() * np.sqrt(252)
        
        # Value at Risk (95% confidence)
        var_95 = np.percentile(returns, 5)
        
        # Conditional VaR (Expected Shortfall)
        cvar_95 = returns[returns <= var_95].mean()
        
        # Maximum Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Calmar Ratio
        annual_return = returns.mean() * 252
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Sortino Ratio
        sortino_ratio = (annual_return / downside_dev) if downside_dev > 0 else 0
        
        return {
            'volatility': volatility,
            'downside_deviation': downside_dev,
            'var_95': var_95,
            'cvar_95': cvar_95,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'sortino_ratio': sortino_ratio
        }
    
    def print_comprehensive_analysis(self):
        """Print complete market analysis"""
        print(f"\n{'═'*90}")
        print(f"COMPREHENSIVE MARKET ANALYSIS: {self.symbol}")
        print(f"{'═'*90}")
        
        # Market Regime
        regime = self.market_regime()
        print(f"\n📊 MARKET REGIME")
        print(f"   Current Regime: {regime['regime'].upper()}")
        print(f"   Confidence: {regime['confidence']*100:.1f}%")
        print(f"   Volatility: {regime['volatility']*100:.2f}%")
        print(f"   Trend Strength: {regime['trend_strength']*100:.2f}%")
        
        # Support/Resistance
        levels = self.support_resistance_levels()
        print(f"\n🎯 KEY LEVELS")
        print(f"   Resistance: {', '.join([f'${x:.2f}' for x in levels['resistance']])}")
        print(f"   Support: {', '.join([f'${x:.2f}' for x in levels['support']])}")
        
        # Fibonacci
        fib = self.fibonacci_levels()
        if fib:
            print(f"\n📐 FIBONACCI RETRACEMENTS")
            for level, price in fib.items():
                print(f"   {level:>5s}: ${price:.2f}")
        
        # Momentum
        momentum = self.momentum_analysis()
        if momentum:
            print(f"\n⚡ MOMENTUM INDICATORS")
            for name, value in momentum.items():
                print(f"   {name:20s}: {value:.2f}")
        
        # Risk Metrics
        risk = self.risk_metrics()
        if risk:
            print(f"\n🛡️  RISK METRICS")
            for name, value in risk.items():
                print(f"   {name:20s}: {value:.4f}")
