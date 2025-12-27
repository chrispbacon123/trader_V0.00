# PHASE 1 REMEDIATION - IN PROGRESS

## Completed (Phase 1A)

### ✅ Returns Definition Fixed
- **canonical_data.py**: Removed `fillna(0)`, added `kind` parameter ('log'|'simple')
- **validated_risk.py**: Removed `fillna(0)` from calculate_returns()
- **Pattern**: All returns now have NaN for first value, downstream must `.dropna()`

### ✅ Centralized Sizing Module Created
- **sizing.py**: New module with `calculate_shares()`, `format_shares()`, `calculate_transaction_costs()`
- Handles fractional vs whole shares consistently
- Tracks cash residual explicitly
- Uses `PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED` from config

### ✅ ML Strategy Fixed (ml_strategy.py)
- Added imports: `CanonicalDataFetcher`, `sizing`, `PORTFOLIO_CFG`
- Fixed `create_features()` to use canonical `Price` column (not raw `Close`)
- Fixed backtest loop to use `calculate_shares()` (no more `int(ideal_shares)`)
- Fixed print formatting to use `format_shares()`

### ✅ Regime Volatility Thresholds (Already Fixed in core_config.py)
- `VOL_LOW_THRESHOLD = 0.12` (12% annualized)
- `VOL_HIGH_THRESHOLD = 0.25` (25% annualized)
- Correctly aligned with typical equity volatility

---

## Remaining (Phase 1B - Critical)

### ❌ Strategy Files Still Need Fixing

#### optimized_ml_strategy.py
- Line 51: Use `Price` not `Close` for Log_Returns
- Line 70: Use `Price` not `Close` for RSI delta
- Line 95: Use `Price` not `Close` for OBV
- Line 311: Replace `int(ideal_shares)` with `calculate_shares()`
- Line 370: Use `format_shares()` for printing

#### simple_strategy.py
- Use canonical Price column
- Line 88: Replace `int(ideal_shares)` with `calculate_shares()`
- Line 128: Use `format_shares()` for printing

#### short_term_strategy.py
- Line 43: Use `Price` not `Close` for RSI delta
- Line 114: Replace `int(ideal_shares)` with `calculate_shares()`
- Line 172: Use `format_shares()` for printing

#### risk_management.py
- Lines 42, 177, 193, 211, 242: Gate `int(shares)` behind fractional flag

#### risk_manager.py
- Lines 103, 229: Gate `int(shares)` behind fractional flag

#### order_execution.py
- Line 138: Gate `int(quantity)` behind fractional flag

---

## Remaining (Phase 1C - Medium Priority)

### ❌ Consistent Price Series

#### performance_analytics.py
- Line 22: Remove `fillna(0)` from calculate_returns()
- Use canonical Price column throughout

#### alpha_engine.py
- Lines 55, 67, 76, 101, 118: Use canonical Price column
- Remove OBV `fillna(0)` at line 101

#### data_handler.py
- Line 117: Use canonical Price column for returns

---

## Remaining (Phase 1D - Architecture)

### ❌ Duplicate Indicator Removal
- `advanced_indicators.py`: Remove RSI/ADX, use ValidatedIndicators
- `data_manager.py`: Remove RSI, use ValidatedIndicators
- `strategy_builder.py`: Remove RSI, use ValidatedIndicators

### ❌ VaR/CVaR Labeling
- `validated_risk.py`: Add horizon and method parameters to var_95(), cvar_95()
- Output format: "VaR(95%, 1-day, historical) = -1.65%"

---

## Test Fixes (Phase 2)

### ❌ Test Files to Fix
- `run_deterministic_tests.py`: Line 398 remove `fillna(0)`
- `tests/test_comprehensive.py`: Lines 325, 344, 357 remove `fillna(0)`
- All tests must validate fractional shares propagate correctly

---

## Estimated Completion

| Phase | Status | Time Remaining |
|-------|--------|----------------|
| Phase 1A (Critical path) | ✅ 60% Complete | 45 min |
| Phase 1B (Strategies) | ⏳ In Progress | 30 min |
| Phase 1C (Consistency) | ⏳ Pending | 20 min |
| Phase 1D (Architecture) | ⏳ Pending | 30 min |
| **Total Phase 1** | **60%** | **~1.5 hours** |

---

## Next Immediate Actions

1. Fix optimized_ml_strategy.py (highest priority - it's the main ML strategy)
2. Fix simple_strategy.py and short_term_strategy.py
3. Fix risk_management.py and risk_manager.py
4. Run test suite to validate changes
5. Fix remaining performance_analytics.py, alpha_engine.py
6. Phase 2: Build comprehensive test harness
7. Phase 3: Generative platform features

---

**Status**: Phase 1 is 60% complete. Core infrastructure (returns, sizing, config) is fixed. Now applying fixes across strategy modules systematically.
