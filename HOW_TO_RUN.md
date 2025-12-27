# How to Run the Trading Platform After Overhaul

## Quick Start (3 Steps)

### Step 1: Ensure Python is Installed
```powershell
# Check if Python is available
python --version

# If not, install it:
winget install Python.Python.3.12

# Verify installation
python --version  # Should show: Python 3.12.x
```

### Step 2: Install Dependencies
```powershell
cd C:\Users\Chris\trader_V0.00

# Install required packages
pip install -r requirements.txt

# Install testing tools (optional but recommended)
pip install pytest pytest-cov
```

### Step 3: Validate the Platform
```powershell
# Run validation script (tests all refactors)
python validate_overhaul.py

# Should see: ✅ ALL VALIDATION CHECKS PASSED
```

---

## Run the Trading Interface

### Option 1: Main Trading Interface (Full Features)
```powershell
python advanced_trading_interface.py
```

**Features:**
- Portfolio management
- Strategy backtesting (ML, Simple, Short-term, Optimized)
- Market analytics
- Sector/basket analysis
- Strategy comparison
- History viewing (now crash-free!)

### Option 2: Market Analytics Only
```powershell
python market_analytics.py SPY
```

### Option 3: Run a Specific Strategy
```powershell
# Simple Mean Reversion
python simple_strategy.py

# ML Strategy
python ml_strategy.py

# Optimized ML
python optimized_ml_strategy.py

# Short-term
python short_term_strategy.py
```

---

## Run Tests

### All Tests
```powershell
python -m pytest -v
```

### Specific Test File
```powershell
python -m pytest tests/test_phase1_correctness.py -v
```

### With Coverage Report
```powershell
python -m pytest --cov=. --cov-report=html
# Opens htmlcov/index.html for detailed coverage
```

### Test Collection Only (verify pytest works)
```powershell
python -m pytest --collect-only
```

---

## Example: Complete Workflow

```powershell
# 1. Navigate to project
cd C:\Users\Chris\trader_V0.00

# 2. Validate everything works
python validate_overhaul.py

# 3. Run tests
python -m pytest -v

# 4. Start trading interface
python advanced_trading_interface.py

# In the interface:
# - Create a portfolio
# - Add some symbols (e.g., SPY, QQQ)
# - Run backtests with different strategies
# - View results history (no more crashes!)
# - Compare strategies
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'yfinance'"
```powershell
pip install yfinance
```

### "ModuleNotFoundError: No module named 'pytest'"
```powershell
pip install pytest
```

### "Import Error: canonical_data"
Make sure you're in the project directory:
```powershell
cd C:\Users\Chris\trader_V0.00
```

### History Shows Strange Data
The platform auto-normalizes old history formats. If you want to reset:
```powershell
# Backup current history
copy strategy_history.json strategy_history.backup.json

# Optional: Clear history to start fresh
del strategy_history.json
```

---

## What Changed in This Overhaul

### You Won't Notice (But It's Better)
- ✅ yfinance is now optional - strategies import faster
- ✅ History schema is stable - no more random crashes
- ✅ All validated modules are connected properly
- ✅ Tests can run without live data

### You Will Notice
- ✅ `View History` menu option never crashes anymore
- ✅ Clearer error messages if yfinance not installed
- ✅ Faster startup (lazy imports)

---

## Advanced Usage

### Run Market Analytics for Multiple Symbols
```powershell
foreach ($sym in @('SPY','QQQ','DIA','IWM')) {
    python market_analytics.py $sym
}
```

### Export Strategy Results
Use the trading interface menu option 8 (Export Strategy) to save strategies as Python files.

### Build Custom Strategies
Use the Strategy Builder in the interface (menu option 14) to create custom parameter combinations.

---

## Status Check

Run this anytime to verify everything is healthy:
```powershell
python validate_overhaul.py
```

Should show:
```
✅ ALL VALIDATION CHECKS PASSED
```

---

## Need Help?

See the documentation:
- `OVERHAUL_SUMMARY.md` - Quick summary of changes
- `PRODUCTION_OVERHAUL_COMPLETE.md` - Detailed technical documentation
- `QUICK_START.md` - Original quick start guide
- `README.md` - Full project documentation
