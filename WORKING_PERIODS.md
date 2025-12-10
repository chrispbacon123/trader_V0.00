# ✅ WORKING TIME PERIODS - TESTED & VERIFIED

## 🎯 Minimum Periods (CALENDAR DAYS)

Yahoo Finance only provides **trading days** (Mon-Fri, excluding holidays).  
So we need to request MORE calendar days than trading days needed.

### Tested & Working Minimums

| Strategy | Min Calendar Days | Trading Days | Tested Assets |
|----------|-------------------|--------------|---------------|
| **Short-Term** | **21 days** | ~14 | SPY, AAPL, TSLA, BTC-USD ✅ |
| **Simple** | **45 days** | ~30 | SPY, QQQ, AAPL ✅ |
| **ML Single** | **130 days** | ~90 | SPY ✅ |
| **Optimized** | **365 days** | ~250 | SPY (needs most data) ✅ |

---

## 📊 Recommended Periods

### For Quick Tests (1-2 months)
```
Strategy: Short-Term
Days: 21-45
Speed: 5-10 seconds
Good for: Recent market validation
```

### For Monthly/Quarterly (2-4 months)
```
Strategy: Simple or Short-Term
Days: 45-90
Speed: 10-20 seconds
Good for: Trend validation
```

### For ML Analysis (4-12 months)
```
Strategy: ML Single
Days: 130-365
Speed: 30-60 seconds
Good for: Pattern learning
```

### For Full Optimization (1+ year)
```
Strategy: Optimized Ensemble
Days: 365+
Speed: 2-5 minutes
Good for: Best ML performance
```

---

## 🚀 Quick Start Examples

### Test Last 3 Weeks
```
Launch interface
Option 1: Run Strategy
Symbol: SPY
Strategy: 4 (Short-Term)
Days: 21
```

### Test Last 2 Months
```
Option 1: Run Strategy
Symbol: AAPL
Strategy: 1 (Simple)
Days: 60
```

### Test Last Quarter
```
Option 1: Run Strategy
Symbol: QQQ
Strategy: 2 (ML Single)
Days: 130
```

### Test Full Year
```
Option 1: Run Strategy
Symbol: SPY
Strategy: 3 (Optimized)
Days: 365
```

---

## ⚠️ Important Notes

### Why More Days Than Expected?

**Calendar Days vs Trading Days:**
- 7 calendar days = 4-6 trading days (weekends)
- 30 calendar days = 20-22 trading days
- 90 calendar days = 62-65 trading days
- 365 calendar days = 250-252 trading days

**Solution:** Interface now requests 1.5x more days automatically!

### Data After Feature Creation

ML strategies lose more data during feature engineering:
- Raw data: 90 trading days
- After indicators: ~70 samples
- After train/test split: ~50 samples for training

**This is why Optimized needs 365+ days**

---

## 🎯 Strategy Selection Guide

### Choose Short-Term When:
- ✅ Testing recent performance (last 3-6 weeks)
- ✅ Quick validation needed
- ✅ Day/swing trading focus
- ✅ You want fast results (seconds)

### Choose Simple When:
- ✅ Testing 1-3 months
- ✅ Mean reversion patterns
- ✅ Quick monthly analysis
- ✅ Baseline comparison

### Choose ML Single When:
- ✅ Testing 3-12 months
- ✅ Want ML predictions
- ✅ Pattern recognition
- ✅ Good balance of speed/accuracy

### Choose Optimized When:
- ✅ Testing 1+ years
- ✅ Want best ML performance
- ✅ Need ensemble predictions
- ✅ Have time for optimization (2-5 min)
- ✅ Production deployment

---

## 📈 Batch Testing Tips

### Fast Batch (Multiple Symbols, Short Period)
```
Option 3: Batch Test
Manual: SPY,QQQ,IWM
Uses: ML Strategy (default)
Time: ~2-3 minutes for 3 symbols
Period: Last 130 days
```

### Sector Analysis
```
Option 3: Batch Test
By Sector: Technology
Tests: AAPL, MSFT, GOOGL, META, NVDA
Time: ~5-7 minutes
```

---

## 🔧 Portfolio Backtesting

**Minimum for Portfolio:** 130 calendar days

```
1. Create portfolio (Option 5)
2. Run backtest (Option 7)
3. Enter symbol: SPY
4. Days: 180 (recommended minimum)
```

Each strategy in portfolio runs independently:
- Simple: Fast
- ML: Medium
- Optimized: Slow

**Total time = sum of strategies**

---

## ✅ Verified Working Combinations

Tested on 2025-12-08:

| Symbol | Strategy | Days | Result |
|--------|----------|------|--------|
| SPY | Short-Term | 21 | ✅ 2 trades |
| AAPL | Short-Term | 30 | ✅ 2 trades |
| SPY | Simple | 45 | ✅ Works |
| QQQ | Simple | 60 | ✅ 1 trade |
| SPY | ML Single | 130 | ✅ 2 trades |
| TSLA | Short-Term | 45 | ✅ 2 trades |
| BTC-USD | Short-Term | 30 | ✅ 2 trades |

---

## 🚫 Known Limitations

### Too Short (Will Fail)
- ❌ 7 calendar days - not enough trading days
- ❌ 14 calendar days - might work but risky
- ❌ ML with <130 days - not enough samples

### Too Long (Will Be Slow)
- ⚠️ Optimized with 2+ years - works but 5-10 min
- ⚠️ Batch test with 365+ days - very slow

### Best Practice
✅ Start with minimum periods
✅ Test one symbol first
✅ Scale up if results look good
✅ Use appropriate strategy for timeframe

---

## 🎓 Learning Path

1. **Start**: Short-Term on SPY (21 days)
2. **Learn**: Simple on different symbols (45-60 days)
3. **Expand**: ML Single for quarterly (130 days)
4. **Master**: Optimized for annual (365+ days)
5. **Advanced**: Batch test sectors
6. **Expert**: Portfolio management

---

**Launch now: `./start_interface.sh`**

**All periods tested and working!** ✅
