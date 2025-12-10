# 📈 Advanced Trading Platform

A comprehensive algorithmic trading platform with ML-powered strategies, portfolio management, and custom strategy builder.

## ✨ Features

- **4 Built-in Strategies**: Simple, ML, Optimized ML, Short-term
- **Custom Strategy Builder**: Create and export your own strategies
- **Portfolio Management**: Multi-strategy allocation
- **Technical Analysis**: Real-time charts and indicators
- **Live Trading Export**: Python, JSON, QuantConnect LEAN

## 🚀 Quick Start

```bash
cd ~/lean-trading
python3 advanced_trading_interface.py
```

Or:
```bash
./run.sh
```

## 📖 Documentation

See [QUICKSTART.md](QUICKSTART.md) for detailed guide.

## 🎯 Main Features

### Strategy Testing
1. Single asset testing
2. Compare all strategies
3. Batch test multiple assets
4. Sector analysis

### Portfolio Management
5-10. Create, view, test, compare portfolios

### Custom Strategy Builder (NEW!)
30. **Create Custom** - Interactive designer
31. **Export for Live** - Python/JSON/LEAN formats
32. **Load & Test** - Review strategies

### Analysis Tools
- Technical analysis
- Market analytics
- Correlation analysis
- Parameter optimization
- Risk analysis

## 📊 Built-in Strategies

| Strategy | Best For | Min Days |
|----------|----------|----------|
| Simple Mean Reversion | Ranging markets | 20 |
| ML Trading | Trending markets | 60 |
| Optimized ML | High volatility | 90 |
| Short-term | Day trading | 15 |

## 💡 Quick Examples

### Test a Strategy
```
Option: 1
Symbol: SPY
Days: 365
Strategy: 1 (Simple)
```

### Create Custom Strategy
```
Option: 30
Name: My Strategy
Indicators: RSI, MACD, Volume
Entry Rules: Define conditions
Exit Rules: Define exits
Risk: Set parameters
Export: Option 31
```

### Build Portfolio
```
Option: 5
Name: Tech Portfolio
Capital: 100000
Allocation: Simple 25%, ML 40%, Optimized 35%
Assets: AAPL, MSFT, GOOGL
```

## 🛠️ Technology

- Python 3.8+
- yfinance (data)
- scikit-learn, xgboost (ML)
- pandas, numpy (analysis)

## 📦 Project Structure

```
lean-trading/
├── advanced_trading_interface.py  # Main app
├── strategy_builder.py            # Custom builder
├── [strategy files]               # Built-in strategies
├── custom_strategies/             # Your strategies
├── strategy_exports/              # Exported code
├── README.md                      # This file
├── QUICKSTART.md                  # Detailed guide
└── run.sh                         # Quick launcher
```

## ⚠️ Important

**Educational use only**
- Not financial advice
- Test thoroughly before live trading
- Paper trade first
- Risk only what you can afford to lose

## 📈 Performance Metrics

All backtests show:
- Total Return
- Sharpe Ratio
- Max Drawdown
- Win Rate
- Profit Factor
- Trade Count

## 🚨 Known Limitations

1. Daily data only (no intraday)
2. ML strategies need 60+ days data
3. Simplified transaction costs
4. Custom strategies need manual implementation

## 🔜 Coming Soon

- Walk-forward analysis
- Monte Carlo simulation
- Intraday data
- More ML models
- Live trading integration

## 📄 License

MIT License - Personal use

## 🙏 Built With

- yfinance - Market data
- scikit-learn - Machine learning
- QuantConnect - LEAN framework

---

**Quick Links:**
- 📖 [Detailed Guide](QUICKSTART.md)
- 🚀 [Start Now](#quick-start)
- 🎓 [Examples](#quick-examples)

**Ready? Run:**
```bash
cd ~/lean-trading && ./run.sh
```

*Version 2.0*
