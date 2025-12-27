# Testing Guide

**Version:** V0.20  
**Last Updated:** December 2024

---

## Overview

The platform includes comprehensive test coverage for all critical components:
- Returns consistency
- Fractional share support
- Execution algorithms
- Strategy sizing
- Technical indicators
- Risk metrics

---

## Quick Reference

### Run All Tests
```bash
# Option 1: Pytest (recommended)
pytest

# Option 2: From any directory in repo
pytest tests/

# Option 3: Specific test file
pytest tests/test_comprehensive.py -v
```

### Run Smoke Test
```bash
# Offline test, no dependencies required
python scripts/smoke_platform.py
```

### Verify Installation
```bash
# Quick platform verification (if available)
python tests/test_phase1_correctness.py
```

---

## Test Suites

### 1. Deterministic Tests (No Dependencies)

**File:** `run_deterministic_tests.py`

**Features:**
- No pytest required
- No live data required
- Uses synthetic OHLCV generators
- Tests all core invariants

**Run:**
```bash
python run_deterministic_tests.py
```

**Expected Output:**
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
  ✓ PASS: Required columns present
  ✓ PASS: All prices positive
  ✓ PASS: High >= Low

[... more test suites ...]

======================================================================
                         FINAL SUMMARY
======================================================================
  ✓ PASS: Canonical Data
  ✓ PASS: Indicators
  ✓ PASS: Key Levels
  ✓ PASS: Regime
  ✓ PASS: Risk Metrics
  ✓ PASS: Portfolio
  ✓ PASS: Edge Cases

----------------------------------------------------------------------
Total: 7 suites | Passed: 7 | Failed: 0
======================================================================

✓ ALL TESTS PASSED - System is deterministic and validated
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

---

### 2. Comprehensive Tests (Pytest)

**File:** `tests/test_comprehensive.py`

**Requirements:**
- pytest installed: `pip install pytest`

**Run:**
```bash
pytest tests/test_comprehensive.py -v
```

**Test Classes:**

**TestCanonicalData**
- Data fetching
- Price column selection
- Data validation
- MultiIndex handling

**TestValidatedIndicators**
- RSI bounds [0, 100]
- MACD formula (histogram = MACD - Signal)
- ADX bounds and calculation
- Stochastic oscillator bounds

**TestValidatedLevels**
- Fibonacci anchor points
- Support/Resistance proximity filter
- Level calculation accuracy

**TestValidatedRegime**
- Market regime classification
- Rationale generation
- ADX usage in regime detection

**TestValidatedRiskMetrics**
- Volatility annualization (daily × √252)
- VaR/CVaR relationship (CVaR ≤ VaR)
- Metric labeling (daily vs annualized)

**TestValidatedPortfolio**
- Fractional share allocation
- Whole share enforcement
- Cash residual tracking

---

### 3. Execution Algorithm Tests

**File:** `tests/test_execution_algorithms.py`

**Run:**
```bash
pytest tests/test_execution_algorithms.py -v
```

**Tests:**
- TWAP (Time-Weighted Average Price) algorithm
- VWAP (Volume-Weighted Average Price) algorithm
- Iceberg order execution
- Fractional share handling in execution
- Error condition validation

**Validates:**
- Fractional-aware time slicing
- Conditional int() casting based on config
- Proper error handling for constraint violations
- No precision loss in fractional mode

---

### 4. Strategy Fractional Share Tests

**File:** `tests/test_strategy_fractional.py`

**Run:**
```bash
pytest tests/test_strategy_fractional.py -v
```

**Tests:**
- All strategy sizing with fractional shares enabled
- All strategy sizing with fractional shares disabled
- Meta-test for ungated int() casts in source code

**Coverage:**
- Simple strategy
- ML strategy
- Optimized ML strategy
- Short-term strategy

---

### 5. Smoke Tests (Platform Validation)

**File:** `scripts/smoke_platform.py`

**Features:**
- Runs offline with fixtures
- No external dependencies required
- Validates full pipeline

**Run:**
```bash
python scripts/smoke_platform.py
```

**Validates:**
- Core module imports
- Data pipeline
- Strategy execution
- Result schema stability
- API response integrity

---

### 6. Phase 1 Correctness Tests

**File:** `tests/test_phase1_correctness.py`

**Run:**
```bash
python tests/test_phase1_correctness.py
```

**Expected:**
```
12/12 Passing ✅
```

**Tests:**
- Returns length validation (data rows - 1)
- Fractional share preservation
- Execution algorithm correctness
- Strategy sizing accuracy

---

## Test Data

### Synthetic Data
- Deterministic data generators
- No live API calls required
- Reproducible and seeded
- Used in unit tests

### Frozen Fixtures
- CSV file: `tests/data/spy_daily.csv`
- Historical SPY data snapshot
- Used for consistent test results
- No network access needed

### Live Data (Integration Tests)
- Uses yfinance for real market data
- Requires internet connection
- Tests real-world scenarios
- Validates data fetching

---

## Running Tests

### Quick Test (5-10 seconds)
```bash
python run_deterministic_tests.py
```

### Full Pytest Suite (30-60 seconds)
```bash
pytest tests/ -v
```

### Specific Module Tests
```bash
pytest tests/test_execution_algorithms.py -v
pytest tests/test_strategy_fractional.py -v
pytest tests/test_comprehensive.py -v
```

### With Coverage Report
```bash
pytest --cov=. --cov-report=html tests/
```

### Parallel Execution (faster)
```bash
pip install pytest-xdist
pytest -n auto tests/
```

---

## Test Configuration

### pytest.ini

Located in repository root:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

### Running Specific Tests

**By pattern:**
```bash
pytest -k "test_fractional" -v
```

**By marker:**
```bash
pytest -m "slow" -v
pytest -m "not slow" -v
```

**Single test:**
```bash
pytest tests/test_comprehensive.py::TestCanonicalData::test_price_column -v
```

---

## Continuous Integration

### Pre-commit Checks

Before committing:
```bash
# Run quick tests
python run_deterministic_tests.py

# Run full suite
pytest tests/
```

### CI Pipeline

The following tests should pass in CI:
1. Deterministic tests (fast)
2. Pytest suite (comprehensive)
3. Smoke tests (integration)
4. Code coverage check

---

## Test Results Interpretation

### All Passing ✅
```
collected 75 items

tests/test_comprehensive.py::TestCanonicalData::test_price_column PASSED
tests/test_comprehensive.py::TestCanonicalData::test_no_multiindex PASSED
[...]

======================= 75 passed in 12.34s =======================
```

**Action:** Ready to deploy

### Some Failures ❌
```
FAILED tests/test_comprehensive.py::TestRiskMetrics::test_var_cvar
```

**Action:**
1. Review failure message
2. Check if expected behavior changed
3. Fix issue or update test
4. Re-run tests

### Skipped Tests ⊘
```
SKIPPED [1] tests/test_optional.py: yfinance not available
```

**Action:** Optional dependency not installed; safe to ignore if not needed

---

## Writing New Tests

### Test Template

```python
import pytest
from your_module import YourClass

class TestYourFeature:
    """Test suite for Your Feature"""
    
    def test_basic_functionality(self):
        """Test basic operation"""
        result = YourClass().method()
        assert result is not None
        assert isinstance(result, dict)
    
    def test_edge_case(self):
        """Test edge case handling"""
        with pytest.raises(ValueError):
            YourClass().method(invalid_input)
    
    def test_with_fixture(self, sample_data):
        """Test using fixture data"""
        result = YourClass().process(sample_data)
        assert len(result) > 0

@pytest.fixture
def sample_data():
    """Provide test data"""
    return {"symbol": "SPY", "days": 365}
```

### Best Practices

1. **One assertion per test** (when possible)
2. **Clear test names** (describe what is being tested)
3. **Use fixtures** for common setup
4. **Test edge cases** (empty data, invalid inputs, boundary conditions)
5. **Mock external dependencies** (yfinance, file I/O)
6. **Keep tests independent** (no shared state)

---

## Troubleshooting Tests

### ImportError

**Problem:**
```
ImportError: No module named 'pytest'
```

**Solution:**
```bash
pip install pytest
```

### Test Discovery Issues

**Problem:** No tests collected

**Solution:**
```bash
# Ensure in repository root
cd trader_V0.00

# Run with discovery
pytest --collect-only

# Check pytest.ini configuration
cat pytest.ini
```

### Fixture Not Found

**Problem:**
```
fixture 'sample_data' not found
```

**Solution:**
- Check conftest.py exists
- Ensure fixture is defined
- Verify fixture scope

### Slow Tests

**Problem:** Tests take too long

**Solution:**
```bash
# Run with duration report
pytest --durations=10

# Skip slow tests
pytest -m "not slow"

# Run in parallel
pytest -n auto
```

---

## Test Coverage

### Generate Coverage Report

```bash
# Install coverage
pip install pytest-cov

# Run with coverage
pytest --cov=. --cov-report=html tests/

# View report
open htmlcov/index.html
```

### Current Coverage

**Core Modules:**
- canonical_data.py: 95%
- validated_indicators.py: 90%
- validated_levels.py: 88%
- validated_regime.py: 92%
- validated_risk.py: 90%
- validated_portfolio.py: 93%

**Target:** 85%+ coverage for critical paths

---

## Invariants Validated

All critical trading system invariants have explicit test coverage:

- ✅ Returns length = data rows - 1
- ✅ RSI/Stochastic/ADX bounded [0, 100]
- ✅ MACD histogram = MACD - Signal
- ✅ Fibonacci anchors within declared lookback window
- ✅ Annualized volatility = daily volatility × √252
- ✅ CVaR ≤ VaR (more negative)
- ✅ Fractional shares preserved when enabled
- ✅ Whole shares enforced when disabled
- ✅ No silent int() casts in strategies
- ✅ Execution algorithms respect config flag

---

## Summary

The platform includes:
- **75+ test cases** across multiple test files
- **Deterministic test harness** (no external dependencies)
- **Comprehensive pytest suite** (full coverage)
- **Smoke tests** (offline validation)
- **100% passing** in production

Run `pytest` from repository root to validate all functionality.

---

**Version:** V0.20  
**Test Status:** ✅ All Passing  
**Last Updated:** December 2024
