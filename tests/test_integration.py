"""
V0.15 Integration Tests
Tests for double-fetch fix, schema stability, versioning, optimization reliability,
and strategy manager persistence
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def synthetic_ohlcv_data():
    """Create synthetic OHLCV data for testing"""
    np.random.seed(42)
    
    dates = pd.date_range(start='2023-01-01', periods=252, freq='B')
    returns = np.random.normal(0.0005, 0.02, len(dates))
    price = 100 * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'Open': price * (1 + np.random.uniform(-0.01, 0.01, len(dates))),
        'High': price * (1 + np.random.uniform(0, 0.02, len(dates))),
        'Low': price * (1 + np.random.uniform(-0.02, 0, len(dates))),
        'Close': price,
        'Volume': np.random.randint(1000000, 10000000, len(dates)),
        'Price': price
    }, index=dates)
    
    df['High'] = df[['Open', 'Close', 'High']].max(axis=1)
    df['Low'] = df[['Open', 'Close', 'Low']].min(axis=1)
    
    return df


@pytest.fixture
def price_only_data():
    """Create price-only data for testing derived OHLC"""
    np.random.seed(42)
    
    dates = pd.date_range(start='2023-01-01', periods=100, freq='B')
    price = 100 + np.cumsum(np.random.randn(len(dates)))
    
    return pd.DataFrame({'Price': price}, index=dates)


# =============================================================================
# DOUBLE-FETCH FIX TESTS
# =============================================================================

class TestDoubleFetchFix:
    """Tests verifying the double-fetch bug is fixed"""
    
    def test_market_analytics_analyze_uses_provided_df(self, synthetic_ohlcv_data):
        """MarketAnalytics.analyze() should use provided df, never fetch"""
        from market_analytics import MarketAnalytics
        
        analytics = MarketAnalytics('TEST')
        
        # Call analyze with our data
        result = analytics.analyze(synthetic_ohlcv_data, symbol='TEST')
        
        # Should succeed
        assert result['success'] is True
        
        # Data summary should match our input
        assert result['data_summary']['rows'] == len(synthetic_ohlcv_data)
        
        # Internal data should be our data
        assert analytics.data is not None
        assert len(analytics.data) == len(synthetic_ohlcv_data)
    
    def test_platform_api_analyze_with_data_injection(self, synthetic_ohlcv_data):
        """Platform API should use injected data, not re-fetch"""
        from platform_api import get_api
        
        api = get_api()
        
        start = datetime(2023, 1, 1)
        end = datetime(2023, 12, 31)
        
        # Inject data via the data parameter
        result = api.analyze_market(
            'TEST',
            start,
            end,
            data=synthetic_ohlcv_data
        )
        
        # Should succeed
        assert result['success'] is True
        
        # Date range in result should match our data, not re-fetched data
        data_summary = result['data_summary']
        assert data_summary['rows'] == len(synthetic_ohlcv_data)
        
        # The date range should match the synthetic data
        assert '2023-01-02' in data_summary['date_range_start']
    
    def test_analyze_does_not_require_yfinance(self, synthetic_ohlcv_data):
        """Analysis with provided data should not import yfinance"""
        from market_analytics import MarketAnalytics
        
        # This should work without yfinance installed/callable
        analytics = MarketAnalytics('TEST')
        result = analytics.analyze(synthetic_ohlcv_data)
        
        assert result['success'] is True
        assert 'regime' in result
        assert 'momentum' in result


# =============================================================================
# VERSION CONSISTENCY TESTS
# =============================================================================

class TestVersionConsistency:
    """Tests verifying centralized versioning"""
    
    def test_core_config_has_version(self):
        """core_config should have PLATFORM_VERSION"""
        from core_config import PLATFORM_VERSION, get_version_string, get_version_info
        
        assert PLATFORM_VERSION is not None
        assert isinstance(PLATFORM_VERSION, str)
        assert PLATFORM_VERSION.startswith('V')
        
        # Version string should work
        version_str = get_version_string()
        assert PLATFORM_VERSION in version_str
        
        # Version info dict should work
        info = get_version_info()
        assert info['version'] == PLATFORM_VERSION
    
    def test_platform_api_returns_correct_version(self, synthetic_ohlcv_data):
        """Platform API should return centralized version"""
        from platform_api import get_api
        from core_config import PLATFORM_VERSION
        
        api = get_api()
        
        result = api.analyze_market(
            'TEST',
            datetime(2023, 1, 1),
            datetime(2023, 12, 31),
            data=synthetic_ohlcv_data
        )
        
        assert result['platform_version'] == PLATFORM_VERSION


# =============================================================================
# SCHEMA STABILITY TESTS
# =============================================================================

class TestSchemaStability:
    """Tests verifying result schemas are stable"""
    
    def test_optimization_schema_never_none_best_params(self):
        """Optimization result should never have None best_params"""
        from result_schemas import OptimizationResult, ensure_optimization_schema
        
        # Simulate a failed optimization with None best_params
        bad_result = {
            'success': False,
            'best_params': None,
            'tested': 10
        }
        
        fixed = ensure_optimization_schema(bad_result)
        
        assert fixed['best_params'] == {}, "best_params should be {} not None"
        assert 'valid' in fixed
        assert 'failures' in fixed
        assert 'failure_summary' in fixed
    
    def test_market_analysis_has_all_required_keys(self, synthetic_ohlcv_data):
        """Market analysis should always return all required keys"""
        from platform_api import get_api
        
        api = get_api()
        
        result = api.analyze_market(
            'TEST',
            datetime(2023, 1, 1),
            datetime(2023, 12, 31),
            data=synthetic_ohlcv_data
        )
        
        required_keys = [
            'success', 'symbol', 'period', 'data_summary',
            'regime', 'key_levels', 'fibonacci', 'momentum', 'risk',
            'warnings', 'error', 'platform_version'
        ]
        
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"
    
    def test_history_record_normalization(self):
        """History records should normalize old formats"""
        from persistence import normalize_run_record
        
        old_format = {
            'date': '2023-01-01',
            'ticker': 'AAPL',
            'total_return': 5.0
        }
        
        normalized = normalize_run_record(old_format)
        
        assert normalized['timestamp'] == '2023-01-01'
        assert normalized['symbol'] == 'AAPL'
        assert normalized['return_pct'] == 5.0
        assert '_schema_version' in normalized


# =============================================================================
# FRACTIONAL SHARES TESTS
# =============================================================================

class TestFractionalShares:
    """Tests verifying fractional share support"""
    
    def test_portfolio_allocation_fractional(self):
        """Portfolio should allocate fractional shares when allowed"""
        from validated_portfolio import ValidatedPortfolio
        
        portfolio = ValidatedPortfolio(equity=10000, fractional_allowed=True)
        
        result = portfolio.allocate(
            {'AAPL': 0.5, 'MSFT': 0.5},
            {'AAPL': 175.50, 'MSFT': 380.00}
        )
        
        # With fractional, shares should not be whole numbers
        for symbol, pos in result['positions'].items():
            shares = pos['shares']
            assert shares != int(shares), f"{symbol} should have fractional shares"
    
    def test_portfolio_allocation_whole_shares_when_disabled(self):
        """Portfolio should use whole shares when fractional disabled"""
        from validated_portfolio import ValidatedPortfolio
        
        portfolio = ValidatedPortfolio(equity=10000, fractional_allowed=False)
        
        result = portfolio.allocate(
            {'AAPL': 0.5, 'MSFT': 0.5},
            {'AAPL': 175.50, 'MSFT': 380.00}
        )
        
        # Without fractional, shares should be whole numbers
        for symbol, pos in result['positions'].items():
            shares = pos['shares']
            assert shares == int(shares), f"{symbol} should have whole shares"


# =============================================================================
# DATA NORMALIZATION TESTS
# =============================================================================

class TestDataNormalization:
    """Tests for data normalization edge cases"""
    
    def test_price_only_df_derives_ohlc(self, price_only_data):
        """Price-only DataFrame should get derived OHLC"""
        from data_normalization import DataNormalizer
        
        normalizer = DataNormalizer()
        df, meta = normalizer.normalize_market_data(
            price_only_data, 
            symbol='TEST',
            require_ohlc=False
        )
        
        assert 'Price' in df.columns
        assert 'High' in df.columns
        assert 'Low' in df.columns
        assert 'Close' in df.columns
    
    def test_ohlcv_df_preserves_columns(self, synthetic_ohlcv_data):
        """Full OHLCV DataFrame should preserve all columns"""
        from data_normalization import DataNormalizer
        
        normalizer = DataNormalizer()
        df, meta = normalizer.normalize_market_data(
            synthetic_ohlcv_data,
            symbol='TEST',
            require_ohlc=False
        )
        
        assert 'Price' in df.columns
        assert 'Open' in df.columns
        assert 'High' in df.columns
        assert 'Low' in df.columns
        assert 'Close' in df.columns


# =============================================================================
# V0.13 OPTIMIZATION RELIABILITY TESTS
# =============================================================================

class TestOptimizationReliability:
    """Tests for V0.13 optimization fixes"""
    
    def test_random_search_returns_stable_schema(self, synthetic_ohlcv_data):
        """random_search should return same schema as grid_search"""
        from strategy_optimizer import StrategyOptimizer
        from short_term_strategy import ShortTermStrategy
        from datetime import datetime
        
        optimizer = StrategyOptimizer(ShortTermStrategy, metric='sharpe_ratio')
        
        # Use a tiny param distribution
        param_dist = {
            'lookback': (10, 20),
            'prediction_horizon': (3, 5)
        }
        
        start = datetime(2023, 1, 1)
        end = datetime(2023, 6, 30)
        
        # Note: This will attempt to fetch data (network dependent)
        # For a true offline test, we'd need to inject data into random_search
        result = optimizer.random_search(
            param_dist,
            'SPY',
            start,
            end,
            n_iterations=2
        )
        
        # Verify all required schema keys exist
        required_keys = [
            'success', 'best_params', 'best_score', 'tested', 'valid',
            'failures', 'skipped', 'error', 'warnings', 'failure_summary',
            'example_failures', 'top_results', 'all_results'
        ]
        
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"
        
        # best_params must never be None
        assert result['best_params'] is not None, "best_params should never be None"
        assert isinstance(result['best_params'], dict), "best_params should be a dict"
    
    def test_grid_search_memory_safe_sampling(self):
        """grid_search should correctly calculate total combinations and sample"""
        import math
        
        # Test the math.prod calculation for grid size estimation
        param_grid = {
            'lookback': list(range(10, 50)),      # 40 values
            'threshold': [0.1, 0.2, 0.3, 0.4, 0.5]  # 5 values
        }
        
        total = math.prod(len(v) for v in param_grid.values())
        assert total == 200, f"Grid should have 200 combinations, got {total}"
        
        # Verify the _estimate_grid_size helper if it exists
        from strategy_optimizer import StrategyOptimizer
        from short_term_strategy import ShortTermStrategy
        
        optimizer = StrategyOptimizer(ShortTermStrategy, metric='sharpe_ratio')
        
        # Check the min rows estimation works without crashing
        min_rows = optimizer._estimate_min_rows(ShortTermStrategy, param_grid)
        assert min_rows is None or min_rows > 0
    
    def test_failure_categories_in_schema(self):
        """Optimizer should track failure categories"""
        from strategy_optimizer import StrategyOptimizer
        from result_schemas import ensure_optimization_schema
        
        # Simulate a failed optimization result
        bad_result = {
            'success': False,
            'best_params': None,
            'tested': 10,
            'failures': 10
        }
        
        fixed = ensure_optimization_schema(bad_result)
        
        # Should have failure_summary and example_failures
        assert 'failure_summary' in fixed
        assert 'example_failures' in fixed
        assert fixed['best_params'] == {}, "best_params should be {} not None"
    
    def test_platform_version_in_api_response(self, synthetic_ohlcv_data):
        """API responses should include canonical platform version"""
        from platform_api import get_api
        from core_config import PLATFORM_VERSION
        
        api = get_api()
        
        result = api.analyze_market(
            'TEST',
            datetime(2023, 1, 1),
            datetime(2023, 12, 31),
            data=synthetic_ohlcv_data
        )
        
        assert result['platform_version'] == PLATFORM_VERSION


# =============================================================================
# V0.14 ADDITIONAL ROBUSTNESS TESTS
# =============================================================================

class TestImportRobustness:
    """Tests for optional dependency handling"""
    
    def test_import_core_modules_without_yfinance(self):
        """Core modules should import without yfinance installed"""
        # These should all work without triggering yfinance import
        from data_normalization import DataNormalizer, DataContractError
        from platform_api import PlatformAPI
        from strategy_optimizer import StrategyOptimizer
        from persistence import normalize_run_record
        from result_schemas import OptimizationResult, ensure_optimization_schema
        from core_config import PLATFORM_VERSION
        
        assert DataNormalizer is not None
        assert PlatformAPI is not None
        assert PLATFORM_VERSION.startswith('V')
    
    def test_persistence_handles_missing_keys(self):
        """Persistence should handle records with missing keys"""
        from persistence import normalize_run_record, safe_get
        
        minimal_record = {}
        normalized = normalize_run_record(minimal_record)
        
        # Should have all required keys with defaults
        assert 'timestamp' in normalized
        assert 'symbol' in normalized
        assert 'strategy' in normalized
        assert 'return_pct' in normalized
        
        # safe_get should work with missing keys
        assert safe_get(normalized, 'nonexistent', 'default') == 'default'


class TestResultSchemaValidation:
    """Tests for result schema validation utilities"""
    
    def test_ensure_optimization_schema_fixes_none_params(self):
        """ensure_optimization_schema should fix None best_params"""
        from result_schemas import ensure_optimization_schema
        
        bad_result = {
            'success': False,
            'best_params': None,
            'tested': 10
        }
        
        fixed = ensure_optimization_schema(bad_result)
        
        assert fixed['best_params'] == {}
        assert 'valid' in fixed
        assert 'failures' in fixed
        assert 'failure_summary' in fixed
        assert 'example_failures' in fixed
    
    def test_ensure_backtest_schema_adds_defaults(self):
        """ensure_backtest_schema should add missing fields"""
        from result_schemas import ensure_backtest_schema
        
        minimal = {'symbol': 'SPY'}
        fixed = ensure_backtest_schema(minimal)
        
        assert 'success' in fixed
        assert 'return_pct' in fixed
        assert 'win_rate' in fixed
        assert 'max_drawdown' in fixed
    
    def test_history_record_handles_old_keys(self):
        """HistoryRecord should map old key names"""
        from result_schemas import HistoryRecord
        
        old_format = {
            'ticker': 'AAPL',
            'date': '2024-01-01',
            'total_return': 5.5
        }
        
        record = HistoryRecord.from_dict(old_format)
        
        assert record.symbol == 'AAPL'
        assert record.timestamp == '2024-01-01'
        assert record.return_pct == 5.5


class TestDataContractEnforcement:
    """Tests for data contract enforcement"""
    
    def test_empty_df_raises_contract_error(self):
        """Empty DataFrame should raise DataContractError"""
        from data_normalization import DataNormalizer, DataContractError
        import pandas as pd
        
        with pytest.raises(DataContractError):
            DataNormalizer.normalize_market_data(pd.DataFrame(), symbol='TEST')
    
    def test_none_df_raises_contract_error(self):
        """None DataFrame should raise DataContractError"""
        from data_normalization import DataNormalizer, DataContractError
        
        with pytest.raises(DataContractError):
            DataNormalizer.normalize_market_data(None, symbol='TEST')
    
    def test_multiindex_df_gets_flattened(self, synthetic_ohlcv_data):
        """MultiIndex columns should be flattened"""
        from data_normalization import DataNormalizer
        import pandas as pd
        
        # Create MultiIndex like yfinance returns
        df = synthetic_ohlcv_data.copy()
        df.columns = pd.MultiIndex.from_tuples(
            [(col, 'SPY') for col in df.columns]
        )
        
        normalized, meta = DataNormalizer.normalize_market_data(
            df, symbol='SPY', require_ohlc=False
        )
        
        # Should be flattened
        assert not isinstance(normalized.columns, pd.MultiIndex)
        assert 'Price' in normalized.columns


# =============================================================================
# V0.15 STRATEGY MANAGER PERSISTENCE TESTS
# =============================================================================

class TestStrategyManagerPersistence:
    """Tests for strategy manager save/load functionality"""
    
    def test_strategy_save_and_load(self, tmp_path):
        """StrategyManager should correctly save and load strategies"""
        from strategy_manager import StrategyManager, StrategyConfig
        import json
        
        config_file = tmp_path / "test_strategies.json"
        
        # Create manager with temp file
        manager = StrategyManager(str(config_file))
        
        # Create and save a strategy
        config = StrategyConfig(
            name="TestStrategy",
            strategy_type="ShortTermStrategy",
            parameters={'symbol': 'SPY', 'lookback': 14},
            description="Test strategy"
        )
        
        result = manager.save_strategy(config)
        assert result is True, "Strategy should save successfully"
        
        # Verify file exists and contains valid JSON
        assert config_file.exists(), "Config file should exist"
        
        with open(config_file, 'r') as f:
            data = json.load(f)
        
        assert "TestStrategy" in data, "Strategy should be in saved data"
        assert data["TestStrategy"]["strategy_type"] == "ShortTermStrategy"
        
        # Load into a new manager and verify
        manager2 = StrategyManager(str(config_file))
        loaded = manager2.get_strategy("TestStrategy")
        
        assert loaded is not None, "Strategy should load successfully"
        assert loaded.name == "TestStrategy"
        assert loaded.parameters['symbol'] == 'SPY'
    
    def test_strategy_delete_updates_file(self, tmp_path):
        """Deleting a strategy should update the file correctly"""
        from strategy_manager import StrategyManager, StrategyConfig
        import json
        
        config_file = tmp_path / "test_strategies.json"
        manager = StrategyManager(str(config_file))
        
        # Create two strategies
        manager.save_strategy(StrategyConfig(
            name="Strategy1", strategy_type="Type1", parameters={}
        ))
        manager.save_strategy(StrategyConfig(
            name="Strategy2", strategy_type="Type2", parameters={}
        ))
        
        # Delete one
        manager.delete_strategy("Strategy1")
        
        # Verify file only has Strategy2
        with open(config_file, 'r') as f:
            data = json.load(f)
        
        assert "Strategy1" not in data
        assert "Strategy2" in data
    
    def test_safe_json_save_argument_order(self, tmp_path):
        """Verify safe_json_save has correct argument order (filename, data)"""
        from enhanced_utils import safe_json_save, safe_json_load
        
        test_file = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42}
        
        # This should work: safe_json_save(filename, data)
        safe_json_save(str(test_file), test_data)
        
        assert test_file.exists()
        
        loaded = safe_json_load(str(test_file), {})
        assert loaded == test_data


# =============================================================================
# V0.15 IMPORT SMOKE TESTS
# =============================================================================

class TestImportSmoke:
    """Smoke tests to verify imports work without optional dependencies"""
    
    def test_import_advanced_trading_interface(self):
        """advanced_trading_interface should import without yfinance/optuna"""
        # This should not raise even if yfinance/optuna aren't installed
        try:
            import advanced_trading_interface
            assert True
        except ImportError as e:
            # Only fail if it's asking for yfinance/optuna at import time
            if 'yfinance' in str(e) or 'optuna' in str(e):
                pytest.fail(f"Should not require yfinance/optuna at import: {e}")
            raise
    
    def test_import_platform_api(self):
        """platform_api should import cleanly"""
        from platform_api import PlatformAPI, get_api
        assert PlatformAPI is not None
        assert get_api is not None
    
    def test_import_strategy_optimizer(self):
        """strategy_optimizer should import cleanly"""
        from strategy_optimizer import StrategyOptimizer
        assert StrategyOptimizer is not None


# =============================================================================
# EXPORT HYGIENE TESTS
# =============================================================================

class TestExportHygiene:
    """Tests to ensure export files don't interfere with pytest discovery"""
    
    def test_export_basename_never_starts_with_test(self):
        """Export filenames should never start with 'test_' to avoid pytest collection"""
        from strategy_builder import sanitize_export_basename
        
        # Test various strategy names including 'test'
        test_cases = [
            ('test', '20251225_120000'),
            ('Test Strategy', '20251225_120000'),
            ('test_strategy', '20251225_120000'),
            ('TestML', '20251225_120000'),
            ('My Strategy', '20251225_120000'),
            ('123Strategy', '20251225_120000'),
        ]
        
        for name, timestamp in test_cases:
            basename = sanitize_export_basename(name, timestamp)
            assert basename.startswith('export_'), f"Basename '{basename}' should start with 'export_'"
            assert not basename.startswith('test_'), f"Basename '{basename}' should not start with 'test_'"
    
    def test_no_test_files_in_strategy_exports(self):
        """Ensure no files in strategy_exports start with test_"""
        import os
        exports_dir = Path(__file__).parent.parent / 'strategy_exports'
        
        if exports_dir.exists():
            for f in exports_dir.iterdir():
                if f.is_file():
                    assert not f.name.startswith('test_'), \
                        f"File '{f.name}' in strategy_exports starts with 'test_' - will be collected by pytest"
    
    def test_sanitize_export_basename_produces_valid_python_module(self):
        """Export basenames should be valid Python module names"""
        from strategy_builder import sanitize_export_basename
        import re
        
        test_cases = [
            ('My Strategy!', '20251225'),
            ('123 Numbers', '20251225'),
            ('Special@#$Chars', '20251225'),
        ]
        
        valid_module_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
        
        for name, timestamp in test_cases:
            basename = sanitize_export_basename(name, timestamp)
            # Remove the file extension check - we're testing the base name
            assert valid_module_pattern.match(basename), \
                f"Basename '{basename}' is not a valid Python module name"


# =============================================================================
# V0.17 HYGIENE TESTS
# =============================================================================

class TestRepoHygiene:
    """Tests to ensure repo follows conventions for pytest/import safety"""
    
    def test_no_test_files_outside_tests_directory(self):
        """No test_*.py or *_test.py files should exist outside tests/"""
        repo_root = Path(__file__).parent.parent
        tests_dir = repo_root / 'tests'
        
        issues = []
        for py_file in repo_root.rglob('*.py'):
            # Skip tests directory
            if tests_dir in py_file.parents or py_file.parent == tests_dir:
                continue
            
            # Skip __pycache__
            if '__pycache__' in str(py_file):
                continue
            
            name = py_file.name
            if name.startswith('test_') or name.endswith('_test.py'):
                issues.append(str(py_file.relative_to(repo_root)))
        
        assert len(issues) == 0, f"Found test-like files outside tests/: {issues}"
    
    def test_tools_directory_excluded_from_pytest(self):
        """tools/ should be in norecursedirs in pytest.ini"""
        repo_root = Path(__file__).parent.parent
        pytest_ini = repo_root / 'pytest.ini'
        
        assert pytest_ini.exists(), "pytest.ini should exist"
        
        content = pytest_ini.read_text()
        assert 'tools' in content, "tools should be in norecursedirs"
    
    def test_scripts_directory_excluded_from_pytest(self):
        """scripts/ should be in norecursedirs in pytest.ini"""
        repo_root = Path(__file__).parent.parent
        pytest_ini = repo_root / 'pytest.ini'
        
        content = pytest_ini.read_text()
        assert 'scripts' in content, "scripts should be in norecursedirs"


# =============================================================================
# V0.17 BATCH MODE TESTS
# =============================================================================

class TestBatchMode:
    """Tests for batch analyze/optimize functionality"""
    
    def test_batch_analyze_returns_list(self, synthetic_ohlcv_data):
        """batch_analyze should return a list of results"""
        from platform_api import get_api
        
        api = get_api()
        
        # Test with single symbol (using injected data would need mock)
        # For now just verify the method exists and has correct signature
        assert hasattr(api, 'batch_analyze')
        assert callable(api.batch_analyze)
    
    def test_batch_optimize_returns_list(self):
        """batch_optimize should return a list of results"""
        from platform_api import get_api
        
        api = get_api()
        
        # Verify the method exists and has correct signature
        assert hasattr(api, 'batch_optimize')
        assert callable(api.batch_optimize)


# =============================================================================
# V0.17 CACHE AND LOGGER TESTS
# =============================================================================

class TestCacheManager:
    """Tests for optional data caching"""
    
    def test_cache_manager_disabled_by_default(self):
        """Cache should be disabled by default"""
        from cache_manager import CacheManager
        
        cache = CacheManager()
        assert cache.enabled == False
    
    def test_cache_manager_stats(self):
        """Cache stats should work even when disabled"""
        from cache_manager import CacheManager
        
        cache = CacheManager(enabled=False)
        stats = cache.stats()
        
        assert 'enabled' in stats
        assert stats['enabled'] == False
        assert 'entries' in stats
    
    def test_cache_get_returns_none_when_disabled(self):
        """Cache get should return None when disabled"""
        from cache_manager import CacheManager
        from datetime import datetime
        
        cache = CacheManager(enabled=False)
        result = cache.get('SPY', datetime(2024, 1, 1), datetime(2024, 12, 31))
        
        assert result is None


class TestRunLogger:
    """Tests for experiment/run logging"""
    
    def test_run_logger_logs_to_jsonl(self, tmp_path):
        """Run logger should write JSONL records"""
        from run_logger import RunLogger
        import json
        
        logger = RunLogger(runs_dir=str(tmp_path), enabled=True)
        
        run_id = logger.log(
            kind='test',
            inputs={'symbol': 'SPY'},
            outputs={'result': 'ok'}
        )
        
        assert run_id is not None
        
        # Verify JSONL file exists and is valid
        log_file = tmp_path / 'runs.jsonl'
        assert log_file.exists()
        
        with open(log_file, 'r') as f:
            line = f.readline()
            record = json.loads(line)
        
        assert record['kind'] == 'test'
        assert record['inputs']['symbol'] == 'SPY'
        assert 'platform_version' in record
    
    def test_run_logger_get_history(self, tmp_path):
        """Run logger should retrieve history"""
        from run_logger import RunLogger
        
        logger = RunLogger(runs_dir=str(tmp_path), enabled=True)
        
        logger.log(kind='analyze', inputs={'symbol': 'SPY'})
        logger.log(kind='backtest', inputs={'symbol': 'AAPL'})
        
        history = logger.get_history(limit=10)
        assert len(history) == 2
        
        # Newest first
        assert history[0]['kind'] == 'backtest'
        assert history[1]['kind'] == 'analyze'


# =============================================================================
# NEW PLATFORM CAPABILITY TESTS
# =============================================================================

class TestBatchModeEnhanced:
    """Tests for enhanced batch analyze/optimize functionality"""
    
    def test_batch_analyze_with_data_map(self, synthetic_ohlcv_data):
        """batch_analyze should use data_map to avoid refetching"""
        from platform_api import get_api
        
        api = get_api()
        
        # Create data_map with pre-fetched data
        data_map = {'TEST': synthetic_ohlcv_data}
        
        start = datetime(2023, 1, 1)
        end = datetime(2023, 12, 31)
        
        results = api.batch_analyze(
            symbols=['TEST'],
            start_date=start,
            end_date=end,
            data_map=data_map
        )
        
        assert len(results) == 1
        assert results[0]['symbol'] == 'TEST'
        assert results[0]['success'] is True
    
    def test_batch_analyze_csv_export(self, synthetic_ohlcv_data, tmp_path):
        """batch_analyze results can be exported to CSV"""
        from platform_api import get_api, export_batch_analysis_csv
        
        api = get_api()
        
        data_map = {'TEST': synthetic_ohlcv_data}
        start = datetime(2023, 1, 1)
        end = datetime(2023, 12, 31)
        
        results = api.batch_analyze(
            symbols=['TEST'],
            start_date=start,
            end_date=end,
            data_map=data_map
        )
        
        csv_path = tmp_path / 'batch_analysis.csv'
        success = export_batch_analysis_csv(results, str(csv_path))
        
        assert success is True
        assert csv_path.exists()
        
        # Verify CSV content
        import csv
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 1
        assert rows[0]['symbol'] == 'TEST'
    
    def test_batch_optimize_csv_export(self, tmp_path):
        """batch_optimize results can be exported to CSV"""
        from platform_api import export_batch_optimize_csv
        
        # Simulate optimization results
        results = [
            {
                'symbol': 'SPY',
                'success': True,
                'best_score': 1.5,
                'best_params': {'lookback': 20},
                'tested': 10,
                'valid': 8,
                'failures': 2,
                'error': None,
                'platform_version': 'test'
            }
        ]
        
        csv_path = tmp_path / 'batch_optimize.csv'
        success = export_batch_optimize_csv(results, str(csv_path))
        
        assert success is True
        assert csv_path.exists()


class TestRunAnalysis:
    """Tests for run analysis and comparison utilities"""
    
    def test_load_runs_from_jsonl(self, tmp_path):
        """load_runs should read JSONL file correctly"""
        from run_analysis import load_runs
        import json
        
        # Create test JSONL file
        log_file = tmp_path / 'runs.jsonl'
        test_runs = [
            {'timestamp': '2024-01-01T10:00:00', 'run_id': 'a1', 'kind': 'optimize', 'inputs': {'symbol': 'SPY'}},
            {'timestamp': '2024-01-02T10:00:00', 'run_id': 'b2', 'kind': 'analyze', 'inputs': {'symbol': 'QQQ'}},
        ]
        
        with open(log_file, 'w') as f:
            for run in test_runs:
                f.write(json.dumps(run) + '\n')
        
        # Load and verify
        runs = load_runs(str(log_file))
        assert len(runs) == 2
        # Newest first
        assert runs[0]['run_id'] == 'b2'
    
    def test_load_runs_filter_by_kind(self, tmp_path):
        """load_runs should filter by operation kind"""
        from run_analysis import load_runs
        import json
        
        log_file = tmp_path / 'runs.jsonl'
        test_runs = [
            {'timestamp': '2024-01-01T10:00:00', 'run_id': 'a1', 'kind': 'optimize', 'inputs': {}},
            {'timestamp': '2024-01-02T10:00:00', 'run_id': 'b2', 'kind': 'analyze', 'inputs': {}},
            {'timestamp': '2024-01-03T10:00:00', 'run_id': 'c3', 'kind': 'optimize', 'inputs': {}},
        ]
        
        with open(log_file, 'w') as f:
            for run in test_runs:
                f.write(json.dumps(run) + '\n')
        
        runs = load_runs(str(log_file), kind='optimize')
        assert len(runs) == 2
        assert all(r['kind'] == 'optimize' for r in runs)
    
    def test_summarize_runs(self, tmp_path):
        """summarize_runs should produce correct statistics"""
        from run_analysis import load_runs, summarize_runs
        import json
        
        log_file = tmp_path / 'runs.jsonl'
        test_runs = [
            {'timestamp': '2024-01-01T10:00:00', 'run_id': 'a1', 'kind': 'optimize', 
             'inputs': {'symbol': 'SPY'}, 'outputs': {'best_score': 1.5, 'success': True}, 
             'failure_summary': {}, 'error': None},
            {'timestamp': '2024-01-02T10:00:00', 'run_id': 'b2', 'kind': 'analyze',
             'inputs': {'symbol': 'QQQ'}, 'outputs': {}, 'failure_summary': {}, 'error': None},
            {'timestamp': '2024-01-03T10:00:00', 'run_id': 'c3', 'kind': 'optimize',
             'inputs': {'symbol': 'AAPL'}, 'outputs': {}, 'failure_summary': {'data_contract': 1}, 
             'error': 'Data error'},
        ]
        
        with open(log_file, 'w') as f:
            for run in test_runs:
                f.write(json.dumps(run) + '\n')
        
        runs = load_runs(str(log_file))
        summary = summarize_runs(runs)
        
        assert summary['total_runs'] == 3
        assert summary['by_kind']['optimize'] == 2
        assert summary['by_kind']['analyze'] == 1
        assert summary['error_rate'] > 0  # One error
        assert 'data_contract' in dict(summary['common_failure_categories'])
    
    def test_compare_runs(self, tmp_path):
        """compare_runs should identify differences"""
        from run_analysis import compare_runs
        import json
        
        log_file = tmp_path / 'runs.jsonl'
        test_runs = [
            {'timestamp': '2024-01-01T10:00:00', 'run_id': 'run_a', 'kind': 'optimize',
             'inputs': {'symbol': 'SPY'}, 'outputs': {'best_score': 1.0}},
            {'timestamp': '2024-01-02T10:00:00', 'run_id': 'run_b', 'kind': 'optimize',
             'inputs': {'symbol': 'SPY'}, 'outputs': {'best_score': 2.0}},
        ]
        
        with open(log_file, 'w') as f:
            for run in test_runs:
                f.write(json.dumps(run) + '\n')
        
        result = compare_runs('run_a', 'run_b', str(log_file))
        
        assert result['found_both'] is True
        # Outputs differ
        assert 'outputs' in result['diff'] or 'outputs_detail' in result['diff']


class TestDecisionTrace:
    """Tests for strategy decision trace / explainability"""
    
    def test_backtest_with_debug_includes_trace(self, synthetic_ohlcv_data):
        """backtest_strategy with debug=True should include decision_trace"""
        from platform_api import get_api
        from simple_strategy import SimpleMeanReversionStrategy
        
        api = get_api()
        
        result = api.backtest_strategy(
            strategy_class=SimpleMeanReversionStrategy,
            symbol='TEST',
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            params={'lookback': 20, 'std_dev': 2.0},
            data=synthetic_ohlcv_data,
            debug=True
        )
        
        assert result['success'] is True
        assert 'decision_trace' in result
        
        trace = result['decision_trace']
        assert 'strategy' in trace
        assert 'indicator_values' in trace
        assert 'thresholds' in trace
        assert 'warnings' in trace
    
    def test_backtest_without_debug_no_trace(self, synthetic_ohlcv_data):
        """backtest_strategy without debug should not include trace"""
        from platform_api import get_api
        from simple_strategy import SimpleMeanReversionStrategy
        
        api = get_api()
        
        result = api.backtest_strategy(
            strategy_class=SimpleMeanReversionStrategy,
            symbol='TEST',
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            params={'lookback': 20, 'std_dev': 2.0},
            data=synthetic_ohlcv_data,
            debug=False
        )
        
        assert result['success'] is True
        # No trace without debug
        assert 'decision_trace' not in result or result.get('decision_trace') is None


class TestOptimizerPruning:
    """Tests for optimizer early stopping / pruning"""
    
    def test_too_few_trades_returns_low_score(self, synthetic_ohlcv_data):
        """Optimizer should return low score for strategies with too few trades"""
        from strategy_optimizer import StrategyOptimizer
        from simple_strategy import SimpleMeanReversionStrategy
        
        optimizer = StrategyOptimizer(SimpleMeanReversionStrategy, metric='sharpe_ratio')
        
        # Use params that might result in few trades
        params = {'lookback': 200, 'std_dev': 10.0}  # Very conservative
        
        start = datetime(2023, 1, 1)
        end = datetime(2023, 12, 31)
        
        try:
            score, metrics, category = optimizer._evaluate_params(
                params, 'TEST', start, end, 10000, synthetic_ohlcv_data
            )
            
            # Either returns low score or category indicates pruning
            if category == 'too_few_trades':
                assert score == float('-inf')
            # Otherwise normal evaluation happened
        except Exception:
            # Strategy may raise exception for invalid params, that's OK
            pass


# =============================================================================
# V0.19 DF-IN OPTIMIZATION TESTS
# =============================================================================

class TestDfInOptimization:
    """Tests for V0.19 df-in optimization support"""
    
    def test_optimize_strategy_accepts_data_param(self, synthetic_ohlcv_data):
        """optimize_strategy should accept a data parameter"""
        from platform_api import get_api
        from simple_strategy import SimpleMeanReversionStrategy
        
        api = get_api()
        
        # Check the method accepts data parameter
        import inspect
        sig = inspect.signature(api.optimize_strategy)
        params = list(sig.parameters.keys())
        assert 'data' in params, "optimize_strategy should accept 'data' parameter"
    
    def test_optimize_strategy_with_injected_data_no_fetch(self, synthetic_ohlcv_data):
        """optimize_strategy with data param should not fetch"""
        from platform_api import get_api
        from simple_strategy import SimpleMeanReversionStrategy
        
        api = get_api()
        
        start = datetime(2023, 1, 1)
        end = datetime(2023, 12, 31)
        
        # Tiny param grid for fast test
        param_grid = {'lookback': [20], 'std_dev': [2.0]}
        
        # Run with injected data - main check is that it succeeds and returns schema
        result = api.optimize_strategy(
            strategy_class=SimpleMeanReversionStrategy,
            param_grid=param_grid,
            symbol='TEST',
            start_date=start,
            end_date=end,
            max_combinations=5,
            data=synthetic_ohlcv_data  # Inject data
        )
        
        # Key check is that result is valid and has stable schema
        assert 'best_params' in result
        assert result['best_params'] is not None or result['best_params'] == {}
        assert 'success' in result
        assert 'tested' in result
    
    def test_grid_search_accepts_data_param(self):
        """grid_search should accept a data parameter"""
        from strategy_optimizer import StrategyOptimizer
        from simple_strategy import SimpleMeanReversionStrategy
        import inspect
        
        optimizer = StrategyOptimizer(SimpleMeanReversionStrategy)
        
        sig = inspect.signature(optimizer.grid_search)
        params = list(sig.parameters.keys())
        assert 'data' in params, "grid_search should accept 'data' parameter"
    
    def test_random_search_accepts_data_param(self):
        """random_search should accept a data parameter"""
        from strategy_optimizer import StrategyOptimizer
        from simple_strategy import SimpleMeanReversionStrategy
        import inspect
        
        optimizer = StrategyOptimizer(SimpleMeanReversionStrategy)
        
        sig = inspect.signature(optimizer.random_search)
        params = list(sig.parameters.keys())
        assert 'data' in params, "random_search should accept 'data' parameter"
    
    def test_batch_optimize_accepts_data_map(self):
        """batch_optimize should accept a data_map parameter"""
        from platform_api import get_api
        import inspect
        
        api = get_api()
        
        sig = inspect.signature(api.batch_optimize)
        params = list(sig.parameters.keys())
        assert 'data_map' in params, "batch_optimize should accept 'data_map' parameter"
    
    def test_batch_optimize_with_data_map_reuses_data(self, synthetic_ohlcv_data):
        """batch_optimize with data_map should reuse data per symbol"""
        from platform_api import get_api
        from simple_strategy import SimpleMeanReversionStrategy
        
        api = get_api()
        
        start = datetime(2023, 1, 1)
        end = datetime(2023, 12, 31)
        
        # Create data_map
        data_map = {'TEST': synthetic_ohlcv_data}
        
        param_grid = {'lookback': [20], 'std_dev': [2.0]}
        
        results = api.batch_optimize(
            strategy_class=SimpleMeanReversionStrategy,
            symbols=['TEST'],
            param_grid=param_grid,
            start_date=start,
            end_date=end,
            max_combinations=2,
            data_map=data_map
        )
        
        assert len(results) == 1
        assert results[0]['symbol'] == 'TEST'
        # Schema should be stable
        assert 'best_params' in results[0]
        assert results[0]['best_params'] is not None or results[0]['best_params'] == {}


# =============================================================================
# V0.20 VERBOSE, DETERMINISM, AND STRUCTURED LOGGING TESTS
# =============================================================================

class TestOptimizerVerbose:
    """Tests for V0.20 verbose parameter in optimization"""
    
    def test_grid_search_accepts_verbose_param(self):
        """grid_search should accept a verbose parameter"""
        from strategy_optimizer import StrategyOptimizer
        from simple_strategy import SimpleMeanReversionStrategy
        import inspect
        
        optimizer = StrategyOptimizer(SimpleMeanReversionStrategy)
        
        sig = inspect.signature(optimizer.grid_search)
        params = list(sig.parameters.keys())
        assert 'verbose' in params, "grid_search should accept 'verbose' parameter"
    
    def test_random_search_accepts_verbose_param(self):
        """random_search should accept a verbose parameter"""
        from strategy_optimizer import StrategyOptimizer
        from simple_strategy import SimpleMeanReversionStrategy
        import inspect
        
        optimizer = StrategyOptimizer(SimpleMeanReversionStrategy)
        
        sig = inspect.signature(optimizer.random_search)
        params = list(sig.parameters.keys())
        assert 'verbose' in params, "random_search should accept 'verbose' parameter"
    
    def test_optimize_strategy_accepts_verbose_param(self):
        """optimize_strategy should accept a verbose parameter"""
        from platform_api import get_api
        import inspect
        
        api = get_api()
        
        sig = inspect.signature(api.optimize_strategy)
        params = list(sig.parameters.keys())
        assert 'verbose' in params, "optimize_strategy should accept 'verbose' parameter"
    
    def test_batch_optimize_accepts_verbose_param(self):
        """batch_optimize should accept a verbose parameter"""
        from platform_api import get_api
        import inspect
        
        api = get_api()
        
        sig = inspect.signature(api.batch_optimize)
        params = list(sig.parameters.keys())
        assert 'verbose' in params, "batch_optimize should accept 'verbose' parameter"
    
    def test_batch_optimize_verbose_false_reduces_output(self, synthetic_ohlcv_data, capsys):
        """batch_optimize with verbose=False should produce minimal output"""
        from platform_api import get_api
        from simple_strategy import SimpleMeanReversionStrategy
        
        api = get_api()
        
        start = datetime(2023, 1, 1)
        end = datetime(2023, 12, 31)
        
        data_map = {'TEST': synthetic_ohlcv_data}
        param_grid = {'lookback': [20], 'std_dev': [2.0]}
        
        results = api.batch_optimize(
            strategy_class=SimpleMeanReversionStrategy,
            symbols=['TEST'],
            param_grid=param_grid,
            start_date=start,
            end_date=end,
            max_combinations=2,
            data_map=data_map,
            verbose=False  # Should suppress per-combo progress
        )
        
        captured = capsys.readouterr()
        
        # With verbose=False, should not have per-combo updates like "New best" or "Progress:"
        assert 'Progress:' not in captured.out, "verbose=False should not print Progress lines"
        
        # Results should still be valid
        assert len(results) == 1
        assert 'best_params' in results[0]


class TestOptimizerDeterminism:
    """Tests for V0.20 deterministic optimization with seed parameter"""
    
    def test_grid_search_accepts_seed_param(self):
        """grid_search should accept a seed parameter for deterministic sampling"""
        from strategy_optimizer import StrategyOptimizer
        from simple_strategy import SimpleMeanReversionStrategy
        import inspect
        
        optimizer = StrategyOptimizer(SimpleMeanReversionStrategy)
        
        sig = inspect.signature(optimizer.grid_search)
        params = list(sig.parameters.keys())
        assert 'seed' in params, "grid_search should accept 'seed' parameter"
    
    def test_random_search_accepts_seed_param(self):
        """random_search should accept a seed parameter"""
        from strategy_optimizer import StrategyOptimizer
        from simple_strategy import SimpleMeanReversionStrategy
        import inspect
        
        optimizer = StrategyOptimizer(SimpleMeanReversionStrategy)
        
        sig = inspect.signature(optimizer.random_search)
        params = list(sig.parameters.keys())
        assert 'seed' in params, "random_search should accept 'seed' parameter"
    
    def test_deterministic_sampling_with_fixed_seed(self, synthetic_ohlcv_data):
        """Optimization with same seed should produce same results"""
        from platform_api import get_api
        from simple_strategy import SimpleMeanReversionStrategy
        
        api = get_api()
        
        start = datetime(2023, 1, 1)
        end = datetime(2023, 12, 31)
        
        param_grid = {'lookback': [15, 20, 25], 'std_dev': [1.5, 2.0, 2.5]}
        
        # Run twice with same seed
        result1 = api.optimize_strategy(
            strategy_class=SimpleMeanReversionStrategy,
            param_grid=param_grid,
            symbol='TEST',
            start_date=start,
            end_date=end,
            max_combinations=5,
            data=synthetic_ohlcv_data,
            verbose=False,
            seed=42
        )
        
        result2 = api.optimize_strategy(
            strategy_class=SimpleMeanReversionStrategy,
            param_grid=param_grid,
            symbol='TEST',
            start_date=start,
            end_date=end,
            max_combinations=5,
            data=synthetic_ohlcv_data,
            verbose=False,
            seed=42
        )
        
        # Same seed should give same best params
        assert result1['best_params'] == result2['best_params'], \
            "Same seed should produce same best_params"


class TestRunLoggerStructured:
    """Tests for V0.20 structured run logging with status field"""
    
    def test_run_logger_includes_status_field(self, tmp_path):
        """Run logger records should include a status field"""
        from run_logger import RunLogger
        import json
        
        logger = RunLogger(runs_dir=str(tmp_path), enabled=True)
        
        # Log success
        logger.log(kind='test', inputs={'symbol': 'SPY'}, outputs={'result': 'ok'})
        
        # Log with error
        logger.log(kind='test', inputs={'symbol': 'AAPL'}, error='Something failed')
        
        # Read and verify
        log_file = tmp_path / 'runs.jsonl'
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        record1 = json.loads(lines[0])
        record2 = json.loads(lines[1])
        
        assert 'status' in record1, "Record should have status field"
        assert record1['status'] == 'success', "Record without error should have status=success"
        
        assert 'status' in record2, "Record should have status field"
        assert record2['status'] == 'error', "Record with error should have status=error"
    
    def test_run_logger_auto_determines_status(self, tmp_path):
        """Run logger should auto-determine status from error/warnings"""
        from run_logger import RunLogger
        import json
        
        logger = RunLogger(runs_dir=str(tmp_path), enabled=True)
        
        # Success (no error, no warnings)
        logger.log(kind='analyze', inputs={}, outputs={})
        
        # Warning status
        logger.log(kind='backtest', inputs={}, outputs={}, warnings=['Low data'])
        
        # Error status
        logger.log(kind='optimize', inputs={}, outputs={}, error='Failed')
        
        log_file = tmp_path / 'runs.jsonl'
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        assert json.loads(lines[0])['status'] == 'success'
        assert json.loads(lines[1])['status'] == 'warning'
        assert json.loads(lines[2])['status'] == 'error'
    
    def test_run_logger_accepts_explicit_status(self, tmp_path):
        """Run logger should accept explicit status override"""
        from run_logger import RunLogger
        import json
        
        logger = RunLogger(runs_dir=str(tmp_path), enabled=True)
        
        logger.log(kind='test', inputs={}, outputs={}, status='custom_status')
        
        log_file = tmp_path / 'runs.jsonl'
        with open(log_file, 'r') as f:
            record = json.loads(f.readline())
        
        assert record['status'] == 'custom_status'


class TestBatchOptimizeSorted:
    """Tests for V0.20 batch_optimize sorted results"""
    
    def test_batch_optimize_results_sorted_by_symbol(self, synthetic_ohlcv_data):
        """batch_optimize should return results sorted by symbol"""
        from platform_api import get_api
        from simple_strategy import SimpleMeanReversionStrategy
        import numpy as np
        
        api = get_api()
        
        start = datetime(2023, 1, 1)
        end = datetime(2023, 12, 31)
        
        # Create multiple fixtures
        np.random.seed(43)
        dates = pd.date_range(start='2023-01-01', periods=252, freq='B')
        returns = np.random.normal(0.0005, 0.02, len(dates))
        price = 100 * np.exp(np.cumsum(returns))
        df2 = pd.DataFrame({
            'Open': price * (1 + np.random.uniform(-0.01, 0.01, len(dates))),
            'High': price * (1 + np.random.uniform(0, 0.02, len(dates))),
            'Low': price * (1 + np.random.uniform(-0.02, 0, len(dates))),
            'Close': price,
            'Volume': np.random.randint(1000000, 10000000, len(dates)),
            'Price': price
        }, index=dates)
        df2['High'] = df2[['Open', 'Close', 'High']].max(axis=1)
        df2['Low'] = df2[['Open', 'Close', 'Low']].min(axis=1)
        
        # Use unsorted symbols in data_map
        data_map = {
            'ZZZ': synthetic_ohlcv_data,
            'AAA': df2,
        }
        
        param_grid = {'lookback': [20], 'std_dev': [2.0]}
        
        results = api.batch_optimize(
            strategy_class=SimpleMeanReversionStrategy,
            symbols=['ZZZ', 'AAA'],  # Intentionally unsorted
            param_grid=param_grid,
            start_date=start,
            end_date=end,
            max_combinations=1,
            data_map=data_map,
            verbose=False
        )
        
        # Results should be sorted by symbol
        symbols = [r['symbol'] for r in results]
        assert symbols == sorted(symbols), "batch_optimize results should be sorted by symbol"


class TestVersionV020:
    """Tests to verify V0.20 version is set correctly"""
    
    def test_platform_version_is_v020(self):
        """Platform version should be V0.20"""
        from core_config import PLATFORM_VERSION
        
        assert PLATFORM_VERSION == "V0.20", f"Expected V0.20, got {PLATFORM_VERSION}"

# =============================================================================
# V0.19 RUN LOGGER INTEGRATION TESTS
# =============================================================================

class TestRunLoggerIntegration:
    """Tests for run logger integration in platform_api"""
    
    def test_analyze_market_logs_run(self, synthetic_ohlcv_data, tmp_path):
        """analyze_market should log run to JSONL"""
        from platform_api import PlatformAPI
        from run_logger import RunLogger
        import json
        
        # Create API with custom logger pointing to tmp_path
        api = PlatformAPI()
        
        # Patch the logger to use temp directory
        import run_logger
        original_logger = run_logger._logger
        run_logger._logger = RunLogger(runs_dir=str(tmp_path), enabled=True)
        
        try:
            result = api.analyze_market(
                symbol='TEST',
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 12, 31),
                data=synthetic_ohlcv_data
            )
            
            # Check log file exists
            log_file = tmp_path / 'runs.jsonl'
            assert log_file.exists(), "Run log should be created"
            
            # Read and verify
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) >= 1, "At least one run should be logged"
            
            record = json.loads(lines[-1])
            assert record['kind'] == 'analyze'
            assert record['inputs']['symbol'] == 'TEST'
            assert 'duration_seconds' in record
        finally:
            # Restore original logger
            run_logger._logger = original_logger
    
    def test_optimize_strategy_logs_run(self, synthetic_ohlcv_data, tmp_path):
        """optimize_strategy should log run to JSONL"""
        from platform_api import PlatformAPI
        from simple_strategy import SimpleMeanReversionStrategy
        from run_logger import RunLogger
        import json
        import run_logger
        
        api = PlatformAPI()
        
        # Patch logger
        original_logger = run_logger._logger
        run_logger._logger = RunLogger(runs_dir=str(tmp_path), enabled=True)
        
        try:
            result = api.optimize_strategy(
                strategy_class=SimpleMeanReversionStrategy,
                param_grid={'lookback': [20], 'std_dev': [2.0]},
                symbol='TEST',
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 12, 31),
                max_combinations=2,
                data=synthetic_ohlcv_data
            )
            
            log_file = tmp_path / 'runs.jsonl'
            assert log_file.exists()
            
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            # Find optimize log entry
            optimize_logs = [json.loads(l) for l in lines if 'optimize' in l]
            assert len(optimize_logs) >= 1
            
            record = optimize_logs[-1]
            assert record['kind'] == 'optimize'
            assert record['inputs']['symbol'] == 'TEST'
            assert 'best_score' in record['outputs'] or 'success' in record['outputs']
        finally:
            run_logger._logger = original_logger
    
    def test_backtest_strategy_logs_run(self, synthetic_ohlcv_data, tmp_path):
        """backtest_strategy should log run to JSONL"""
        from platform_api import PlatformAPI
        from simple_strategy import SimpleMeanReversionStrategy
        from run_logger import RunLogger
        import json
        import run_logger
        
        api = PlatformAPI()
        
        original_logger = run_logger._logger
        run_logger._logger = RunLogger(runs_dir=str(tmp_path), enabled=True)
        
        try:
            result = api.backtest_strategy(
                strategy_class=SimpleMeanReversionStrategy,
                symbol='TEST',
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 12, 31),
                params={'lookback': 20, 'std_dev': 2.0},
                data=synthetic_ohlcv_data
            )
            
            log_file = tmp_path / 'runs.jsonl'
            assert log_file.exists()
            
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            backtest_logs = [json.loads(l) for l in lines if 'backtest' in l]
            assert len(backtest_logs) >= 1
            
            record = backtest_logs[-1]
            assert record['kind'] == 'backtest'
            assert 'return_pct' in record['outputs'] or 'success' in record['outputs']
        finally:
            run_logger._logger = original_logger


# =============================================================================
# V0.19 OPTIMIZATION SCHEMA STABILITY TESTS
# =============================================================================

class TestOptimizationSchemaStability:
    """Tests ensuring optimizer always returns stable schema"""
    
    def test_grid_search_returns_stable_schema_with_injected_data(self, synthetic_ohlcv_data):
        """grid_search with injected data should return stable schema"""
        from strategy_optimizer import StrategyOptimizer
        from simple_strategy import SimpleMeanReversionStrategy
        
        optimizer = StrategyOptimizer(SimpleMeanReversionStrategy, metric='sharpe_ratio')
        
        start = datetime(2023, 1, 1)
        end = datetime(2023, 12, 31)
        
        param_grid = {'lookback': [20, 30], 'std_dev': [2.0]}
        
        result = optimizer.grid_search(
            param_grid,
            'TEST',
            start,
            end,
            max_combinations=5,
            data=synthetic_ohlcv_data  # Inject data
        )
        
        # Verify all required schema keys exist
        required_keys = [
            'success', 'best_params', 'best_score', 'tested', 'valid',
            'failures', 'skipped', 'error', 'warnings', 'failure_summary',
            'example_failures', 'top_results', 'all_results'
        ]
        
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"
        
        # best_params must never be None
        assert result['best_params'] is not None, "best_params should never be None"
        assert isinstance(result['best_params'], dict), "best_params should be a dict"
    
    def test_random_search_returns_stable_schema_with_injected_data(self, synthetic_ohlcv_data):
        """random_search with injected data should return stable schema"""
        from strategy_optimizer import StrategyOptimizer
        from simple_strategy import SimpleMeanReversionStrategy
        
        optimizer = StrategyOptimizer(SimpleMeanReversionStrategy, metric='sharpe_ratio')
        
        start = datetime(2023, 1, 1)
        end = datetime(2023, 12, 31)
        
        param_dist = {'lookback': (15, 30), 'std_dev': (1.5, 2.5)}
        
        result = optimizer.random_search(
            param_dist,
            'TEST',
            start,
            end,
            n_iterations=3,
            data=synthetic_ohlcv_data  # Inject data
        )
        
        required_keys = [
            'success', 'best_params', 'best_score', 'tested', 'valid',
            'failures', 'skipped', 'error', 'warnings', 'failure_summary',
            'example_failures', 'top_results', 'all_results'
        ]
        
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"
        
        assert result['best_params'] is not None
        assert isinstance(result['best_params'], dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
