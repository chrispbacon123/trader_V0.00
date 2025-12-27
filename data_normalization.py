"""
Robust Data Normalization
Handles all data shape variations and ensures consistent schema across the platform
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
import warnings


class DataContractError(Exception):
    """Raised when data cannot be normalized to meet platform requirements"""
    pass


class DataNormalizer:
    """
    Single source of truth for data normalization across the platform.
    Every feature must use this before processing data.
    """
    
    @staticmethod
    def normalize_market_data(
        df: pd.DataFrame,
        symbol: str = None,
        require_ohlc: bool = False
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Normalize any market data DataFrame to platform standard.
        
        Args:
            df: Input DataFrame (can be MultiIndex, missing columns, etc.)
            symbol: Optional symbol name for MultiIndex extraction
            require_ohlc: If True, require OHLC columns; if False, derive from Price
        
        Returns:
            tuple: (normalized_df, metadata_dict)
            
        Guarantees:
            - Always has 'Price' column
            - Clean datetime index (sorted, no duplicates)
            - Consistent column names
            - No NaNs in Price column
            - OHLC columns present (derived if needed)
        
        Raises:
            DataContractError: If data cannot be normalized
        """
        if df is None or df.empty:
            raise DataContractError("Input DataFrame is None or empty")
        
        metadata = {
            'warnings': [],
            'transformations': [],
            'original_shape': df.shape,
            'original_columns': list(df.columns)
        }
        
        # Step 1: Handle MultiIndex columns
        df, meta = DataNormalizer._flatten_multiindex(df, symbol)
        metadata['transformations'].extend(meta.get('transformations', []))
        metadata['warnings'].extend(meta.get('warnings', []))
        
        # Step 2: Standardize column names
        df, meta = DataNormalizer._standardize_column_names(df)
        metadata['transformations'].extend(meta.get('transformations', []))
        
        # Step 3: Create canonical Price column
        df, meta = DataNormalizer._create_canonical_price(df)
        metadata['transformations'].extend(meta.get('transformations', []))
        metadata['price_source'] = meta.get('price_source', 'Unknown')
        
        # Step 4: Clean index
        df, meta = DataNormalizer._clean_index(df)
        metadata['transformations'].extend(meta.get('transformations', []))
        metadata['warnings'].extend(meta.get('warnings', []))
        
        # Step 5: Handle missing OHLC columns
        df, meta = DataNormalizer._ensure_ohlc(df, require_ohlc)
        metadata['transformations'].extend(meta.get('transformations', []))
        metadata['warnings'].extend(meta.get('warnings', []))
        
        # Step 6: Clean NaNs
        df, meta = DataNormalizer._clean_nans(df)
        metadata['transformations'].extend(meta.get('transformations', []))
        metadata['rows_dropped'] = meta.get('rows_dropped', 0)
        
        # Step 7: Validate result
        DataNormalizer._validate_normalized_data(df)
        
        metadata['final_shape'] = df.shape
        metadata['final_columns'] = list(df.columns)
        
        return df, metadata
    
    @staticmethod
    def _flatten_multiindex(
        df: pd.DataFrame, 
        symbol: str = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """Handle yfinance MultiIndex columns"""
        metadata = {'transformations': [], 'warnings': []}
        
        if not isinstance(df.columns, pd.MultiIndex):
            return df, metadata
        
        metadata['transformations'].append('Flattened MultiIndex columns')
        
        # If symbol provided, extract that ticker
        if symbol and symbol in df.columns.get_level_values(1):
            df = df.xs(symbol, axis=1, level=1)
            metadata['transformations'].append(f'Extracted ticker: {symbol}')
        else:
            # Take first ticker or flatten to first level
            if df.columns.nlevels == 2:
                # Get unique tickers
                tickers = df.columns.get_level_values(1).unique()
                if len(tickers) > 1:
                    metadata['warnings'].append(
                        f'Multiple tickers found: {list(tickers)}. Using first: {tickers[0]}'
                    )
                df.columns = df.columns.get_level_values(0)
            else:
                df.columns = df.columns.get_level_values(0)
        
        return df, metadata
    
    @staticmethod
    def _standardize_column_names(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """Standardize column names to Title Case"""
        metadata = {'transformations': []}
        
        col_mapping = {
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'adj close': 'Adj Close',
            'adjusted close': 'Adj Close',
            'adjclose': 'Adj Close',
            'volume': 'Volume',
            'price': 'Price'
        }
        
        new_cols = []
        renamed = False
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if col_lower in col_mapping:
                new_cols.append(col_mapping[col_lower])
                if col_mapping[col_lower] != col:
                    renamed = True
            else:
                new_cols.append(col)
        
        df.columns = new_cols
        
        if renamed:
            metadata['transformations'].append('Standardized column names')
        
        return df, metadata
    
    @staticmethod
    def _create_canonical_price(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """Create canonical Price column with fallback logic"""
        metadata = {'transformations': [], 'price_source': None}
        
        # If Price already exists and is valid, keep it
        if 'Price' in df.columns and not df['Price'].isna().all():
            metadata['price_source'] = 'Existing Price column'
            return df, metadata
        
        # Priority: Adj Close > Close > fallback error
        if 'Adj Close' in df.columns and not df['Adj Close'].isna().all():
            df['Price'] = df['Adj Close']
            metadata['price_source'] = 'Adj Close'
            metadata['transformations'].append('Created Price from Adj Close')
        elif 'Close' in df.columns and not df['Close'].isna().all():
            df['Price'] = df['Close']
            metadata['price_source'] = 'Close'
            metadata['transformations'].append('Created Price from Close')
        else:
            # Last resort: check for any numeric column that could be price
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                # Use first non-NaN numeric column
                for col in numeric_cols:
                    if not df[col].isna().all() and (df[col] > 0).any():
                        df['Price'] = df[col]
                        metadata['price_source'] = f'Fallback: {col}'
                        metadata['transformations'].append(f'Created Price from {col} (fallback)')
                        break
            
            if 'Price' not in df.columns:
                raise DataContractError(
                    f"Cannot create canonical Price column. Available columns: {df.columns.tolist()}"
                )
        
        return df, metadata
    
    @staticmethod
    def _clean_index(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """Clean and validate index"""
        metadata = {'transformations': [], 'warnings': []}
        
        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            try:
                df.index = pd.to_datetime(df.index, utc=True)
                metadata['transformations'].append('Converted index to DatetimeIndex')
            except Exception as e:
                raise DataContractError(f"Cannot convert index to datetime: {e}")
        
        # Remove timezone info for consistency (work with tz-naive datetimes)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
            metadata['transformations'].append('Removed timezone info from index')
        
        # Sort by date
        if not df.index.is_monotonic_increasing:
            df = df.sort_index()
            metadata['transformations'].append('Sorted index')
        
        # Remove duplicates
        if df.index.duplicated().any():
            dup_count = df.index.duplicated().sum()
            df = df[~df.index.duplicated(keep='last')]
            metadata['transformations'].append(f'Removed {dup_count} duplicate dates')
            metadata['warnings'].append(f'Removed {dup_count} duplicate dates (kept last)')
        
        return df, metadata
    
    @staticmethod
    def _ensure_ohlc(df: pd.DataFrame, require_ohlc: bool) -> Tuple[pd.DataFrame, Dict]:
        """Ensure OHLC columns exist, derive from Price if needed"""
        metadata = {'transformations': [], 'warnings': []}
        
        required_ohlc = ['Open', 'High', 'Low', 'Close']
        missing_ohlc = [col for col in required_ohlc if col not in df.columns]
        
        if not missing_ohlc:
            return df, metadata
        
        if require_ohlc:
            raise DataContractError(f"Required OHLC columns missing: {missing_ohlc}")
        
        # Derive from Price (flat day assumption)
        if 'Price' in df.columns:
            for col in missing_ohlc:
                df[col] = df['Price']
            metadata['transformations'].append(
                f'Derived {missing_ohlc} from Price (flat day assumption)'
            )
            metadata['warnings'].append(
                'OHLC derived from Price - intraday data not available'
            )
        
        # Ensure Volume exists (default to 0 if missing)
        if 'Volume' not in df.columns:
            df['Volume'] = 0
            metadata['transformations'].append('Added Volume column (default 0)')
            metadata['warnings'].append('Volume data not available')
        
        return df, metadata
    
    @staticmethod
    def _clean_nans(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """Remove rows with NaN in Price column"""
        metadata = {'transformations': [], 'rows_dropped': 0}
        
        initial_len = len(df)
        
        # Drop rows where Price is NaN
        if 'Price' in df.columns:
            df = df.dropna(subset=['Price'])
        
        rows_dropped = initial_len - len(df)
        
        if rows_dropped > 0:
            metadata['transformations'].append(f'Dropped {rows_dropped} rows with NaN Price')
            metadata['rows_dropped'] = rows_dropped
        
        return df, metadata
    
    @staticmethod
    def _validate_normalized_data(df: pd.DataFrame):
        """Final validation of normalized data"""
        # Must have Price
        if 'Price' not in df.columns:
            raise DataContractError("Normalized data missing Price column")
        
        # Must have data
        if df.empty:
            raise DataContractError("Normalized data is empty after cleaning")
        
        # Price must not have NaNs
        if df['Price'].isna().any():
            raise DataContractError("Price column contains NaN values after normalization")
        
        # Price must be positive
        if (df['Price'] <= 0).any():
            raise DataContractError("Price column contains non-positive values")
        
        # Must have datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            raise DataContractError("Index is not DatetimeIndex")
    
    @staticmethod
    def print_normalization_report(metadata: Dict):
        """Print human-readable normalization report"""
        print(f"\n{'='*80}")
        print("DATA NORMALIZATION REPORT")
        print(f"{'='*80}")
        print(f"Original Shape:  {metadata['original_shape']}")
        print(f"Final Shape:     {metadata['final_shape']}")
        print(f"Rows Dropped:    {metadata.get('rows_dropped', 0)}")
        print(f"Price Source:    {metadata.get('price_source', 'Unknown')}")
        
        if metadata.get('transformations'):
            print(f"\nTransformations Applied:")
            for t in metadata['transformations']:
                print(f"  • {t}")
        
        if metadata.get('warnings'):
            print(f"\n⚠️  Warnings:")
            for w in metadata['warnings']:
                print(f"  • {w}")
        
        print(f"{'='*80}\n")


def normalize_run_record(record: Dict) -> Dict:
    """
    Normalize strategy run records to consistent schema.
    Handles backward compatibility with old history formats.
    
    Required fields after normalization:
        - timestamp
        - symbol
        - strategy
        - return_pct
    """
    normalized = {}
    
    # Timestamp
    normalized['timestamp'] = record.get('timestamp', record.get('date', 'Unknown'))
    
    # Symbol
    normalized['symbol'] = record.get('symbol', record.get('ticker', 'Unknown'))
    
    # Strategy name
    normalized['strategy'] = record.get(
        'strategy',
        record.get('strategy_name', record.get('model', 'Unknown'))
    )
    
    # Return
    normalized['return_pct'] = record.get(
        'return_pct',
        record.get('return', record.get('pnl_pct', 0.0))
    )
    
    # Optional fields (preserve if present)
    optional_fields = [
        'confidence', 'sharpe', 'max_drawdown', 'win_rate',
        'total_trades', 'final_portfolio_value', 'notes'
    ]
    
    for field in optional_fields:
        if field in record:
            normalized[field] = record[field]
    
    return normalized


def safe_column_access(df: pd.DataFrame, col: str, fallback: str = None) -> pd.Series:
    """
    Safely access DataFrame column with fallback.
    
    Usage:
        high = safe_column_access(df, 'High', 'Price')
        # Returns df['High'] if exists, else df['Price'], else raises clear error
    """
    if col in df.columns:
        return df[col]
    
    if fallback and fallback in df.columns:
        return df[fallback]
    
    available = df.columns.tolist()
    raise DataContractError(
        f"Column '{col}' not found. "
        f"Available: {available}. "
        f"Did you forget to normalize the data?"
    )
