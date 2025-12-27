"""
Regression test for grid size estimation
Ensures no NameError/UnboundLocalError and correct calculation
"""

import math

def _estimate_grid_size(param_grid: dict) -> int:
    """
    Estimate the total number of combinations in a parameter grid.
    O(n) time complexity - does not materialize combinations.
    
    Args:
        param_grid: Dictionary of parameter names to lists of values
        
    Returns:
        Total number of combinations
    """
    if not param_grid:
        return 0
    return math.prod(len(values) for values in param_grid.values())


def test_estimate_grid_size():
    """Test grid size estimation"""
    
    # Test case 1: Empty grid
    assert _estimate_grid_size({}) == 0, "Empty grid should return 0"
    
    # Test case 2: Single parameter
    assert _estimate_grid_size({'a': [1, 2, 3]}) == 3, "Single param should return length"
    
    # Test case 3: Two parameters
    assert _estimate_grid_size({
        'a': [1, 2, 3],
        'b': [4, 5]
    }) == 6, "Two params: 3 * 2 = 6"
    
    # Test case 4: Three parameters (realistic scenario)
    assert _estimate_grid_size({
        'lookback': [7, 14, 21],
        'entry_threshold': [0.01, 0.02, 0.03],
        'exit_threshold': [0.005, 0.01, 0.015]
    }) == 27, "Three params: 3 * 3 * 3 = 27"
    
    # Test case 5: Large grid
    assert _estimate_grid_size({
        'a': list(range(10)),
        'b': list(range(10)),
        'c': list(range(10))
    }) == 1000, "Large grid: 10 * 10 * 10 = 1000"
    
    print("✅ All grid size estimation tests passed!")


if __name__ == '__main__':
    test_estimate_grid_size()
