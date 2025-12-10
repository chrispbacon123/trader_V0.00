#!/usr/bin/env python3
"""
System Status Checker
Comprehensive validation of all platform features
"""

import sys
import os
from pathlib import Path
import importlib

class SystemStatus:
    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []
    
    def check_imports(self):
        """Check all required imports"""
        print("\n🔍 Checking imports...")
        
        required_modules = [
            ('yfinance', 'yfinance'),
            ('pandas', 'pandas'),
            ('numpy', 'numpy'),
            ('sklearn', 'scikit-learn'),
            ('xgboost', 'xgboost'),
        ]
        
        optional_modules = [
            ('optuna', 'optuna'),
            ('QuantLib', 'QuantLib-Python'),
        ]
        
        for module, package in required_modules:
            try:
                importlib.import_module(module)
                self.checks_passed.append(f"✓ {package}")
            except ImportError:
                self.checks_failed.append(f"✗ {package} (required)")
        
        for module, package in optional_modules:
            try:
                importlib.import_module(module)
                self.checks_passed.append(f"✓ {package}")
            except ImportError:
                self.warnings.append(f"⚠ {package} (optional - some features unavailable)")
    
    def check_files(self):
        """Check all required files exist"""
        print("🔍 Checking files...")
        
        required_files = [
            'advanced_trading_interface.py',
            'ml_strategy.py',
            'simple_strategy.py',
            'short_term_strategy.py',
            'optimized_ml_strategy.py',
            'enhanced_utils.py',
            'strategy_builder.py',
            'strategy_exporter.py',
        ]
        
        for filename in required_files:
            filepath = Path(filename)
            if filepath.exists():
                self.checks_passed.append(f"✓ {filename}")
            else:
                self.checks_failed.append(f"✗ {filename} missing")
    
    def check_strategies(self):
        """Check strategy classes"""
        print("🔍 Checking strategies...")
        
        try:
            from simple_strategy import SimpleMeanReversionStrategy
            from ml_strategy import MLTradingStrategy
            from short_term_strategy import ShortTermStrategy
            from optimized_ml_strategy import OptimizedMLStrategy
            
            strategies = [
                ('Simple', SimpleMeanReversionStrategy),
                ('ML', MLTradingStrategy),
                ('ShortTerm', ShortTermStrategy),
                ('Optimized', OptimizedMLStrategy),
            ]
            
            for name, cls in strategies:
                # Check if backtest method exists
                if hasattr(cls, 'backtest'):
                    self.checks_passed.append(f"✓ {name} strategy")
                else:
                    self.checks_failed.append(f"✗ {name} strategy missing backtest")
                    
        except Exception as e:
            self.checks_failed.append(f"✗ Strategy import failed: {e}")
    
    def check_data_directories(self):
        """Check/create required directories"""
        print("🔍 Checking directories...")
        
        dirs = [
            'results',
            'saved_strategies',
            'saved_portfolios',
            'strategy_exports',
            'live_strategies',
            'custom_strategies',
        ]
        
        for dirname in dirs:
            dirpath = Path(dirname)
            if dirpath.exists():
                self.checks_passed.append(f"✓ {dirname}/")
            else:
                try:
                    dirpath.mkdir(exist_ok=True)
                    self.checks_passed.append(f"✓ {dirname}/ (created)")
                except Exception as e:
                    self.checks_failed.append(f"✗ {dirname}/ ({e})")
    
    def check_json_files(self):
        """Check/create JSON data files"""
        print("🔍 Checking data files...")
        
        json_files = {
            'portfolios.json': {},
            'settings.json': {'default_capital': 100000, 'default_target': 15.0},
            'watchlists.json': {},
            'strategy_history.json': [],
        }
        
        for filename, default_content in json_files.items():
            filepath = Path(filename)
            if filepath.exists():
                try:
                    import json
                    with open(filepath, 'r') as f:
                        json.load(f)
                    self.checks_passed.append(f"✓ {filename}")
                except json.JSONDecodeError:
                    self.warnings.append(f"⚠ {filename} (corrupted, will backup)")
            else:
                try:
                    import json
                    with open(filepath, 'w') as f:
                        json.dump(default_content, f, indent=2)
                    self.checks_passed.append(f"✓ {filename} (created)")
                except Exception as e:
                    self.checks_failed.append(f"✗ {filename} ({e})")
    
    def test_data_download(self):
        """Test data download capability"""
        print("🔍 Testing data download...")
        
        try:
            import yfinance as yf
            from datetime import datetime, timedelta
            
            end = datetime.now()
            start = end - timedelta(days=7)
            
            data = yf.download('SPY', start=start, end=end, progress=False)
            
            if data is not None and len(data) > 0:
                self.checks_passed.append(f"✓ Data download (got {len(data)} days)")
            else:
                self.warnings.append("⚠ Data download returned empty")
                
        except Exception as e:
            self.checks_failed.append(f"✗ Data download failed: {e}")
    
    def run_all_checks(self):
        """Run all system checks"""
        print("\n" + "="*70)
        print("SYSTEM STATUS CHECK")
        print("="*70)
        
        self.check_imports()
        self.check_files()
        self.check_strategies()
        self.check_data_directories()
        self.check_json_files()
        self.test_data_download()
        
        print("\n" + "="*70)
        print("RESULTS")
        print("="*70)
        
        if self.checks_passed:
            print(f"\n✅ Passed ({len(self.checks_passed)}):")
            for check in self.checks_passed[:10]:  # Show first 10
                print(f"   {check}")
            if len(self.checks_passed) > 10:
                print(f"   ... and {len(self.checks_passed) - 10} more")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if self.checks_failed:
            print(f"\n❌ Failed ({len(self.checks_failed)}):")
            for check in self.checks_failed:
                print(f"   {check}")
        
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        
        total = len(self.checks_passed) + len(self.checks_failed)
        success_rate = (len(self.checks_passed) / total * 100) if total > 0 else 0
        
        print(f"Total Checks: {total}")
        print(f"Passed: {len(self.checks_passed)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Failed: {len(self.checks_failed)}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if len(self.checks_failed) == 0:
            print("\n✅ System is READY")
            print("\nTo start:")
            print("  python3 advanced_trading_interface.py")
        else:
            print("\n⚠️  System has issues that need attention")
            print("Please fix failed checks before proceeding")
        
        print("="*70 + "\n")
        
        return len(self.checks_failed) == 0

if __name__ == '__main__':
    checker = SystemStatus()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)
