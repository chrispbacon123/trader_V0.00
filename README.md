# Advanced Quantitative Trading Platform 🚀

Professional-grade algorithmic trading platform with ML-powered strategies, advanced analytics, and comprehensive risk management.

## Quick Start

```bash
# Clone repository
git clone https://github.com/chrispbacon123/trader_V0.00.git
cd trader_V0.00

# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install pandas numpy scikit-learn yfinance matplotlib seaborn plotly scipy joblib ta-lib

# Launch the platform
./launch.sh  # Or: python advanced_trading_interface.py
```

## Features

### 📊 Core Operations
- Single & Portfolio Strategy Backtesting
- Multi-Strategy Comparison
- Technical Analysis Dashboard

### 🔨 Strategy Development
- Custom Strategy Builder
- Parameter Optimization
- Market Screening & Analytics

### 📈 Advanced Analytics
- **Monte Carlo Simulation** - Probabilistic risk modeling
- **Walk-Forward Analysis** - Out-of-sample validation
- **Advanced Risk Metrics** - VaR, CVaR, Calmar, Omega, Ulcer Index

### 🛡️ Risk Management
- Position sizing algorithms
- Drawdown controls
- Volatility adjustment
- Correlation analysis

## Installation

The quick start above covers installation. For manual setup:

```bash
# Option 1: Using virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install pandas numpy scikit-learn yfinance matplotlib seaborn plotly scipy joblib ta-lib

# Option 2: Using system Python (not recommended)
pip install --user pandas numpy scikit-learn yfinance matplotlib seaborn plotly scipy joblib ta-lib
```

**Note:** The platform requires Python 3.8+ and uses a virtual environment to avoid conflicts.

## Supported Assets
- Stocks (NYSE, NASDAQ)
- ETFs
- Cryptocurrencies (BTC-USD, ETH-USD, etc.)
- Forex pairs
- Indices (SPY, QQQ, DIA)

## Built-in Strategies
- Simple Mean Reversion
- ML Trading (Random Forest)
- Optimized ML
- Short Term Mean Reversion

## Advanced Risk Metrics
- Value at Risk (Historical, Parametric, Cornish-Fisher)
- Conditional VaR (Expected Shortfall)
- Maximum Drawdown & Duration
- Sharpe, Sortino, Calmar Ratios
- Omega Ratio, Ulcer Index
- Tail Ratio, Gain/Pain Ratio

## Educational Use Only ⚠️
- Past performance ≠ future results
- For research and learning
- Not financial advice
- Test thoroughly before live trading

## Quick Example

1. Run: `python3 advanced_trading_interface.py`
2. Choose option `1` (Run Single Strategy)
3. Enter symbol: `SPY`
4. Select strategy: `1` (Mean Reversion)
5. Use default dates (press Enter)
6. View results!

## Support

- GitHub Issues
- In-app help (option `16`)

## Troubleshooting

### "ModuleNotFoundError: No module named 'pandas'"
Make sure you've activated the virtual environment:
```bash
source venv/bin/activate  # On Mac/Linux
```

### "Insufficient data" errors
- Short-term strategies need 20+ calendar days
- ML strategies need 90+ calendar days  
- Optimized ensemble needs 250+ calendar days
- Use longer date ranges or request extended historical data

### Permission denied when running ./launch.sh
```bash
chmod +x launch.sh
./launch.sh
```

### General data issues
- Check internet connection
- Verify symbol is correct (e.g., "AAPL" not "Apple")
- Try a different symbol (SPY usually works)
- Weekend/market closed? Use earlier dates

---

**Always validate strategies thoroughly before deploying real capital.**
