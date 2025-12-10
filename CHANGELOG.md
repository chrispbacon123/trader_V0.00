# Changelog

## [2.0.0] - 2023-12-10

### 🎉 Major Features

#### Custom Strategy Builder
- **Option 30**: Interactive strategy designer
- **Option 31**: Export for live trading (Python/JSON/LEAN)
- **Option 32**: Load and review strategies
- Define indicators, entry/exit rules, risk parameters
- Save and reuse strategies

### 🐛 Critical Fixes

#### Backtest Errors
✅ Fixed: `too many values to unpack (expected 3, got 4)`
- Updated all backtest calls to handle 4 return values
- Fixed portfolio backtest (line 1083)
- Fixed single strategy (line 310)
- Fixed comparison (line 799)

#### Data Issues
✅ Fixed: Insufficient data errors
✅ Improved: Validation and error messages
✅ Added: Better date range handling
✅ Enhanced: Compatibility with all asset types

### ✨ Enhancements

- Comprehensive help system
- Better error messages
- Improved documentation
- Quick start scripts
- Enhanced user experience

### 📦 New Files

- `strategy_builder.py`
- `QUICKSTART.md`
- `README.md` (updated)
- `run.sh`
- `CHANGELOG.md`

### ✅ Tested

All 32 menu options verified working:
- Single & batch strategy tests
- Portfolio management
- Custom strategy builder
- Export functionality
- Technical analysis
- Optimization tools

## [1.5.0] - Previous

- ML strategies
- Portfolio management
- Technical analysis
- Batch testing

## [1.0.0] - Initial

- Simple strategy
- Basic backtesting
- Results tracking

---

## Known Limitations

1. Daily data only (no intraday)
2. ML needs 60+ days data
3. Simplified transaction costs
4. Custom strategies need manual implementation

## Coming Soon

- Walk-forward analysis
- Monte Carlo simulation
- Intraday data
- Live trading integration

---

*Version 2.0 - December 2023*
