"""
Advanced Data Manager with caching, validation, and multiple data sources
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import warnings
import os
import json
from pathlib import Path

warnings.filterwarnings('ignore')

# Lazy import yfinance - only when needed
yf = None

def _ensure_yfinance():
    """Lazy load yfinance when needed for live data"""
    global yf
    if yf is None:
        try:
            import yfinance as yf_module
            yf = yf_module
        except ImportError:
            raise ImportError(
                "yfinance is required to fetch live market data.\n"
                "Install it with: pip install yfinance\n"
                "Or provide data via CSV/DataFrame to avoid this dependency."
            )


class DataManager:
    """Advanced data management with caching and validation"""
    
    def __init__(self, cache_dir: str = "data_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.data_cache = {}
        
    def get_cache_path(self, symbol: str, start_date: str, end_date: str) -> Path:
        """Generate cache file path"""
        cache_file = f"{symbol}_{start_date}_{end_date}.csv"
        return self.cache_dir / cache_file
    
    def load_from_cache(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Load data from cache if available and fresh"""
        cache_path = self.get_cache_path(symbol, start_date, end_date)
        
        if cache_path.exists():
            try:
                # Check if cache is less than 1 day old
                cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
                if cache_age < timedelta(days=1):
                    df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                    return df
            except Exception as e:
                print(f"Cache read error: {e}")
        
        return None
    
    def save_to_cache(self, df: pd.DataFrame, symbol: str, start_date: str, end_date: str):
        """Save data to cache"""
        cache_path = self.get_cache_path(symbol, start_date, end_date)
        try:
            df.to_csv(cache_path)
        except Exception as e:
            print(f"Cache save error: {e}")
    
    def fetch_data(self, symbol: str, start_date: str, end_date: str,
                   use_cache: bool = True) -> pd.DataFrame:
        """Fetch market data with caching"""
        
        # Check cache first
        if use_cache:
            cached_data = self.load_from_cache(symbol, start_date, end_date)
            if cached_data is not None:
                return cached_data
        
        # Fetch from Yahoo Finance
        try:
            _ensure_yfinance()
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, auto_adjust=True)
            
            if df.empty:
                raise ValueError(f"No data available for {symbol}")
            
            # Save to cache
            if use_cache:
                self.save_to_cache(df, symbol, start_date, end_date)
            
            return df
            
        except Exception as e:
            raise ValueError(f"Error fetching data for {symbol}: {e}")
    
    def fetch_multiple(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple symbols"""
        data = {}
        for symbol in symbols:
            try:
                data[symbol] = self.fetch_data(symbol, start_date, end_date)
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
        return data
    
    def validate_data(self, df: pd.DataFrame, symbol: str) -> Tuple[bool, List[str]]:
        """Validate data quality"""
        issues = []
        
        if df.empty:
            return False, ["DataFrame is empty"]
        
        # Check for required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing columns: {missing_cols}")
        
        # Check for missing values
        null_counts = df[required_cols].isnull().sum()
        if null_counts.any():
            issues.append(f"Missing values: {null_counts[null_counts > 0].to_dict()}")
        
        # Check for zero/negative prices
        price_cols = ['Open', 'High', 'Low', 'Close']
        for col in price_cols:
            if col in df.columns and (df[col] <= 0).any():
                issues.append(f"Zero/negative prices in {col}")
        
        # Check for logical price relationships
        if all(col in df.columns for col in ['High', 'Low', 'Open', 'Close']):
            if (df['High'] < df['Low']).any():
                issues.append("High < Low detected")
            if (df['High'] < df['Open']).any() or (df['High'] < df['Close']).any():
                issues.append("High < Open/Close detected")
            if (df['Low'] > df['Open']).any() or (df['Low'] > df['Close']).any():
                issues.append("Low > Open/Close detected")
        
        # Check for suspicious volume
        if 'Volume' in df.columns:
            if (df['Volume'] == 0).sum() > len(df) * 0.1:
                issues.append("More than 10% of days have zero volume")
        
        return len(issues) == 0, issues
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare data"""
        df = df.copy()
        
        # Forward fill missing values (max 3 days)
        df = df.fillna(method='ffill', limit=3)
        
        # Remove remaining rows with NaN
        df = df.dropna()
        
        # Ensure proper data types
        numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Sort by date
        df = df.sort_index()
        
        return df
    
    def add_technical_indicators(self, df: pd.DataFrame, 
                                 indicators: List[str] = None) -> pd.DataFrame:
        """Add technical indicators to dataframe"""
        df = df.copy()
        
        if indicators is None:
            indicators = ['sma', 'ema', 'rsi', 'macd', 'bbands', 'atr']
        
        try:
            # Simple Moving Averages
            if 'sma' in indicators:
                df['SMA_20'] = df['Close'].rolling(window=20).mean()
                df['SMA_50'] = df['Close'].rolling(window=50).mean()
                df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            # Exponential Moving Averages
            if 'ema' in indicators:
                df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
                df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
            
            # RSI
            if 'rsi' in indicators:
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD
            if 'macd' in indicators:
                exp1 = df['Close'].ewm(span=12, adjust=False).mean()
                exp2 = df['Close'].ewm(span=26, adjust=False).mean()
                df['MACD'] = exp1 - exp2
                df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
                df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
            
            # Bollinger Bands
            if 'bbands' in indicators:
                df['BB_Middle'] = df['Close'].rolling(window=20).mean()
                df['BB_Std'] = df['Close'].rolling(window=20).std()
                df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * 2)
                df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * 2)
            
            # ATR (Average True Range)
            if 'atr' in indicators:
                high_low = df['High'] - df['Low']
                high_close = np.abs(df['High'] - df['Close'].shift())
                low_close = np.abs(df['Low'] - df['Close'].shift())
                ranges = pd.concat([high_low, high_close, low_close], axis=1)
                true_range = ranges.max(axis=1)
                df['ATR'] = true_range.rolling(14).mean()
            
            # Volume indicators
            if 'volume' in indicators:
                df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
                df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
            
            # Momentum
            if 'momentum' in indicators:
                df['Momentum'] = df['Close'].pct_change(periods=10)
                df['ROC'] = ((df['Close'] - df['Close'].shift(10)) / df['Close'].shift(10)) * 100
            
            # Stochastic Oscillator
            if 'stoch' in indicators:
                low_14 = df['Low'].rolling(window=14).min()
                high_14 = df['High'].rolling(window=14).max()
                df['Stoch_K'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
                df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()
            
        except Exception as e:
            print(f"Error adding indicators: {e}")
        
        return df
    
    def resample_data(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """Resample data to different timeframe"""
        
        resample_map = {
            '1min': '1T',
            '5min': '5T',
            '15min': '15T',
            '30min': '30T',
            '1hour': '1H',
            '4hour': '4H',
            'daily': 'D',
            'weekly': 'W',
            'monthly': 'M'
        }
        
        freq = resample_map.get(timeframe, 'D')
        
        resampled = df.resample(freq).agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        })
        
        return resampled.dropna()
    
    def get_market_info(self, symbol: str) -> Dict:
        """Get detailed market information"""
        try:
            _ensure_yfinance()
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'beta': info.get('beta', 1.0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'avg_volume': info.get('averageVolume', 0),
                '52w_high': info.get('fiftyTwoWeekHigh', 0),
                '52w_low': info.get('fiftyTwoWeekLow', 0),
            }
        except Exception as e:
            print(f"Error getting market info for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    def clear_cache(self, older_than_days: int = 7):
        """Clear old cache files"""
        cutoff_time = datetime.now() - timedelta(days=older_than_days)
        
        for cache_file in self.cache_dir.glob("*.csv"):
            file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if file_time < cutoff_time:
                cache_file.unlink()
                print(f"Deleted old cache: {cache_file.name}")
