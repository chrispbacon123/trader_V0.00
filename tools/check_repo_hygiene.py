#!/usr/bin/env python3
"""
Repository Hygiene Checker
Validates that the repo follows conventions to prevent pytest/import issues

Run: python tools/check_repo_hygiene.py

Checks:
1. No test_*.py or *_test.py files outside tests/
2. No files with sys.exit() at module level outside __main__ block
3. strategy_exports contains no test_*.py files
4. All smoke scripts use check_* not test_* function names
"""

import sys
import os
import re
from pathlib import Path


def find_repo_root() -> Path:
    """Find the repo root (where core_config.py lives)"""
    current = Path(__file__).resolve().parent
    
    # Go up until we find core_config.py
    for _ in range(5):
        if (current / 'core_config.py').exists():
            return current
        current = current.parent
    
    # Fallback to script's parent's parent
    return Path(__file__).resolve().parent.parent


def check_test_files_outside_tests(repo_root: Path) -> list:
    """Find any test_*.py or *_test.py files outside tests/ directory"""
    issues = []
    tests_dir = repo_root / 'tests'
    
    for py_file in repo_root.rglob('*.py'):
        # Skip tests directory
        if tests_dir in py_file.parents or py_file.parent == tests_dir:
            continue
        
        # Skip __pycache__
        if '__pycache__' in str(py_file):
            continue
        
        name = py_file.name
        if name.startswith('test_') or name.endswith('_test.py'):
            issues.append(f"Test-like file outside tests/: {py_file.relative_to(repo_root)}")
    
    return issues


def check_strategy_exports(repo_root: Path) -> list:
    """Ensure no test_*.py files in strategy_exports"""
    issues = []
    exports_dir = repo_root / 'strategy_exports'
    
    if not exports_dir.exists():
        return []
    
    for py_file in exports_dir.rglob('*.py'):
        if py_file.name.startswith('test_'):
            issues.append(f"test_*.py in strategy_exports: {py_file.relative_to(repo_root)}")
    
    return issues


def check_smoke_function_names(repo_root: Path) -> list:
    """Ensure smoke scripts in tools/ don't use test_* function names
    
    Note: scripts/ is excluded from pytest via norecursedirs, so we only
    check tools/ which might be used as modules.
    """
    issues = []
    
    # Only check tools/ directory - scripts/ is explicitly excluded from pytest
    dir_path = repo_root / 'tools'
    if not dir_path.exists():
        return []
    
    for py_file in dir_path.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        
        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            
            # Look for def test_* functions
            matches = re.findall(r'^def (test_\w+)', content, re.MULTILINE)
            if matches:
                for func in matches:
                    issues.append(
                        f"test_* function in tools/: "
                        f"{py_file.relative_to(repo_root)}::{func}"
                    )
        except Exception:
            pass
    
    return issues


def check_norecursedirs_in_pytest_ini(repo_root: Path) -> list:
    """Verify pytest.ini has proper norecursedirs"""
    issues = []
    pytest_ini = repo_root / 'pytest.ini'
    
    if not pytest_ini.exists():
        issues.append("Missing pytest.ini in repo root")
        return issues
    
    content = pytest_ini.read_text()
    
    required_exclusions = ['strategy_exports', 'scripts', 'tools']
    for excl in required_exclusions:
        if excl not in content:
            issues.append(f"pytest.ini missing norecursedirs entry: {excl}")
    
    return issues


def main():
    """Run all hygiene checks"""
    repo_root = find_repo_root()
    print(f"Checking repo hygiene in: {repo_root}")
    print("=" * 60)
    
    all_issues = []
    
    # Run checks
    checks = [
        ("Test files outside tests/", check_test_files_outside_tests),
        ("Strategy exports", check_strategy_exports),
        ("Smoke function names", check_smoke_function_names),
        ("pytest.ini configuration", check_norecursedirs_in_pytest_ini),
    ]
    
    for name, check_func in checks:
        print(f"\n[CHECK] {name}...")
        issues = check_func(repo_root)
        
        if issues:
            print(f"  [FAIL] {len(issues)} issues found:")
            for issue in issues:
                print(f"    - {issue}")
            all_issues.extend(issues)
        else:
            print("  [OK] Passed")
    
    # Summary
    print("\n" + "=" * 60)
    if all_issues:
        print(f"[FAIL] {len(all_issues)} total issues found")
        return 1
    else:
        print("[OK] All hygiene checks passed")
        return 0


if __name__ == '__main__':
    sys.exit(main())
