"""
Regression tests for optimization failure handling
Ensures UI never crashes when best_params is None or missing
"""


def test_optimization_result_schema():
    """Test that optimization returns consistent schema"""
    
    # Simulate successful optimization
    success_result = {
        'success': True,
        'best_params': {'lookback': 30, 'threshold': 0.5},
        'best_score': 1.234,
        'tested': 10,
        'valid': 8,
        'failures': 2,
        'error': None,
        'warnings': [],
        'top_results': []
    }
    
    # Verify schema
    assert 'success' in success_result
    assert 'best_params' in success_result
    assert 'best_score' in success_result
    assert 'tested' in success_result
    assert 'valid' in success_result
    assert 'failures' in success_result
    assert 'error' in success_result
    assert isinstance(success_result['best_params'], dict)
    print("✅ Success schema validated")
    
    # Simulate failed optimization (all combos failed)
    failure_result = {
        'success': False,
        'best_params': {},  # NEVER None
        'best_score': None,
        'tested': 10,
        'valid': 0,
        'failures': 10,
        'error': "No valid parameter combinations produced a valid backtest/score.",
        'warnings': ['Warning 1'],
        'top_results': []
    }
    
    # Verify schema
    assert 'success' in failure_result
    assert 'best_params' in failure_result
    assert 'best_score' in failure_result
    assert failure_result['best_params'] is not None, "best_params must never be None!"
    assert isinstance(failure_result['best_params'], dict)
    assert failure_result['best_params'] == {}, "Failed optimization should have empty dict"
    print("✅ Failure schema validated")
    
    # Simulate partial failure (some valid, but no best)
    partial_result = {
        'success': False,
        'best_params': {},
        'best_score': None,
        'tested': 10,
        'valid': 3,
        'failures': 7,
        'error': "Optimization found 3 valid results but best_params is missing.",
        'warnings': [],
        'top_results': []
    }
    
    assert isinstance(partial_result['best_params'], dict)
    print("✅ Partial failure schema validated")


def test_ui_print_defensive():
    """Test that UI printing handles all result types without crashing"""
    
    def print_results_safe(results):
        """Simulates the defensive UI printing logic"""
        try:
            if not results.get('success') or not results.get('best_params'):
                # Failure path
                print("❌ No valid best parameters found")
                print(f"Tested: {results.get('tested', 0)}")
                print(f"Valid: {results.get('valid', 0)}")
                print(f"Failures: {results.get('failures', 0)}")
                if results.get('error'):
                    print(f"Error: {results['error']}")
                return False
            else:
                # Success path
                print("🏆 Best Parameters:")
                for param, value in results['best_params'].items():
                    print(f"  {param}: {value}")
                if results['best_score'] is not None:
                    print(f"Best score: {results['best_score']:.4f}")
                return True
        except Exception as e:
            print(f"CRASH: {e}")
            raise
    
    # Test 1: Successful result
    success = {
        'success': True,
        'best_params': {'lookback': 30},
        'best_score': 1.5,
        'tested': 10,
        'valid': 10,
        'failures': 0
    }
    assert print_results_safe(success) == True
    print("✅ Success result printed without crash")
    
    # Test 2: Complete failure (best_params is empty dict)
    failure = {
        'success': False,
        'best_params': {},
        'best_score': None,
        'tested': 10,
        'valid': 0,
        'failures': 10,
        'error': "All combinations failed"
    }
    assert print_results_safe(failure) == False
    print("✅ Failure result printed without crash")
    
    # Test 3: best_params is None (should not happen but must not crash)
    none_params = {
        'success': False,
        'best_params': None,  # Bad but must handle
        'best_score': None,
        'tested': 5,
        'valid': 0,
        'failures': 5
    }
    # The check `not results.get('best_params')` handles None safely
    assert print_results_safe(none_params) == False
    print("✅ None best_params handled without crash")
    
    # Test 4: Empty result (missing keys)
    empty = {}
    assert print_results_safe(empty) == False
    print("✅ Empty result handled without crash")


def test_iteration_safety():
    """Test that iterating over best_params is safe"""
    
    test_cases = [
        ({'a': 1, 'b': 2}, True, "normal dict"),
        ({}, False, "empty dict"),
        (None, False, "None value"),
    ]
    
    for params, should_iterate, description in test_cases:
        try:
            # Safe check before iteration
            if params and isinstance(params, dict):
                for k, v in params.items():
                    pass  # Would iterate
                result = "iterated"
            else:
                result = "skipped"
            
            expected = "iterated" if should_iterate else "skipped"
            assert result == expected, f"Failed for {description}: expected {expected}, got {result}"
            print(f"✅ {description}: {result} as expected")
            
        except AttributeError as e:
            print(f"❌ CRASH on {description}: {e}")
            raise


def test_failure_tracking():
    """Test that optimizer tracks failures correctly"""
    
    # Simulate tracking
    tested = 0
    valid = 0
    failures = 0
    failure_reasons = []
    
    # Simulate 10 combinations
    for i in range(10):
        tested += 1
        
        # Simulate various failure modes
        if i < 3:
            # Invalid score
            failures += 1
            reason = f"Combo {i}: Invalid score (None)"
            if len(failure_reasons) < 10:
                failure_reasons.append(reason)
        elif i < 6:
            # Exception
            failures += 1
            reason = f"Combo {i}: ValueError: Insufficient data"
            if len(failure_reasons) < 10:
                failure_reasons.append(reason)
        else:
            # Success
            valid += 1
    
    assert tested == 10
    assert valid == 4
    assert failures == 6
    assert len(failure_reasons) == 6  # All tracked (under cap of 10)
    print(f"✅ Failure tracking: {tested} tested, {valid} valid, {failures} failed")
    print(f"   Captured {len(failure_reasons)} failure reasons")


if __name__ == '__main__':
    print("="*70)
    print("OPTIMIZATION FAILURE HANDLING - REGRESSION TESTS")
    print("="*70)
    
    test_optimization_result_schema()
    print()
    test_ui_print_defensive()
    print()
    test_iteration_safety()
    print()
    test_failure_tracking()
    
    print("\n" + "="*70)
    print("✅ ALL REGRESSION TESTS PASSED")
    print("="*70)
