#!/usr/bin/env python3
"""
V0.03 Platform Verification
Quick check that all V0.03 fixes are in place
"""

import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists"""
    path = Path(filepath)
    if path.exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} MISSING: {filepath}")
        return False

def check_directory_exists(dirpath, description):
    """Check if a directory exists"""
    path = Path(dirpath)
    if path.exists() and path.is_dir():
        print(f"✅ {description}: {dirpath}")
        return True
    else:
        print(f"❌ {description} MISSING: {dirpath}")
        return False

def check_no_test_files_in_root():
    """Check that no test files remain in root"""
    root = Path('.')
    test_files = list(root.glob('test_*.py')) + list(root.glob('*_test.py'))
    
    if not test_files:
        print("✅ No test files in root directory")
        return True
    else:
        print(f"❌ Found test files in root: {[str(f) for f in test_files]}")
        return False

def check_pytest_ini_content():
    """Check pytest.ini has correct content"""
    pytest_ini = Path('pytest.ini')
    
    if not pytest_ini.exists():
        print("❌ pytest.ini does not exist")
        return False
    
    content = pytest_ini.read_text()
    
    checks = [
        ('python_files = tests/test_*.py', 'Test file pattern'),
        ('testpaths = tests', 'Test paths'),
        ('norecursedirs', 'Excluded directories')
    ]
    
    all_good = True
    for pattern, description in checks:
        if pattern in content:
            print(f"✅ pytest.ini has {description}")
        else:
            print(f"❌ pytest.ini missing {description}")
            all_good = False
    
    return all_good

def check_canonical_data_lazy_import():
    """Check that canonical_data.py has lazy yfinance import"""
    canonical = Path('canonical_data.py')
    
    if not canonical.exists():
        print("❌ canonical_data.py not found")
        return False
    
    content = canonical.read_text()
    
    # Check for lazy import pattern
    if 'global yf' in content and 'import yfinance' in content:
        if content.find('global yf') < content.find('import yfinance as yf'):
            print("✅ canonical_data.py has lazy yfinance import")
            return True
    
    print("❌ canonical_data.py may not have lazy import")
    return False

def check_order_execution_float_quantity():
    """Check that Order class accepts float quantities"""
    order_exec = Path('order_execution.py')
    
    if not order_exec.exists():
        print("❌ order_execution.py not found")
        return False
    
    content = order_exec.read_text()
    
    # Check for float quantity in Order.__init__
    if 'quantity: float' in content or 'quantity:float' in content:
        print("✅ Order class accepts float quantities")
        return True
    else:
        print("❌ Order class may not accept float quantities")
        return False

def check_gitignore_exports():
    """Check that .gitignore excludes export directories"""
    gitignore = Path('.gitignore')
    
    if not gitignore.exists():
        print("❌ .gitignore not found")
        return False
    
    content = gitignore.read_text()
    
    checks = [
        'strategy_exports/',
        'custom_strategies/',
        'live_strategies/',
        'data_cache/'
    ]
    
    all_good = True
    for item in checks:
        if item in content:
            print(f"✅ .gitignore excludes {item}")
        else:
            print(f"❌ .gitignore may not exclude {item}")
            all_good = False
    
    return all_good

def main():
    """Run all verification checks"""
    print("="*80)
    print("V0.03 PLATFORM VERIFICATION")
    print("="*80)
    print()
    
    checks = []
    
    # Check directory structure
    print("📁 Directory Structure:")
    checks.append(check_directory_exists('tests', 'Tests directory'))
    checks.append(check_directory_exists('scripts', 'Scripts directory'))
    print()
    
    # Check key files
    print("📄 Key Files:")
    checks.append(check_file_exists('pytest.ini', 'Pytest config'))
    checks.append(check_file_exists('V0.03_HARDENING_COMPLETE.md', 'V0.03 docs'))
    checks.append(check_file_exists('V0.03_QUICK_SUMMARY.md', 'V0.03 summary'))
    checks.append(check_file_exists('tests/test_execution_algorithms.py', 'Execution tests'))
    checks.append(check_file_exists('tests/test_strategy_fractional.py', 'Strategy tests'))
    checks.append(check_file_exists('scripts/platform_smoke.py', 'Smoke test (moved)'))
    print()
    
    # Check no test files in root
    print("🧹 Root Directory Clean:")
    checks.append(check_no_test_files_in_root())
    print()
    
    # Check pytest.ini content
    print("⚙️  Pytest Configuration:")
    checks.append(check_pytest_ini_content())
    print()
    
    # Check lazy imports
    print("📦 Optional Dependencies:")
    checks.append(check_canonical_data_lazy_import())
    print()
    
    # Check fractional support
    print("💰 Fractional Shares:")
    checks.append(check_order_execution_float_quantity())
    print()
    
    # Check gitignore
    print("🙈 Git Exclusions:")
    checks.append(check_gitignore_exports())
    print()
    
    # Summary
    print("="*80)
    passed = sum(checks)
    total = len(checks)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"VERIFICATION SUMMARY: {passed}/{total} checks passed ({percentage:.0f}%)")
    print("="*80)
    
    if passed == total:
        print("✅ V0.03 VERIFICATION COMPLETE - ALL CHECKS PASSED")
        return 0
    else:
        print(f"⚠️  V0.03 VERIFICATION INCOMPLETE - {total - passed} checks failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
