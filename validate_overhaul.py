"""
Quick Validation Script
Verifies core refactors without requiring pytest or yfinance
"""

import sys
import os

print("="*80)
print("PRODUCTION OVERHAUL - VALIDATION CHECK")
print("="*80)

# Test 1: Can we import modules without yfinance?
print("\n[Test 1] Import validation (no yfinance required)...")
try:
    from ml_strategy import MLTradingStrategy
    from simple_strategy import SimpleMeanReversionStrategy
    from optimized_ml_strategy import OptimizedMLStrategy
    from short_term_strategy import ShortTermStrategy
    from advanced_trading_interface import AdvancedTradingInterface
    print("✅ All strategies import successfully without yfinance")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: ValidatedRisk compatibility wrapper exists
print("\n[Test 2] ValidatedRisk API compatibility...")
try:
    from validated_risk import ValidatedRisk, ValidatedRiskMetrics
    assert hasattr(ValidatedRisk, 'compute_risk_metrics')
    print("✅ ValidatedRisk.compute_risk_metrics() exists")
except (ImportError, AssertionError) as e:
    print(f"❌ ValidatedRisk compatibility failed: {e}")
    sys.exit(1)

# Test 3: History normalization exists
print("\n[Test 3] History schema normalization...")
try:
    interface = AdvancedTradingInterface()
    assert hasattr(interface, 'normalize_history_record')
    
    # Test normalization with old format
    old_record = {
        'strategy_name': 'OldStrategy',
        'ticker': 'SPY', 
        'total_return': 5.5
    }
    normalized = interface.normalize_history_record(old_record)
    assert normalized['strategy'] == 'OldStrategy'
    assert normalized['symbol'] == 'SPY'
    assert normalized['return_pct'] == 5.5
    print("✅ History normalization working correctly")
except (ImportError, AssertionError, AttributeError) as e:
    print(f"❌ History normalization failed: {e}")
    sys.exit(1)

# Test 4: Lazy yfinance pattern
print("\n[Test 4] Lazy yfinance import pattern...")
try:
    from ml_strategy import _ensure_yfinance
    # Should not fail on import
    print("✅ Lazy yfinance pattern implemented")
    
    # Try to call it (will fail if yfinance not installed, but that's OK)
    try:
        yf = _ensure_yfinance()
        print("  Note: yfinance is installed")
    except ImportError:
        print("  Note: yfinance not installed (expected in test environment)")
except Exception as e:
    print(f"❌ Lazy import pattern failed: {e}")
    sys.exit(1)

# Test 5: Canonical data patterns
print("\n[Test 5] Canonical data module...")
try:
    from canonical_data import CanonicalDataFetcher
    fetcher = CanonicalDataFetcher()
    print("✅ CanonicalDataFetcher available")
except ImportError as e:
    print(f"❌ Canonical data failed: {e}")
    sys.exit(1)

# Test 6: Validated modules
print("\n[Test 6] Validated modules...")
try:
    from validated_indicators import ValidatedIndicators
    from validated_levels import ValidatedKeyLevels
    from validated_regime import ValidatedRegime
    from validated_portfolio import ValidatedPortfolio
    print("✅ All validated modules available")
except ImportError as e:
    print(f"❌ Validated modules failed: {e}")
    sys.exit(1)

# Test 7: Core config
print("\n[Test 7] Core configuration...")
try:
    from core_config import (
        PORTFOLIO_CFG, INDICATOR_CFG, LEVEL_CFG, 
        REGIME_CFG, RISK_CFG, DATA_CFG
    )
    print("✅ Core configuration available")
    print(f"  Fractional shares: {PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED}")
    print(f"  RSI period: {INDICATOR_CFG.RSI_PERIOD}")
    print(f"  Regime vol thresholds: {REGIME_CFG.VOL_LOW_THRESHOLD} / {REGIME_CFG.VOL_HIGH_THRESHOLD}")
except ImportError as e:
    print(f"❌ Core config failed: {e}")
    sys.exit(1)

# Test 8: Sizing module
print("\n[Test 8] Centralized sizing...")
try:
    from sizing import calculate_shares, calculate_shares_from_weight, format_shares
    from core_config import PORTFOLIO_CFG
    
    # Test fractional
    PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = True
    shares_frac = calculate_shares(cash=10000, price=100, buffer=0.05)
    assert isinstance(shares_frac, float)
    
    # Test integer
    PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = False
    shares_int = calculate_shares(cash=10000, price=100, buffer=0.05)
    assert isinstance(shares_int, int)
    
    print("✅ Sizing respects fractional flag")
except (ImportError, AssertionError) as e:
    print(f"❌ Sizing module failed: {e}")
    sys.exit(1)

# Test 9: pytest configuration
print("\n[Test 9] pytest configuration...")
if os.path.exists('pytest.ini'):
    with open('pytest.ini') as f:
        content = f.read()
        assert 'python_files = tests/test_*.py' in content
        assert 'testpaths = tests' in content
    print("✅ pytest.ini correctly configured")
else:
    print("❌ pytest.ini not found")
    sys.exit(1)

# Test 10: tests package
print("\n[Test 10] Tests package structure...")
if os.path.exists('tests/__init__.py'):
    print("✅ tests/__init__.py exists")
else:
    print("❌ tests/__init__.py missing")
    sys.exit(1)

print("\n" + "="*80)
print("✅ ALL VALIDATION CHECKS PASSED")
print("="*80)
print("\nNext steps:")
print("1. Install Python: winget install Python.Python.3.12")
print("2. Install dependencies: pip install -r requirements.txt")
print("3. Run pytest: python -m pytest -v")
print("4. Continue with Phase 1B (correctness fixes)")
print("="*80)
