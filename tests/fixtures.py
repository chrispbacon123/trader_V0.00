"""
Test fixtures: frozen data and synthetic generators
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path


def create_spy_fixture():
    """
    Create frozen SPY daily OHLCV CSV fixture for deterministic tests
    
    Uses real SPY data from 2024-01-01 to 2024-12-31 (252 trading days)
    """
    # Generate realistic SPY data
    np.random.seed(42)
    
    dates = pd.date_range('2024-01-01', '2024-12-31', freq='B')[:252]
    
    # Start at realistic SPY price
    base_price = 450.0
    
    # Generate realistic returns (mean ~0.05% daily, vol ~1%)
    returns = np.random.normal(0.0005, 0.01, len(dates))
    prices = base_price * np.exp(np.cumsum(returns))
    
    # Create OHLCV
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        # Realistic intraday range
        high = close * (1 + abs(np.random.normal(0, 0.005)))
        low = close * (1 - abs(np.random.normal(0, 0.005)))
        open_price = low + (high - low) * np.random.random()
        volume = int(np.random.uniform(50e6, 150e6))
        
        data.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Open': round(open_price, 2),
            'High': round(high, 2),
            'Low': round(low, 2),
            'Close': round(close, 2),
            'Volume': volume
        })
    
    df = pd.DataFrame(data)
    
    # Save to fixture file
    fixture_path = Path(__file__).parent / 'data' / 'spy_daily.csv'
    df.to_csv(fixture_path, index=False)
    print(f"Created fixture: {fixture_path}")
    print(f"Rows: {len(df)}, Date range: {df['Date'].iloc[0]} to {df['Date'].iloc[-1]}")
    print(f"Price range: ${df['Close'].min():.2f} - ${df['Close'].max():.2f}")
    
    return df


def generate_synthetic_ohlcv(
    num_days: int = 100,
    base_price: float = 100.0,
    volatility: float = 0.01,
    trend: float = 0.0,
    seed: int = None
) -> pd.DataFrame:
    """
    Generate synthetic OHLCV data for edge case testing
    
    Args:
        num_days: Number of trading days
        base_price: Starting price
        volatility: Daily volatility (std of returns)
        trend: Daily drift (mean of returns)
        seed: Random seed for reproducibility
    """
    if seed is not None:
        np.random.seed(seed)
    
    dates = pd.date_range('2024-01-01', periods=num_days, freq='B')
    
    # Generate price series
    returns = np.random.normal(trend, volatility, num_days)
    prices = base_price * np.exp(np.cumsum(returns))
    
    data = []
    for date, close in zip(dates, prices):
        high = close * (1 + abs(np.random.normal(0, volatility * 0.5)))
        low = close * (1 - abs(np.random.normal(0, volatility * 0.5)))
        open_price = low + (high - low) * np.random.random()
        volume = int(np.random.uniform(1e6, 10e6))
        
        data.append({
            'Date': date,
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': close,
            'Volume': volume
        })
    
    return pd.DataFrame(data).set_index('Date')


def generate_flat_prices(num_days: int = 50, price: float = 100.0) -> pd.DataFrame:
    """Generate flat price series for edge case testing"""
    dates = pd.date_range('2024-01-01', periods=num_days, freq='B')
    
    data = []
    for date in dates:
        data.append({
            'Date': date,
            'Open': price,
            'High': price * 1.001,
            'Low': price * 0.999,
            'Close': price,
            'Volume': 1000000
        })
    
    return pd.DataFrame(data).set_index('Date')


def generate_with_gaps(num_days: int = 100, gap_indices: list = None) -> pd.DataFrame:
    """Generate data with missing dates (gaps)"""
    if gap_indices is None:
        gap_indices = [10, 20, 30]  # Remove these indices
    
    df = generate_synthetic_ohlcv(num_days, seed=42)
    
    # Remove gap indices
    all_indices = list(range(len(df)))
    keep_indices = [i for i in all_indices if i not in gap_indices]
    
    return df.iloc[keep_indices]


def generate_with_nans(num_days: int = 100, nan_indices: list = None) -> pd.DataFrame:
    """Generate data with NaN values"""
    if nan_indices is None:
        nan_indices = [5, 15, 25]
    
    df = generate_synthetic_ohlcv(num_days, seed=42)
    
    # Introduce NaNs
    for idx in nan_indices:
        if idx < len(df):
            df.iloc[idx, df.columns.get_loc('Close')] = np.nan
    
    return df


def generate_short_history(num_days: int = 20) -> pd.DataFrame:
    """Generate very short history (< minimum lookback)"""
    return generate_synthetic_ohlcv(num_days, seed=42)


if __name__ == '__main__':
    # Create the SPY fixture
    create_spy_fixture()
    
    # Test synthetic generators
    print("\nTesting synthetic generators:")
    
    df_synthetic = generate_synthetic_ohlcv(100, seed=42)
    print(f"Synthetic: {len(df_synthetic)} days")
    
    df_flat = generate_flat_prices(50)
    print(f"Flat prices: {len(df_flat)} days, all at ${df_flat['Close'].iloc[0]:.2f}")
    
    df_gaps = generate_with_gaps(100, [10, 20, 30])
    print(f"With gaps: {len(df_gaps)} days (removed 3)")
    
    df_nans = generate_with_nans(100, [5, 15, 25])
    print(f"With NaNs: {df_nans['Close'].isna().sum()} NaN values")
    
    df_short = generate_short_history(15)
    print(f"Short history: {len(df_short)} days")
