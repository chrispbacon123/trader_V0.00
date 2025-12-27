# 🚀 Trading Platform - Quick Start Guide

## 🎯 How to Start

### Windows
```powershell
cd trader_V0.00
python advanced_trading_interface.py
```

### Mac/Linux
```bash
cd ~/lean-trading
python3 advanced_trading_interface.py
```

## 📋 Main Features

### Strategy Operations
1. **Run Single Strategy** - Test one asset with one strategy
2. **Compare All** - See all 4 strategies side-by-side  
3. **Batch Test** - Screen multiple assets
4. **Sector Analysis** - Test across industries

### Portfolio Management  
5. **Create Portfolio** - Multi-strategy allocation
7. **Portfolio Backtest** - Test portfolio performance
8. **Compare Portfolios** - Find best allocations

### Custom Strategy Builder (NEW!)
30. **Create Custom** - Interactive strategy designer
31. **Export for Live** - Python/JSON/LEAN formats
32. **Load & Test** - View saved strategies

### Analysis Tools
11. Technical Analysis Dashboard
15. Market Analytics
16. Correlation Analysis  
25. Parameter Optimization
27. Risk Analysis

## 🎓 Quick Examples

### Test SPY with Simple Strategy
1. Choose option `1`
2. Enter symbol: `SPY`
3. Enter days: `365` (1 year)
4. Choose strategy: `1` (Simple)

### Compare All Strategies
1. Choose option `2`
2. Enter symbol: `AAPL`
3. Enter days: `730` (2 years)
4. View comparison table

### Create Custom Strategy
1. Choose option `30`
2. Name your strategy
3. Select indicators (RSI, MACD, etc.)
4. Define entry/exit rules
5. Set risk parameters
6. Export option `31` for live trading

## 📊 Strategy Guide

| Strategy | Best For | Min Days | Speed |
|----------|----------|----------|-------|
| Simple | Ranging markets | 20 | Fast |
| ML | Trending markets | 60 | Medium |
| Optimized | High volatility | 90 | Slower |
| Short-term | Day trading | 15 | Fast |

## 💡 Asset Types

- **Stocks**: AAPL, MSFT, GOOGL, TSLA, etc.
- **ETFs**: SPY, QQQ, IWM, DIA, VTI, etc.
- **Crypto**: BTC-USD, ETH-USD, SOL-USD, etc.

## 📈 Key Metrics

- **Total Return**: Overall profit/loss %
- **Sharpe Ratio**: Risk-adjusted return (>1 good, >2 excellent)
- **Max Drawdown**: Worst decline
- **Win Rate**: % profitable trades (>50% good)
- **Profit Factor**: Wins/Losses (>1.5 good)

## 🛡️ Best Practices

1. **Start small** - Test with major ETFs (SPY, QQQ)
2. **Use defaults** - Parameters are pre-optimized
3. **Longer is better** - 2+ years for reliable results
4. **Diversify** - Multiple uncorrelated assets
5. **Risk management** - Never risk >2% per trade

## 🚨 Common Issues

### "Insufficient data"
→ Increase days or use Short-term strategy

### "No data available"  
→ Check symbol spelling, try SPY

### Slow performance
→ Reduce date range, use Simple strategy

### Poor results
→ Try different timeframe, check market conditions

## 📤 Export Options

### Results (Option 14)
- CSV format with all trades
- Ready for Excel/Python

### Strategies (Option 31)
- **Python**: Standalone class
- **JSON**: Configuration file
- **LEAN**: QuantConnect algorithm

## 🎯 Common Workflows

### Screen Stocks
1. Batch test (Option 3)
2. Filter by Sharpe ratio
3. Pick top performers

### Build Portfolio
1. Create portfolio (Option 5)
2. Allocate strategies
3. Backtest (Option 7)

### Deploy Live
1. Optimize parameters (Option 25)
2. Create custom strategy (Option 30)
3. Export (Option 31)
4. Implement entry/exit logic
5. Paper trade first!

## ⚠️ Important Notes

- **Test thoroughly** before live trading
- **Paper trade** before using real money
- **Monitor closely** when live
- **Past performance ≠ future results**

## 📚 Resources

- [QuantConnect Docs](https://www.quantconnect.com/docs)
- [Algorithmic Trading](https://www.investopedia.com/algorithmic-trading-4427765)
- Yahoo Finance for data

---

**Type `?` or `help` for in-app help menu**

Happy Trading! 📈

---

## 🔧 Recent Updates (December 2024)

### Data Integrity Fixes ✅
Fixed critical issues in support/resistance and pattern recognition:
- Limited analysis to recent 100 days (prevents old data contamination)
- Added 20% price proximity filter to current price
- Enhanced symbol isolation (no cross-contamination)
- Created test suite: `python test_data_integrity.py`

**Impact:** More accurate market analytics for better trading decisions

### New Dependencies
- `xgboost` - Gradient boosting for ML strategies
- `optuna` - Hyperparameter optimization

### Installation Updated
Windows installation now documented in README.md and APP_INFO.md

**See CHANGELOG.md for complete version history**
