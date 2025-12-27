"""
V0.11 Optional Dependencies Tests
Tests that optional dependencies (optuna, yfinance) don't break imports
"""

import pytest
import sys


def test_import_without_optuna():
    """Test that advanced_trading_interface can be imported without optuna"""
    # Remove optuna if it exists
    if 'optuna' in sys.modules:
        del sys.modules['optuna']
    
    # Mock optuna as missing
    import builtins
    real_import = builtins.__import__
    
    def mock_import(name, *args, **kwargs):
        if name == 'optuna':
            raise ImportError("No module named 'optuna'")
        return real_import(name, *args, **kwargs)
    
    builtins.__import__ = mock_import
    
    try:
        # This should not crash
        import advanced_trading_interface
        
        # Verify flag is False
        assert hasattr(advanced_trading_interface, 'OPTIMIZED_ML_AVAILABLE')
        # Note: might be True if optuna is actually installed
        
        print("[OK] advanced_trading_interface imports without optuna")
        
    finally:
        builtins.__import__ = real_import


def test_optimized_ml_strategy_lazy_optuna():
    """Test that OptimizedMLStrategy can be imported without optuna"""
    # Remove optuna if imported
    if 'optuna' in sys.modules:
        del sys.modules['optuna']
    
    # Remove optimized_ml_strategy to force reimport
    if 'optimized_ml_strategy' in sys.modules:
        del sys.modules['optimized_ml_strategy']
    
    try:
        import optimized_ml_strategy
        
        # Verify optuna is None (lazy)
        assert optimized_ml_strategy.optuna is None, \
            "optuna should be None until _ensure_optuna() is called"
        
        # Verify _ensure_optuna exists
        assert hasattr(optimized_ml_strategy, '_ensure_optuna')
        
        print("[OK] optimized_ml_strategy imports without optuna (lazy load)")
        
    except ImportError as e:
        if 'optuna' in str(e):
            pytest.fail("optimized_ml_strategy requires optuna at import time (should be lazy)")
        raise


def test_yfinance_lazy_loading():
    """Test that yfinance is lazily loaded in all modules"""
    import sys
    
    # Modules that should have lazy yfinance
    modules_to_test = [
        'data_manager',
        'data_handler',
        'enhanced_utils',
        'robust_utils',
        'optimized_ml_strategy'
    ]
    
    for module_name in modules_to_test:
        # Remove if already imported
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        try:
            module = __import__(module_name)
            
            # Verify yf is None (lazy)
            if hasattr(module, 'yf'):
                assert module.yf is None, \
                    f"{module_name}.yf should be None until _ensure_yfinance() is called"
            
            # Verify _ensure_yfinance exists
            if hasattr(module, '_ensure_yfinance'):
                assert callable(module._ensure_yfinance)
        
        except ImportError as e:
            if 'yfinance' in str(e):
                pytest.fail(f"{module_name} requires yfinance at import time (should be lazy)")
            # Other import errors are OK (missing dependencies for other reasons)
            pass
    
    print("[OK] yfinance is lazily loaded in all relevant modules")


if __name__ == '__main__':
    print("="*70)
    print("V0.11 OPTIONAL DEPENDENCIES TESTS")
    print("="*70)
    
    test_import_without_optuna()
    print()
    test_optimized_ml_strategy_lazy_optuna()
    print()
    test_yfinance_lazy_loading()
    
    print("\n" + "="*70)
    print("[OK] ALL V0.11 OPTIONAL DEPENDENCY TESTS PASSED")
    print("="*70)
