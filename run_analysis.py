"""
Run Analysis and Comparison Utilities

Provides tools to load, summarize, and compare logged runs from runs/runs.jsonl.
Works without pandas for lightweight CLI usage.

Usage:
    from run_analysis import load_runs, summarize_runs, compare_runs
    
    # Load all optimization runs
    runs = load_runs(kind='optimize')
    
    # Get summary statistics
    summary = summarize_runs(runs)
    
    # Compare two runs
    diff = compare_runs('abc123', 'def456')
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import Counter


def load_runs(
    path: str = "runs/runs.jsonl",
    kind: Optional[str] = None,
    symbol: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Load run records from JSONL log file
    
    Args:
        path: Path to runs.jsonl file
        kind: Filter by operation kind (analyze, backtest, optimize, allocate)
        symbol: Filter by symbol (checks inputs.symbol)
        since: Only runs after this timestamp
        limit: Maximum number of runs to return
        
    Returns:
        List of run records (newest first)
    """
    log_path = Path(path)
    if not log_path.exists():
        return []
    
    runs = []
    try:
        with open(log_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    
                    # Apply filters
                    if kind and record.get('kind') != kind:
                        continue
                    
                    if symbol:
                        rec_symbol = record.get('inputs', {}).get('symbol', '')
                        if rec_symbol != symbol:
                            continue
                    
                    if since:
                        try:
                            record_time = datetime.fromisoformat(record['timestamp'])
                            if record_time < since:
                                continue
                        except (KeyError, ValueError):
                            pass
                    
                    runs.append(record)
                except json.JSONDecodeError:
                    continue
    except Exception:
        return []
    
    # Return newest first, limited
    return list(reversed(runs))[:limit]


def summarize_runs(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate summary statistics for a list of runs
    
    Args:
        runs: List of run records from load_runs
        
    Returns:
        Summary dict with:
        - total_runs: int
        - by_kind: dict[str, int]
        - by_symbol: dict[str, int]
        - error_rate: float
        - top_strategies: list (for optimize runs)
        - best_scores: dict[str, float] (symbol -> best score)
        - common_failure_categories: list
        - first_run: str (timestamp)
        - last_run: str (timestamp)
    """
    if not runs:
        return {
            'total_runs': 0,
            'by_kind': {},
            'by_symbol': {},
            'error_rate': 0.0,
            'top_strategies': [],
            'best_scores': {},
            'common_failure_categories': [],
            'first_run': None,
            'last_run': None
        }
    
    # Counters
    kind_counts = Counter()
    symbol_counts = Counter()
    failure_categories = Counter()
    errors = 0
    best_scores = {}  # symbol -> best score
    strategies = Counter()  # strategy -> count of successful runs
    
    for run in runs:
        kind = run.get('kind', 'unknown')
        kind_counts[kind] += 1
        
        # Symbol from inputs
        symbol = run.get('inputs', {}).get('symbol', 'unknown')
        symbol_counts[symbol] += 1
        
        # Track errors
        if run.get('error'):
            errors += 1
        
        # Track failure categories
        for cat, count in run.get('failure_summary', {}).items():
            failure_categories[cat] += count
        
        # Track best scores for optimization runs
        if kind == 'optimize':
            outputs = run.get('outputs', {})
            score = outputs.get('best_score')
            if score is not None and isinstance(score, (int, float)):
                if symbol not in best_scores or score > best_scores[symbol]:
                    best_scores[symbol] = score
            
            # Track strategy usage
            strategy = run.get('inputs', {}).get('strategy', 'unknown')
            if run.get('outputs', {}).get('success'):
                strategies[strategy] += 1
    
    return {
        'total_runs': len(runs),
        'by_kind': dict(kind_counts),
        'by_symbol': dict(symbol_counts.most_common(10)),  # Top 10 symbols
        'error_rate': errors / len(runs) if runs else 0.0,
        'top_strategies': strategies.most_common(5),
        'best_scores': best_scores,
        'common_failure_categories': failure_categories.most_common(5),
        'first_run': runs[-1]['timestamp'] if runs else None,
        'last_run': runs[0]['timestamp'] if runs else None
    }


def compare_runs(
    run_id_a: str,
    run_id_b: str,
    path: str = "runs/runs.jsonl"
) -> Dict[str, Any]:
    """
    Compare two runs by run_id
    
    Args:
        run_id_a: First run ID
        run_id_b: Second run ID
        path: Path to runs.jsonl
        
    Returns:
        Comparison dict with:
        - found_both: bool
        - run_a: dict (run record or None)
        - run_b: dict (run record or None)
        - diff: dict (field -> (value_a, value_b) for differing fields)
    """
    # Load all runs and find by ID
    all_runs = load_runs(path, limit=10000)
    
    run_a = None
    run_b = None
    
    for run in all_runs:
        if run.get('run_id') == run_id_a:
            run_a = run
        if run.get('run_id') == run_id_b:
            run_b = run
        if run_a and run_b:
            break
    
    if not run_a or not run_b:
        return {
            'found_both': False,
            'run_a': run_a,
            'run_b': run_b,
            'diff': {},
            'error': f"Run(s) not found: {run_id_a if not run_a else ''} {run_id_b if not run_b else ''}"
        }
    
    # Compute diff for key fields
    diff = {}
    compare_fields = ['kind', 'inputs', 'outputs', 'error', 'warnings']
    
    for field in compare_fields:
        val_a = run_a.get(field)
        val_b = run_b.get(field)
        if val_a != val_b:
            diff[field] = (val_a, val_b)
    
    # Special handling for nested outputs
    if 'outputs' not in diff:
        out_a = run_a.get('outputs', {})
        out_b = run_b.get('outputs', {})
        output_diff = {}
        all_keys = set(out_a.keys()) | set(out_b.keys())
        for k in all_keys:
            if out_a.get(k) != out_b.get(k):
                output_diff[k] = (out_a.get(k), out_b.get(k))
        if output_diff:
            diff['outputs_detail'] = output_diff
    
    return {
        'found_both': True,
        'run_a': run_a,
        'run_b': run_b,
        'diff': diff
    }


def get_run_by_id(run_id: str, path: str = "runs/runs.jsonl") -> Optional[Dict[str, Any]]:
    """Get a single run by ID"""
    runs = load_runs(path, limit=10000)
    for run in runs:
        if run.get('run_id') == run_id:
            return run
    return None


def format_run_summary(run: Dict[str, Any]) -> str:
    """Format a single run record as a readable string"""
    lines = []
    lines.append(f"Run ID: {run.get('run_id', 'N/A')}")
    lines.append(f"  Time: {run.get('timestamp', 'N/A')}")
    lines.append(f"  Kind: {run.get('kind', 'N/A')}")
    
    inputs = run.get('inputs', {})
    if inputs.get('symbol'):
        lines.append(f"  Symbol: {inputs['symbol']}")
    if inputs.get('strategy'):
        lines.append(f"  Strategy: {inputs['strategy']}")
    
    outputs = run.get('outputs', {})
    if outputs.get('best_score') is not None:
        lines.append(f"  Best Score: {outputs['best_score']:.4f}")
    if outputs.get('return_pct') is not None:
        lines.append(f"  Return: {outputs['return_pct']:.2f}%")
    
    if run.get('error'):
        lines.append(f"  Error: {run['error'][:100]}")
    
    warnings = run.get('warnings', [])
    if warnings:
        lines.append(f"  Warnings: {len(warnings)}")
    
    return '\n'.join(lines)


def print_runs_report(
    path: str = "runs/runs.jsonl",
    kind: Optional[str] = None,
    limit: int = 10
):
    """
    Print a formatted report of recent runs
    
    Args:
        path: Path to runs.jsonl
        kind: Filter by operation kind
        limit: Max runs to show
    """
    runs = load_runs(path, kind=kind, limit=limit)
    
    if not runs:
        print("No runs found.")
        return
    
    summary = summarize_runs(runs)
    
    print("=" * 60)
    print("RUNS REPORT")
    print("=" * 60)
    print(f"Total runs: {summary['total_runs']}")
    print(f"Error rate: {summary['error_rate']:.1%}")
    print(f"Date range: {summary['first_run']} to {summary['last_run']}")
    
    print("\nBy operation type:")
    for kind, count in summary['by_kind'].items():
        print(f"  {kind}: {count}")
    
    if summary['by_symbol']:
        print("\nTop symbols:")
        for symbol, count in list(summary['by_symbol'].items())[:5]:
            print(f"  {symbol}: {count} runs")
    
    if summary['best_scores']:
        print("\nBest optimization scores:")
        for symbol, score in list(summary['best_scores'].items())[:5]:
            print(f"  {symbol}: {score:.4f}")
    
    if summary['common_failure_categories']:
        print("\nCommon failure categories:")
        for cat, count in summary['common_failure_categories']:
            print(f"  {cat}: {count}")
    
    print("\n" + "-" * 60)
    print(f"Recent runs (last {min(limit, len(runs))}):")
    print("-" * 60)
    
    for run in runs[:limit]:
        print(format_run_summary(run))
        print()


if __name__ == '__main__':
    # CLI usage
    import sys
    
    if len(sys.argv) > 1:
        kind_filter = sys.argv[1] if sys.argv[1] in ['analyze', 'backtest', 'optimize', 'allocate'] else None
    else:
        kind_filter = None
    
    print_runs_report(kind=kind_filter)
