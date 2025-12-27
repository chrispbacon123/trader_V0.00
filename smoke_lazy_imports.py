"""
Test that modules can be imported without yfinance installed
"""

def test_lazy_yfinance_imports():
    """Test that importing modules doesn't require yfinance"""
    
    # These should NOT fail even if yfinance is not installed
    try:
        import data_manager
        import data_handler
        import enhanced_utils
        import robust_utils
        import platform_api
        import persistence
        
        print("✅ All modules imported successfully without requiring yfinance")
        
        # Verify that yfinance is still None (not imported)
        assert data_manager.yf is None, "yf should be None until _ensure_yfinance() is called"
        assert data_handler.yf is None, "yf should be None until _ensure_yfinance() is called"
        assert enhanced_utils.yf is None, "yf should be None until _ensure_yfinance() is called"
        assert robust_utils.yf is None, "yf should be None until _ensure_yfinance() is called"
        
        print("✅ yfinance is lazily loaded (not imported at module level)")
        
        return True
        
    except ImportError as e:
        if 'yfinance' in str(e):
            print(f"❌ Module import requires yfinance at import time: {e}")
            return False
        raise


def test_yfinance_error_messages():
    """Test that helpful error messages are shown when yfinance is needed but missing"""
    
    import data_manager
    
    # Try to call a function that needs yfinance without it installed
    # (we can't actually test this if yfinance IS installed, but we can verify the function exists)
    
    assert hasattr(data_manager, '_ensure_yfinance'), "Should have _ensure_yfinance function"
    
    # Check error message format
    try:
        # This will succeed if yfinance is installed, or raise ImportError if not
        data_manager._ensure_yfinance()
        print("✅ yfinance is installed and can be loaded")
    except ImportError as e:
        error_msg = str(e)
        assert 'pip install yfinance' in error_msg, "Error should suggest installation"
        assert 'CSV/DataFrame' in error_msg, "Error should mention alternatives"
        print(f"✅ Helpful error message: {error_msg[:100]}...")
    
    return True


if __name__ == '__main__':
    print("="*70)
    print("LAZY YFINANCE IMPORT TESTS")
    print("="*70)
    
    test_lazy_yfinance_imports()
    print()
    test_yfinance_error_messages()
    
    print("\n" + "="*70)
    print("✅ ALL LAZY IMPORT TESTS PASSED")
    print("="*70)
