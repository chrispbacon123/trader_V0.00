# ⚡ SHORT-TERM TRADING NOW SUPPORTED!

## ✅ NEW: Flexible Timeframes

You can now backtest strategies over **much shorter periods**:

### 📊 Minimum Periods by Strategy

| Strategy | Old Minimum | NEW Minimum | Best For |
|----------|-------------|-------------|----------|
| **Short-Term** ⚡ | N/A | **7 days** | Day/swing trading |
| **Simple Mean Reversion** | 365 days | **30 days** | Monthly testing |
| **ML Single Model** | 365 days | **90 days** | Quarterly analysis |
| **Optimized Ensemble** | 365 days | **120 days** | 4-month+ tests |

---

## 🎯 NEW Strategy: Short-Term Trading

**Perfect for:**
- Testing last week's performance
- Quick strategy validation
- Day/swing trading signals
- Rapid market changes

**Features:**
- Fast EMA crossovers (5/15 periods)
- 7-period RSI for quick signals
- Volume spike detection
- 3-day momentum tracking

**Minimum: Just 7 days of data!**

---

## 💡 Example Use Cases

### 1. Test This Week's Performance
```
Option: 1 (Run Strategy)
Symbol: SPY
Strategy: 4 (Short-Term)
Days: 7
Capital: 10000
```

### 2. Compare Last Month
```
Option: 1
Symbol: TSLA
Strategy: 4 (Short-Term)
Days: 30
→ See how it performed in recent market
```

### 3. Quick Crypto Test
```
Option: 1
Symbol: BTC-USD
Strategy: 4 (Short-Term)
Days: 14
→ Test 2-week crypto swing
```

### 4. Monthly Stock Analysis
```
Option: 1
Symbol: AAPL
Strategy: 1 (Simple)
Days: 30
→ Test 1-month mean reversion
```

---

## 📈 Recommended Periods

### Short-Term Strategy (7-90 days)
- **7-14 days**: Week/bi-weekly testing
- **30 days**: Monthly performance
- **60-90 days**: Quarter analysis

### Simple Strategy (30-180 days)
- **30 days**: Quick validation
- **90 days**: Quarter test
- **180 days**: Half-year analysis

### ML Strategies (90-365+ days)
- **90 days**: Minimum for training
- **180 days**: Better ML performance
- **365+ days**: Optimal for ML models

---

## ⚙️ How It Works

The interface now **auto-adjusts** minimum requirements:

```
Simple Strategy:     30+ days required
ML Strategy:         90+ days required  
Optimized Ensemble: 120+ days required
Short-Term:           7+ days required  ⚡
```

When you choose a strategy, you'll see:
```
Lookback period in days (default: 30, min: 7): _
```

The minimum changes based on your strategy choice!

---

## 🚀 Updated Workflows

### Workflow: Test Recent Performance

```
1. Launch interface
2. Option 1 (Run Strategy)
3. Symbol: SPY (or any symbol)
4. Strategy: 4 (Short-Term)
5. Days: 7 (or 14, 30)
6. See results in seconds!
```

### Workflow: Weekly vs Monthly Comparison

```
Week Test:
- Strategy: 4, Days: 7
- Note return %

Month Test:
- Strategy: 4, Days: 30  
- Compare returns

Quarter Test:
- Strategy: 1, Days: 90
- See longer trend
```

---

## 📊 Short-Term Strategy Details

**Indicators Used:**
- **EMA 5/15**: Fast crossover signals
- **RSI(7)**: Quick overbought/oversold
- **3-day Momentum**: Recent price action
- **Volume Spikes**: Confirmation signals

**Trading Logic:**
- **Buy**: EMA crossover + positive momentum + RSI < 70
- **Sell**: Reverse crossover OR RSI > 75 OR momentum < -2%

**Best For:**
- Volatile markets
- Quick reversals
- Day/swing trading
- Short-term opportunities

---

## 🎯 When to Use Each Period

### 7-30 Days (Short-Term)
✅ Test recent market changes
✅ Validate quick strategies
✅ Day/swing trading signals
❌ Not enough for ML training

### 30-90 Days
✅ Monthly/quarterly analysis
✅ Simple strategies work well
✅ Recent trend validation
⚠️ Minimum for ML strategies

### 90-180 Days
✅ Better ML performance
✅ Seasonal patterns
✅ Good balance of data
✅ Recommended for ML

### 365+ Days
✅ Best for ML/Optimized
✅ Full year trends
✅ Reliable statistics
✅ Long-term validation

---

## 💡 Pro Tips

1. **Start short** - Test 7-30 days first to validate concept
2. **Scale up** - If short-term works, try longer periods
3. **Compare periods** - Run 7d, 30d, 90d on same symbol
4. **Match strategy to timeframe**:
   - 7-30 days → Short-Term
   - 30-90 days → Simple
   - 90+ days → ML/Optimized

---

## ✅ All Working Timeframes

Test immediately:
- ✅ **1 week** (7 days) - Short-Term strategy
- ✅ **2 weeks** (14 days) - Short-Term strategy
- ✅ **1 month** (30 days) - Simple or Short-Term
- ✅ **3 months** (90 days) - Any strategy
- ✅ **6 months** (180 days) - All strategies
- ✅ **1 year+** (365+ days) - Optimal for all

---

## 🚀 Launch & Try

```bash
./start_interface.sh
```

Try these now:
```
Test this week: Option 1 → Strategy 4 → Days: 7
Test last month: Option 1 → Strategy 4 → Days: 30
Test quarter: Option 1 → Strategy 1 → Days: 90
```

**From 7 days to multiple years - all supported!** ⚡
