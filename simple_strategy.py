"""
Simple Mean Reversion Strategy using QuantConnect-style API
This can be adapted for LEAN when Docker is set up
"""

import pandas as pd

# Lazy import yfinance - optional dependency
yf = None

def _ensure_yfinance():
    """Lazy load yfinance when needed"""
    global yf
    if yf is None:
        try:
            import yfinance as yf_module
            yf = yf_module
        except ImportError:
            raise ImportError(
                "yfinance is required for data download. "
                "Install with: pip install yfinance"
            )
    return yf
import numpy as np
from datetime import datetime, timedelta

class SimpleMeanReversionStrategy:
    def __init__(self, symbol='SPY', initial_capital=100000, lookback=20, std_dev=2):
        self.symbol = symbol
        self.initial_capital = initial_capital
        self.lookback = lookback
        self.std_dev = std_dev
        self.position = 0
        self.cash = initial_capital
        self.equity = []
        
    def download_data(self, start_date, end_date):
        """Download historical data - request extra days to account for trading days only"""
        yf_module = _ensure_yfinance()
        # Add buffer for weekends/holidays (multiply by 1.5 to get enough trading days)
        days_diff = (end_date - start_date).days
        buffer_start = end_date - timedelta(days=int(days_diff * 1.5))
        
        data = yf_module.download(self.symbol, start=buffer_start, end=end_date, progress=False)
        # Flatten multi-index if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
        return data
    
    def calculate_signals(self, data):
        """Calculate mean reversion signals"""
        df = data.copy()
        df['SMA'] = df['Close'].rolling(window=self.lookback).mean()
        df['STD'] = df['Close'].rolling(window=self.lookback).std()
        df['Upper'] = df['SMA'] + (self.std_dev * df['STD'])
        df['Lower'] = df['SMA'] - (self.std_dev * df['STD'])
        
        # Generate signals using vectorized operations
        df['Signal'] = 0
        conditions = [
            (df['Close'] < df['Lower']),
            (df['Close'] > df['Upper'])
        ]
        choices = [1, -1]
        df['Signal'] = np.select(conditions, choices, default=0)
        
        return df
    
    def backtest(self, start_date, end_date, data=None):
        """
        Run backtest
        
        Args:
            start_date: Start date for backtest
            end_date: End date for backtest
            data: Optional pre-fetched DataFrame. If None, will download.
        """
        # Use provided data or download
        if data is None:
            data = self.download_data(start_date, end_date)
        else:
            # Normalize provided data
            from data_normalization import DataNormalizer
            normalizer = DataNormalizer()
            data, _ = normalizer.normalize_market_data(
                data.copy(), 
                symbol=self.symbol, 
                require_ohlc=False
            )
        
        # Validate data
        if data is None or len(data) == 0:
            raise ValueError(f"No data available for {self.symbol}")
        
        # Need lookback + buffer, minimum 20 trading days
        min_required = max(self.lookback + 10, 20)
        if len(data) < min_required:
            raise ValueError(f"Insufficient data for {self.symbol}. Need at least {min_required} trading days (request 30+ calendar days), got {len(data)}")
        
        data = self.calculate_signals(data)
        
        # Track portfolio value
        portfolio_value = self.cash
        shares = 0
        trades = []
        
        for date, row in data.iterrows():
            if pd.isna(row['Signal']) or date < data.index[self.lookback]:
                continue
                
            price = row['Close']
            
            # Execute trades with fractional share support
            if row['Signal'] == 1 and shares == 0:  # Buy
                from sizing import calculate_shares
                
                target_cash = self.cash * 0.95
                shares, _ = calculate_shares(target_cash, price)
                
                if shares > 0:
                    cost = shares * price
                    self.cash -= cost
                    trades.append((date, 'BUY', price, shares))
                
            elif row['Signal'] == -1 and shares > 0:  # Sell
                proceeds = shares * price
                self.cash += proceeds
                trades.append((date, 'SELL', price, shares))
                shares = 0
            
            # Calculate portfolio value
            portfolio_value = self.cash + (shares * price)
            self.equity.append({'Date': date, 'Value': portfolio_value})
        
        # Close any open position
        if shares > 0:
            final_price = data['Close'].iloc[-1]
            self.cash += shares * final_price
            portfolio_value = self.cash
        
        return data, trades, portfolio_value, self.equity
    
    def print_results(self, final_value, trades):
        """Print backtest results"""
        initial_value = 100000
        total_return = ((final_value - initial_value) / initial_value) * 100
        
        print(f"\n{'='*50}")
        print(f"BACKTEST RESULTS - {self.symbol}")
        print(f"{'='*50}")
        print(f"Initial Capital: ${initial_value:,.2f}")
        print(f"Final Portfolio Value: ${final_value:,.2f}")
        print(f"Total Return: {total_return:.2f}%")
        print(f"Total Trades: {len(trades)}")
        print(f"\nRecent Trades:")
        from core_config import PORTFOLIO_CFG
        shares_fmt = ".4f" if PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED else ".0f"
        for trade in trades[-5:]:
            print(f"  {trade[0].strftime('%Y-%m-%d')} - {trade[1]} {trade[3]:{shares_fmt}} shares @ ${trade[2]:.2f}")

if __name__ == "__main__":
    # Initialize strategy
    strategy = SimpleMeanReversionStrategy(symbol='SPY', lookback=20, std_dev=2)
    
    # Run backtest
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    print("Running backtest...")
    data, trades, final_value = strategy.backtest(start_date, end_date)
    
    # Print results
    strategy.print_results(final_value, trades)
