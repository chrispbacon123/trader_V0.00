"""
V0.11 Export Hygiene Tests
Tests for LINE ITEM 5: generated code has valid identifiers
"""

import pytest
import re
import tempfile
import os
from pathlib import Path


def test_sanitize_identifier_valid_names():
    """Test that sanitize_identifier produces valid Python identifiers"""
    from strategy_builder import sanitize_identifier
    
    test_cases = [
        ('MyStrategy', 'MyStrategy'),
        ('my strategy', 'my_strategy'),
        ('Strategy 123', 'Strategy_123'),
        ('test-strategy', 'teststrategy'),
        ('test.strategy', 'teststrategy'),
        ('test@strategy!', 'teststrategy'),
        ('', 'CustomAlgorithm'),  # Empty default
    ]
    
    for input_name, expected in test_cases:
        result = sanitize_identifier(input_name)
        assert result == expected, f"Expected {expected}, got {result}"
        
        # Verify result is valid identifier
        assert result.isidentifier(), f"{result} is not a valid Python identifier"
    
    print("[OK] sanitize_identifier produces valid identifiers")


def test_sanitize_identifier_starts_with_digit():
    """Test that identifiers starting with digit are fixed"""
    from strategy_builder import sanitize_identifier
    
    test_cases = [
        '123Strategy',
        '1_test',
        '99problems',
    ]
    
    for name in test_cases:
        result = sanitize_identifier(name)
        
        # Should start with 'Algo_'
        assert result.startswith('Algo_'), f"Expected 'Algo_' prefix for {name}, got {result}"
        
        # Should be valid identifier
        assert result.isidentifier(), f"{result} is not a valid identifier"
    
    print("[OK] sanitize_identifier fixes digit-starting names")


def test_sanitize_identifier_regex_validation():
    """Test that all results match valid identifier pattern"""
    from strategy_builder import sanitize_identifier
    
    # Valid identifier pattern
    pattern = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
    
    test_inputs = [
        'Normal',
        'with spaces',
        'with-dashes',
        'with.dots',
        'with@symbols!',
        '123startdigit',
        'émoji😀',
        '___underscores___',
        'CamelCase',
        'snake_case',
    ]
    
    for input_name in test_inputs:
        result = sanitize_identifier(input_name)
        
        # Must match valid identifier pattern
        assert pattern.match(result), \
            f"Result '{result}' from input '{input_name}' doesn't match identifier pattern"
    
    print("[OK] All sanitized identifiers match valid pattern")


def test_lean_export_class_name_valid():
    """Test that LEAN exports have valid class names"""
    from strategy_builder import StrategyBuilder, sanitize_identifier
    
    builder = StrategyBuilder()
    
    # Create strategy with problematic name
    strategy = {
        'name': '123 Test Strategy!',
        'description': 'Test',
        'type': 'trend_following',
        'indicators': ['SMA'],
        'entry_rules': ['Price crosses above SMA'],
        'exit_rules': ['Price crosses below SMA'],
        'parameters': {'lookback_period': 20},
        'risk_management': {
            'position_size_pct': 10,
            'stop_loss_pct': 5,
            'take_profit_pct': 15
        }
    }
    
    # Export to temp dir
    with tempfile.TemporaryDirectory() as tmpdir:
        builder.exports_dir = tmpdir
        builder._export_lean_algorithm(strategy, '20251225_test')
        
        # Find generated file
        files = list(Path(tmpdir).glob('*_lean.py'))
        assert len(files) == 1, "Should generate exactly one LEAN file"
        
        # Read file and check class name
        content = files[0].read_text()
        
        # Extract class name
        class_match = re.search(r'class\s+(\w+)\s*\(', content)
        assert class_match, "Should have a class definition"
        
        class_name = class_match.group(1)
        
        # Verify valid identifier
        assert class_name.isidentifier(), \
            f"Class name '{class_name}' is not a valid identifier"
        
        # Should not start with digit
        assert not class_name[0].isdigit(), \
            f"Class name '{class_name}' starts with digit"
        
        # Should contain "Algorithm"
        assert 'Algorithm' in class_name, \
            f"Class name '{class_name}' should contain 'Algorithm'"
    
    print("[OK] LEAN export generates valid class names")


def test_lean_export_no_syntax_errors():
    """Test that generated LEAN code has no syntax errors"""
    from strategy_builder import StrategyBuilder
    import ast
    
    builder = StrategyBuilder()
    
    strategy = {
        'name': 'TestStrategy',
        'description': 'Test strategy',
        'type': 'mean_reversion',
        'indicators': ['RSI', 'MACD'],
        'entry_rules': ['RSI below 30'],
        'exit_rules': ['RSI above 70'],
        'parameters': {'lookback_period': 14},
        'risk_management': {
            'position_size_pct': 5,
            'stop_loss_pct': 3,
            'take_profit_pct': 10
        }
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        builder.exports_dir = tmpdir
        builder._export_lean_algorithm(strategy, '20251225_test')
        
        files = list(Path(tmpdir).glob('*_lean.py'))
        content = files[0].read_text()
        
        # Try to parse as Python (will raise SyntaxError if invalid)
        try:
            # Replace LEAN-specific imports that won't resolve
            test_content = content.replace('from AlgorithmImports import *', 
                                          '# from AlgorithmImports import *')
            ast.parse(test_content)
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")
    
    print("[OK] LEAN export generates syntactically valid Python")


def test_strategy_exports_folder_excluded_from_pytest():
    """Test that strategy_exports is excluded from pytest discovery"""
    # Read pytest.ini directly
    with open('pytest.ini', 'r') as f:
        content = f.read()
    
    # Check norecursedirs line
    assert 'norecursedirs' in content, "pytest.ini should have norecursedirs"
    assert 'strategy_exports' in content, \
        "strategy_exports should be in norecursedirs"
    
    print("[OK] strategy_exports excluded from pytest discovery")


def test_filename_sanitization():
    """Test that export filenames are valid"""
    from strategy_builder import sanitize_identifier
    
    # Test filenames
    test_names = [
        'Test Strategy',
        '123-strategy',
        'strategy.with.dots',
        'strategy@special!chars',
    ]
    
    for name in test_names:
        sanitized = sanitize_identifier(name)
        filename = f"{sanitized}_20251225_lean.py"
        
        # Should be a valid filename (no special chars)
        assert not any(c in filename for c in '<>:"|?*'), \
            f"Filename '{filename}' contains invalid characters"
        
        # Should be importable (no leading digits, valid identifier base)
        base = filename.split('_')[0]
        if base:
            assert base[0].isalpha() or base[0] == '_', \
                f"Filename base '{base}' should start with letter or underscore"
    
    print("[OK] Export filenames are valid and safe")


def test_export_creates_valid_python_module():
    """Integration test: exported file can be compiled as Python module"""
    from strategy_builder import StrategyBuilder
    import py_compile
    
    builder = StrategyBuilder()
    
    strategy = {
        'name': 'Integration Test',
        'description': 'Full integration test',
        'type': 'trend_following',
        'indicators': ['SMA', 'EMA', 'RSI'],
        'entry_rules': ['SMA crosses above EMA'],
        'exit_rules': ['SMA crosses below EMA'],
        'parameters': {'lookback_period': 20},
        'risk_management': {
            'position_size_pct': 10,
            'stop_loss_pct': 5,
            'take_profit_pct': 15
        }
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        builder.exports_dir = tmpdir
        builder._export_lean_algorithm(strategy, '20251225_integration')
        
        # Find file
        files = list(Path(tmpdir).glob('*_lean.py'))
        assert len(files) == 1
        
        filepath = files[0]
        
        # Try to compile (checks syntax)
        try:
            # Just check it compiles, don't execute (LEAN imports won't work)
            compile(filepath.read_text(), str(filepath), 'exec')
        except SyntaxError as e:
            pytest.fail(f"Generated module has syntax error: {e}")
    
    print("[OK] Exported files compile as valid Python modules")


def test_no_quantity_int_in_lean_export():
    """Test that LEAN export uses SetHoldings, not quantity=int()"""
    from strategy_builder import StrategyBuilder
    
    builder = StrategyBuilder()
    
    strategy = {
        'name': 'FractionalTest',
        'description': 'Test fractional position sizing',
        'type': 'mean_reversion',
        'indicators': ['RSI'],
        'entry_rules': ['RSI below 30'],
        'exit_rules': ['RSI above 70'],
        'parameters': {'lookback_period': 14},
        'risk_management': {
            'position_size_pct': 10,
            'stop_loss_pct': 5,
            'take_profit_pct': 15
        }
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        builder.exports_dir = tmpdir
        builder._export_lean_algorithm(strategy, '20251225_fractional')
        
        files = list(Path(tmpdir).glob('*_lean.py'))
        content = files[0].read_text()
        
        # Should use SetHoldings for fractional sizing
        assert 'SetHoldings' in content, \
            "LEAN export should use SetHoldings for position sizing"
        
        # Should NOT use quantity = int(
        assert 'quantity = int(' not in content.lower(), \
            "LEAN export should not use int() for quantity (fractional unsafe)"
    
    print("[OK] LEAN export uses fractional-safe SetHoldings")


if __name__ == '__main__':
    print("="*70)
    print("V0.11 EXPORT HYGIENE TESTS (LINE ITEM 5)")
    print("="*70)
    
    test_sanitize_identifier_valid_names()
    print()
    test_sanitize_identifier_starts_with_digit()
    print()
    test_sanitize_identifier_regex_validation()
    print()
    test_lean_export_class_name_valid()
    print()
    test_lean_export_no_syntax_errors()
    print()
    test_strategy_exports_folder_excluded_from_pytest()
    print()
    test_filename_sanitization()
    print()
    test_export_creates_valid_python_module()
    print()
    test_no_quantity_int_in_lean_export()
    
    print("\n" + "="*70)
    print("[OK] ALL LINE ITEM 5 TESTS PASSED")
    print("="*70)
