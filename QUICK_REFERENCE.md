# 📋 Quick Reference Card - Advanced Trading Platform

## 🚀 Launch
```bash
cd ~/lean-trading
python3 advanced_trading_interface.py
```

---

## 🎯 Most Used Features

### Beginners Start Here
| Option | Feature | Use Case |
|--------|---------|----------|
| ? | **Help Guide** | Learn everything |
| 1 | **Run Single Strategy** | Test one asset |
| 15 | **Market Analytics** | Understand market |
| 11 | **Technical Analysis** | Check indicators |

### Strategy Testing
| Option | Feature | Time | Use When |
|--------|---------|------|----------|
| 1 | Single Strategy | 10-60s | Testing one asset |
| 2 | Compare All | 3-5min | Finding best strategy |
| 3 | Batch Test | 2-10min | Testing multiple assets |
| 4 | Sector Analysis | 1-3min | Sector comparison |

### Advanced Analysis
| Option | Feature | Output |
|--------|---------|--------|
| 15 | Market Analytics | Regime, levels, indicators |
| 16 | Correlation | Asset relationships |
| 25 | Optimize Parameters | Best settings |
| 27 | Risk Analysis | Complete risk profile |

### Portfolio Management
| Option | Feature | Purpose |
|--------|---------|---------|
| 5 | Create Portfolio | New multi-strategy portfolio |
| 7 | Portfolio Backtest | Test performance |
| 8 | Compare Portfolios | Find best allocation |

### Strategy Library
| Option | Feature | Purpose |
|--------|---------|---------|
| 17 | Save Strategy | Store configuration |
| 18 | Load & Run | Quick deployment |
| 22 | Leaderboard | Best performers |

---

## 🔧 Common Tasks

### Task: "Test SPY with best strategy"
```
1. Option 15: SPY → Check market regime
2. Option 2: SPY → Compare strategies
3. Option 1: Run winner with optimal period
```

### Task: "Optimize a strategy"
```
1. Option 26: Configure settings
2. Option 25: Run optimization
3. Option 17: Save best config
4. Option 22: Check leaderboard
```

### Task: "Build diversified portfolio"
```
1. Option 16: Check correlations
2. Option 5: Create portfolio
3. Option 7: Backtest
4. Option 8: Compare with others
```

### Task: "Analyze risk"
```
1. Option 15: Market analytics
2. Option 27: Risk dashboard
3. Option 11: Technical check
→ Make informed decision
```

---

## 📊 Strategy Selection Guide

### Use Short-Term (< 3 months)
```
Option 1 → Strategy 4
- Fast execution (5-15s)
- Recent trends
- Min: 21 days
```

### Use Simple (3-12 months)
```
Option 1 → Strategy 1
- Fast execution (10-20s)
- Mean reversion
- Min: 45 days
```

### Use ML Single (6-24 months)
```
Option 1 → Strategy 2
- Medium speed (30-90s)
- Pattern learning
- Min: 130 days
```

### Use Optimized (12+ months)
```
Option 1 → Strategy 3
- Slow (2-5 min)
- Best accuracy
- Min: 365 days
```

---

## ⚙️ Settings Cheat Sheet

### Default Settings (Option 23)
- Capital: $100,000
- Target Return: 15%
- Period: 180 days

### Advanced Settings (Option 26)
**Risk:**
- Max Position: 20%
- Stop Loss: 5%
- Take Profit: 15%

**ML:**
- Lookback: 60 days
- Prediction: 5 days
- Min Samples: 50

**Backtest:**
- Commission: 0.1%
- Slippage: 0.05%

---

## 🎯 Performance Metrics Explained

### Returns
- **Total Return**: (Final - Initial) / Initial × 100%
- **Good**: >10% annual
- **Excellent**: >20% annual

### Risk-Adjusted
- **Sharpe Ratio**: Return per unit of risk
  - <1: Poor
  - 1-2: Good
  - >2: Excellent

- **Sortino Ratio**: Like Sharpe, downside only
  - Higher is better

- **Calmar Ratio**: Return / Max Drawdown
  - >0.5: Good
  - >1.0: Excellent

### Risk Metrics
- **Max Drawdown**: Largest peak-to-trough decline
  - <10%: Low risk
  - 10-20%: Moderate
  - >20%: High risk

- **Volatility**: Annualized standard deviation
  - <15%: Low
  - 15-30%: Moderate
  - >30%: High

### Trading Stats
- **Win Rate**: % of profitable trades
  - >50%: Good
  - >60%: Very good

- **Profit Factor**: Gross profit / Gross loss
  - >1.5: Good
  - >2.0: Excellent

---

## 🔍 Market Regime Guide

### Trending Up
- Use momentum strategies
- ML strategies perform well
- Follow the trend

### Trending Down
- Use caution
- Short-term strategies better
- Consider waiting

### Ranging
- Use mean reversion
- Simple strategy works well
- Trade the range

### Volatile
- Use smaller positions
- Wider stops
- Short-term only

---

## 💾 Data Files

### Important Files
- `portfolios.json` - Your portfolios
- `strategy_configs.json` - Saved strategies
- `strategy_history.json` - All results
- `watchlists.json` - Symbol lists
- `advanced_settings.json` - Custom settings

### Backup These Files!
```bash
# Create backup
tar -czf trading_backup_$(date +%Y%m%d).tar.gz *.json

# Restore backup
tar -xzf trading_backup_YYYYMMDD.tar.gz
```

---

## 🚨 Quick Troubleshooting

### "Insufficient data"
→ Increase lookback period
→ Use older/more liquid asset

### "No data available"
→ Check symbol spelling
→ Crypto must end in -USD
→ Check internet connection

### Strategy too slow
→ Use Short-Term or Simple
→ Reduce lookback period
→ Test fewer combinations

### Optimization fails
→ Check parameter ranges
→ Ensure adequate data
→ Try simpler strategy first

---

## 📞 Get Help

### In-App
- Press **?** anytime for full help
- Each menu shows examples
- Error messages explain fixes

### Documentation
- `FINAL_STATUS_COMPLETE.md` - Complete guide
- `ENHANCEMENT_COMPLETE.md` - New features
- `QUICK_REFERENCE.md` - This file

---

## 💡 Pro Tips

### Speed
✅ Use Short-Term for quick tests  
✅ Batch test watchlists  
✅ Save successful configs  
✅ Use comparison before optimization  

### Accuracy
✅ Use longer periods when possible  
✅ Compare multiple strategies  
✅ Check market regime first  
✅ Verify with technical analysis  

### Risk Management
✅ Set realistic targets  
✅ Monitor drawdowns  
✅ Diversify across assets  
✅ Use stop losses  

### Workflow
✅ Analyze → Test → Optimize → Save → Deploy  
✅ Check regime before trading  
✅ Compare correlations for portfolios  
✅ Export results regularly  

---

## 🎓 Learning Path

### Week 1: Basics
1. Run Option ? (Help)
2. Test single strategies (Option 1)
3. View technical analysis (Option 11)
4. Create first portfolio (Option 5)

### Week 2: Analysis
1. Market analytics (Option 15)
2. Compare strategies (Option 2)
3. Risk analysis (Option 27)
4. Correlation study (Option 16)

### Week 3: Optimization
1. Optimize parameters (Option 25)
2. Save best configs (Option 17)
3. Build strategy library (Options 18-22)
4. Test portfolios (Option 7)

### Week 4: Advanced
1. Configure settings (Option 26)
2. Batch testing (Option 3)
3. Sector analysis (Option 4)
4. Compare portfolios (Option 8)

---

## 🏆 Success Checklist

### First Run
- [ ] Launch interface successfully
- [ ] Press ? and read help
- [ ] Run single strategy on SPY
- [ ] View results

### Beginner Goals
- [ ] Test all 4 strategies
- [ ] Compare strategies
- [ ] Check market analytics
- [ ] Create first portfolio

### Intermediate Goals
- [ ] Optimize parameters
- [ ] Save strategy configs
- [ ] Build watchlist
- [ ] Export results

### Advanced Goals
- [ ] Configure advanced settings
- [ ] Multi-asset portfolio
- [ ] Correlation-based allocation
- [ ] Complete optimization workflow

---

## 📈 Example Commands

### Quick Single Test
```
Option 1 → Symbol: SPY → Strategy: 4 → Days: 45
```

### Full Comparison
```
Option 2 → Symbol: AAPL → Days: 180
```

### Sector Scan
```
Option 4 → Choose: Technology → Quick Overview
```

### Portfolio Test
```
Option 7 → Choose portfolio → Symbol: SPY → Days: 365
```

### Optimization
```
Option 25 → Strategy: 2 (ML) → Symbol: QQQ → Days: 180
```

---

**🎯 Remember:** This tool is for analysis and education, not financial advice.  
**💾 Always:** Back up your configurations and results regularly.  
**📊 Test:** Everything with small amounts before scaling up.

**Happy Trading! 🚀**
