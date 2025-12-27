# Running the Trading Platform (V0.17)

## Quick Start

### Run the Main UI
```bash
cd trader_V0.00
python advanced_trading_interface.py
```

### Run Tests

**From the inner project folder (recommended):**
```bash
cd trader_V0.00
pytest
```

**From the outer folder (also works):**
```bash
cd C:\Users\Chris
pytest
```

Both locations work thanks to the outer `pytest.ini` that points to the correct test directory.

### Run Smoke Tests (Offline, Deterministic)

The smoke runner validates the full pipeline without network calls:
```bash
cd trader_V0.00
python tools/smoke_platform.py           # Offline with fixture
python tools/smoke_platform.py --live    # Live data (requires yfinance)
```

### Check Repository Hygiene

Verify the repo follows conventions to prevent pytest/import issues:
```bash
cd trader_V0.00
python tools/check_repo_hygiene.py
```

## Key Entry Points

| Purpose | Command |
|---------|---------|
| Main Trading UI | `python advanced_trading_interface.py` |
| Run All Tests | `pytest` |
| Compile Check | `python -m compileall .` |
| Platform Smoke Test | `python tools/smoke_platform.py` |
| Repo Hygiene Check | `python tools/check_repo_hygiene.py` |

## New in V0.17

- **tools/ directory**: Smoke tests and utilities moved here
- **Cache Manager**: Optional local caching for fetched data (`cache_manager.py`)
- **Run Logger**: Experiment logging to JSONL (`run_logger.py`)
- **Batch Mode**: `platform_api.batch_analyze()` and `batch_optimize()` for multiple symbols
- **Hygiene Tests**: Automated checks to prevent test discovery issues

## Optional Dependencies

The platform works without these, but some features require them:

- **yfinance**: Required for live market data fetching
- **optuna**: Required for advanced ML strategy optimization

Install with:
```bash
pip install yfinance optuna
```

If not installed, the relevant menu options will show a friendly message asking you to install them.

## Project Structure

```
trader_V0.00/
├── advanced_trading_interface.py  # Main UI entry point
├── platform_api.py                # Canonical API surface
├── core_config.py                 # Version and configuration
├── cache_manager.py               # Optional data caching
├── run_logger.py                  # Experiment/run logging
├── conftest.py                    # Pytest collection hook
├── tests/                         # Pytest test suite
│   ├── test_integration.py        # Main integration tests
│   └── data/                      # Test fixtures
├── tools/                         # Smoke tests and utilities
│   ├── smoke_platform.py          # Full pipeline validation
│   └── check_repo_hygiene.py      # Repo convention checker
├── scripts/                       # Legacy manual scripts
├── strategy_exports/              # User-exported strategies
│   └── export_*.py                # Always prefixed with 'export_'
└── ...
```

## Troubleshooting

### Pytest collects wrong files
Make sure you're running pytest from either:
1. `trader_V0.00/` folder (uses inner pytest.ini)
2. Parent folder with the outer pytest.ini

Both pytest.ini files exclude `scripts/`, `tools/`, `strategy_exports/`, and other non-test directories.

### Strategy exports named test_*.py
Fixed in V0.16. All new exports use `export_` prefix to avoid pytest collection.

### Strategy save/load errors
Fixed in V0.15. If you have corrupted config files, delete `strategy_configs.json` and restart.

### Import errors for yfinance/optuna
These are optional. The platform will work for offline analysis and backtesting without them.
