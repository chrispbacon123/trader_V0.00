"""
Robust utility functions with comprehensive error handling
"""
from datetime import datetime, timedelta
import sys
import io

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

def safe_download_data(symbol, days):
    """Safely download data with error handling"""
    try:
        _ensure_yfinance()
        end = datetime.now()
        start = end - timedelta(days=int(days * 1.5))
        data = yf.download(symbol, start=start, end=end, progress=False)
        
        if data.empty:
            return None, f"No data available for {symbol}"
        
        return data, None
    except Exception as e:
        return None, f"Error downloading {symbol}: {str(e)[:100]}"

def validate_symbol(symbol):
    """Check if symbol is valid"""
    try:
        data, error = safe_download_data(symbol, 7)
        if error or data is None or len(data) < 3:
            return False, f"Invalid or insufficient data for {symbol}"
        return True, None
    except:
        return False, f"Cannot validate {symbol}"

def suppress_output(func):
    """Decorator to suppress print output"""
    def wrapper(*args, **kwargs):
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            result = func(*args, **kwargs)
            sys.stdout = old_stdout
            return result, None
        except Exception as e:
            sys.stdout = old_stdout
            return None, str(e)
    return wrapper

def safe_run_strategy(strategy_class, symbol, days, capital, **kwargs):
    """Safely run a strategy with error handling"""
    try:
        # Validate symbol first
        valid, error = validate_symbol(symbol)
        if not valid:
            return None, error
        
        # Create strategy
        strategy = strategy_class(symbol, **kwargs)
        strategy.cash = capital
        if hasattr(strategy, 'initial_cash'):
            strategy.initial_cash = capital
        
        # Run backtest
        end = datetime.now()
        start = end - timedelta(days=days)
        
        result = strategy.backtest(start, end)
        return result, None
        
    except Exception as e:
        return None, f"Strategy error: {str(e)[:150]}"

def format_currency(value):
    """Format currency values safely"""
    try:
        return f"${value:,.2f}"
    except:
        return f"${value}"

def safe_calculate_metrics(equity_curve):
    """Safely calculate performance metrics"""
    try:
        import pandas as pd
        import numpy as np
        
        if not equity_curve or len(equity_curve) < 2:
            return {'sharpe': 0, 'max_dd': 0, 'volatility': 0}
        
        df = pd.DataFrame(equity_curve)
        df['Returns'] = df['Value'].pct_change()
        
        sharpe = (df['Returns'].mean() / df['Returns'].std()) * np.sqrt(252) if df['Returns'].std() > 0 else 0
        max_dd = ((df['Value'].cummax() - df['Value']) / df['Value'].cummax()).max() * 100
        volatility = df['Returns'].std() * np.sqrt(252) * 100
        
        return {
            'sharpe': float(sharpe) if not pd.isna(sharpe) else 0,
            'max_dd': float(max_dd) if not pd.isna(max_dd) else 0,
            'volatility': float(volatility) if not pd.isna(volatility) else 0
        }
    except:
        return {'sharpe': 0, 'max_dd': 0, 'volatility': 0}
