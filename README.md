# Advanced Quantitative Trading Platform 🚀

**Copyright © 2024-2025 chrispbacon123. All Rights Reserved.**  
**Proprietary Software - Personal/Home Use Only**

> **🎉 V0.20 RELEASE** ✅  
> Production-ready platform with comprehensive testing and documentation.
> 
> **📚 START HERE:**
> - **Quick overview:** Read this README
> - **Complete guide:** See [USER_GUIDE.md](USER_GUIDE.md)
> - **Setup instructions:** See [SETUP.md](SETUP.md)
> - **Run tests:** `pytest` (from any directory in repo) - See [TESTING.md](TESTING.md)
> - **Run UI:** `python advanced_trading_interface.py`

Professional-grade algorithmic trading platform with ML-powered strategies, advanced analytics, and comprehensive risk management.

---

## 🆕 What's New - V0.20 (December 2024)

### V0.20 Documentation & Consolidation ✅
- **Consolidated Documentation:** All guides unified into clear, sectioned documents
- **Updated References:** All documentation updated to V0.20
- **Simplified Structure:** Reduced from 90+ docs to 6 core documents
- **Clear Navigation:** Easy-to-follow guides for all user levels

### Core Documentation
1. **[README.md](README.md)** - This file: Quick overview and getting started
2. **[USER_GUIDE.md](USER_GUIDE.md)** - Complete user guide with workflows and examples
3. **[SETUP.md](SETUP.md)** - Installation and configuration instructions
4. **[TESTING.md](TESTING.md)** - Testing guide and validation procedures
5. **[CHANGELOG.md](CHANGELOG.md)** - Version history and updates
6. **[DEVELOPMENT.md](DEVELOPMENT.md)** - Technical details for developers

### Platform Features (Inherited from V0.14)
- **Version Consolidation:** Single canonical version in `core_config.PLATFORM_VERSION`
- **Smoke Test Runner:** `scripts/smoke_platform.py` runs offline with fixtures
- **Integration Tests:** 75+ tests covering all core functionality
- **Schema Stability:** All API responses have guaranteed keys (no KeyError crashes)
- **Optional Dependencies:** yfinance/optuna lazy-loaded, UI works without them

### Run Commands
```bash
# Run tests (from repo root)
pytest

# Run smoke test (offline, no yfinance needed)
python scripts/smoke_platform.py

# Run UI
python advanced_trading_interface.py
```

---

## 🔄 Version History

### V0.20 (Current) - Documentation Consolidation
- Unified documentation structure
- Clear sectioned guides
- Updated to current version
- Removed outdated status files

### V0.14 - Production Hardening
- Centralized versioning
- Smoke test runner
- Schema stability guarantees
- 75+ tests passing

### V0.13 - Optimization Reliability
- Double-fetch bug fixed
- Optimizer schema stability
- Random search support
- Memory-safe grid sampling

### V0.12 - Correctness Pass
- Data normalization unified
- Risk metrics labeled (daily vs annualized)
- Fractional shares end-to-end

### V0.03-V0.11 - Platform Development
- Test infrastructure (pytest)
- Optional dependencies
- Validated modules
- ML strategies

---

## Quick Start

### Windows
```powershell
cd trader_V0.00
python advanced_trading_interface.py
```

### Mac/Linux
```bash
# Clone repository
git clone https://github.com/chrispbacon123/trader_V0.00.git
cd trader_V0.00

# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
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

### Windows Installation
```powershell
# Install Python 3.12
winget install Python.Python.3.12

# Install required packages
python -m pip install yfinance pandas numpy scikit-learn xgboost optuna

# Run the platform
cd trader_V0.00
python advanced_trading_interface.py
```

### Mac/Linux Installation
```bash
# Option 1: Using virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install pandas numpy scikit-learn yfinance matplotlib seaborn plotly scipy joblib ta-lib xgboost optuna

# Option 2: Using system Python (not recommended)
pip install --user pandas numpy scikit-learn yfinance matplotlib seaborn plotly scipy joblib ta-lib xgboost optuna
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

## License

This software is proprietary and for personal, non-commercial, home use only. See [LICENSE](LICENSE) for full terms.

**Key Restrictions:**
- ✅ Personal/home use only
- ❌ No commercial use
- ❌ No redistribution
- ❌ No modification or derivative works
- ❌ No live trading or production use

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

---

## Recent Updates (December 2024)

### Data Integrity Fixes ✅
Fixed critical issues with support/resistance and pattern recognition calculations:

**Issues Resolved:**
- Support/resistance levels were analyzing entire historical dataset, mixing old price ranges
- Pattern recognition could include outlier levels from different market conditions
- Potential cross-contamination between different symbols

**Fixes Applied:**
- Limited support/resistance analysis to recent 100 days only
- Added 20% price proximity filter to current price
- Enhanced pattern recognition with temporal bounds
- Added fallback logic for edge cases
- Created comprehensive test suite (`test_data_integrity.py`)

**Impact:** Market analytics now provide accurate, relevant levels for current trading decisions without historical contamination.

**Files Modified:**
- `market_analytics.py` - Fixed support_resistance_levels()
- `advanced_indicators.py` - Fixed PatternRecognition.find_support_resistance()
- `test_data_integrity.py` - New test suite for data validation

**Testing:** Run `python test_data_integrity.py` to verify data integrity after updates.

### Dependencies Updated
Added required packages for ML strategies:
- `xgboost` - Gradient boosting for ML strategies
- `optuna` - Hyperparameter optimization

---

## System Validation & Testing 🧪

### Deterministic Test Harness
The platform includes a comprehensive test suite that validates all trading system invariants:

**Run Tests:**
```bash
python run_deterministic_tests.py
```

**What's Tested:**
- ✓ Canonical price series consistency (no MultiIndex confusion)
- ✓ Technical indicators bounded (RSI/Stoch/ADX in [0,100])
- ✓ MACD histogram = MACD - Signal
- ✓ Fibonacci anchors from declared lookback window
- ✓ Support/Resistance within proximity filter
- ✓ Market regime reconciles with ADX
- ✓ Risk metrics properly annualized and labeled
- ✓ Fractional share support (when enabled)
- ✓ Cash residuals tracked explicitly
- ✓ Edge cases handled (flat prices, short history, NaNs)

**Test Data:**
- Uses synthetic deterministic data generators (no live API calls required)
- Frozen SPY fixture available in `tests/data/spy_daily.csv`
- All tests are reproducible and seeded

**Documentation:**
- See [TESTING.md](TESTING.md) for full testing details
- Pytest suite also available in `tests/test_comprehensive.py`

### Validated Modules
The platform uses a validated architecture with explicit guarantees:

**Core Modules:**
- `canonical_data.py` - Single canonical price series, no MultiIndex
- `validated_indicators.py` - Wilder's RSI/ADX, bounded outputs
- `validated_levels.py` - Auditable Fibonacci anchors, proximity-filtered S/R
- `validated_regime.py` - Regime classification with rationale
- `validated_risk.py` - Labeled daily/annualized metrics
- `validated_portfolio.py` - Fractional share support with cash tracking

**Configuration:**
- All lookback windows centralized in `core_config.py`
- No magic numbers scattered in code
- Realistic default thresholds (e.g., 12-25% annualized volatility)

### Fractional Share Support
The platform fully supports fractional shares (broker-dependent):

**Enable/Disable:**
```python
# In core_config.py
PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = True  # or False
```

**Behavior:**
- When `True`: Shares are floats (e.g., 132.4567 shares)
- When `False`: Shares rounded down to integers (e.g., 132 shares)
- Cash residuals explicitly tracked in both cases
- Transaction costs and slippage properly applied

**Files Updated:**
- `validated_portfolio.py` - Core allocation logic
- `ml_strategy.py`, `optimized_ml_strategy.py`, `simple_strategy.py`, `short_term_strategy.py` - All strategies support fractional shares

---
