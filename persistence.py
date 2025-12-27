"""
Persistence utilities for history/record normalization
Prevents KeyError crashes from schema drift in saved data
"""

import json
from typing import Dict, List
from datetime import datetime
from pathlib import Path

from core_config import PLATFORM_VERSION


def normalize_run_record(record: dict) -> dict:
    """
    Normalize a run record to ensure required keys exist
    
    Maps older keys and provides defaults for missing data
    
    Required keys:
    - timestamp: ISO timestamp of run
    - symbol: Stock symbol
    - strategy: Strategy name
    - return_pct: Return percentage
    
    Args:
        record: Raw record dict (may have missing/old keys)
    
    Returns:
        Normalized record with all required keys
    """
    normalized = {}
    
    # Timestamp
    normalized['timestamp'] = record.get('timestamp') or record.get('date') or datetime.now().isoformat()
    
    # Symbol
    normalized['symbol'] = record.get('symbol') or record.get('ticker') or 'UNKNOWN'
    
    # Strategy
    normalized['strategy'] = (
        record.get('strategy') or
        record.get('strategy_name') or
        record.get('type') or
        'Unknown Strategy'
    )
    
    # Return percentage
    normalized['return_pct'] = (
        record.get('return_pct') or
        record.get('total_return') or
        record.get('return') or
        0.0
    )
    
    # Optional but common fields
    normalized['initial_capital'] = record.get('initial_capital', 100000)
    normalized['final_value'] = record.get('final_value') or record.get('final_portfolio_value')
    normalized['num_trades'] = record.get('num_trades') or record.get('trades', 0)
    normalized['sharpe_ratio'] = record.get('sharpe_ratio')
    normalized['max_drawdown'] = record.get('max_drawdown') or record.get('max_dd')
    normalized['win_rate'] = record.get('win_rate')
    
    # Schema version for future migrations
    normalized['_schema_version'] = record.get('_schema_version', 1)
    normalized['_platform_version'] = record.get('_platform_version', PLATFORM_VERSION)
    
    # Preserve any extra fields
    for key, value in record.items():
        if key not in normalized:
            normalized[key] = value
    
    return normalized


def migrate_record(record: dict, target_version: int = 2) -> dict:
    """
    Migrate record to latest schema version
    
    Args:
        record: Record to migrate
        target_version: Target schema version
    
    Returns:
        Migrated record
    """
    current_version = record.get('_schema_version', 1)
    
    if current_version >= target_version:
        return record
    
    # Migration from v1 to v2
    if current_version == 1 and target_version >= 2:
        # Rename old keys
        if 'ticker' in record and 'symbol' not in record:
            record['symbol'] = record.pop('ticker')
        if 'total_return' in record and 'return_pct' not in record:
            record['return_pct'] = record.pop('total_return')
        if 'date' in record and 'timestamp' not in record:
            record['timestamp'] = record.pop('date')
        
        record['_schema_version'] = 2
    
    return record


def load_history(path: str, migrate: bool = True) -> List[dict]:
    """
    Load history file and normalize all records
    
    Args:
        path: Path to history JSON file
        migrate: If True, migrate records to latest schema and save back
    
    Returns:
        List of normalized records
    """
    path_obj = Path(path)
    
    if not path_obj.exists():
        return []
    
    try:
        with open(path_obj, 'r') as f:
            raw_records = json.load(f)
        
        # Handle both list and dict formats
        if isinstance(raw_records, dict):
            # Old format: dict of lists
            all_records = []
            for strategy_records in raw_records.values():
                if isinstance(strategy_records, list):
                    all_records.extend(strategy_records)
            raw_records = all_records
        
        # Normalize and optionally migrate all records
        normalized = []
        needs_save = False
        
        for rec in raw_records:
            # Check if migration needed
            old_version = rec.get('_schema_version', 1)
            
            # Migrate to latest schema
            migrated = migrate_record(rec, target_version=2)
            normalized_rec = normalize_run_record(migrated)
            
            # Track if any records were migrated
            if old_version < 2:
                needs_save = True
            
            normalized.append(normalized_rec)
        
        # Save back if migration occurred
        if migrate and needs_save and normalized:
            try:
                with open(path_obj, 'w') as f:
                    json.dump(normalized, f, indent=2)
            except Exception:
                pass  # Don't fail on write-back errors
        
        return normalized
        
    except json.JSONDecodeError as e:
        print(f"Warning: Could not parse history file {path}: {e}")
        return []
    except Exception as e:
        print(f"Warning: Error loading history from {path}: {e}")
        return []


def append_history(path: str, record: dict) -> bool:
    """
    Append a normalized record to history file
    
    Args:
        path: Path to history JSON file
        record: Record to append (will be normalized)
    
    Returns:
        True if successful, False otherwise
    """
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load existing history
        history = load_history(path)
        
        # Normalize new record
        normalized = normalize_run_record(record)
        
        # Append
        history.append(normalized)
        
        # Save
        with open(path_obj, 'w') as f:
            json.dump(history, f, indent=2)
        
        return True
        
    except Exception as e:
        print(f"Error appending to history {path}: {e}")
        return False


def safe_get(record: dict, key: str, default=None):
    """
    Safely get value from record with default
    
    Use this in UI code instead of direct access
    
    Example:
        return_pct = safe_get(record, 'return_pct', 0.0)
    """
    return record.get(key, default)


def format_history_summary(records: List[dict]) -> str:
    """
    Format history records into a readable summary
    
    Args:
        records: List of normalized records
    
    Returns:
        Formatted string summary
    """
    if not records:
        return "No history records found"
    
    lines = []
    lines.append(f"History Summary ({len(records)} records)")
    lines.append("=" * 80)
    
    # Group by strategy
    by_strategy = {}
    for rec in records:
        strategy = rec.get('strategy', 'Unknown')
        if strategy not in by_strategy:
            by_strategy[strategy] = []
        by_strategy[strategy].append(rec)
    
    for strategy, strat_records in by_strategy.items():
        lines.append(f"\n{strategy} ({len(strat_records)} runs):")
        
        returns = [r.get('return_pct', 0) for r in strat_records]
        avg_return = sum(returns) / len(returns) if returns else 0
        
        lines.append(f"  Average Return: {avg_return:.2f}%")
        lines.append(f"  Best Return: {max(returns):.2f}%")
        lines.append(f"  Worst Return: {min(returns):.2f}%")
        
        # Recent runs
        recent = sorted(strat_records, key=lambda x: x.get('timestamp', ''), reverse=True)[:3]
        lines.append(f"  Recent Runs:")
        for r in recent:
            symbol = r.get('symbol', '?')
            ret = r.get('return_pct', 0)
            timestamp = r.get('timestamp', '')[:10]
            lines.append(f"    {timestamp} {symbol}: {ret:.2f}%")
    
    return "\n".join(lines)
