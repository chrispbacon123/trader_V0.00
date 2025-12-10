# 📊 Trading Strategy CLI - Quick Start Guide

## 🚀 Launch the Interface

```bash
cd ~/lean-trading
python3 trading_cli.py
```

---

## 📋 Main Menu Features

### 1. **Run Individual Strategies**
- **Option 1**: Simple Mean Reversion (fast baseline)
- **Option 2**: ML Single Model (moderate speed)
- **Option 3**: Optimized Ensemble (most sophisticated)

### 2. **Compare All Strategies** (Option 4)
Runs all three strategies sequentially and displays:
- Side-by-side performance comparison
- Best return highlighter
- Best Sharpe ratio highlighter

### 3. **View Results History** (Option 5)
- See all previous strategy runs
- Shows timestamp, strategy, symbol, and return
- Tracks last 10 runs

### 4. **Custom Strategy Run** (Option 6)
Choose your own:
- Strategy (Simple/ML/Optimized)
- Symbol (SPY, QQQ, AAPL, etc.)
- Lookback period (days)
- Number of optimization trials (for Ensemble)

### 5. **Export Results to CSV** (Option 7)
- Exports all history to timestamped CSV file
- Perfect for Excel analysis or record keeping

### 6. **Clear History** (Option 8)
- Wipe all saved results
- Requires confirmation

---

## 💡 Usage Examples

### Quick Comparison
```
Choose: 4 (Compare All Strategies)
Wait for all three to complete
View side-by-side comparison table
```

### Test Different Symbol
```
Choose: 6 (Custom Strategy Run)
Strategy: 3 (Optimized Ensemble)
Symbol: QQQ
Days: 365
Trials: 15
```

### Build Trading Journal
```
1. Run strategies throughout the week
2. Use Option 5 to view all runs
3. Use Option 7 to export to CSV
4. Analyze in Excel/spreadsheet
```

---

## 📁 What Gets Saved

### `strategy_history.json`
- Persistent storage of all strategy runs
- Includes:
  - Timestamp
  - Strategy name
  - Symbol
  - Returns, Sharpe, drawdown
  - Win rate, trade count

### Exported CSV Files
- Format: `strategy_results_YYYYMMDD_HHMMSS.csv`
- Contains all historical runs
- Easy to import into analysis tools

---

## 🎯 Best Practices

1. **Start with Comparison**: Run Option 4 first to see all strategies
2. **Try Different Symbols**: Test on QQQ, IWM, individual stocks
3. **Keep History**: Don't clear unless necessary - builds valuable data
4. **Export Regularly**: Save CSV exports for long-term tracking
5. **Custom Testing**: Use Option 6 to iterate on specific symbols

---

## 🔮 Future Expansion Ideas

The CLI is designed to be easily expandable. You can add:

- **More strategies**: Just import and add menu option
- **Parameter tuning**: UI for adjusting lookback, thresholds
- **Real-time monitoring**: Live portfolio tracking
- **Alerts**: Notification when conditions are met
- **Multi-symbol runs**: Batch testing across watchlists
- **Visualization**: Charts and graphs of results
- **Backtesting scenarios**: Bull/bear market analysis
- **Walk-forward optimization**: Automated retraining

---

## ⌨️ Keyboard Shortcuts

- **Enter**: Continue after viewing results
- **0**: Exit application
- **1-8**: Menu selections

---

## 🐛 Troubleshooting

**Q: CLI won't start?**
A: Make sure you're in the lean-trading directory:
```bash
cd ~/lean-trading
python3 trading_cli.py
```

**Q: Import errors?**
A: Verify all strategy files are in the same directory

**Q: Lost history?**
A: History is auto-saved to `strategy_history.json` - check if file exists

---

## 📊 Understanding the Comparison Table

```
Strategy              Return    Sharpe   MaxDD  Trades  WinRate
-------------------------------------------------------------------
Simple Mean Rev.      12.96%      N/A     N/A      5      N/A
ML Single Model        2.19%     1.15   1.57%    12    66.7%
Optimized Ensemble     1.10%     2.04   0.00%     4   100.0%
```

- **Return**: Total percentage gain/loss
- **Sharpe**: Risk-adjusted return (higher = better)
- **MaxDD**: Maximum drawdown percentage
- **Trades**: Total number of trades executed
- **WinRate**: Percentage of profitable trades

---

**Tip**: The "best" strategy depends on your goals:
- Maximum return? → Simple Mean Reversion
- Best risk-adjusted? → Optimized Ensemble
- Most trades? → ML Single Model

---

**Ready to expand?** The code is modular - add new strategies by:
1. Creating new strategy class
2. Importing in `trading_cli.py`
3. Adding menu option and run function
