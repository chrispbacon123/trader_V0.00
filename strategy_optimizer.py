"""
Strategy Parameter Optimizer
Optimizes strategy parameters using grid search, random search, or Bayesian optimization
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Callable
from itertools import product as iter_product
import json
import math
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')


class StrategyOptimizer:
    """Optimize strategy parameters"""
    
    def __init__(self, strategy_class, metric='sharpe_ratio'):
        self.strategy_class = strategy_class
        self.metric = metric  # sharpe_ratio, total_return, win_rate, profit_factor
        self.best_params = None
        self.best_score = float('-inf')
        self.optimization_results = []
        
    def grid_search(self, param_grid: Dict[str, List], 
                    symbol: str, start_date, end_date, 
                    initial_capital: float = 10000,
                    max_combinations: int = 100,
                    data: pd.DataFrame = None,
                    verbose: bool = True,
                    seed: int = 42) -> Dict[str, Any]:
        """
        Grid search over parameter space
        
        Fetches data ONCE and reuses for all combinations (unless data is provided).
        
        Args:
            param_grid: Dict mapping param names to lists of values
            symbol: Ticker symbol
            start_date: Start date
            end_date: End date
            initial_capital: Initial capital for backtests
            max_combinations: Maximum combinations to test
            data: Optional pre-fetched normalized DataFrame. If provided,
                  skips data fetch entirely (for df-in optimization).
            verbose: Whether to print progress updates. Default True for
                     interactive use, set False for batch operations.
            seed: Random seed for deterministic sampling. Default 42.
        
        Returns:
            Consistent schema dict with:
            - success: bool
            - best_params: dict (never None, {} if no solution)
            - best_score: float | None
            - tested: int (total combinations tested)
            - valid: int (successful evaluations)
            - failures: int (failed evaluations)
            - skipped: int (skipped combinations)
            - error: str | None
            - warnings: list[str]
            - failure_summary: dict[str, int] (counts by category)
            - example_failures: list[str] (first ~10)
            - top_results: list (up to 10 best results)
            - all_results: list (for backwards compat)
        """
        if verbose:
            print(f"\nStarting Grid Search Optimization")
            print(f"   Symbol: {symbol}")
            print(f"   Metric: {self.metric}")
            print(f"   Period: {start_date.date()} to {end_date.date()}")
        
        # Initialize tracking
        tested = 0
        valid = 0
        failures = 0
        skipped = 0
        failure_reasons = []
        failure_categories = {}  # Track by category
        warnings_list = []
        
        # USE PROVIDED DATA or FETCH ONCE for all combinations
        df = data
        if df is not None:
            if verbose:
                print(f"   Using provided data ({len(df)} rows)")
        else:
            try:
                from data_manager import DataManager
                from data_normalization import DataNormalizer, DataContractError
                
                if verbose:
                    print(f"   Fetching and normalizing data...")
                data_manager = DataManager()
                raw_df = data_manager.fetch_data(
                    symbol,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
                
                if raw_df is None or len(raw_df) == 0:
                    return {
                        'success': False,
                        'best_params': {},
                        'best_score': None,
                        'tested': 0,
                        'valid': 0,
                        'failures': 0,
                        'skipped': 0,
                        'error': f"No data available for {symbol}",
                        'warnings': [],
                        'failure_summary': {'data_fetch': 1},
                        'example_failures': [f"Failed to fetch data for {symbol}"],
                        'top_results': [],
                        'all_results': []
                    }
                
                normalizer = DataNormalizer()
                df, metadata = normalizer.normalize_market_data(
                    raw_df,
                    symbol=symbol,
                    require_ohlc=False
                )
                
                if verbose:
                    print(f"   OK Loaded {len(df)} rows of normalized data")
                
                # Warmup-aware check: estimate minimum rows needed
                min_required_rows = self._estimate_min_rows(self.strategy_class, param_grid)
                if min_required_rows and len(df) < min_required_rows:
                    msg = f"Insufficient data: {len(df)} rows available, ~{min_required_rows} needed for indicators/warmup"
                    warnings_list.append(msg)
                    if verbose:
                        print(f"   [WARN]  {msg}")
                    # Continue anyway but warn user
            
            except DataContractError as e:
                return {
                    'success': False,
                    'best_params': {},
                    'best_score': None,
                    'tested': 0,
                    'valid': 0,
                    'failures': 0,
                    'skipped': 0,
                    'error': f"Data contract error: {str(e)}",
                    'warnings': [],
                    'failure_summary': {'data_contract': 1},
                    'example_failures': [str(e)],
                    'top_results': [],
                    'all_results': []
                }
            except Exception as e:
                return {
                    'success': False,
                    'best_params': {},
                    'best_score': None,
                    'tested': 0,
                    'valid': 0,
                    'failures': 0,
                    'skipped': 0,
                    'error': f"Data fetch error: {type(e).__name__}: {str(e)}",
                    'warnings': [],
                    'failure_summary': {'data_fetch_exception': 1},
                    'example_failures': [f"{type(e).__name__}: {str(e)}"],
                    'top_results': [],
                    'all_results': []
                }
        
        # Generate combinations - MEMORY SAFE for large grids
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        
        # Compute total without materializing
        total_combinations = math.prod(len(v) for v in param_values)
        
        if total_combinations <= max_combinations:
            # Small grid: iterate all combinations directly from generator
            combinations_iter = iter_product(*param_values)
            num_to_test = total_combinations
        else:
            # Large grid: sample deterministically without materializing all
            msg = f"Too many combinations ({total_combinations:,}), sampling {max_combinations}"
            if verbose:
                print(f"   [WARN]  {msg}")
            warnings_list.append(msg)
            
            # Use reservoir sampling or indexed sampling
            np.random.seed(seed)
            sampled_indices = set(np.random.choice(total_combinations, min(max_combinations, total_combinations), replace=False))
            
            def sampled_combinations():
                """Yield only the sampled combinations without materializing all"""
                for idx, values in enumerate(iter_product(*param_values)):
                    if idx in sampled_indices:
                        yield values
            
            combinations_iter = sampled_combinations()
            num_to_test = len(sampled_indices)
        
        if verbose:
            print(f"   Testing {num_to_test} parameter combinations...")
        
        results = []
        for i, values in enumerate(combinations_iter, 1):
            params = dict(zip(param_names, values))
            tested += 1
            
            try:
                # Run backtest with these parameters (passing pre-fetched data)
                score, metrics, category = self._evaluate_params(
                    params, symbol, start_date, end_date, initial_capital, df
                )
                
                # Check for valid score
                if score is None or not np.isfinite(score):
                    failures += 1
                    cat = category or 'invalid_score'
                    failure_categories[cat] = failure_categories.get(cat, 0) + 1
                    reason = f"{params}: Invalid score ({score})"
                    if len(failure_reasons) < 10:
                        failure_reasons.append(reason)
                    continue
                
                valid += 1
                results.append({
                    'params': params,
                    'score': score,
                    'metrics': metrics
                })
                
                if score > self.best_score:
                    self.best_score = score
                    self.best_params = params
                    if verbose:
                        print(f"   OK New best: {score:.4f} with {params}")
                    
                # Progress
                if verbose and i % 10 == 0:
                    print(f"   Progress: {i}/{num_to_test} ({i/num_to_test*100:.1f}%)")
                    
            except Exception as e:
                failures += 1
                # Parse category from exception message if present
                error_str = str(e)
                cat = 'strategy_exception'
                for known_cat in ['data_contract', 'insufficient_history', 'invalid_score']:
                    if error_str.startswith(f"{known_cat}:"):
                        cat = known_cat
                        break
                failure_categories[cat] = failure_categories.get(cat, 0) + 1
                reason = f"{params}: {type(e).__name__}: {str(e)[:100]}"
                if len(failure_reasons) < 10:
                    failure_reasons.append(reason)
                if verbose:
                    print(f"   X Error with {params}: {e}")
                continue
        
        # Sort results
        self.optimization_results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        # Determine success
        success = valid > 0 and self.best_params is not None
        
        # Build consistent result schema
        result_dict = {
            'success': success,
            'best_params': self.best_params if self.best_params is not None else {},
            'best_score': self.best_score if success else None,
            'tested': tested,
            'valid': valid,
            'failures': failures,
            'skipped': skipped,
            'error': None,
            'warnings': warnings_list,
            'failure_summary': failure_categories,
            'example_failures': failure_reasons,
            'top_results': self.optimization_results[:10],
            'all_results': self.optimization_results[:10]  # For backwards compat
        }
        
        # Set error message if no valid results
        if not success:
            if valid == 0:
                result_dict['error'] = (
                    f"No valid parameter combinations produced a valid backtest/score. "
                    f"Tested {tested} combinations, all failed. "
                    f"See failure_summary for breakdown."
                )
            else:
                result_dict['error'] = f"Optimization found {valid} valid results but best_params is missing."
        
        # Print summary
        if verbose:
            print(f"\n{'[OK]' if success else '[FAIL]'} Optimization {'Complete' if success else 'Failed'}!")
            print(f"   Tested: {tested} | Valid: {valid} | Failed: {failures} | Skipped: {skipped}")
            if success:
                print(f"   Best Score: {self.best_score:.4f}")
                print(f"   Best Params: {self.best_params}")
            else:
                print(f"   Error: {result_dict['error']}")
                if failure_categories:
                    print(f"   Failure categories:")
                    for cat, count in sorted(failure_categories.items(), key=lambda x: -x[1])[:3]:
                        print(f"     {cat}: {count}")
                if failure_reasons:
                    print(f"   Example failures (first {min(len(failure_reasons), 3)}):")
                    for reason in failure_reasons[:3]:
                        print(f"     - {reason}")
        
        return result_dict
    
    def random_search(self, param_distributions: Dict[str, Tuple], 
                      symbol: str, start_date, end_date,
                      initial_capital: float = 10000,
                      n_iterations: int = 50,
                      data: pd.DataFrame = None,
                      verbose: bool = True,
                      seed: int = 42) -> Dict[str, Any]:
        """
        Random search over parameter space
        
        Fetches data ONCE and reuses for all iterations (unless data is provided).
        
        Args:
            param_distributions: Dict mapping param names to (min, max) tuples
            symbol: Ticker symbol
            start_date: Start date
            end_date: End date
            initial_capital: Initial capital for backtests
            n_iterations: Number of random samples to try
            data: Optional pre-fetched normalized DataFrame. If provided,
                  skips data fetch entirely (for df-in optimization).
            verbose: Whether to print progress updates. Default True for
                     interactive use, set False for batch operations.
            seed: Random seed for deterministic sampling. Default 42.
        
        param_distributions example:
        {
            'lookback': (30, 120),  # min, max for integer
            'prediction_horizon': (3, 10),
            'threshold': (0.4, 0.8)  # min, max for float
        }
        
        Returns:
            Consistent schema dict (same as grid_search)
        """
        if verbose:
            print(f"\n🎲 Starting Random Search Optimization")
            print(f"   Symbol: {symbol}")
            print(f"   Iterations: {n_iterations}")
        
        # Initialize tracking (same as grid_search)
        tested = 0
        valid = 0
        failures = 0
        skipped = 0
        failure_reasons = []
        failure_categories = {}
        warnings_list = []
        
        # USE PROVIDED DATA or FETCH ONCE for all iterations
        df = data
        if df is not None:
            if verbose:
                print(f"   Using provided data ({len(df)} rows)")
        else:
            try:
                from data_manager import DataManager
                from data_normalization import DataNormalizer, DataContractError
                
                if verbose:
                    print(f"   Fetching and normalizing data...")
                data_manager = DataManager()
                raw_df = data_manager.fetch_data(
                    symbol,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
                
                if raw_df is None or len(raw_df) == 0:
                    return {
                        'success': False,
                        'best_params': {},
                        'best_score': None,
                        'tested': 0,
                        'valid': 0,
                        'failures': 0,
                        'skipped': 0,
                        'error': f"No data available for {symbol}",
                        'warnings': [],
                        'failure_summary': {'data_fetch': 1},
                        'example_failures': [f"Failed to fetch data for {symbol}"],
                        'top_results': [],
                        'all_results': []
                    }
                
                normalizer = DataNormalizer()
                df, metadata = normalizer.normalize_market_data(
                    raw_df,
                    symbol=symbol,
                    require_ohlc=False
                )
                
                if verbose:
                    print(f"   OK Loaded {len(df)} rows of normalized data")
                
            except Exception as e:
                return {
                    'success': False,
                    'best_params': {},
                    'best_score': None,
                    'tested': 0,
                    'valid': 0,
                    'failures': 0,
                    'skipped': 0,
                    'error': f"Data fetch error: {type(e).__name__}: {str(e)}",
                    'warnings': [],
                    'failure_summary': {'data_fetch_exception': 1},
                    'example_failures': [f"{type(e).__name__}: {str(e)}"],
                    'top_results': [],
                    'all_results': []
                }
        
        results = []
        np.random.seed(seed)
        
        for i in range(n_iterations):
            # Sample random parameters
            params = {}
            for param_name, (min_val, max_val) in param_distributions.items():
                if isinstance(min_val, int) and isinstance(max_val, int):
                    params[param_name] = np.random.randint(min_val, max_val + 1)
                else:
                    params[param_name] = np.random.uniform(min_val, max_val)
            
            tested += 1
            
            try:
                # Pass pre-fetched data to avoid per-iteration downloads
                score, metrics, category = self._evaluate_params(
                    params, symbol, start_date, end_date, initial_capital, df
                )
                
                # Check for valid score
                if score is None or not np.isfinite(score):
                    failures += 1
                    cat = category or 'invalid_score'
                    failure_categories[cat] = failure_categories.get(cat, 0) + 1
                    reason = f"{params}: Invalid score ({score})"
                    if len(failure_reasons) < 10:
                        failure_reasons.append(reason)
                    continue
                
                valid += 1
                results.append({
                    'params': params,
                    'score': score,
                    'metrics': metrics
                })
                
                if score > self.best_score:
                    self.best_score = score
                    self.best_params = params
                    if verbose:
                        print(f"   OK Iteration {i+1}: New best {score:.4f}")
                    
            except Exception as e:
                failures += 1
                # Parse category from exception message if present
                error_str = str(e)
                cat = 'strategy_exception'
                for known_cat in ['data_contract', 'insufficient_history', 'invalid_score']:
                    if error_str.startswith(f"{known_cat}:"):
                        cat = known_cat
                        break
                failure_categories[cat] = failure_categories.get(cat, 0) + 1
                reason = f"{params}: {type(e).__name__}: {str(e)[:100]}"
                if len(failure_reasons) < 10:
                    failure_reasons.append(reason)
                if verbose:
                    print(f"   X Iteration {i+1} failed: {e}")
                continue
        
        self.optimization_results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        # Determine success
        success = valid > 0 and self.best_params is not None
        
        # Build consistent result schema (same as grid_search)
        result_dict = {
            'success': success,
            'best_params': self.best_params if self.best_params is not None else {},
            'best_score': self.best_score if success else None,
            'tested': tested,
            'valid': valid,
            'failures': failures,
            'skipped': skipped,
            'error': None,
            'warnings': warnings_list,
            'failure_summary': failure_categories,
            'example_failures': failure_reasons,
            'top_results': self.optimization_results[:10],
            'all_results': self.optimization_results[:10]
        }
        
        # Set error message if no valid results
        if not success:
            result_dict['error'] = (
                f"No valid parameter combinations produced a valid backtest/score. "
                f"Tested {tested} iterations, all failed. "
                f"See failure_summary for breakdown."
            )
        
        # Print summary
        if verbose:
            print(f"\n{'[OK]' if success else '[FAIL]'} Random Search {'Complete' if success else 'Failed'}!")
            print(f"   Tested: {tested} | Valid: {valid} | Failed: {failures}")
            if success:
                print(f"   Best Score: {self.best_score:.4f}")
                print(f"   Best Params: {self.best_params}")
        
        return result_dict
    
    def _evaluate_params(self, params: Dict, symbol: str, 
                         start_date, end_date, initial_capital: float, 
                         data=None) -> Tuple[float, Dict, str]:
        """
        Evaluate strategy with given parameters
        
        Args:
            params: Strategy parameters
            symbol: Symbol to test
            start_date: Start date
            end_date: End date  
            initial_capital: Initial capital
            data: Pre-fetched normalized DataFrame (optional)
            
        Returns:
            (score, metrics, failure_category)
        """
        try:
            # Create strategy instance with parameters
            strategy = self.strategy_class(
                symbol=symbol,
                initial_capital=initial_capital,
                **params
            )
            
            # Run backtest - pass data if available
            if data is not None:
                backtest_results = strategy.backtest(start_date, end_date, data=data)
            else:
                backtest_results = strategy.backtest(start_date, end_date)
            
            # Different strategies return different tuples
            if len(backtest_results) == 3:
                # Simple strategy: data, trades, final_value
                df, trades, final_value = backtest_results
                equity_curve = []
            elif len(backtest_results) == 4:
                # ML/Optimized: df, trades, final_value, equity_curve
                df, trades, final_value, equity_curve = backtest_results
            else:
                raise ValueError(f"Unexpected backtest return format: {len(backtest_results)} values")
            
            # Calculate metrics
            total_return = ((final_value - initial_capital) / initial_capital) * 100
            
            # EARLY PRUNING: Check for pathological results
            # Too few trades suggests strategy didn't trigger properly
            min_trades_threshold = 2  # At least one round-trip
            if len(trades) < min_trades_threshold:
                # Return low score but don't fail - strategy may be valid but conservative
                return float('-inf'), {
                    'total_return': total_return,
                    'sharpe_ratio': 0,
                    'win_rate': 0,
                    'num_trades': len(trades),
                    'pruned_reason': 'too_few_trades'
                }, 'too_few_trades'
            
            if len(trades) > 0:
                # Handle different trade formats
                if isinstance(trades[0], dict):
                    # ML strategy format (list of dicts)
                    wins = sum(1 for t in trades if t.get('profit', 0) > 0)
                    win_rate = wins / len(trades)
                    
                    profits = [t['profit'] for t in trades if t.get('profit', 0) > 0]
                    losses = [abs(t['profit']) for t in trades if t.get('profit', 0) < 0]
                else:
                    # Simple strategy format (list of tuples)
                    # Trades come in pairs: buy, sell
                    wins = 0
                    profits = []
                    losses = []
                    for i in range(0, len(trades)-1, 2):
                        if i+1 < len(trades):
                            buy_price = trades[i][2]
                            sell_price = trades[i+1][2]
                            profit = sell_price - buy_price
                            if profit > 0:
                                wins += 1
                                profits.append(profit)
                            else:
                                losses.append(abs(profit))
                    win_rate = wins / (len(trades)//2) if len(trades) > 0 else 0
                
                avg_win = np.mean(profits) if profits else 0
                avg_loss = np.mean(losses) if losses else 1
                profit_factor = (sum(profits) / sum(losses)) if losses and sum(losses) > 0 else 0
            else:
                win_rate = 0
                profit_factor = 0
                avg_win = 0
                avg_loss = 0
            
            # Calculate Sharpe ratio
            if equity_curve and len(equity_curve) > 1:
                # Handle both list of dicts and list of values
                if isinstance(equity_curve, list) and len(equity_curve) > 0:
                    if isinstance(equity_curve[0], dict):
                        values = [e['Value'] for e in equity_curve]
                    else:
                        values = equity_curve
                    
                    equity_series = pd.Series(values)
                    returns = equity_series.pct_change().dropna()
                    
                    if len(returns) > 0 and returns.std() > 0:
                        sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
                    else:
                        sharpe_ratio = 0
                    
                    # Calculate max drawdown
                    rolling_max = equity_series.expanding().max()
                    drawdowns = (equity_series - rolling_max) / rolling_max
                    max_drawdown = abs(drawdowns.min()) * 100 if len(drawdowns) > 0 else 0
                else:
                    sharpe_ratio = 0
                    max_drawdown = 0
            else:
                sharpe_ratio = 0
                max_drawdown = 0
            
            metrics = {
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'max_drawdown': max_drawdown,
                'num_trades': len(trades),
                'avg_win': avg_win,
                'avg_loss': avg_loss
            }
            
            # Select score based on metric
            score = metrics.get(self.metric, 0)
            
            return score, metrics, None  # No failure category
            
        except ValueError as e:
            error_msg = str(e).lower()
            if 'insufficient' in error_msg or 'not enough' in error_msg:
                category = 'insufficient_history'
            elif 'no data' in error_msg:
                category = 'data_contract'
            else:
                category = 'strategy_exception'
            raise Exception(f"{category}: {e}")
        except Exception as e:
            category = 'strategy_exception'
            raise Exception(f"{category}: {e}")
    
    def _estimate_min_rows(self, strategy_class, param_grid: Dict) -> int:
        """
        Estimate minimum rows needed based on strategy and parameters
        
        Returns:
            Estimated minimum rows, or None if can't estimate
        """
        try:
            # Get max lookback from param_grid
            max_lookback = 0
            if 'lookback' in param_grid:
                max_lookback = max(param_grid['lookback'])
            
            # Strategy-specific minimums (conservative estimates)
            strategy_name = strategy_class.__name__
            
            if 'ML' in strategy_name or 'Optimized' in strategy_name:
                # ML strategies need more data for training
                return max(max_lookback * 2, 100)
            elif 'ShortTerm' in strategy_name:
                # Short-term needs less
                return max(max_lookback * 1.5, 30)
            else:
                # Default conservative estimate
                return max(max_lookback * 1.5, 50)
        except:
            # If estimation fails, return None (skip check)
            return None
    
    def save_results(self, filename: str = None):
        """Save optimization results"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'optimization_results_{timestamp}.json'
        
        data = {
            'best_params': self.best_params,
            'best_score': self.best_score,
            'metric': self.metric,
            'results': self.optimization_results,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to {filename}")
        
    def plot_optimization_surface(self, param1: str, param2: str):
        """Plot 2D optimization surface (requires matplotlib)"""
        try:
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            
            # Extract data for 2 parameters
            x = [r['params'][param1] for r in self.optimization_results if param1 in r['params']]
            y = [r['params'][param2] for r in self.optimization_results if param2 in r['params']]
            z = [r['score'] for r in self.optimization_results if param1 in r['params'] and param2 in r['params']]
            
            if len(x) < 3:
                print("Not enough data points for surface plot")
                return
            
            fig = plt.figure(figsize=(12, 8))
            ax = fig.add_subplot(111, projection='3d')
            
            scatter = ax.scatter(x, y, z, c=z, cmap='viridis', s=50)
            ax.set_xlabel(param1)
            ax.set_ylabel(param2)
            ax.set_zlabel(self.metric)
            ax.set_title(f'Optimization Surface: {param1} vs {param2}')
            
            plt.colorbar(scatter, label=self.metric)
            plt.tight_layout()
            
            filename = f'optimization_surface_{param1}_{param2}.png'
            plt.savefig(filename, dpi=150)
            print(f"📊 Surface plot saved to {filename}")
            
        except ImportError:
            print("matplotlib not available for plotting")
        except Exception as e:
            print(f"Error creating plot: {e}")
