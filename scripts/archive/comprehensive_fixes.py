"""
Comprehensive System Fixes and Enhancements
Systematically fixes all errors and adds robust features
"""

import os
import sys
import json
from datetime import datetime

class SystemFixer:
    def __init__(self):
        self.fixes_applied = []
        self.errors_found = []
        
    def fix_backtest_unpacking(self):
        """Fix all backtest return value unpacking issues"""
        print("🔧 Fixing backtest unpacking issues...")
        
        file_path = '/Users/jonathanbrooks/lean-trading/advanced_trading_interface.py'
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Fix patterns that expect 3 values instead of 4
        fixes = [
            # Line 517: ShortTermStrategy
            ('data, trades, final = strategy.backtest(start, end)',
             'data, trades, final, equity = strategy.backtest(start, end)'),
            
            # Line 914: Another ShortTermStrategy  
            ('                    data, trades, final = strategy.backtest(start, end)',
             '                    data, trades, final, equity = strategy.backtest(start, end)'),
        ]
        
        for old, new in fixes:
            if old in content:
                content = content.replace(old, new)
                self.fixes_applied.append(f"Fixed unpacking: {old[:50]}...")
        
        # Handle line 2051 which doesn't unpack at all
        if 'results = strategy.backtest(start_date, end_date)' in content:
            content = content.replace(
                'results = strategy.backtest(start_date, end_date)',
                'data, trades, final_value, equity = strategy.backtest(start_date, end_date)'
            )
            self.fixes_applied.append("Fixed generic backtest unpacking")
        
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✅ Applied {len(self.fixes_applied)} backtest unpacking fixes")
        else:
            print("✅ No backtest unpacking issues found")
    
    def add_universal_error_handling(self):
        """Add robust error handling wrapper"""
        print("🔧 Adding universal error handling...")
        
        wrapper_code = '''
    def safe_backtest(self, strategy, start_date, end_date, **kwargs):
        """Universal backtest wrapper with error handling"""
        try:
            result = strategy.backtest(start_date, end_date, **kwargs)
            
            # Handle different return formats
            if isinstance(result, tuple):
                if len(result) == 4:
                    return result  # (data, trades, final_value, equity)
                elif len(result) == 3:
                    # Old format - add empty equity
                    return result[0], result[1], result[2], []
                elif len(result) == 2:
                    # Minimal format
                    return None, result[0], result[1], []
            
            return None, [], 0, []
            
        except ValueError as e:
            if "Insufficient data" in str(e):
                print(f"⚠️  {e}")
                print(f"💡 Try increasing the lookback period or checking data availability")
            else:
                print(f"❌ ValueError: {e}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error in backtest: {e}")
            import traceback
            traceback.print_exc()
            raise
'''
        
        file_path = '/Users/jonathanbrooks/lean-trading/advanced_trading_interface.py'
        
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Find a good place to insert (after __init__)
        for i, line in enumerate(lines):
            if 'def __init__(self):' in line and i > 10:
                # Find end of __init__
                for j in range(i+1, len(lines)):
                    if lines[j].strip() and not lines[j].startswith(' ' * 8) and lines[j].strip() != '':
                        if 'def ' in lines[j]:
                            # Insert before next method
                            lines.insert(j, wrapper_code + '\n')
                            self.fixes_applied.append("Added safe_backtest wrapper")
                            break
                break
        
        with open(file_path, 'w') as f:
            f.writelines(lines)
        
        print("✅ Added universal error handling")
    
    def validate_all_strategies(self):
        """Validate all strategy files return consistent format"""
        print("🔧 Validating strategy return formats...")
        
        strategy_files = [
            'ml_strategy.py',
            'simple_strategy.py', 
            'short_term_strategy.py',
            'optimized_ml_strategy.py'
        ]
        
        for filename in strategy_files:
            filepath = f'/Users/jonathanbrooks/lean-trading/{filename}'
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Check for return statement in backtest
                if 'def backtest' in content:
                    if 'return' in content and 'trades' in content:
                        # Count returns that might be wrong format
                        import re
                        returns = re.findall(r'return\s+[\w,\s]+', content)
                        for ret in returns:
                            if 'backtest' in content[max(0, content.find(ret)-200):content.find(ret)]:
                                # This is in backtest method
                                if ret.count(',') == 2:  # 3 values
                                    print(f"⚠️  {filename} might return 3 values instead of 4")
                                    self.errors_found.append(f"{filename}: Check return format")
                                elif ret.count(',') == 3:  # 4 values - correct
                                    print(f"✅ {filename} returns correct 4 values")
        
        print(f"✅ Validated {len(strategy_files)} strategy files")
    
    def add_data_validation(self):
        """Add comprehensive data validation"""
        print("🔧 Adding data validation utilities...")
        
        validation_code = '''
def validate_backtest_data(symbol, start_date, end_date, min_days=20):
    """Validate data availability before running backtest"""
    import yfinance as yf
    from datetime import timedelta
    
    # Request more calendar days to ensure enough trading days
    buffer_start = start_date - timedelta(days=int((end_date - start_date).days * 0.5))
    
    try:
        data = yf.download(symbol, start=buffer_start, end=end_date, progress=False)
        
        if data is None or len(data) == 0:
            return False, f"No data available for {symbol}"
        
        trading_days = len(data)
        if trading_days < min_days:
            return False, f"Insufficient data: {trading_days} trading days (need {min_days})"
        
        return True, f"✓ {trading_days} trading days available"
        
    except Exception as e:
        return False, f"Error downloading data: {e}"
'''
        
        filepath = '/Users/jonathanbrooks/lean-trading/enhanced_utils.py'
        
        with open(filepath, 'a') as f:
            f.write('\n\n' + validation_code)
        
        self.fixes_applied.append("Added data validation utility")
        print("✅ Added data validation utilities")
    
    def create_comprehensive_test(self):
        """Create comprehensive test suite"""
        print("🔧 Creating comprehensive test suite...")
        
        test_code = '''#!/usr/bin/env python3
"""
Comprehensive System Test
Tests all features systematically
"""

import sys
sys.path.insert(0, '/Users/jonathanbrooks/lean-trading')

from datetime import datetime, timedelta
from simple_strategy import SimpleMeanReversionStrategy
from ml_strategy import MLTradingStrategy
from short_term_strategy import ShortTermStrategy
from optimized_ml_strategy import OptimizedMLStrategy

def test_strategy(strategy_class, name, symbol='SPY', days=365):
    """Test a single strategy"""
    print(f"\\n{'='*60}")
    print(f"Testing {name}")
    print('='*60)
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        strategy = strategy_class(symbol=symbol)
        strategy.cash = 100000
        
        print(f"Running backtest on {symbol} for {days} days...")
        result = strategy.backtest(start_date, end_date)
        
        # Validate return format
        if not isinstance(result, tuple):
            print(f"❌ {name}: backtest didn't return tuple")
            return False
        
        if len(result) != 4:
            print(f"❌ {name}: backtest returned {len(result)} values, expected 4")
            return False
        
        data, trades, final_value, equity = result
        
        # Validate return values
        if trades is None or not isinstance(trades, list):
            print(f"❌ {name}: trades is not a list")
            return False
        
        if not isinstance(final_value, (int, float)):
            print(f"❌ {name}: final_value is not numeric")
            return False
        
        if equity is None or not isinstance(equity, list):
            print(f"❌ {name}: equity is not a list")
            return False
        
        # Print results
        return_pct = ((final_value - 100000) / 100000) * 100
        print(f"✅ {name} passed all checks")
        print(f"   Trades: {len(trades)}")
        print(f"   Final Value: ${final_value:,.2f}")
        print(f"   Return: {return_pct:.2f}%")
        return True
        
    except Exception as e:
        print(f"❌ {name} failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive tests"""
    print("\\n" + "="*60)
    print("COMPREHENSIVE SYSTEM TEST")
    print("="*60)
    
    tests = [
        (SimpleMeanReversionStrategy, "Simple Strategy", 'SPY', 180),
        (MLTradingStrategy, "ML Strategy", 'SPY', 365),
        (ShortTermStrategy, "Short-Term Strategy", 'SPY', 90),
        (OptimizedMLStrategy, "Optimized ML Strategy", 'SPY', 365),
    ]
    
    results = {}
    for strategy_class, name, symbol, days in tests:
        results[name] = test_strategy(strategy_class, name, symbol, days)
    
    print("\\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:30} {status}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\\nTotal: {passed}/{total} tests passed")
    
    return all(results.values())

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
'''
        
        filepath = '/Users/jonathanbrooks/lean-trading/comprehensive_test.py'
        with open(filepath, 'w') as f:
            f.write(test_code)
        
        os.chmod(filepath, 0o755)
        self.fixes_applied.append("Created comprehensive test suite")
        print("✅ Created comprehensive test suite")
    
    def run_all_fixes(self):
        """Execute all fixes in order"""
        print("\n" + "="*70)
        print("COMPREHENSIVE SYSTEM FIXES")
        print("="*70 + "\n")
        
        self.fix_backtest_unpacking()
        self.validate_all_strategies()
        self.add_data_validation()
        self.create_comprehensive_test()
        # self.add_universal_error_handling()  # Skip for now to avoid breaking changes
        
        print("\n" + "="*70)
        print("FIXES SUMMARY")
        print("="*70)
        
        print(f"\n✅ Applied {len(self.fixes_applied)} fixes:")
        for fix in self.fixes_applied:
            print(f"   • {fix}")
        
        if self.errors_found:
            print(f"\n⚠️  Found {len(self.errors_found)} potential issues:")
            for error in self.errors_found:
                print(f"   • {error}")
        
        print("\n" + "="*70)
        print("Next Steps:")
        print("="*70)
        print("1. Run: ./comprehensive_test.py")
        print("2. Fix any remaining issues identified")
        print("3. Test the main interface: python3 advanced_trading_interface.py")
        print("="*70 + "\n")

if __name__ == '__main__':
    fixer = SystemFixer()
    fixer.run_all_fixes()
