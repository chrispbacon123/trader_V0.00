"""
Run/Experiment Logger
Logs all platform operations to JSONL for tracking and debugging

Usage:
    from run_logger import log_run, get_run_history
    
    # Log an analysis run
    log_run(
        kind='analyze',
        inputs={'symbol': 'SPY', 'start': '2024-01-01'},
        outputs={'regime': 'bullish', 'sharpe': 1.2},
        warnings=['Low volatility period']
    )
    
    # Get recent runs
    runs = get_run_history(limit=10)
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from core_config import PLATFORM_VERSION


class RunLogger:
    """
    JSONL-based run/experiment logger
    
    Each run is a single JSON line with:
    - timestamp
    - run_id (UUID)
    - kind (analyze/backtest/optimize/allocate)
    - inputs (parameters)
    - outputs (key results)
    - warnings
    - failure_summary (if any)
    - platform_version
    """
    
    def __init__(self, runs_dir: str = "runs", enabled: bool = True):
        """
        Initialize run logger
        
        Args:
            runs_dir: Directory for run logs
            enabled: Whether logging is active
        """
        self.runs_dir = Path(runs_dir)
        self.enabled = enabled
        self.log_file = self.runs_dir / "runs.jsonl"
        
        if self.enabled:
            self.runs_dir.mkdir(parents=True, exist_ok=True)
    
    def log(
        self,
        kind: str,
        inputs: Dict[str, Any],
        outputs: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None,
        failure_summary: Optional[Dict[str, int]] = None,
        error: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        status: Optional[str] = None
    ) -> Optional[str]:
        """
        Log a platform run
        
        Args:
            kind: Type of operation (analyze, backtest, optimize, allocate)
            inputs: Input parameters
            outputs: Key output values (optional)
            warnings: List of warning messages
            failure_summary: Failure counts by category
            error: Error message if failed
            duration_seconds: Execution time
            status: Explicit status string (auto-determined if not provided)
            
        Returns:
            run_id if logged, None if logging disabled/failed
        """
        if not self.enabled:
            return None
        
        run_id = str(uuid.uuid4())[:8]
        
        # Auto-determine status if not provided
        if status is None:
            if error:
                status = 'error'
            elif warnings:
                status = 'warning'
            else:
                status = 'success'
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'run_id': run_id,
            'kind': kind,
            'status': status,
            'inputs': self._sanitize_for_json(inputs),
            'outputs': self._sanitize_for_json(outputs or {}),
            'warnings': warnings or [],
            'failure_summary': failure_summary or {},
            'error': error,
            'duration_seconds': duration_seconds,
            'platform_version': PLATFORM_VERSION
        }
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(record, default=str) + '\n')
            return run_id
        except Exception as e:
            # Logging failure is non-fatal - just warn
            print(f"[WARN] Run logging failed: {e}")
            return None
    
    def _sanitize_for_json(self, obj: Any) -> Any:
        """Make object JSON-serializable"""
        if obj is None:
            return None
        if isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._sanitize_for_json(v) for v in obj]
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        if hasattr(obj, '__dict__'):
            return str(obj)
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)
    
    def get_history(
        self,
        limit: int = 100,
        kind: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get run history
        
        Args:
            limit: Maximum number of runs to return
            kind: Filter by operation kind
            since: Only runs after this timestamp
            
        Returns:
            List of run records (newest first)
        """
        if not self.log_file.exists():
            return []
        
        runs = []
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        
                        # Apply filters
                        if kind and record.get('kind') != kind:
                            continue
                        if since:
                            record_time = datetime.fromisoformat(record['timestamp'])
                            if record_time < since:
                                continue
                        
                        runs.append(record)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            return []
        
        # Return newest first, limited
        return list(reversed(runs))[:limit]
    
    def summarize(self) -> Dict[str, Any]:
        """Get summary statistics of all runs"""
        runs = self.get_history(limit=10000)
        
        if not runs:
            return {
                'total_runs': 0,
                'by_kind': {},
                'error_rate': 0.0
            }
        
        by_kind = {}
        errors = 0
        
        for run in runs:
            kind = run.get('kind', 'unknown')
            by_kind[kind] = by_kind.get(kind, 0) + 1
            if run.get('error'):
                errors += 1
        
        return {
            'total_runs': len(runs),
            'by_kind': by_kind,
            'error_rate': errors / len(runs) if runs else 0.0,
            'first_run': runs[-1]['timestamp'] if runs else None,
            'last_run': runs[0]['timestamp'] if runs else None
        }
    
    def clear(self):
        """Clear all run history"""
        if self.log_file.exists():
            self.log_file.unlink()


# Global logger instance
_logger: Optional[RunLogger] = None


def get_logger(enabled: bool = True) -> RunLogger:
    """Get or create global logger instance"""
    global _logger
    if _logger is None:
        _logger = RunLogger(enabled=enabled)
    return _logger


def log_run(
    kind: str,
    inputs: Dict[str, Any],
    outputs: Optional[Dict[str, Any]] = None,
    warnings: Optional[List[str]] = None,
    failure_summary: Optional[Dict[str, int]] = None,
    error: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    status: Optional[str] = None
) -> Optional[str]:
    """Convenience function to log a run using global logger"""
    return get_logger().log(
        kind=kind,
        inputs=inputs,
        outputs=outputs,
        warnings=warnings,
        failure_summary=failure_summary,
        error=error,
        duration_seconds=duration_seconds,
        status=status
    )


def get_run_history(
    limit: int = 100,
    kind: Optional[str] = None,
    since: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """Convenience function to get run history"""
    return get_logger().get_history(limit=limit, kind=kind, since=since)
