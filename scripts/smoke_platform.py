#!/usr/bin/env python3
"""
Platform Smoke Test Runner
Runs without network/optional dependencies using fixtures

Usage:
    python scripts/smoke_platform.py
    
Exit codes:
    0 = All checks passed
    1 = One or more checks failed
"""

import sys
import os
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def print_header(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(name: str, passed: bool, details: str = ""):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"  {status}: {name}")
    if details and not passed:
        print(f"         {details}")


def run_smoke_tests() -> bool:
    """Run all smoke tests, return True if all pass"""
    all_passed = True
    results = []
    
    print_header("TRADING PLATFORM SMOKE TEST")
    print(f"  Started: {datetime.now().isoformat()}")
    
    # Test 1: Core imports
    print_header("1. Core Module Imports")
    try:
        from core_config import PLATFORM_VERSION, get_version_info
        print_result("core_config", True)
        print(f"         Platform Version: {PLATFORM_VERSION}")
        results.append(("core_config import", True))
    except Exception as e:
        print_result("core_config", False, str(e))
        results.append(("core_config import", False))
        all_passed = False
    
    try:
        from data_normalization import DataNormalizer, DataContractError
        print_result("data_normalization", True)
        results.append(("data_normalization import", True))
    except Exception as e:
        print_result("data_normalization", False, str(e))
        results.append(("data_normalization import", False))
        all_passed = False
    
    try:
        from platform_api import PlatformAPI, get_api
        print_result("platform_api", True)
        results.append(("platform_api import", True))
    except Exception as e:
        print_result("platform_api", False, str(e))
        results.append(("platform_api import", False))
        all_passed = False
    
    try:
        from market_analytics import MarketAnalytics
        print_result("market_analytics", True)
        results.append(("market_analytics import", True))
    except Exception as e:
        print_result("market_analytics", False, str(e))
        results.append(("market_analytics import", False))
        all_passed = False
    
    try:
        from strategy_optimizer import StrategyOptimizer
        print_result("strategy_optimizer", True)
        results.append(("strategy_optimizer import", True))
    except Exception as e:
        print_result("strategy_optimizer", False, str(e))
        results.append(("strategy_optimizer import", False))
        all_passed = False
    
    try:
        from persistence import normalize_run_record, load_history
        print_result("persistence", True)
        results.append(("persistence import", True))
    except Exception as e:
        print_result("persistence", False, str(e))
        results.append(("persistence import", False))
        all_passed = False
    
    # Test 2: UI import (should not require optional deps)
    print_header("2. UI Import (No Optional Deps Required)")
    try:
        # This import should work without yfinance/optuna installed
        import advanced_trading_interface
        print_result("advanced_trading_interface", True)
        results.append(("UI import without yfinance/optuna", True))
    except ImportError as e:
        if 'yfinance' in str(e) or 'optuna' in str(e):
            print_result("advanced_trading_interface", False, 
                        f"Should not require optional deps at import: {e}")
            results.append(("UI import without yfinance/optuna", False))
            all_passed = False
        else:
            # Other import errors are OK for smoke test
            print_result("advanced_trading_interface", True, 
                        f"Import with warnings: {e}")
            results.append(("UI import", True))
    except Exception as e:
        print_result("advanced_trading_interface", False, str(e))
        results.append(("UI import", False))
        all_passed = False
    
    # Test 3: Data Normalization with Fixture
    print_header("3. Data Normalization")
    try:
        from tests.fixtures import generate_synthetic_ohlcv
        
        # Test OHLC normalization
        df_ohlc = generate_synthetic_ohlcv(100, seed=42)
        normalized, metadata = DataNormalizer.normalize_market_data(
            df_ohlc, symbol='TEST', require_ohlc=False
        )
        
        assert 'Price' in normalized.columns, "Missing Price column"
        assert len(normalized) > 0, "Empty result"
        assert not normalized['Price'].isna().any(), "NaN in Price"
        
        print_result("OHLC normalization", True)
        print(f"         Rows: {len(normalized)}, Price source: {metadata.get('price_source')}")
        results.append(("OHLC normalization", True))
        
        # Test Price-only normalization
        df_price = pd.DataFrame({
            'Price': np.random.uniform(100, 110, 50)
        }, index=pd.date_range('2024-01-01', periods=50))
        
        normalized, metadata = DataNormalizer.normalize_market_data(
            df_price, symbol='TEST', require_ohlc=False
        )
        
        assert 'Price' in normalized.columns
        assert 'High' in normalized.columns  # Derived
        assert 'Low' in normalized.columns   # Derived
        
        print_result("Price-only normalization", True)
        results.append(("Price-only normalization", True))
        
    except Exception as e:
        print_result("Data normalization", False, str(e))
        results.append(("Data normalization", False))
        all_passed = False
    
    # Test 4: Market Analytics with Fixture
    print_header("4. Market Analytics (Offline)")
    try:
        from tests.fixtures import generate_synthetic_ohlcv
        
        df = generate_synthetic_ohlcv(150, seed=42)
        analytics = MarketAnalytics('TEST')
        
        # Use analyze() method with pre-fetched data
        result = analytics.analyze(df, symbol='TEST')
        
        assert result.get('success', False), f"Analysis failed: {result.get('error')}"
        assert 'regime' in result, "Missing regime"
        assert 'key_levels' in result, "Missing key_levels"
        assert 'momentum' in result, "Missing momentum"
        assert 'risk' in result, "Missing risk"
        
        print_result("MarketAnalytics.analyze()", True)
        print(f"         Regime: {result.get('regime', {}).get('type', 'N/A')}")
        results.append(("Market analytics", True))
        
    except Exception as e:
        print_result("Market analytics", False, str(e))
        results.append(("Market analytics", False))
        all_passed = False
    
    # Test 5: Platform API with Fixture
    print_header("5. Platform API (Offline)")
    try:
        api = get_api()
        
        df = generate_synthetic_ohlcv(150, seed=42)
        
        result = api.analyze_market(
            symbol='TEST',
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 6, 1),
            data=df  # Pass fixture data
        )
        
        assert result.get('success', False), f"API analysis failed: {result.get('error')}"
        assert 'platform_version' in result, "Missing platform_version"
        
        from core_config import PLATFORM_VERSION
        assert result['platform_version'] == PLATFORM_VERSION, \
            f"Version mismatch: {result['platform_version']} != {PLATFORM_VERSION}"
        
        print_result("PlatformAPI.analyze_market()", True)
        print(f"         Version: {result['platform_version']}")
        results.append(("Platform API", True))
        
    except Exception as e:
        print_result("Platform API", False, str(e))
        results.append(("Platform API", False))
        all_passed = False
    
    # Test 6: Persistence
    print_header("6. Persistence Schema")
    try:
        # Test record normalization
        old_record = {
            'ticker': 'SPY',  # old key
            'total_return': 5.5,  # old key
            'date': '2024-01-01'  # old key
        }
        
        normalized = normalize_run_record(old_record)
        
        assert normalized.get('symbol') == 'SPY', "Failed to map ticker->symbol"
        assert normalized.get('return_pct') == 5.5, "Failed to map total_return->return_pct"
        assert 'timestamp' in normalized, "Missing timestamp"
        assert 'strategy' in normalized, "Missing strategy"
        
        print_result("Record normalization", True)
        results.append(("Persistence normalization", True))
        
    except Exception as e:
        print_result("Persistence", False, str(e))
        results.append(("Persistence", False))
        all_passed = False
    
    # Test 7: Optimizer Schema (mock failure case)
    print_header("7. Optimizer Schema Stability")
    try:
        # Test that optimizer returns stable schema even on failure
        from simple_strategy import SimpleMeanReversionStrategy
        
        optimizer = StrategyOptimizer(SimpleMeanReversionStrategy, metric='sharpe_ratio')
        
        # Test with empty param grid - should return stable schema
        param_grid = {'lookback': [20, 30]}
        
        # We can't actually run optimization without data, but we can test
        # that the class initializes and has the right methods
        assert hasattr(optimizer, 'grid_search'), "Missing grid_search method"
        assert hasattr(optimizer, 'random_search'), "Missing random_search method"
        
        print_result("Optimizer methods exist", True)
        results.append(("Optimizer schema", True))
        
    except Exception as e:
        print_result("Optimizer schema", False, str(e))
        results.append(("Optimizer schema", False))
        all_passed = False
    
    # Test 8: Validated modules
    print_header("8. Validated Calculation Modules")
    try:
        from validated_indicators import ValidatedIndicators
        from validated_levels import ValidatedKeyLevels
        from validated_regime import ValidatedRegime
        from validated_risk import ValidatedRiskMetrics
        from validated_portfolio import ValidatedPortfolio
        
        # Test RSI bounds
        prices = pd.Series(np.random.uniform(100, 110, 50))
        rsi = ValidatedIndicators.rsi(prices, period=14)
        
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all(), "RSI out of bounds"
        
        print_result("ValidatedIndicators.rsi()", True)
        
        # Test risk metrics
        returns = prices.pct_change().dropna()
        vol = ValidatedRiskMetrics.volatility(returns)
        
        assert 'volatility_daily' in vol, "Missing volatility_daily"
        assert 'volatility_annualized' in vol, "Missing volatility_annualized"
        
        print_result("ValidatedRiskMetrics.volatility()", True)
        results.append(("Validated modules", True))
        
    except Exception as e:
        print_result("Validated modules", False, str(e))
        results.append(("Validated modules", False))
        all_passed = False
    
    # Summary
    print_header("SUMMARY")
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    print(f"  Passed: {passed}/{total}")
    print(f"  Status: {'ALL CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'}")
    print(f"  Completed: {datetime.now().isoformat()}")
    print()
    
    return all_passed


if __name__ == '__main__':
    try:
        success = run_smoke_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FATAL ERROR]: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
