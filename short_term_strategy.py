"""
Short-Term Trading Strategy
Optimized for 7-90 day periods
Uses faster indicators and momentum signals
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class ShortTermStrategy:
    def __init__(self, symbol='SPY', initial_capital=100000, fast_period=5, slow_period=15):
        self.symbol = symbol
        self.initial_capital = initial_capital
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.cash = initial_capital
        
    def download_data(self, start_date, end_date):
        """Download historical data - request extra days to account for trading days only"""
        # Add buffer for weekends/holidays (multiply by 1.5 to get enough trading days)
        days_diff = (end_date - start_date).days
        buffer_start = end_date - timedelta(days=int(days_diff * 1.5))
        
        data = yf.download(self.symbol, start=buffer_start, end=end_date, progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
        return data
    
    def calculate_signals(self, data):
        """Calculate short-term trading signals"""
        df = data.copy()
        
        # Fast and slow EMAs for quick response
        df['EMA_Fast'] = df['Close'].ewm(span=self.fast_period, adjust=False).mean()
        df['EMA_Slow'] = df['Close'].ewm(span=self.slow_period, adjust=False).mean()
        
        # Momentum
        df['Momentum'] = df['Close'].pct_change(periods=3)
        
        # Short-term RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
        rs = gain / loss
        df['RSI_7'] = 100 - (100 / (1 + rs))
        
        # Volume momentum
        df['Volume_MA'] = df['Volume'].rolling(window=10).mean()
        df['Volume_Spike'] = df['Volume'] > (df['Volume_MA'] * 1.5)
        
        # Generate signals
        df['Signal'] = 0
        
        # Buy: Fast EMA crosses above Slow EMA + momentum positive + RSI not overbought
        buy_condition = (
            (df['EMA_Fast'] > df['EMA_Slow']) & 
            (df['EMA_Fast'].shift(1) <= df['EMA_Slow'].shift(1)) &  # Crossover
            (df['Momentum'] > 0) &
            (df['RSI_7'] < 70)
        )
        
        # Sell: Fast EMA crosses below Slow EMA OR RSI overbought OR momentum negative
        sell_condition = (
            ((df['EMA_Fast'] < df['EMA_Slow']) & (df['EMA_Fast'].shift(1) >= df['EMA_Slow'].shift(1))) |
            (df['RSI_7'] > 75) |
            (df['Momentum'] < -0.02)
        )
        
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df
    
    def backtest(self, start_date, end_date):
        """Run backtest"""
        data = self.download_data(start_date, end_date)
        
        # Validate data
        if data is None or len(data) == 0:
            raise ValueError(f"No data available for {self.symbol}")
        
        # Need slow_period + buffer, minimum 10 trading days
        min_required = max(self.slow_period + 5, 10)
        if len(data) < min_required:
            raise ValueError(f"Insufficient data for {self.symbol}. Need at least {min_required} trading days (request 14+ calendar days), got {len(data)}")
        
        data = self.calculate_signals(data)
        
        # Track portfolio
        portfolio_value = self.cash
        shares = 0
        trades = []
        equity_curve = []
        
        for date, row in data.iterrows():
            if pd.isna(row['Signal']):
                continue
            
            price = row['Close']
            signal = row['Signal']
            
            # Buy signal
            if signal == 1 and shares == 0:
                shares = int(self.cash * 0.95 / price)
                cost = shares * price
                self.cash -= cost
                trades.append((date, 'BUY', price, shares))
            
            # Sell signal
            elif signal == -1 and shares > 0:
                proceeds = shares * price
                self.cash += proceeds
                trades.append((date, 'SELL', price, shares))
                shares = 0
            
            # Track value
            portfolio_value = self.cash + (shares * price)
            equity_curve.append({'Date': date, 'Value': portfolio_value})
        
        # Close any open position
        if shares > 0:
            final_price = data['Close'].iloc[-1]
            self.cash += shares * final_price
            portfolio_value = self.cash
        
        return data, trades, portfolio_value, equity_curve
    
    def print_results(self, final_value, trades, equity_curve):
        """Print backtest results"""
        initial_value = 100000
        total_return = ((final_value - initial_value) / initial_value) * 100
        
        # Calculate metrics
        equity_df = pd.DataFrame(equity_curve)
        if len(equity_df) > 1:
            equity_df['Returns'] = equity_df['Value'].pct_change()
            sharpe = (equity_df['Returns'].mean() / equity_df['Returns'].std()) * np.sqrt(252)
            max_dd = ((equity_df['Value'].cummax() - equity_df['Value']) / equity_df['Value'].cummax()).max() * 100
        else:
            sharpe, max_dd = 0, 0
        
        wins = sum(1 for i in range(0, len(trades)-1, 2) if i+1 < len(trades) and trades[i+1][2] > trades[i][2])
        win_rate = (wins / (len(trades)//2) * 100) if len(trades) > 1 else 0
        
        print(f"\n{'='*50}")
        print(f"SHORT-TERM STRATEGY RESULTS - {self.symbol}")
        print(f"{'='*50}")
        print(f"Initial Capital: ${initial_value:,.2f}")
        print(f"Final Value: ${final_value:,.2f}")
        print(f"Total Return: {total_return:.2f}%")
        print(f"Sharpe Ratio: {sharpe:.2f}")
        print(f"Max Drawdown: {max_dd:.2f}%")
        print(f"Total Trades: {len(trades)}")
        print(f"Win Rate: {win_rate:.2f}%")
        
        if len(trades) > 0:
            print(f"\nAll Trades:")
            for trade in trades[-10:]:
                print(f"  {trade[0].strftime('%Y-%m-%d')} {trade[1]:4s} {trade[3]:3d} shares @ ${trade[2]:.2f}")


if __name__ == "__main__":
    # Test with different periods
    print("Testing Short-Term Strategy\n")
    
    for days in [30, 60, 90]:
        print(f"\n{'='*60}")
        print(f"Testing {days}-day period")
        print(f"{'='*60}")
        
        strategy = ShortTermStrategy(symbol='SPY', fast_period=5, slow_period=15)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            data, trades, final_value, equity = strategy.backtest(start_date, end_date)
            strategy.print_results(final_value, trades, equity)
        except Exception as e:
            print(f"Error: {e}")
