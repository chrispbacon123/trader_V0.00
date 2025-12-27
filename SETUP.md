# Setup Guide

**Version:** V0.20  
**Last Updated:** December 2024  
**Copyright © 2024-2025 chrispbacon123. All Rights Reserved.**

> ⚠️ **PROPRIETARY SOFTWARE** - Personal/home use only. See [LICENSE](LICENSE).

---

---

## Prerequisites

- **Python 3.8 or higher** (Python 3.10+ recommended)
- **Git** (for cloning repository)
- **Internet connection** (for downloading market data)
- **4GB+ RAM** (for ML models)

## Step-by-Step Installation

### 1. Clone the Repository

```bash
git clone https://github.com/chrispbacon123/trader_V0.00.git
cd trader_V0.00
```

### 2. Create Virtual Environment

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages:
- pandas (data manipulation)
- numpy (numerical computing)
- yfinance (market data)
- scikit-learn (machine learning)
- xgboost (gradient boosting)
- lightgbm (light gradient boosting)
- matplotlib & seaborn (visualization)
- ta (technical analysis)
- optuna (optimization)

### 4. Verify Installation

Run the test suite:
```bash
python test_platform.py
```

You should see:
```
🎉 ALL TESTS PASSED!
```

### 5. Launch the Platform

**Method 1: Using launcher (recommended)**
```bash
chmod +x launch.sh  # First time only
./launch.sh
```

**Method 2: Direct execution**
```bash
python advanced_trading_interface.py
```

## First Run

When you first launch the platform, it will:
1. Create necessary directories (`custom_strategies/`, `strategy_exports/`)
2. Initialize configuration files
3. Display the main menu

## Troubleshooting

### Python Version Issues

**Check your Python version:**
```bash
python3 --version
```

**If < 3.8, install newer Python:**
- macOS: `brew install python@3.11`
- Ubuntu: `sudo apt install python3.11`
- Windows: Download from python.org

### Missing Dependencies

**If imports fail:**
```bash
source venv/bin/activate  # Activate venv first!
pip install --upgrade pip
pip install -r requirements.txt
```

### Permission Errors

**On macOS/Linux:**
```bash
chmod +x launch.sh
chmod +x test_platform.py
```

### Import Errors

**If you see "ModuleNotFoundError":**

1. Make sure virtual environment is activated:
   ```bash
   source venv/bin/activate  # You should see (venv) in prompt
   ```

2. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Check you're in the right directory:
   ```bash
   pwd  # Should show .../trader_V0.00 or .../lean-trading
   ```

### Data Download Errors

**If Yahoo Finance fails:**
- Check internet connection
- Try a different symbol (some may be delisted)
- Wait a few minutes (rate limiting)
- Use VPN if region-blocked

### Memory Errors

**If ML models crash:**
- Close other applications
- Use smaller backtest periods
- Reduce number of parallel optimizations

### macOS Specific

**If "externally-managed-environment" error:**
Always use virtual environment (already created in setup):
```bash
source venv/bin/activate
```

## Testing the Installation

### Quick Test

Run a simple backtest:
```bash
python advanced_trading_interface.py
```

Then select:
- Option 1 (Run Single Strategy)
- Symbol: SPY
- Days: 365
- Strategy: 1 (Simple)

You should see results and performance metrics.

### Full Test

Run comprehensive tests:
```bash
python test_platform.py --verbose
```

## Directory Structure After Setup

```
trader_V0.00/
├── venv/                          # Virtual environment (don't commit)
├── advanced_trading_interface.py  # Main application
├── strategy_builder.py            # Custom strategy builder
├── ml_strategy.py                 # ML trading strategy
├── simple_strategy.py             # Mean reversion strategy
├── optimized_ml_strategy.py       # Ensemble ML strategy
├── short_term_strategy.py         # Short-term trading
├── enhanced_utils.py              # Utility functions
├── strategy_manager.py            # Strategy management
├── market_analytics.py            # Market analysis tools
├── strategy_optimizer.py          # Optimization engine
├── unified_backtest_engine.py     # Backtesting core
├── advanced_settings.py           # Settings manager
├── requirements.txt               # Python dependencies
├── test_platform.py              # Test suite
├── launch.sh                     # Quick launcher
├── README.md                     # Overview
├── SETUP.md                      # This file
├── custom_strategies/            # Your custom strategies
└── strategy_exports/             # Exported strategies
```

## Updating the Platform

Pull latest changes:
```bash
cd trader_V0.00
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

## Uninstalling

```bash
cd ..
rm -rf trader_V0.00
```

## Next Steps

1. ✅ Complete installation
2. ✅ Run test suite
3. ✅ Launch platform
4. 📖 Read README.md for usage guide
5. 🎯 Start with simple backtests
6. 🚀 Build custom strategies
7. 💼 Create portfolios

## Support

- **Issues**: Report on GitHub Issues
- **Documentation**: See README.md
- **Examples**: Check menu option 11 (Help)

---

**You're all set! Happy trading! 📈**
