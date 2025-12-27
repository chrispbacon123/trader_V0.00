# Testing Quick Reference 🧪

## TL;DR - Run This Now

```bash
cd C:\Users\Chris\trader_V0.00
python run_deterministic_tests.py
```

Expected output: **✓ ALL TESTS PASSED**

---

## What Gets Tested

### 1. Price Data ✓
- No mixed tickers or MultiIndex confusion
- All required OHLCV columns present
- Prices validated (High >= Low, all positive)

### 2. Technical Indicators ✓
- RSI: [0, 100] range
- Stochastic: [0, 100] range
- ADX: [0, 100] range
- MACD: histogram = MACD - Signal
- No NaNs after warmup period

### 3. Key Levels ✓
- Fibonacci anchors from correct lookback window
- S/R levels within proximity filter
- No far-off artifacts from old data

### 4. Market Regime ✓
- Has explicit rationale string
- Volatility is annualized (12-25% typical)
- Reconciles with ADX metrics

### 5. Risk Metrics ✓
- Volatility: both daily and annualized
- Annualization: daily * sqrt(252)
- VaR/CVaR: labeled with horizon and method

### 6. Fractional Shares ✓
- When enabled: shares are floats
- When disabled: shares are integers
- Cash residuals tracked explicitly
- Total accounts balance (equity = invested + cash + costs)

### 7. Edge Cases ✓
- Flat prices don't crash
- Short history handled gracefully
- NaN values handled properly

---

## Test Files

### Main Test Script
**`run_deterministic_tests.py`**
- Standalone (no pytest needed)
- Uses synthetic data (no API calls)
- 7 test suites, 60+ tests
- Takes ~5 seconds to run

### Advanced Testing (Optional)
**`tests/test_comprehensive.py`**
- Full pytest suite
- Requires: `pip install pytest`
- Run with: `pytest tests/test_comprehensive.py -v`

### Test Data
**`tests/data/spy_daily.csv`**
- Frozen SPY data for deterministic tests
- Used by pytest suite

**`tests/fixtures.py`**
- Synthetic data generators
- Used by both test suites

---

## Quick Checks

### Check 1: Indicators Bounded
```python
python -c "from run_deterministic_tests import test_indicators; test_indicators()"
```
Should show: RSI, Stochastic, ADX all in [0, 100]

### Check 2: Fractional Shares Work
```python
python -c "from run_deterministic_tests import test_portfolio_fractional; test_portfolio_fractional()"
```
Should show: fractional shares when enabled, whole shares when disabled

### Check 3: Regime Coherence
```python
python -c "from run_deterministic_tests import test_regime; test_regime()"
```
Should show: regime has rationale, confidence in [0,1], ADX bounded

---

## Configuration

### Enable/Disable Fractional Shares
Edit `core_config.py`:
```python
PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = True  # or False
```

### Adjust Lookback Windows
Edit `core_config.py`:
```python
LEVEL_CFG.FIB_LOOKBACK = 100         # Fibonacci window
REGIME_CFG.REGIME_LOOKBACK = 50       # Regime window
INDICATOR_CFG.RSI_PERIOD = 14         # RSI period
```

### Adjust Regime Thresholds
Edit `core_config.py`:
```python
REGIME_CFG.VOL_LOW_THRESHOLD = 0.12   # 12% annualized
REGIME_CFG.VOL_HIGH_THRESHOLD = 0.25  # 25% annualized
```

---

## Common Issues

### Test Fails: "RSI out of bounds"
**Cause:** Indicator calculation error  
**Fix:** Check `validated_indicators.py` for correct Wilder's RSI formula

### Test Fails: "Fib anchor not in window"
**Cause:** Lookback window mismatch  
**Fix:** Verify `LEVEL_CFG.FIB_LOOKBACK` matches actual window used

### Test Fails: "Regime always VOLATILE"
**Cause:** Volatility thresholds too low  
**Fix:** Update `REGIME_CFG.VOL_HIGH_THRESHOLD` to realistic value (0.25)

### Test Fails: "Shares not fractional"
**Cause:** Fractional shares disabled or int() cast  
**Fix:** Set `FRACTIONAL_SHARES_ALLOWED = True` and remove int() casts

---

## Expected Test Output

```
======================================================================
                  DETERMINISTIC TEST HARNESS
======================================================================

Running comprehensive validation without pytest or live data...

======================================================================
TEST SUITE: Canonical Data
======================================================================
  ✓ PASS: Price column exists
  ✓ PASS: No MultiIndex columns
  ✓ PASS: Required column 'Open' present
  ✓ PASS: Required column 'High' present
  ✓ PASS: Required column 'Low' present
  ✓ PASS: Required column 'Close' present
  ✓ PASS: Required column 'Volume' present
  ✓ PASS: All prices positive
  ✓ PASS: High >= Low

----------------------------------------------------------------------
Total: 9 | Passed: 9 | Failed: 0
======================================================================

... (6 more suites) ...

======================================================================
                        FINAL SUMMARY
======================================================================
  ✓ PASS: Canonical Data
  ✓ PASS: Technical Indicators
  ✓ PASS: Key Levels (Fibonacci & S/R)
  ✓ PASS: Market Regime Classification
  ✓ PASS: Risk Metrics
  ✓ PASS: Portfolio Allocation (Fractional Shares)
  ✓ PASS: Edge Cases

----------------------------------------------------------------------
Total: 7 suites | Passed: 7 | Failed: 0
======================================================================

✓ ALL TESTS PASSED - System is deterministic and validated
```

---

## When to Run Tests

### Always Run Before:
- ✓ Deploying to production
- ✓ Making trades with real money
- ✓ Presenting results to stakeholders
- ✓ Committing major code changes

### Run After:
- ✓ Modifying indicator formulas
- ✓ Changing lookback windows
- ✓ Updating portfolio allocation logic
- ✓ Adjusting regime thresholds
- ✓ Any code changes to validated modules

### Optional:
- After minor documentation changes
- After adding new strategies (if they don't touch core modules)

---

## Integration with Platform

Tests validate the **core engine**, but don't test:
- Live data fetching from yfinance (that's external)
- User interface / menu system
- File I/O (portfolio saving/loading)
- Network connectivity

These are integration concerns, not unit/system concerns.

---

## Test Philosophy

### What We Test
**Invariants** - Properties that must always be true:
- Indicators bounded
- Math consistency (MACD histogram = MACD - Signal)
- Anchors in declared windows
- Accounts balance

### What We Don't Test
**External dependencies** - Things outside our control:
- yfinance API availability
- Internet connectivity
- User input validation (handled separately)

### Why Synthetic Data
- **Deterministic**: Same input → same output
- **Fast**: No network calls
- **Reliable**: No API rate limits or downtime
- **Comprehensive**: Can create edge cases on demand

---

## Further Reading

- **Full validation report**: `VALIDATION_COMPLETE.md`
- **Test harness details**: `DETERMINISTIC_TESTS_COMPLETE.md`
- **Main documentation**: `README.md`
- **Configuration**: `core_config.py`

---

## Quick Command Reference

```bash
# Run all tests
python run_deterministic_tests.py

# Run with pytest (if installed)
pytest tests/test_comprehensive.py -v

# Generate test data fixture (if needed)
python tests/fixtures.py

# Check Python version
python --version  # Should be 3.8+

# Check dependencies
pip list | grep -E "pandas|numpy|yfinance"
```

---

**Last Updated**: December 2024  
**Test Coverage**: 100% of core invariants  
**Status**: ✅ All tests passing  

---

*Remember: Tests validate the engine, but YOU validate the strategy.*
