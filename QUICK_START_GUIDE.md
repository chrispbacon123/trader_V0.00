# Trading Platform Quick Start Guide

## Starting the Platform

### Option 1: Simple Start
```bash
cd ~/lean-trading
python3 advanced_trading_interface.py
```

### Option 2: Using Start Script
```bash
cd ~/lean-trading
./START.sh
```

## Main Features

### 1. Strategy Testing (Options 1-4)
Test individual strategies on assets:
- **Option 1**: Run single strategy on one asset
- **Option 2**: Compare all strategies on same asset
- **Option 3**: Test strategies across multiple assets
- **Option 4**: Analyze by sector/industry

**Recommended**: Start with Option 2 on SPY for 365 days

### 2. Portfolio Management (Options 5-10)
Create and test portfolios with mixed strategies:
- Create portfolio with custom allocations
- Backtest across different assets
- Compare performance

**Min backtest period**: 120 days for portfolios

### 3. Technical Analysis (Option 11)
Real-time technical indicators:
- RSI, MACD, Bollinger Bands
- Volume analysis
- Support/Resistance levels

### 4. Custom Strategy Builder (Option 30)
Create your own strategies:
1. Choose base type (trend/mean reversion/ML)
2. Add indicators
3. Set entry/exit rules
4. Backtest and refine

### 5. Export for Live Trading (Option 31)
Export tested strategies:
- Python class format
- JSON configuration
- QuantConnect LEAN format
- Complete deployment package

## Data Requirements

### Minimum Periods
- **Simple Strategy**: 30+ calendar days (20 trading days)
- **Short-Term**: 30+ calendar days
- **ML Strategy**: 90+ calendar days (60 trading days)
- **Optimized ML**: 180+ calendar days
- **Portfolio**: 120+ calendar days

### Supported Assets
- **Stocks**: Any US ticker (AAPL, GOOGL, MSFT, etc.)
- **ETFs**: SPY, QQQ, IWM, etc.
- **Crypto**: BTC-USD, ETH-USD, etc. (via yfinance)

## Common Workflows

### Workflow 1: Test a Stock
```
1. Choose Option 1 (Run Strategy)
2. Select strategy (e.g., ML Strategy)
3. Enter symbol (e.g., AAPL)
4. Enter period (e.g., 365)
5. Review results
```

### Workflow 2: Find Best Strategy
```
1. Choose Option 2 (Compare All)
2. Enter symbol (e.g., SPY)
3. Enter period (e.g., 365)
4. Compare returns and metrics
```

### Workflow 3: Build Custom Strategy
```
1. Choose Option 30 (Strategy Builder)
2. Name your strategy
3. Select type and indicators
4. Set rules and parameters
5. Backtest
6. Export (Option 31) if satisfied
```

### Workflow 4: Create Portfolio
```
1. Choose Option 5 (Create Portfolio)
2. Set name and capital
3. Allocate % to each strategy
4. Set target return (optional)
5. Choose Option 7 to backtest
```

## Tips for Success

### For Beginners
1. Start with Option 2 on SPY with 365 days
2. Compare strategy performance
3. Try different stocks with best strategy
4. Learn from results before creating custom strategies

### For Advanced Users
1. Use Option 30 to build custom strategies
2. Optimize with Option 25
3. Run Walk-Forward Analysis (Option 28)
4. Monte Carlo Simulation (Option 29)
5. Export best strategies (Option 31)

### Risk Management
- Always backtest with sufficient data (1+ years recommended)
- Test on multiple assets before live deployment
- Start with paper trading
- Use appropriate position sizing (default 95% is aggressive)

## Common Errors & Solutions

### "Insufficient data"
- **Cause**: Not enough trading days
- **Solution**: Increase lookback period or request more calendar days
- **Note**: 365 calendar days ≈ 252 trading days

### "No data available"
- **Cause**: Invalid symbol or data source issue
- **Solution**: Verify ticker symbol, check internet connection

### "too many values to unpack"
- **Cause**: Fixed in latest version
- **Solution**: Restart platform if you see this

### Strategy fails on certain assets
- **Cause**: Insufficient data or volatility
- **Solution**: Try longer period or different asset

## Advanced Features

### Optimization (Option 25)
- Automatically finds best parameters
- Uses Optuna for hyperparameter tuning
- Can take 5-15 minutes

### Walk-Forward Analysis (Option 28)
- Tests strategy across rolling windows
- More realistic performance assessment
- Helps detect overfitting

### Monte Carlo Simulation (Option 29)
- Simulates thousands of possible outcomes
- Calculates risk metrics
- Provides confidence intervals

### Market Regime Detection (Option 15)
- Identifies bull/bear/sideways markets
- Adjusts strategy recommendations
- Uses volatility and trend analysis

## Exporting Strategies

When you export a strategy (Option 31), you get:

1. **Configuration file**: JSON with all parameters
2. **Model file**: Trained ML model (if applicable)
3. **Deployment script**: Python template for live trading
4. **Documentation**: README with setup instructions

### Deployment Locations
- `~/lean-trading/live_strategies/`: Individual exports
- `~/lean-trading/strategy_exports/`: Batch exports

## Getting Help

### In-Platform Help
- Press `?` at main menu for detailed guide
- Option 34 shows complete documentation

### External Resources
- QuantConnect Docs: https://www.quantconnect.com/docs
- yfinance: https://pypi.org/project/yfinance/
- QuantLib: https://www.quantlib.org/

## Limitations

1. **Data Source**: Uses yfinance (free but may have delays)
2. **No Real-Time Trading**: Platform is for backtesting only
3. **US Markets Focused**: Best for US stocks/ETFs
4. **ML Training Time**: Can take minutes for optimized strategies
5. **Memory**: Large datasets may require 4GB+ RAM

## Best Practices

1. **Always backtest 1+ years** before live trading
2. **Test on multiple assets** to ensure robustness
3. **Paper trade first** with any new strategy
4. **Monitor performance** regularly
5. **Adjust for market conditions** using regime detection
6. **Start small** with real capital
7. **Set stop losses** for risk management

## Quick Reference

| Option | Feature | Min Period | Time |
|--------|---------|------------|------|
| 1 | Single Strategy | 30-90 days | 10-30s |
| 2 | Compare All | 90+ days | 1-3 min |
| 3 | Batch Test | 90+ days | 2-10 min |
| 7 | Portfolio | 120+ days | 1-5 min |
| 11 | Technical Analysis | Real-time | <5s |
| 25 | Optimization | 365+ days | 5-15 min |
| 30 | Custom Strategy | Varies | 1-5 min |
| 31 | Export | N/A | <10s |

## Support

For issues:
1. Check this guide
2. Review error messages carefully
3. Ensure sufficient data period
4. Verify symbol is valid
5. Check internet connection

---

**Remember**: Past performance does not guarantee future results. 
Always trade responsibly and only with capital you can afford to lose.
