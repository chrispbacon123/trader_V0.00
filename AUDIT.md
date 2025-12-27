# PRODUCTION AUDIT FINDINGS
**Date**: 2025-12-24  
**Status**: Phase 0 - Complete call graph mapping and defect identification

## EXECUTIVE SUMMARY
This audit traces the end-to-end call graph for report generation, strategy execution, portfolio sizing, and backtesting. It identifies all correctness bugs, silent inconsistencies, and architectural issues that prevent this platform from being production-grade.

---

## 1. CALL GRAPH ANALYSIS

### 1.1 Report Generation Pipeline
```
trading_cli.py → market_analytics.py → MarketAnalytics.print_comprehensive_analysis()
    ├── CanonicalDataFetcher.fetch() → standardized OHLCV + Price column
    ├── ValidatedIndicators → RSI, Stoch, MACD, ADX (Wilder methods)
    ├── ValidatedKeyLevels → S/R, Fibonacci (with anchor validation)
    ├── ValidatedRegime → regime classification (reconciled with ADX)
    └── ValidatedRisk → volatility, VaR, CVaR, Sharpe, Sortino, Calmar
```
**Status**: ✅ REFACTORED - Now uses validated modules consistently

### 1.2 Strategy Signal Generation
```
Strategy Modules:
├── ml_strategy.py → RandomForestClassifier on technical features
├── optimized_ml_strategy.py → Ensemble (RF + GB + SVC) with feature engineering
├── simple_strategy.py → SMA crossover
└── short_term_strategy.py → RSI overbought/oversold

All strategies:
1. Fetch raw data via yfinance
2. Compute features (Close, RSI, MACD, etc.)
3. Generate signals (-1, 0, 1)
4. Size positions → **DEFECT: hard int() casts**
5. Execute trades
```

### 1.3 Portfolio Sizing/Execution
```
ValidatedPortfolio.allocate_to_targets()
    ├── ideal_shares = target_value / price
    ├── if fractional_allowed: shares = ideal_shares
    └── else: shares = np.floor(ideal_shares)

Strategy modules (ml_strategy, optimized_ml_strategy, simple_strategy, short_term_strategy):
    ├── **DEFECT**: Direct int(ideal_shares) casts that bypass PORTFOLIO_CFG
    └── **DEFECT**: No routing through ValidatedPortfolio for consistency
```

### 1.4 Backtest Loop
```
unified_backtest_engine.py → BacktestEngine
    ├── Run strategy over historical data
    ├── Track equity curve
    ├── Calculate returns: equity_curve.pct_change().dropna()
    └── Compute metrics via performance_analytics.py
```

---

## 2. CRITICAL DEFECTS

### 2.1 ❌ RETURNS DEFINITION INCONSISTENCY

**Problem**: Multiple conflicting return definitions across the codebase

| Module | Return Type | First Value | Notes |
|--------|-------------|-------------|-------|
| `canonical_data.py:218` | Log returns | `fillna(0)` | ❌ Synthetic zero injected |
| `validated_risk.py:26` | Log returns | `fillna(0)` | ❌ Synthetic zero injected |
| `ml_strategy.py:48` | Log returns | Not filled | ✅ Correct (NaN) |
| `optimized_ml_strategy.py:51` | Log returns | Not filled | ✅ Correct (NaN) |
| `performance_analytics.py:22` | Simple returns | `fillna(0)` | ❌ Synthetic zero injected |
| `validated_regime.py:79` | Simple returns | `.dropna()` | ✅ Correct |
| `run_deterministic_tests.py:398` | Log returns | `fillna(0)` | ❌ Synthetic zero in tests |
| `tests/test_comprehensive.py:325` | Log returns | `fillna(0)` | ❌ Synthetic zero in tests |

**Impact**: 
- Risk metrics (volatility, Sharpe, VaR) computed on contaminated returns series
- First period artificially contributes 0% return instead of being excluded
- Inconsistent sample sizes across metrics (N vs N-1)

**Fix Required**:
- Remove ALL `fillna(0)` from return calculations
- Standardize on log returns: `np.log(prices / prices.shift(1))`
- First value must be NaN, downstream must `.dropna()`
- Add central function: `get_returns(prices, kind='log') -> pd.Series`

---

### 2.2 ❌ FRACTIONAL SHARES: SILENT WHOLE-SHARE CASTS

**Problem**: Strategy modules bypass `PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED`

| File | Line | Code | Issue |
|------|------|------|-------|
| `ml_strategy.py` | 259 | `shares = int(ideal_shares)` | Hard cast to int |
| `optimized_ml_strategy.py` | 311 | `shares = int(ideal_shares)` | Hard cast to int |
| `simple_strategy.py` | 88 | `shares = int(ideal_shares)` | Hard cast to int |
| `short_term_strategy.py` | 114 | `shares = int(ideal_shares)` | Hard cast to int |
| `risk_management.py` | 42, 177, 193, 211, 242 | `shares = int(shares)` | Multiple hard casts |
| `risk_manager.py` | 103, 229 | `shares = int(shares)` | Hard casts |
| `order_execution.py` | 138 | `quantity = int(quantity)` | Hard cast |

**Impact**:
- Config flag `FRACTIONAL_SHARES_ALLOWED` is ignored
- Cash residual not tracked (capital efficiency loss)
- Tests pass but actual strategies force whole shares

**Fix Required**:
- Gate ALL int/floor casts: `if not PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED: shares = int(shares)`
- Centralize sizing logic in ONE place (prefer `ValidatedPortfolio`)
- Track cash residual explicitly: `cash_residual = target_value - (shares * price)`

---

### 2.3 ❌ VOLATILITY UNIT INCOHERENCE

**Problem**: Regime thresholds and computed volatility use different units

```python
# validated_regime.py:79-85
returns = recent_df['Price'].pct_change().dropna()  # Daily simple returns
vol = returns.std() * np.sqrt(252)  # Annualized
# BUT compares to:
RegimeConfig.VOL_LOW_THRESHOLD = 0.015  # "annualized" but way too low
RegimeConfig.VOL_HIGH_THRESHOLD = 0.03   # "annualized" but way too low
```

**Impact**:
- SPY (typical annualized vol ~15-20%) is always classified as VOLATILE
- Thresholds are 100x too small (1.5% vs 15%)
- Output says "annualized" but thresholds don't match real equity volatility

**Fix Required**:
- Update `RegimeConfig.VOL_LOW_THRESHOLD = 0.10` (10% annualized)
- Update `RegimeConfig.VOL_HIGH_THRESHOLD = 0.25` (25% annualized)
- Add assertion: `assert 'annualized' in label → vol computed with sqrt(252)`
- Print measured vol and thresholds in same units in rationale

---

### 2.4 ❌ PRICE SERIES INCONSISTENCY

**Problem**: Different price series used for returns across modules

| Module | Price for Returns | Notes |
|--------|-------------------|-------|
| `canonical_data.py` | `Price` column (canonical) | ✅ Correct |
| `validated_risk.py` | `Price` column | ✅ Correct |
| `validated_regime.py` | `Price` column | ✅ Correct |
| `ml_strategy.py` | `Close` (raw yfinance) | ❌ Not canonical |
| `optimized_ml_strategy.py` | `Close` (raw yfinance) | ❌ Not canonical |
| `performance_analytics.py` | `Close` | ❌ Not canonical |
| `alpha_engine.py` | `Close` | ❌ Not canonical |
| `data_handler.py` | `Close` | ❌ Not canonical |

**Impact**:
- Returns computed on unadjusted Close miss splits/dividends
- Metrics from different modules not comparable
- `CanonicalDataFetcher` provides `Adj Close → Price` but strategies ignore it

**Fix Required**:
- Standardize ALL return calculations to use canonical `Price` column
- Strategy modules must use `CanonicalDataFetcher` or at minimum copy `Adj Close → Price`
- Add validation: `assert 'Price' in df.columns` before computing returns

---

### 2.5 ⚠️ HORIZON/LOOKBACK INCONSISTENCY

**Problem**: Magic numbers for lookbacks scattered throughout codebase

| Metric | Config Constant | Actual Usage |
|--------|----------------|--------------|
| RSI period | `INDICATOR_CFG.RSI_PERIOD = 14` | ✅ Used via ValidatedIndicators |
| Fibonacci lookback | `LEVEL_CFG.FIB_LOOKBACK = 100` | ✅ Used via ValidatedKeyLevels |
| Regime lookback | `REGIME_CFG.REGIME_LOOKBACK = 252` | ✅ Used via ValidatedRegime |
| Risk lookback | `RISK_CFG.RISK_LOOKBACK = 252` | ✅ Used via ValidatedRisk |
| Strategy features | Hardcoded 5,10,20,50,200 | ❌ Not in config |
| ADX period | Hardcoded 14 | ❌ Should be `INDICATOR_CFG.ADX_PERIOD` |

**Impact**:
- Inconsistent horizons when report sections computed independently
- Hard to verify anchors match declared windows
- Difficult to configure for different timeframes

**Fix Required**:
- Move all lookback magic numbers to `core_config.py`
- Add `INDICATOR_CFG.MA_PERIODS = [5, 10, 20, 50, 200]`
- Ensure printed outputs always label their horizon: "RSI(14)", "Fib(100d)"

---

### 2.6 ❌ VAR/CVAR SAMPLE SIZE MISMATCH

**Problem**: VaR/CVaR computed without explicit horizon declaration

```python
# validated_risk.py:86-118
def var_95(returns: pd.Series) -> Dict:
    returns_clean = returns.dropna()
    var = np.percentile(returns_clean, 5)  # 5th percentile
    # But what is the horizon? Daily? Multi-day? Not labeled.
```

**Impact**:
- VaR reported as single number without horizon context
- Sample size not validated against returns length
- Method not specified (historical vs parametric)

**Fix Required**:
- Add explicit `horizon` parameter (default 1 day)
- Add explicit `method` parameter ('historical', 'parametric')
- Validate: `assert len(returns_clean) >= 30, "Insufficient data for VaR"`
- Label output: "VaR(95%, 1-day, historical) = -1.65%"

---

## 3. ARCHITECTURAL ISSUES

### 3.1 Duplicate Indicator Implementations
- `advanced_indicators.py` re-implements RSI/ADX (different from ValidatedIndicators)
- `strategy_builder.py` re-implements RSI (different formula)
- `data_manager.py` re-implements RSI (different formula)

**Fix**: Remove duplicates, use ValidatedIndicators everywhere

### 3.2 No Centralized Sizing Logic
- Each strategy module implements its own share sizing
- No consistent handling of commissions/slippage
- Cash residual not tracked

**Fix**: Create `sizing.py` with:
```python
def calculate_shares(target_value, price, fractional_allowed, min_position_value):
    ideal_shares = target_value / price
    if fractional_allowed:
        shares = ideal_shares
    else:
        shares = np.floor(ideal_shares)
    
    position_value = shares * price
    cash_residual = target_value - position_value
    
    if position_value < min_position_value:
        return 0, target_value  # No position
    
    return shares, cash_residual
```

### 3.3 Test Suite Uses Contaminated Returns
- `run_deterministic_tests.py` and `tests/test_comprehensive.py` use `.fillna(0)`
- Tests pass even though logic is wrong
- Need deterministic fixtures (CSV) not live yfinance

**Fix**: Phase 2 will add proper test harness

---

## 4. PHASE 1 REMEDIATION PLAN

### 4.1 Fix Returns Definition (CRITICAL)
**Files to modify**:
- ✅ `canonical_data.py:218` - Remove fillna(0)
- ✅ `validated_risk.py:26` - Remove fillna(0)
- ❌ `performance_analytics.py:22` - Remove fillna(0)
- ❌ `alpha_engine.py:67,101` - Use canonical returns
- ❌ `run_deterministic_tests.py:398` - Remove fillna(0)
- ❌ `tests/test_comprehensive.py:325,344,357` - Remove fillna(0)

**Add central utility**:
```python
# canonical_data.py
def get_returns(prices: pd.Series, kind: str = 'log') -> pd.Series:
    """
    Calculate returns from price series.
    
    Args:
        prices: Price series (must be canonical Price column)
        kind: 'log' (default) or 'simple'
    
    Returns:
        Series with NaN for first value (NOT filled)
    """
    if kind == 'log':
        return np.log(prices / prices.shift(1))
    elif kind == 'simple':
        return prices.pct_change()
    else:
        raise ValueError(f"kind must be 'log' or 'simple', got {kind}")
```

### 4.2 Fix Fractional Shares End-to-End (CRITICAL)
**Pattern to apply everywhere**:
```python
from core_config import PORTFOLIO_CFG

ideal_shares = target_value / price

if PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED:
    shares = ideal_shares
else:
    shares = np.floor(ideal_shares)

position_value = shares * price
cash_residual = target_value - position_value
```

**Files to modify**:
- `ml_strategy.py:259`
- `optimized_ml_strategy.py:311`
- `simple_strategy.py:88`
- `short_term_strategy.py:114`
- `risk_management.py:42,177,193,211,242`
- `risk_manager.py:103,229`
- `order_execution.py:138`
- `strategy_builder.py` (if it does sizing)

### 4.3 Fix Regime Volatility Thresholds (CRITICAL)
**File**: `core_config.py`
```python
VOL_LOW_THRESHOLD: float = 0.10   # 10% annualized
VOL_HIGH_THRESHOLD: float = 0.25  # 25% annualized
```

**File**: `validated_regime.py`
- Add assertion that measured vol is realistic (e.g., 0.05 < vol < 1.0)
- Print thresholds and measured vol in rationale

### 4.4 Standardize to Canonical Price Series (HIGH)
**Files to modify**:
- `ml_strategy.py:48` - Use canonical Price, not Close
- `optimized_ml_strategy.py:51` - Use canonical Price
- `performance_analytics.py:22` - Use canonical Price
- `alpha_engine.py:*` - Use canonical Price
- `data_handler.py:117` - Use canonical Price

**Pattern**:
```python
from canonical_data import CanonicalDataFetcher
fetcher = CanonicalDataFetcher()
df, metadata = fetcher.fetch(symbol, start, end, interval)
# Now df has 'Price' column (Adj Close if available, else Close)
returns = fetcher.get_returns(df)  # Log returns from canonical Price
```

### 4.5 Add VaR/CVaR Horizon/Method Labels (MEDIUM)
**File**: `validated_risk.py`
```python
def var_95(returns: pd.Series, horizon: int = 1, method: str = 'historical') -> Dict:
    """
    Calculate Value at Risk
    
    Args:
        returns: Daily returns (must be clean, no NaN)
        horizon: Number of days (default 1)
        method: 'historical' or 'parametric'
    """
    returns_clean = returns.dropna()
    assert len(returns_clean) >= 30, "Insufficient data for VaR"
    
    if method == 'historical':
        var = np.percentile(returns_clean, 5)
    elif method == 'parametric':
        var = returns_clean.mean() - 1.645 * returns_clean.std()
    
    return {
        'value': var,
        'horizon': f'{horizon}-day',
        'method': method,
        'sample_size': len(returns_clean)
    }
```

---

## 5. SUCCESS CRITERIA

### Phase 1 Complete When:
- ✅ No `.fillna(0)` on returns anywhere
- ✅ All return calculations use canonical `Price` column
- ✅ All strategies respect `FRACTIONAL_SHARES_ALLOWED` flag
- ✅ Regime volatility thresholds produce sensible classifications
- ✅ VaR/CVaR outputs include horizon and method labels
- ✅ No integer share casts outside fractional flag check
- ✅ All lookback windows use config constants

### Phase 2 Complete When:
- ✅ Test suite uses deterministic fixtures (CSV)
- ✅ Tests validate: RSI/Stoch/ADX in [0,100], MACD_hist == MACD - signal
- ✅ Tests validate: fib anchors within declared lookback
- ✅ Tests validate: annualized vol == daily vol * sqrt(252)
- ✅ Tests validate: fractional shares propagate end-to-end
- ✅ Tests validate: returns length == rows - 1 (no synthetic zero)

### Phase 3 Complete When:
- ✅ Pipeline API: `analyze(symbol) -> structured dict`
- ✅ Strategy interface: signals → weights → sizing → execution
- ✅ Backtest improvements: slippage/commission/leverage/logging
- ✅ Diagnostics mode prints all assumptions

---

## 6. FILES REQUIRING CHANGES

### CRITICAL (Phase 1a - Returns + Fractional)
1. `canonical_data.py` - Remove fillna(0), add get_returns()
2. `validated_risk.py` - Remove fillna(0)
3. `ml_strategy.py` - Fix returns, fix fractional shares
4. `optimized_ml_strategy.py` - Fix returns, fix fractional shares
5. `simple_strategy.py` - Fix fractional shares
6. `short_term_strategy.py` - Fix fractional shares
7. `risk_management.py` - Fix fractional shares (5 locations)
8. `risk_manager.py` - Fix fractional shares (2 locations)
9. `order_execution.py` - Fix fractional shares
10. `core_config.py` - Fix regime vol thresholds

### HIGH (Phase 1b - Consistency)
11. `performance_analytics.py` - Use canonical Price, remove fillna
12. `alpha_engine.py` - Use canonical Price
13. `data_handler.py` - Use canonical Price
14. `validated_regime.py` - Add assertion and threshold printing
15. `validated_risk.py` - Add VaR/CVaR horizon/method labels

### MEDIUM (Phase 1c - Architecture)
16. `strategy_builder.py` - Use ValidatedIndicators, fix fractional
17. Create `sizing.py` - Centralized share calculation
18. Remove duplicate indicators from `advanced_indicators.py`, `data_manager.py`

### TEST FIXES (Phase 2)
19. `run_deterministic_tests.py` - Remove fillna(0)
20. `tests/test_comprehensive.py` - Remove fillna(0), add new tests
21. `tests/fixtures.py` - Add synthetic generators
22. `tests/data/spy_daily.csv` - Add frozen fixture

---

## 7. ESTIMATED IMPACT

| Issue | Severity | Files Affected | Est. Fix Time |
|-------|----------|----------------|---------------|
| Returns fillna(0) | **CRITICAL** | 7 | 30 min |
| Fractional shares bypass | **CRITICAL** | 9 | 45 min |
| Regime vol thresholds | **CRITICAL** | 2 | 15 min |
| Price series inconsistency | **HIGH** | 6 | 60 min |
| VaR/CVaR labeling | **MEDIUM** | 1 | 20 min |
| Duplicate indicators | **LOW** | 3 | 30 min |

**Total Phase 1**: ~3 hours  
**Total Phase 2**: ~2 hours  
**Total Phase 3**: ~4 hours  

**TOTAL PROJECT**: ~9 hours to production-ready

---

## NEXT STEPS

1. **Execute Phase 1a** (returns + fractional) - CRITICAL PATH
2. **Run existing tests** to identify breakage
3. **Execute Phase 1b** (consistency)
4. **Execute Phase 1c** (architecture)
5. **Build Phase 2 test harness**
6. **Iterate until tests green**
7. **Execute Phase 3 generative features**

---

**End of Audit - Ready to proceed with remediation**
