# How to Run the Trading Platform

## Quick Start

### 1. Validate Everything Works
```bash
python run_comprehensive_validation.py
```
✅ Should show: "ALL VALIDATION TESTS PASSED"

### 2. Run the Main Interface
```bash
python advanced_trading_interface.py
```

Or use the trading CLI:
```bash
python trading_cli.py
```

## Python Path Setup (Windows)

If you get "Python was not found", use the full path:
```powershell
& 'C:\Users\Chris\AppData\Local\Programs\Python\Python312\python.exe' run_comprehensive_validation.py
```

Or add to PATH permanently:
1. Search "Environment Variables" in Windows
2. Edit System Environment Variables
3. Add: `C:\Users\Chris\AppData\Local\Programs\Python\Python312`
4. Restart terminal

## What Each Script Does

### Core Validation
- `run_comprehensive_validation.py` - Tests all features without network (17 tests)

### Main Interfaces
- `advanced_trading_interface.py` - Full portfolio manager with menu
- `trading_cli.py` - Simple command-line interface

### Analysis Tools
- `market_analytics.py` - Run as script for market analysis
- `system_status.py` - Check system configuration

### Testing (in `tests/` folder)
- `test_phase1_correctness.py` - Core correctness tests
- `test_comprehensive.py` - Full system tests
- `test_execution_algorithms.py` - Order execution tests
- `test_strategy_fractional.py` - Fractional shares tests

## Current System Status

✅ **Data Normalization**: Complete - handles all edge cases  
✅ **Canonical Data**: Returns calculated correctly (no synthetic zeros)  
✅ **Validated Indicators**: RSI/Stoch/MACD/ADX all bounded correctly  
✅ **Validated Risk**: Volatility/VaR/CVaR/Sharpe/Sortino with correct units  
✅ **Regime Classification**: Coherent with ADX, realistic thresholds  
✅ **Key Levels**: S/R and Fibonacci with auditable anchors  
✅ **Fractional Shares**: Configurable, end-to-end support  
✅ **History Schema**: Backward compatible with normalization  

## Common Issues

### KeyError: 'High' / 'Close' / 'Price'
**Fixed!** All modules now use `DataNormalizer.normalize_market_data()` before processing.

If you see this error in a new module, add:
```python
from data_normalization import DataNormalizer

df, metadata = DataNormalizer.normalize_market_data(raw_df, symbol='SPY')
# Now safe to use df['Price'], df['High'], etc.
```

### "yfinance is required"
The validation script doesn't need yfinance. But if running strategies with live data:
```bash
pip install yfinance
```

Or use CSV data - normalization handles both.

### Tests failing
Check your Python version:
```bash
python --version  # Should be 3.8+
```

Install requirements:
```bash
pip install -r requirements.txt
```

## Documentation

- `DATA_NORMALIZATION_COMPLETE.md` - Data normalization details
- `README.md` - Project overview
- `QUICK_START_GUIDE.md` - Getting started
- `DOCUMENTATION_INDEX_V0.04.md` - All documentation

## Example Usage

### 1. Validate the System
```bash
python run_comprehensive_validation.py
```

### 2. Analyze a Symbol
```python
from market_analytics import MarketAnalytics

analytics = MarketAnalytics('SPY')
analytics.fetch_data(period='1y')
analytics.print_comprehensive_analysis('SPY')
```

### 3. Run a Strategy
```python
from ml_strategy import MLTradingStrategy
from datetime import datetime, timedelta

strategy = MLTradingStrategy(symbol='SPY')
end = datetime.now()
start = end - timedelta(days=365)

data, trades, final_value = strategy.backtest(start, end)
strategy.print_results(final_value, trades)
```

### 4. Check Fractional Shares Config
```python
from core_config import PORTFOLIO_CFG

print(f"Fractional shares: {PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED}")
print(f"Min cash buffer: ${PORTFOLIO_CFG.MIN_CASH_BUFFER}")
```

## Tips

1. **Always run validation first** to ensure system is healthy
2. **Use normalized data** - call `DataNormalizer.normalize_market_data()` before processing
3. **Check metadata** - normalization returns useful warnings and transformations
4. **History is backward compatible** - old records work seamlessly

## Support

Platform is now **production-grade**:
- Mathematically correct (all indicators validated)
- Internally consistent (no unit confusion)
- Fully test-backed (17+ tests passing)
- Handles edge cases (MultiIndex, Price-only, short history)
- Clear error messages (no cryptic KeyErrors)

Run `run_comprehensive_validation.py` anytime to verify system health!

---
Last Updated: December 24, 2024
