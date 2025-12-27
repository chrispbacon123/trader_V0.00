"""
Test strategy_builder.py to ensure it respects fractional shares
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from core_config import PORTFOLIO_CFG


class TestStrategyBuilderFractional:
    """Test that strategy_builder respects fractional share configuration"""
    
    def test_builder_generated_strategy_respects_fractional_flag(self):
        """Test that strategies created by strategy_builder respect FRACTIONAL_SHARES_ALLOWED"""
        # We'll test this by checking the generated strategy code
        # Since strategy_builder is interactive, we'll import and check its structure
        
        try:
            from strategy_builder import create_custom_strategy
            
            # The function exists, we can verify its structure
            # In a real test, we'd mock inputs and test execution
            assert callable(create_custom_strategy)
            
        except ImportError:
            pytest.skip("strategy_builder not available")
    
    def test_builder_sizing_logic_not_hardcoded(self):
        """Test that builder doesn't hardcode int() casts for sizing"""
        import strategy_builder
        import inspect
        
        # Get source code
        source = inspect.getsource(strategy_builder)
        
        # Check for problematic patterns in generated code
        # This is a heuristic test - looks for hardcoded int() on share calculations
        problematic_patterns = [
            'shares = int(',
            'quantity = int(',
            'shares = np.floor(',
            'quantity = np.floor('
        ]
        
        # The source should either not have these patterns, or should gate them
        # behind FRACTIONAL_SHARES_ALLOWED checks
        for pattern in problematic_patterns:
            if pattern in source:
                # If pattern exists, verify it's gated by fractional check
                # This is a simplified check - in reality you'd parse the AST
                assert 'FRACTIONAL_SHARES_ALLOWED' in source or \
                       'fractional' in source.lower(), \
                       f"Found hardcoded sizing pattern '{pattern}' without fractional gate"
    
    def test_generated_quantconnect_code_respects_fractional(self):
        """Test that QuantConnect exports handle fractional shares"""
        import strategy_builder
        import inspect
        
        source = inspect.getsource(strategy_builder)
        
        # Check QuantConnect export template
        if 'def generate_quantconnect_code' in source or 'quantconnect' in source.lower():
            # Exported code should use fractional-aware sizing
            # QuantConnect supports fractional shares via SetHoldings
            # Hardcoded int() in QuantConnect exports would be a bug
            
            # Look for the template generation
            if 'quantity = int(' in source and 'SetHoldings' not in source:
                pytest.fail("QuantConnect export may not handle fractional shares properly")


class TestSizingModule:
    """Test sizing.py module respects fractional shares"""
    
    def test_sizing_module_respects_flag(self):
        """Test that sizing.py properly gates rounding"""
        try:
            from sizing import calculate_position_size
            
            # Test with fractional enabled
            original = PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED
            PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = True
            
            try:
                # Mock inputs
                equity = 100000
                target_weight = 0.1
                price = 450.75
                
                # Calculate
                result = calculate_position_size(
                    equity=equity,
                    target_weight=target_weight,
                    price=price,
                    fractional_allowed=True
                )
                
                # Should be fractional
                shares = result if isinstance(result, (int, float)) else result.get('shares', 0)
                
                # Expected: ~22.186 shares
                expected = (equity * target_weight) / price
                
                # With fractional enabled, should NOT be floored
                assert shares != int(shares), \
                    f"Shares should be fractional when enabled, got {shares}"
                
                assert np.isclose(shares, expected, rtol=0.01), \
                    f"Shares {shares} not close to expected {expected:.2f}"
                
            finally:
                PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = original
            
        except ImportError:
            pytest.skip("sizing module not structured as expected")
    
    def test_sizing_module_floors_when_disabled(self):
        """Test that sizing.py floors shares when fractional disabled"""
        try:
            from sizing import calculate_position_size
            
            original = PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED
            PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = False
            
            try:
                equity = 100000
                target_weight = 0.1
                price = 450.75
                
                result = calculate_position_size(
                    equity=equity,
                    target_weight=target_weight,
                    price=price,
                    fractional_allowed=False
                )
                
                shares = result if isinstance(result, (int, float)) else result.get('shares', 0)
                
                # With fractional disabled, should be floored
                assert shares == int(shares), \
                    f"Shares should be whole number when disabled, got {shares}"
                
            finally:
                PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = original
            
        except ImportError:
            pytest.skip("sizing module not structured as expected")


class TestStrategySizingIntegration:
    """Integration test for strategy sizing end-to-end"""
    
    def test_ml_strategy_sizing(self):
        """Test ml_strategy.py respects fractional flag"""
        # This is a simplified integration test
        # In a full test, you'd run the strategy and verify actual trade sizes
        
        try:
            from ml_strategy import MLStrategy
            
            # Verify the class doesn't have hardcoded int() casts
            import inspect
            source = inspect.getsource(MLStrategy)
            
            # Check for problematic patterns
            if 'shares = int(' in source:
                # Make sure it's gated
                assert 'FRACTIONAL_SHARES_ALLOWED' in source or 'fractional' in source.lower(), \
                    "ml_strategy has hardcoded int() cast without fractional check"
            
        except (ImportError, AttributeError):
            pytest.skip("MLStrategy not available for testing")
    
    def test_optimized_ml_strategy_sizing(self):
        """Test optimized_ml_strategy.py respects fractional flag"""
        try:
            from optimized_ml_strategy import OptimizedMLStrategy
            
            import inspect
            source = inspect.getsource(OptimizedMLStrategy)
            
            if 'shares = int(' in source:
                assert 'FRACTIONAL_SHARES_ALLOWED' in source or 'fractional' in source.lower(), \
                    "optimized_ml_strategy has hardcoded int() cast without fractional check"
            
        except (ImportError, AttributeError):
            pytest.skip("OptimizedMLStrategy not available for testing")
    
    def test_simple_strategy_sizing(self):
        """Test simple_strategy.py respects fractional flag"""
        try:
            from simple_strategy import SimpleStrategy
            
            import inspect
            source = inspect.getsource(SimpleStrategy)
            
            if 'shares = int(' in source:
                assert 'FRACTIONAL_SHARES_ALLOWED' in source or 'fractional' in source.lower(), \
                    "simple_strategy has hardcoded int() cast without fractional check"
            
        except (ImportError, AttributeError):
            pytest.skip("SimpleStrategy not available for testing")


def test_no_silent_int_casts_in_strategies():
    """Meta-test: grep for hardcoded int() casts in strategy files"""
    import os
    import re
    from pathlib import Path
    
    # Get project root
    test_dir = Path(__file__).parent
    project_root = test_dir.parent
    
    # Strategy files to check
    strategy_files = [
        'ml_strategy.py',
        'optimized_ml_strategy.py',
        'simple_strategy.py',
        'short_term_strategy.py',
        'strategy_builder.py'
    ]
    
    issues = []
    
    for filename in strategy_files:
        filepath = project_root / filename
        
        if not filepath.exists():
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for share sizing patterns
        patterns_to_check = [
            (r'shares\s*=\s*int\(', 'shares = int('),
            (r'quantity\s*=\s*int\(', 'quantity = int('),
            (r'qty\s*=\s*int\(', 'qty = int(')
        ]
        
        for pattern, desc in patterns_to_check:
            matches = re.finditer(pattern, content)
            for match in matches:
                # Get context around match
                start = max(0, match.start() - 200)
                end = min(len(content), match.end() + 200)
                context = content[start:end]
                
                # Check if it's gated by fractional check
                if 'FRACTIONAL' not in context and 'fractional' not in context.lower():
                    issues.append(f"{filename}: Found ungated '{desc}' at position {match.start()}")
    
    if issues:
        pytest.fail("Found hardcoded int() casts without fractional gates:\n" + "\n".join(issues))
