# Phase 1: Correctness Fixes - Execution Log

## Completed Fixes

### 1. Fractional Shares End-to-End ✓
**Files Modified:**
- `strategy_builder.py`: Replaced `int(position_value / current_price)` with `calculate_shares()` from `sizing.py`
- `short_term_strategy.py`: Replaced manual `int(ideal_shares)` logic with `calculate_shares()`

**Remaining Files to Fix:**
- `simple_strategy.py`: Line 88 still has `int(ideal_shares)` 
- `risk_management.py`: Lines 42, 177, 193, 211, 242 have `int(shares)`
- `risk_manager.py`: Lines 103, 229 have `int(max_shares)` and `int(shares_diff)`
- `order_execution.py`: Line 138 has `int(quantity)`

**Status:** Partial - Need to fix remaining modules

### 2. Canonical Returns (No Synthetic Zeros)
**Files to Audit:**
- `canonical_data.py`: ✓ Already correct - `get_returns()` returns NaN for first value
- Need to audit all consumers to ensure they use `.dropna()` properly

**Status:** Canonical module correct, need to audit consumers

### 3. Unit Coherence (Volatility/Risk)
**Files to Check:**
- `validated_regime.py`: Need to verify annualized vol thresholds are realistic
- `validated_risk.py`: Need to verify VaR/CVaR horizon labels
- `market_analytics.py`: Need to verify all output units are labeled

**Status:** Not started

### 4. Timeframe/Horizon Consistency
**Need to Verify:**
- All indicator lookbacks use `core_config.py` constants
- All regime/level/risk modules label their horizons
- Fib anchors print dates (already done in `validated_levels.py`)

**Status:** Partial - validated modules done, need to audit strategies

## Next Actions

1. Complete fractional share fixes in remaining modules
2. Audit all returns consumers for proper `.dropna()` usage
3. Fix regime volatility thresholds
4. Add horizon/unit labels to all outputs
5. Run comprehensive tests

## Files Still Using Hardcoded `int()` Casts

```
simple_strategy.py:88
risk_management.py:42,177,193,211,242
risk_manager.py:103,229
order_execution.py:138
```

All of these need to be gated behind `PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED`.
