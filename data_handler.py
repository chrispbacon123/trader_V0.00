"""
Data Handler Module
Centralized data fetching and management for all strategies
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import warnings
warnings.filterwarnings('ignore')


class DataHandler:
    """Centralized data handling for the trading platform"""
    
    def __init__(self):
        self.cache = {}
        
    def get_stock_data(self, symbol: str, start_date: datetime, end_date: datetime, 
                       interval: str = '1d') -> pd.DataFrame:
        """
        Fetch stock data from Yahoo Finance with error handling
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval (1d, 1h, etc.)
            
        Returns:
            DataFrame with OHLCV data
        """
        cache_key = f"{symbol}_{start_date}_{end_date}_{interval}"
        
        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key].copy()
        
        try:
            # Download data
            df = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                interval=interval,
                progress=False,
                auto_adjust=True
            )
            
            # Handle MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
            
            # Ensure we have required columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_cols:
                if col not in df.columns:
                    raise ValueError(f"Missing required column: {col}")
            
            # Remove any NaN rows
            df = df.dropna()
            
            # Cache the data
            if len(df) > 0:
                self.cache[cache_key] = df.copy()
            
            return df
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_multiple_stocks(self, symbols: List[str], start_date: datetime, 
                           end_date: datetime) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple symbols
        
        Returns:
            Dictionary mapping symbol to DataFrame
        """
        results = {}
        for symbol in symbols:
            df = self.get_stock_data(symbol, start_date, end_date)
            if len(df) > 0:
                results[symbol] = df
        return results
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get the latest price for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d')
            if len(data) > 0:
                return data['Close'].iloc[-1]
        except Exception as e:
            print(f"Error getting latest price for {symbol}: {e}")
        return None
    
    def validate_symbol(self, symbol: str) -> bool:
        """Check if a symbol is valid"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return 'symbol' in info or 'shortName' in info
        except:
            return False
    
    def get_historical_returns(self, symbol: str, periods: int = 252) -> pd.Series:
        """Get historical returns for a symbol"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=periods + 50)
        
        df = self.get_stock_data(symbol, start_date, end_date)
        if len(df) > 0:
            return df['Close'].pct_change().dropna()
        return pd.Series()
    
    def clear_cache(self):
        """Clear the data cache"""
        self.cache.clear()
