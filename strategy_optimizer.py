"""
Strategy Parameter Optimizer
Optimizes strategy parameters using grid search, random search, or Bayesian optimization
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Callable
from itertools import product
import json
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
                    max_combinations: int = 100) -> Dict[str, Any]:
        """
        Grid search over parameter space
        
        param_grid example:
        {
            'lookback': [30, 60, 90],
            'prediction_horizon': [3, 5, 7],
            'threshold': [0.5, 0.6, 0.7]
        }
        """
        print(f"\n🔍 Starting Grid Search Optimization")
        print(f"   Symbol: {symbol}")
        print(f"   Metric: {self.metric}")
        print(f"   Period: {start_date.date()} to {end_date.date()}")
        
        # Generate all combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))
        
        if len(combinations) > max_combinations:
            print(f"   ⚠️  Too many combinations ({len(combinations)}), sampling {max_combinations}")
            np.random.seed(42)
            indices = np.random.choice(len(combinations), max_combinations, replace=False)
            combinations = [combinations[i] for i in indices]
        
        print(f"   Testing {len(combinations)} parameter combinations...")
        
        results = []
        for i, values in enumerate(combinations, 1):
            params = dict(zip(param_names, values))
            
            try:
                # Run backtest with these parameters
                score, metrics = self._evaluate_params(
                    params, symbol, start_date, end_date, initial_capital
                )
                
                results.append({
                    'params': params,
                    'score': score,
                    'metrics': metrics
                })
                
                if score > self.best_score:
                    self.best_score = score
                    self.best_params = params
                    print(f"   ✓ New best: {score:.4f} with {params}")
                    
                # Progress
                if i % 10 == 0:
                    print(f"   Progress: {i}/{len(combinations)} ({i/len(combinations)*100:.1f}%)")
                    
            except Exception as e:
                print(f"   ✗ Error with {params}: {e}")
                continue
        
        self.optimization_results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        print(f"\n✅ Optimization Complete!")
        print(f"   Best Score: {self.best_score:.4f}")
        print(f"   Best Params: {self.best_params}")
        
        return {
            'best_params': self.best_params,
            'best_score': self.best_score,
            'all_results': self.optimization_results[:10]  # Top 10
        }
    
    def random_search(self, param_distributions: Dict[str, Tuple], 
                      symbol: str, start_date, end_date,
                      initial_capital: float = 10000,
                      n_iterations: int = 50) -> Dict[str, Any]:
        """
        Random search over parameter space
        
        param_distributions example:
        {
            'lookback': (30, 120),  # min, max for integer
            'prediction_horizon': (3, 10),
            'threshold': (0.4, 0.8)  # min, max for float
        }
        """
        print(f"\n🎲 Starting Random Search Optimization")
        print(f"   Symbol: {symbol}")
        print(f"   Iterations: {n_iterations}")
        
        results = []
        np.random.seed(42)
        
        for i in range(n_iterations):
            # Sample random parameters
            params = {}
            for param_name, (min_val, max_val) in param_distributions.items():
                if isinstance(min_val, int) and isinstance(max_val, int):
                    params[param_name] = np.random.randint(min_val, max_val + 1)
                else:
                    params[param_name] = np.random.uniform(min_val, max_val)
            
            try:
                score, metrics = self._evaluate_params(
                    params, symbol, start_date, end_date, initial_capital
                )
                
                results.append({
                    'params': params,
                    'score': score,
                    'metrics': metrics
                })
                
                if score > self.best_score:
                    self.best_score = score
                    self.best_params = params
                    print(f"   ✓ Iteration {i+1}: New best {score:.4f}")
                    
            except Exception as e:
                print(f"   ✗ Iteration {i+1} failed: {e}")
                continue
        
        self.optimization_results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        return {
            'best_params': self.best_params,
            'best_score': self.best_score,
            'all_results': self.optimization_results[:10]
        }
    
    def _evaluate_params(self, params: Dict, symbol: str, 
                         start_date, end_date, initial_capital: float) -> Tuple[float, Dict]:
        """Evaluate strategy with given parameters"""
        try:
            # Create strategy instance with parameters
            strategy = self.strategy_class(
                symbol=symbol,
                initial_capital=initial_capital,
                **params
            )
            
            # Run backtest - handle different return values
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
            
            return score, metrics
            
        except Exception as e:
            raise Exception(f"Evaluation failed: {e}")
    
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
