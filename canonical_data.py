"""
Canonical Data Fetcher
Ensures clean, standardized data with explicit price series selection and validation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

from core_config import DATA_CFG

# Lazy import yfinance - optional dependency
yf = None


class CanonicalDataFetcher:
    """
    Fetches and standardizes market data with explicit guarantees:
    - Single ticker per fetch (no MultiIndex mixing)
    - Canonical price column (Adj Close preferred)
    - Validated date ranges
    - Clean column names
    """
    
    def __init__(self):
        self.cache: Dict[str, pd.DataFrame] = {}
        
    def fetch_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        validate: bool = True
    ) -> Tuple[pd.DataFrame, Dict[str, any]]:
        """
        Fetch data for a single symbol with full validation
        
        Returns:
            tuple: (DataFrame with standardized columns, metadata dict)
        """
        # Input validation
        symbol = symbol.upper().strip()
        if not symbol:
            raise ValueError("Symbol cannot be empty")
        
        if end_date <= start_date:
            raise ValueError(f"End date {end_date} must be after start date {start_date}")
        
        # Cache key
        cache_key = f"{symbol}_{start_date.date()}_{end_date.date()}"
        
        if cache_key in self.cache:
            df = self.cache[cache_key].copy()
            metadata = self._extract_metadata(df, symbol, start_date, end_date, cached=True)
            return df, metadata
        
        # Fetch from yfinance
        global yf
        if yf is None:
            try:
                import yfinance as yf_module
                yf = yf_module
            except ImportError:
                raise ImportError(
                    "yfinance is required to fetch live data. "
                    "Install it with: pip install yfinance\n"
                    "Or provide data via DataFrame directly to avoid this dependency."
                )
        
        try:
            raw_data = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                progress=False,
                auto_adjust=True  # This prevents MultiIndex with single ticker
            )
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data for {symbol}: {e}")
        
        if raw_data.empty:
            raise ValueError(f"No data returned for {symbol} from {start_date.date()} to {end_date.date()}")
        
        # Handle MultiIndex (can happen even with single ticker in some yfinance versions)
        if isinstance(raw_data.columns, pd.MultiIndex):
            # Flatten MultiIndex by taking the first level
            raw_data.columns = raw_data.columns.get_level_values(0)
        
        # Standardize column names
        df = self._standardize_columns(raw_data)
        
        # Validate required columns
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns for {symbol}: {missing}")
        
        # Add canonical price column
        df = self._add_canonical_price(df)
        
        # Remove NaN rows
        initial_len = len(df)
        df = df.dropna(subset=['Price'])
        final_len = len(df)
        
        if final_len == 0:
            raise ValueError(f"All data for {symbol} contains NaN values")
        
        # Validation
        if validate:
            self._validate_data(df, symbol)
        
        # Cache
        self.cache[cache_key] = df.copy()
        
        # Extract metadata
        metadata = self._extract_metadata(
            df, symbol, start_date, end_date, 
            cached=False, rows_dropped=initial_len-final_len
        )
        
        return df, metadata
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names to Title Case"""
        # yfinance returns: Open, High, Low, Close, Adj Close, Volume
        # Ensure consistent naming
        df = df.copy()
        
        # Rename if needed
        col_mapping = {
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'adj close': 'Adj Close',
            'volume': 'Volume'
        }
        
        df.columns = [col_mapping.get(col.lower(), col) for col in df.columns]
        
        return df
    
    def _add_canonical_price(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add canonical 'Price' column based on config"""
        df = df.copy()
        
        # With auto_adjust=True, Close is already adjusted
        # Use Close as the canonical price
        if 'Close' in df.columns:
            df['Price'] = df['Close']
            df.attrs['price_source'] = 'Close (adjusted)'
        else:
            raise ValueError(
                f"Close column not available in columns: {df.columns.tolist()}"
            )
        
        return df
    
    def _validate_data(self, df: pd.DataFrame, symbol: str):
        """Validate data quality"""
        # Check for negative prices
        price_cols = ['Open', 'High', 'Low', 'Close', 'Price']
        for col in price_cols:
            if col in df.columns:
                if (df[col] <= 0).any():
                    raise ValueError(f"Negative or zero prices found in {col} for {symbol}")
        
        # Check High >= Low
        if (df['High'] < df['Low']).any():
            raise ValueError(f"High < Low detected for {symbol}")
        
        # Check High >= Close >= Low
        if ((df['Close'] > df['High']) | (df['Close'] < df['Low'])).any():
            raise ValueError(f"Close outside High/Low range for {symbol}")
        
        # Check for reasonable volume (allow zero for some assets)
        if 'Volume' in df.columns:
            if (df['Volume'] < 0).any():
                raise ValueError(f"Negative volume detected for {symbol}")
        
        # Check date continuity (warn only)
        date_diffs = df.index.to_series().diff()
        max_gap = date_diffs.max()
        if max_gap > timedelta(days=10):
            warnings.warn(
                f"Large data gap detected for {symbol}: {max_gap.days} days. "
                "This may affect calculations."
            )
    
    def _extract_metadata(
        self, 
        df: pd.DataFrame, 
        symbol: str, 
        start_date: datetime,
        end_date: datetime,
        cached: bool = False,
        rows_dropped: int = 0
    ) -> Dict[str, any]:
        """Extract metadata about the fetched data"""
        return {
            'symbol': symbol,
            'requested_start': start_date.date(),
            'requested_end': end_date.date(),
            'actual_start': df.index.min().date(),
            'actual_end': df.index.max().date(),
            'num_rows': len(df),
            'rows_dropped': rows_dropped,
            'price_source': df.attrs.get('price_source', 'Unknown'),
            'cached': cached,
            'columns': df.columns.tolist()
        }
    
    def get_returns(
        self, 
        df: pd.DataFrame, 
        price_col: str = 'Price',
        kind: str = 'log'
    ) -> pd.Series:
        """
        Calculate returns from canonical price series
        
        Args:
            df: DataFrame with price data
            price_col: Column to use for returns (default: 'Price')
            kind: 'log' (default) or 'simple'
        
        Returns:
            Series with NaN for first value (downstream must dropna())
            
        Note:
            First return is NaN (NOT filled with 0). This is correct.
            Filling first return with 0 contaminates statistics.
        """
        if price_col not in df.columns:
            raise ValueError(f"Price column '{price_col}' not found")
        
        if kind == 'log':
            # Log returns: ln(P_t / P_{t-1})
            returns = np.log(df[price_col] / df[price_col].shift(1))
        elif kind == 'simple':
            # Simple returns: (P_t - P_{t-1}) / P_{t-1}
            returns = df[price_col].pct_change()
        else:
            raise ValueError(f"kind must be 'log' or 'simple', got '{kind}'")
        
        # DO NOT fill NaN - first return must be NaN
        return returns
    
    def clear_cache(self):
        """Clear the data cache"""
        self.cache.clear()
    
    def print_data_summary(self, df: pd.DataFrame, metadata: Dict):
        """Print a summary of fetched data for verification"""
        print(f"\n{'='*80}")
        print(f"DATA SUMMARY: {metadata['symbol']}")
        print(f"{'='*80}")
        print(f"Price Source:    {metadata['price_source']}")
        print(f"Requested:       {metadata['requested_start']} to {metadata['requested_end']}")
        print(f"Actual:          {metadata['actual_start']} to {metadata['actual_end']}")
        print(f"Rows:            {metadata['num_rows']}")
        print(f"Rows Dropped:    {metadata['rows_dropped']}")
        print(f"Cached:          {metadata['cached']}")
        print(f"Current Price:   ${df['Price'].iloc[-1]:.2f}")
        print(f"Price Range:     ${df['Price'].min():.2f} - ${df['Price'].max():.2f}")
        print(f"{'='*80}\n")


# Global fetcher instance
FETCHER = CanonicalDataFetcher()
