"""
Enhanced utilities with comprehensive error handling and validation
"""
import yfinance as yf
import pandas as pd
import numpy as np
import re
import os
import json
import time
from datetime import datetime, timedelta
from functools import wraps
import urllib.request

class ValidationError(Exception):
    """Custom validation error"""
    pass

class NetworkError(Exception):
    """Custom network error"""
    pass

def check_internet_connection():
    """Check if internet connection is available"""
    try:
        urllib.request.urlopen('https://www.google.com', timeout=3)
        return True
    except:
        return False

def validate_symbol(symbol):
    """Validate symbol format"""
    if not symbol:
        raise ValidationError("Symbol cannot be empty")
    
    if not isinstance(symbol, str):
        raise ValidationError("Symbol must be a string")
    
    # Remove whitespace
    symbol = symbol.strip().upper()
    
    # Check for invalid characters
    if not re.match(r'^[A-Z0-9\-\.]+$', symbol):
        raise ValidationError(f"Invalid symbol format: {symbol}")
    
    # Check length
    if len(symbol) > 10:
        raise ValidationError(f"Symbol too long (max 10 chars): {symbol}")
    
    return symbol

def validate_days(days, min_days=1, max_days=3650):
    """Validate day count"""
    try:
        if isinstance(days, str):
            days = int(days)
        elif not isinstance(days, int):
            days = int(days)
    except (ValueError, TypeError):
        raise ValidationError(f"Days must be a number, got: {days}")
    
    if days < min_days:
        raise ValidationError(f"Days must be at least {min_days}, got: {days}")
    
    if days > max_days:
        raise ValidationError(f"Days cannot exceed {max_days}, got: {days}")
    
    return days

def validate_capital(capital, min_capital=100, max_capital=1e12):
    """Validate capital amount"""
    try:
        if isinstance(capital, str):
            capital = float(capital.replace(',', '').replace('$', ''))
        elif not isinstance(capital, (int, float)):
            capital = float(capital)
    except (ValueError, TypeError):
        raise ValidationError(f"Capital must be a number, got: {capital}")
    
    if capital < min_capital:
        raise ValidationError(f"Capital must be at least ${min_capital}, got: ${capital}")
    
    if capital > max_capital:
        raise ValidationError(f"Capital too large (max ${max_capital:,.0f}), got: ${capital:,.0f}")
    
    return capital

def validate_percentage(pct, min_pct=0, max_pct=100):
    """Validate percentage"""
    try:
        if isinstance(pct, str):
            pct = float(pct.replace('%', '').strip())
        elif not isinstance(pct, (int, float)):
            pct = float(pct)
    except (ValueError, TypeError):
        raise ValidationError(f"Percentage must be a number, got: {pct}")
    
    if pct < min_pct:
        raise ValidationError(f"Percentage must be at least {min_pct}%, got: {pct}%")
    
    if pct > max_pct:
        raise ValidationError(f"Percentage cannot exceed {max_pct}%, got: {pct}%")
    
    # Return as decimal (0.15 instead of 15)
    if pct > 1 and pct <= 100:
        return pct / 100
    return pct

def validate_portfolio_name(name):
    """Validate portfolio name"""
    if not name:
        raise ValidationError("Portfolio name cannot be empty")
    
    if not isinstance(name, str):
        raise ValidationError("Portfolio name must be a string")
    
    name = name.strip()
    
    # Check for invalid characters (allow alphanumeric, spaces, hyphens, underscores)
    if not re.match(r'^[A-Za-z0-9 _-]+$', name):
        raise ValidationError(f"Portfolio name contains invalid characters: {name}")
    
    if len(name) > 50:
        raise ValidationError(f"Portfolio name too long (max 50 chars)")
    
    return name

def retry_with_backoff(func, max_retries=3, initial_delay=1):
    """Retry function with exponential backoff"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        delay = initial_delay
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2
        
        raise last_error
    
    return wrapper

@retry_with_backoff
def download_data_with_retry(symbol, start, end):
    """Download data with retry logic"""
    if not check_internet_connection():
        raise NetworkError("No internet connection available")
    
    data = yf.download(symbol, start=start, end=end, progress=False)
    
    if data.empty:
        raise ValidationError(f"No data available for {symbol}")
    
    return data

def safe_json_load(filename, default=None):
    """Safely load JSON file"""
    if not os.path.exists(filename):
        return default if default is not None else {}
    
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"⚠️  Warning: {filename} corrupted, using backup")
        backup = filename + '.backup'
        if os.path.exists(backup):
            with open(backup, 'r') as f:
                return json.load(f)
        return default if default is not None else {}
    except Exception as e:
        print(f"⚠️  Warning: Error loading {filename}: {e}")
        return default if default is not None else {}

def safe_json_save(filename, data):
    """Safely save JSON file with backup"""
    # Create backup of existing file
    if os.path.exists(filename):
        backup = filename + '.backup'
        try:
            with open(filename, 'r') as f:
                backup_data = f.read()
            with open(backup, 'w') as f:
                f.write(backup_data)
        except:
            pass
    
    # Save new data
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")
        return False

def check_disk_space(min_mb=100):
    """Check available disk space"""
    try:
        stat = os.statvfs('.')
        available_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
        return available_mb >= min_mb
    except:
        return True  # Assume sufficient space if check fails

def format_time_remaining(seconds):
    """Format seconds into human-readable time"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds/60)}m {int(seconds%60)}s"
    else:
        return f"{int(seconds/3600)}h {int((seconds%3600)/60)}m"

def calculate_metrics_safe(equity_curve):
    """Safely calculate performance metrics"""
    try:
        if not equity_curve or len(equity_curve) < 2:
            return {
                'sharpe': 0.0,
                'max_dd': 0.0,
                'volatility': 0.0,
                'total_return': 0.0,
                'win_rate': 0.0
            }
        
        df = pd.DataFrame(equity_curve)
        
        if 'Value' not in df.columns:
            return {
                'sharpe': 0.0,
                'max_dd': 0.0,
                'volatility': 0.0,
                'total_return': 0.0,
                'win_rate': 0.0
            }
        
        df['Returns'] = df['Value'].pct_change()
        
        # Sharpe ratio
        mean_return = df['Returns'].mean()
        std_return = df['Returns'].std()
        sharpe = (mean_return / std_return) * np.sqrt(252) if std_return > 0 else 0
        
        # Max drawdown
        cummax = df['Value'].cummax()
        drawdown = (cummax - df['Value']) / cummax
        max_dd = drawdown.max() * 100
        
        # Volatility
        volatility = std_return * np.sqrt(252) * 100
        
        # Total return
        if len(df) > 0:
            initial = df['Value'].iloc[0]
            final = df['Value'].iloc[-1]
            total_return = ((final - initial) / initial) * 100 if initial > 0 else 0
        else:
            total_return = 0
        
        # Win rate
        positive_returns = df['Returns'] > 0
        win_rate = positive_returns.sum() / len(df['Returns']) * 100 if len(df['Returns']) > 0 else 0
        
        return {
            'sharpe': float(sharpe) if not pd.isna(sharpe) else 0.0,
            'max_dd': float(max_dd) if not pd.isna(max_dd) else 0.0,
            'volatility': float(volatility) if not pd.isna(volatility) else 0.0,
            'total_return': float(total_return) if not pd.isna(total_return) else 0.0,
            'win_rate': float(win_rate) if not pd.isna(win_rate) else 0.0
        }
    except Exception as e:
        print(f"⚠️  Metrics calculation error: {str(e)[:50]}")
        return {
            'sharpe': 0.0,
            'max_dd': 0.0,
            'volatility': 0.0,
            'total_return': 0.0,
            'win_rate': 0.0
        }

def progress_bar(current, total, prefix='', suffix='', length=50):
    """Display progress bar"""
    percent = current / total
    filled = int(length * percent)
    bar = '█' * filled + '░' * (length - filled)
    print(f'\r{prefix} |{bar}| {percent*100:.1f}% {suffix}', end='', flush=True)
    if current == total:
        print()

class ProgressTracker:
    """Track progress of operations"""
    def __init__(self, total, description="Progress"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
    
    def update(self, increment=1):
        """Update progress"""
        self.current += increment
        elapsed = time.time() - self.start_time
        
        if self.current > 0:
            avg_time = elapsed / self.current
            remaining = avg_time * (self.total - self.current)
            eta = format_time_remaining(remaining)
        else:
            eta = "calculating..."
        
        progress_bar(self.current, self.total, 
                    prefix=self.description,
                    suffix=f'ETA: {eta}')
    
    def finish(self):
        """Mark as complete"""
        self.current = self.total
        elapsed = time.time() - self.start_time
        self.update(0)
        print(f"✅ Complete in {format_time_remaining(elapsed)}")



def validate_backtest_data(symbol, start_date, end_date, min_days=20):
    """Validate data availability before running backtest"""
    import yfinance as yf
    from datetime import timedelta
    
    # Request more calendar days to ensure enough trading days
    buffer_start = start_date - timedelta(days=int((end_date - start_date).days * 0.5))
    
    try:
        data = yf.download(symbol, start=buffer_start, end=end_date, progress=False)
        
        if data is None or len(data) == 0:
            return False, f"No data available for {symbol}"
        
        trading_days = len(data)
        if trading_days < min_days:
            return False, f"Insufficient data: {trading_days} trading days (need {min_days})"
        
        return True, f"✓ {trading_days} trading days available"
        
    except Exception as e:
        return False, f"Error downloading data: {e}"
