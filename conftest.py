"""
Pytest configuration for the trading platform.

This conftest.py ensures proper test discovery and prevents
pytest from collecting files in non-test directories.
"""

# Directories to never recurse into
def pytest_ignore_collect(collection_path, config):
    """Ignore directories that shouldn't be collected as tests."""
    ignore_dirs = {
        'strategy_exports',
        'scripts',
        'custom_strategies',
        'live_strategies',
        'data_cache',
        'runs',
        '.cache',
        'archive',
    }
    
    # Check if path is in an ignored directory
    parts = collection_path.parts
    for ignore_dir in ignore_dirs:
        if ignore_dir in parts:
            return True
    
    return None
