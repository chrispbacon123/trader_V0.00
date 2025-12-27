# Advanced Quantitative Trading Platform - User Guide

**Version:** V0.20  
**Last Updated:** December 2024  
**Copyright © 2024-2025 chrispbacon123. All Rights Reserved.**

> ⚠️ **PROPRIETARY SOFTWARE** - This software is for personal, non-commercial, home use only.  
> See [LICENSE](LICENSE) for full terms and restrictions.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Running the Platform](#running-the-platform)
3. [Main Features](#main-features)
4. [Data Requirements](#data-requirements)
5. [Common Workflows](#common-workflows)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Quick Start

### 30-Second Start

```bash
# 1. Navigate to the platform directory
cd trader_V0.00

# 2. Run the platform
python advanced_trading_interface.py

# Or use the CLI
python trading_cli.py analyze SPY --days 90
```

### First Run Example

1. Run: `python advanced_trading_interface.py`
2. Choose option `1` (Run Single Strategy)
3. Enter symbol: `SPY`
4. Select strategy: `1` (Mean Reversion)
5. Use default dates (press Enter)
6. View results!

---

## Running the Platform

### Option 1: Interactive Interface
```bash
python advanced_trading_interface.py
```

### Option 2: Command Line Interface
```bash
python trading_cli.py
```

### Option 3: Using Launch Scripts
```bash
# Mac/Linux
./launch.sh

# Windows
START.sh
```

---

## Main Features

### 1. Strategy Testing (Options 1-4)

**Single Strategy Backtest**
- Test individual strategies on specific assets
- Customize parameters and date ranges
- View detailed performance metrics

**Compare All Strategies**
- Run multiple strategies on the same asset
- Side-by-side performance comparison
- Identify best performers

**Batch Testing**
- Test strategies across multiple assets
- Sector and industry analysis
- Comprehensive performance overview

### 2. Portfolio Management (Options 5-10)

**Create Custom Portfolios**
- Mix multiple strategies
- Set allocation percentages
- Define target returns

**Portfolio Backtesting**
- Test across different market conditions
- Track risk-adjusted returns
- Analyze diversification benefits

**Minimum Requirements:**
- 120+ calendar days for portfolio backtests
- At least 2 strategies recommended

### 3. Technical Analysis (Option 11)

**Real-time Indicators:**
- RSI, MACD, Bollinger Bands
- Volume analysis
- Support/Resistance levels
- Market regime detection

**Market Analytics:**
- Trend identification
- Volatility analysis
- Pattern recognition

### 4. Custom Strategy Builder (Option 30)

**Interactive Designer:**
1. Choose base strategy type (trend/mean reversion/ML)
2. Add technical indicators
3. Set entry and exit rules
4. Define risk parameters
5. Backtest and refine

**Save and Reuse:**
- Save strategies for later use
- Export to multiple formats
- Share configurations

### 5. Strategy Export (Option 31)

**Export Formats:**
- Python class format
- JSON configuration
- QuantConnect LEAN format

**Deployment Package Includes:**
- Configuration files
- Trained ML models (if applicable)
- Deployment scripts
- Documentation

---

## Data Requirements

### Minimum Periods

| Strategy Type | Minimum Days | Recommended Days |
|--------------|--------------|------------------|
| Simple Strategy | 30 calendar days | 90+ days |
| Short-Term Strategy | 30 calendar days | 90+ days |
| ML Strategy | 90 calendar days | 180+ days |
| Optimized ML | 180 calendar days | 365+ days |
| Portfolio | 120 calendar days | 365+ days |

**Note:** More data typically leads to more reliable results

### Supported Assets

- **Stocks:** Any US ticker (AAPL, GOOGL, MSFT, etc.)
- **ETFs:** SPY, QQQ, IWM, DIA, etc.
- **Cryptocurrencies:** BTC-USD, ETH-USD, etc.
- **Forex:** Major currency pairs
- **Indices:** S&P 500, NASDAQ, Dow Jones

---

## Common Workflows

### Workflow 1: Test a Stock

```
1. Start platform: python advanced_trading_interface.py
2. Choose Option 1 (Run Strategy)
3. Select strategy: ML Strategy (option 2)
4. Enter symbol: AAPL
5. Enter period: 365 days
6. Review results and metrics
```

### Workflow 2: Find Best Strategy for an Asset

```
1. Choose Option 2 (Compare All Strategies)
2. Enter symbol: SPY
3. Enter period: 365 days
4. Review comparison table
5. Note best performer
```

### Workflow 3: Build Custom Strategy

```
1. Choose Option 30 (Strategy Builder)
2. Name your strategy
3. Select type and indicators
4. Set entry/exit rules
5. Define risk parameters
6. Backtest with test data
7. Export (Option 31) if satisfied
```

### Workflow 4: Create Portfolio

```
1. Choose Option 5 (Create Portfolio)
2. Set name and initial capital
3. Allocate percentage to each strategy
4. Set target return (optional)
5. Choose Option 7 to backtest
6. Review performance metrics
```

### Workflow 5: Optimize Strategy Parameters

```
1. Choose Option 25 (Parameter Optimization)
2. Select strategy to optimize
3. Define parameter ranges
4. Set number of trials (15-30 recommended)
5. Wait for optimization (5-15 minutes)
6. Review best parameters
7. Save optimized strategy
```

---

## Advanced Features

### Monte Carlo Simulation (Option 29)

**Purpose:** Probabilistic risk modeling

**How to Use:**
1. Select Option 29 from main menu
2. Choose strategy and asset
3. Set number of simulations (1000-10000)
4. Review probability distributions
5. Analyze risk metrics

**Outputs:**
- Distribution of possible returns
- Confidence intervals
- Risk of ruin estimates
- Downside risk analysis

### Walk-Forward Analysis (Option 28)

**Purpose:** Out-of-sample validation

**How to Use:**
1. Select Option 28
2. Choose strategy
3. Define in-sample/out-of-sample windows
4. Run analysis
5. Compare in-sample vs out-of-sample performance

**Benefits:**
- Detect overfitting
- More realistic performance estimates
- Time-series validation

### Market Regime Detection (Option 15)

**Purpose:** Identify market conditions

**Regimes Detected:**
- Bull market (uptrend + low volatility)
- Bear market (downtrend + high volatility)
- Sideways/Ranging (no trend)

**Uses:**
- Adjust strategy selection
- Modify position sizing
- Set appropriate risk parameters

### Parameter Optimization (Option 25)

**Purpose:** Find optimal strategy parameters

**Method:**
- Uses Optuna for hyperparameter tuning
- Bayesian optimization
- Efficient search space exploration

**Time Required:**
- 5-15 minutes depending on:
  - Number of trials (15-30 typical)
  - Strategy complexity
  - Data size

---

## Troubleshooting

### Common Errors and Solutions

#### "Insufficient data"
**Cause:** Not enough trading days for strategy requirements

**Solution:**
- Increase lookback period
- Request more calendar days
- Note: 365 calendar days ≈ 252 trading days

#### "No data available"
**Cause:** Invalid symbol or data source issue

**Solution:**
- Verify ticker symbol is correct
- Check internet connection
- Try a different symbol (SPY usually works)
- Check if market is open (use earlier dates on weekends)

#### "ModuleNotFoundError: No module named 'pandas'"
**Cause:** Virtual environment not activated or dependencies not installed

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

#### Strategy fails on certain assets
**Cause:** Insufficient data, volatility, or trading history

**Solution:**
- Try longer period (365+ days)
- Try different asset (more liquid stocks)
- Check asset is actively traded

#### Performance is slow
**Cause:** Large dataset or complex optimization

**Solution:**
- Reduce number of optimization trials
- Use shorter backtest period initially
- Close other applications
- Ensure sufficient RAM (4GB+ recommended)

### Data Download Issues

**Yahoo Finance Errors:**
- Check internet connection
- Verify symbol exists and is active
- Wait a few minutes (rate limiting)
- Try VPN if region-blocked

**Weekend/Market Closed:**
- Use historical dates (not current day)
- Set end date to last trading day

### Permission Errors (Mac/Linux)

```bash
chmod +x launch.sh
chmod +x *.sh
```

---

## Best Practices

### General Guidelines

1. **Always backtest with 1+ years** of data before live trading
2. **Test on multiple assets** to ensure robustness
3. **Paper trade first** with any new strategy
4. **Monitor performance** regularly
5. **Adjust for market conditions** using regime detection
6. **Start small** with real capital
7. **Set stop losses** for risk management

### Risk Management

- **Position Sizing:** Default 95% is aggressive; consider 50-70% for live trading
- **Drawdown Limits:** Set maximum acceptable drawdown (e.g., 20%)
- **Diversification:** Use portfolios with multiple strategies
- **Correlation:** Monitor correlation between strategies

### Strategy Development

1. **Start Simple:** Begin with simple mean reversion
2. **Understand Metrics:** Learn Sharpe ratio, drawdown, win rate
3. **Avoid Overfitting:** Use walk-forward analysis
4. **Test Robustness:** Try multiple symbols and time periods
5. **Document Everything:** Keep notes on parameter choices

### Data Quality

- **Use Adjusted Close** for historical analysis (accounts for splits/dividends)
- **Check for Gaps:** Ensure continuous data
- **Verify Volume:** Low volume stocks may have unreliable signals

### Performance Evaluation

**Key Metrics to Track:**
- **Total Return:** Overall profitability
- **Sharpe Ratio:** Risk-adjusted returns (>1.0 is good)
- **Maximum Drawdown:** Worst peak-to-trough decline
- **Win Rate:** Percentage of profitable trades
- **Calmar Ratio:** Return / Max Drawdown

---

## Quick Reference

### Menu Options Summary

| Option | Feature | Time Required | Data Needed |
|--------|---------|---------------|-------------|
| 1 | Single Strategy | 10-30s | 30-90 days |
| 2 | Compare All | 1-3 min | 90+ days |
| 3 | Batch Test | 2-10 min | 90+ days |
| 7 | Portfolio Backtest | 1-5 min | 120+ days |
| 11 | Technical Analysis | <5s | Real-time |
| 15 | Market Regime | <5s | 60+ days |
| 25 | Optimization | 5-15 min | 365+ days |
| 28 | Walk-Forward | 2-10 min | 180+ days |
| 29 | Monte Carlo | 1-5 min | 90+ days |
| 30 | Custom Strategy | 1-5 min | Varies |
| 31 | Export Strategy | <10s | N/A |

### Built-in Strategies

1. **Simple Mean Reversion**
   - Fast baseline strategy
   - Works well in ranging markets
   - Minimal data requirements

2. **ML Single Model**
   - Random Forest classifier
   - Moderate complexity
   - 90+ days data needed

3. **Optimized ML Ensemble**
   - Multiple models combined
   - Most sophisticated
   - 180+ days data needed
   - Optimization recommended

4. **Short-Term Mean Reversion**
   - Quick entry/exit signals
   - Higher trade frequency
   - 30+ days data needed

---

## Support and Resources

### In-Platform Help
- Press `?` at main menu for detailed guide
- Use Option 34 for complete documentation

### External Resources
- QuantConnect Docs: https://www.quantconnect.com/docs
- yfinance Documentation: https://pypi.org/project/yfinance/

### Getting Help
For issues:
1. Check this guide
2. Review error messages carefully
3. Ensure sufficient data period
4. Verify symbol is valid
5. Check internet connection
6. Report issues on GitHub

---

## Educational Use Only

⚠️ **Important Disclaimer:**
- Past performance does not guarantee future results
- This platform is for research and learning purposes
- Not financial advice
- Always test thoroughly before live trading
- Only trade with capital you can afford to lose

---

**Version:** V0.20  
**Platform Status:** Production-Ready  
**Last Updated:** December 2024
