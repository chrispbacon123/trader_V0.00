#!/usr/bin/env python3
"""
Runs Report CLI Tool

Print a formatted report of logged runs from runs/runs.jsonl.
Does not require pandas.

Usage:
    python tools/runs_report.py              # All recent runs
    python tools/runs_report.py optimize     # Only optimization runs
    python tools/runs_report.py --limit 20   # Show 20 runs
    python tools/runs_report.py --compare abc123 def456  # Compare two runs
    python tools/runs_report.py --top        # Show top scores by strategy/symbol
    python tools/runs_report.py --failures   # Show common failure categories
"""

import sys
from pathlib import Path

# Ensure we can import from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_last_n_runs(runs, n=10):
    """Print a table of last N runs"""
    print("\n" + "-" * 70)
    print(f"LAST {min(n, len(runs))} RUNS")
    print("-" * 70)
    print(f"{'Timestamp':<20} {'Kind':<12} {'Symbol':<8} {'Status':<10} {'Metric':<15}")
    print("-" * 70)
    
    for run in runs[:n]:
        timestamp = run.get('timestamp', 'N/A')[:19]  # Trim microseconds
        kind = run.get('kind', 'N/A')[:11]
        symbol = run.get('inputs', {}).get('symbol', 'N/A')[:7]
        
        # Determine status
        if run.get('error'):
            status = 'ERROR'
        elif run.get('status'):
            status = run.get('status').upper()
        else:
            status = 'OK'
        
        # Get key metric based on kind
        outputs = run.get('outputs', {})
        if kind == 'optimize':
            metric = f"score={outputs.get('best_score', 'N/A')}"
            if outputs.get('best_score') is not None:
                try:
                    metric = f"score={float(outputs.get('best_score')):.4f}"
                except (TypeError, ValueError):
                    pass
        elif kind == 'backtest':
            ret = outputs.get('return_pct', outputs.get('return', 'N/A'))
            if ret != 'N/A':
                try:
                    metric = f"return={float(ret):.2f}%"
                except (TypeError, ValueError):
                    metric = f"return={ret}"
            else:
                metric = 'N/A'
        elif kind == 'analyze':
            regime = outputs.get('regime', 'N/A')
            metric = f"regime={regime}"
        else:
            metric = 'N/A'
        
        print(f"{timestamp:<20} {kind:<12} {symbol:<8} {status:<10} {metric:<15}")


def print_top_scores(runs, n=10):
    """Print top scores by strategy/symbol"""
    print("\n" + "-" * 70)
    print("TOP SCORES BY SYMBOL")
    print("-" * 70)
    
    # Collect best scores
    best_scores = {}  # symbol -> (score, strategy, run_id)
    
    for run in runs:
        if run.get('kind') != 'optimize':
            continue
        
        outputs = run.get('outputs', {})
        score = outputs.get('best_score')
        if score is None:
            continue
        
        try:
            score = float(score)
        except (TypeError, ValueError):
            continue
        
        symbol = run.get('inputs', {}).get('symbol', 'UNKNOWN')
        strategy = run.get('inputs', {}).get('strategy', 'UNKNOWN')
        run_id = run.get('run_id', 'N/A')
        
        if symbol not in best_scores or score > best_scores[symbol][0]:
            best_scores[symbol] = (score, strategy, run_id)
    
    if not best_scores:
        print("No optimization runs with valid scores found.")
        return
    
    # Sort by score descending
    sorted_scores = sorted(best_scores.items(), key=lambda x: -x[1][0])[:n]
    
    print(f"{'Symbol':<10} {'Best Score':<12} {'Strategy':<25} {'Run ID':<10}")
    print("-" * 70)
    
    for symbol, (score, strategy, run_id) in sorted_scores:
        print(f"{symbol:<10} {score:<12.4f} {strategy[:24]:<25} {run_id:<10}")


def print_failure_categories(runs, n=10):
    """Print common failure categories"""
    print("\n" + "-" * 70)
    print("FAILURE CATEGORIES")
    print("-" * 70)
    
    from collections import Counter
    
    failure_counts = Counter()
    error_examples = {}  # category -> first example
    
    for run in runs:
        summary = run.get('failure_summary', {})
        for cat, count in summary.items():
            failure_counts[cat] += count
            if cat not in error_examples:
                examples = run.get('example_failures', [])
                if examples:
                    error_examples[cat] = examples[0][:80]
    
    if not failure_counts:
        print("No failures recorded.")
        return
    
    print(f"{'Category':<25} {'Count':<8} {'Example':<40}")
    print("-" * 70)
    
    for cat, count in failure_counts.most_common(n):
        example = error_examples.get(cat, 'N/A')[:39]
        print(f"{cat[:24]:<25} {count:<8} {example:<40}")


def main():
    """Main entry point"""
    from run_analysis import load_runs, summarize_runs, compare_runs, print_runs_report
    
    args = sys.argv[1:]
    
    # Parse arguments
    kind_filter = None
    limit = 10
    compare_mode = False
    compare_ids = []
    show_top = False
    show_failures = False
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ['analyze', 'backtest', 'optimize', 'allocate', 'batch_optimize']:
            kind_filter = arg
        elif arg == '--limit' and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 1
        elif arg == '--compare' and i + 2 < len(args):
            compare_mode = True
            compare_ids = [args[i + 1], args[i + 2]]
            i += 2
        elif arg == '--top':
            show_top = True
        elif arg == '--failures':
            show_failures = True
        elif arg in ['-h', '--help']:
            print(__doc__)
            return 0
        i += 1
    
    if compare_mode:
        # Compare two runs
        result = compare_runs(compare_ids[0], compare_ids[1])
        
        if not result['found_both']:
            print(f"Error: {result.get('error', 'Run(s) not found')}")
            return 1
        
        print("=" * 60)
        print("RUN COMPARISON")
        print("=" * 60)
        
        print(f"\nRun A: {compare_ids[0]}")
        if result['run_a']:
            print(f"  Kind: {result['run_a'].get('kind')}")
            print(f"  Time: {result['run_a'].get('timestamp')}")
            print(f"  Status: {result['run_a'].get('status', 'N/A')}")
        
        print(f"\nRun B: {compare_ids[1]}")
        if result['run_b']:
            print(f"  Kind: {result['run_b'].get('kind')}")
            print(f"  Time: {result['run_b'].get('timestamp')}")
            print(f"  Status: {result['run_b'].get('status', 'N/A')}")
        
        if result['diff']:
            print("\nDifferences:")
            for field, (val_a, val_b) in result['diff'].items():
                print(f"\n  {field}:")
                print(f"    A: {val_a}")
                print(f"    B: {val_b}")
        else:
            print("\nNo differences found in key fields.")
        
        return 0
    
    # Load runs
    runs = load_runs(kind=kind_filter, limit=max(limit, 100))
    
    if not runs:
        print("No runs found.")
        return 0
    
    # Print summary
    summary = summarize_runs(runs)
    
    print("=" * 70)
    print("RUNS REPORT")
    print("=" * 70)
    print(f"Total runs: {summary['total_runs']}")
    print(f"Error rate: {summary['error_rate']:.1%}")
    if summary['first_run']:
        print(f"Date range: {summary['first_run'][:19]} to {summary['last_run'][:19]}")
    
    print("\nBy operation type:")
    for kind, count in summary['by_kind'].items():
        print(f"  {kind}: {count}")
    
    # Show requested views
    if show_top:
        print_top_scores(runs)
    
    if show_failures:
        print_failure_categories(runs)
    
    # Always show last N runs
    print_last_n_runs(runs, limit)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
