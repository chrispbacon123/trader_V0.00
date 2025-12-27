"""
Unified Backtest Engine
Provides consistent interface for all trading strategies
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import warnings

warnings.filterwarnings('ignore')


@dataclass
class BacktestResult:
    """Standardized backtest result"""
    symbol: str
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_value: float
    total_return: float
    trades: List[Dict]
    equity_curve: pd.Series
    data: pd.DataFrame
    metrics: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'symbol': self.symbol,
            'strategy': self.strategy_name,
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'initial_capital': self.initial_capital,
            'final_value': self.final_value,
            'total_return': self.total_return,
            'trades_count': len(self.trades),
            'metrics': self.metrics
        }


class UnifiedBacktestEngine:
    """Unified engine for running backtests across different strategies"""
    
    def __init__(self):
        self.results_cache = {}
        
    def run_backtest(self, 
                     strategy: Any,
                     symbol: str,
                     start_date: datetime,
                     end_date: datetime,
                     initial_capital: float = 100000,
                     **kwargs) -> BacktestResult:
        """
        Run backtest with any strategy and return standardized results
        
        Args:
            strategy: Strategy instance (must have backtest method)
            symbol: Trading symbol
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Starting capital
            **kwargs: Additional strategy-specific parameters
            
        Returns:
            BacktestResult: Standardized backtest results
        """
        
        # Ensure strategy has proper initial capital
        if hasattr(strategy, 'cash'):
            strategy.cash = initial_capital
        if hasattr(strategy, 'initial_cash'):
            strategy.initial_cash = initial_capital
            
        # Run the backtest
        try:
            result = strategy.backtest(start_date, end_date, **kwargs)
            
            # Handle different return formats
            if isinstance(result, tuple):
                if len(result) == 4:
                    # Format: (data, trades, final_value, equity)
                    data, trades, final_value, equity = result
                elif len(result) == 3:
                    # Format: (data, trades, final_value)
                    data, trades, final_value = result
                    equity = self._create_equity_curve(trades, initial_capital)
                elif len(result) == 2:
                    # Format: (trades, final_value)
                    trades, final_value = result
                    data = pd.DataFrame()
                    equity = self._create_equity_curve(trades, initial_capital)
                else:
                    raise ValueError(f"Unexpected backtest return format: {len(result)} values")
            else:
                raise ValueError(f"Backtest must return tuple, got {type(result)}")
            
            # Normalize equity to Series if it's a list of dicts or list of values
            if isinstance(equity, list):
                if len(equity) > 0:
                    if isinstance(equity[0], dict):
                        # List of {'Date': ..., 'Value': ...} dicts
                        equity = pd.Series(
                            [e.get('Value', e.get('value', initial_capital)) for e in equity],
                            index=[e.get('Date', e.get('date')) for e in equity] if 'Date' in equity[0] or 'date' in equity[0] else None
                        )
                    else:
                        # List of numeric values
                        equity = pd.Series(equity)
                else:
                    equity = pd.Series([initial_capital, final_value])
                
        except Exception as e:
            # Return failed result
            return BacktestResult(
                symbol=symbol,
                strategy_name=strategy.__class__.__name__,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                final_value=initial_capital,
                total_return=0.0,
                trades=[],
                equity_curve=pd.Series([initial_capital]),
                data=pd.DataFrame(),
                metrics={'error': str(e)}
            )
        
        # Calculate metrics
        total_return = ((final_value - initial_capital) / initial_capital) * 100
        
        metrics = self._calculate_metrics(
            trades=trades,
            equity_curve=equity,
            initial_capital=initial_capital,
            final_value=final_value
        )
        
        # Create standardized result
        result = BacktestResult(
            symbol=symbol,
            strategy_name=strategy.__class__.__name__,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_value=final_value,
            total_return=total_return,
            trades=trades if isinstance(trades, list) else [],
            equity_curve=equity if isinstance(equity, pd.Series) else pd.Series([final_value]),
            data=data if isinstance(data, pd.DataFrame) else pd.DataFrame(),
            metrics=metrics
        )
        
        return result
    
    def _create_equity_curve(self, trades: List[Dict], initial_capital: float) -> pd.Series:
        """Create equity curve from trades"""
        if not trades:
            return pd.Series([initial_capital])
        
        equity = [initial_capital]
        current_value = initial_capital
        
        for trade in trades:
            if 'profit' in trade:
                current_value += trade['profit']
            elif 'pnl' in trade:
                current_value += trade['pnl']
            equity.append(current_value)
        
        return pd.Series(equity)
    
    def _calculate_metrics(self, 
                          trades: List[Dict],
                          equity_curve: pd.Series,
                          initial_capital: float,
                          final_value: float) -> Dict:
        """Calculate comprehensive performance metrics"""
        
        metrics = {
            'total_trades': len(trades),
            'total_return_pct': ((final_value - initial_capital) / initial_capital) * 100,
            'final_value': final_value
        }
        
        if len(trades) == 0:
            return metrics
        
        # Trade analysis
        try:
            # Helper to extract profit from trades (handles tuple and dict formats)
            def get_trade_profit(trade):
                if isinstance(trade, dict):
                    return trade.get('profit', trade.get('pnl', 0))
                elif isinstance(trade, (tuple, list)) and len(trade) >= 4:
                    # Trade format: (date, action, price, shares) - can't compute profit from single trade
                    return None  # Return None to signal we can't extract profit
                return 0
            
            # Try to get profits - if trades are tuples, we need to pair BUY/SELL
            profits = []
            if trades and isinstance(trades[0], (tuple, list)):
                # Tuple format - calculate profits from BUY/SELL pairs
                buy_trades = [(t[0], t[2], t[3]) for t in trades if len(t) >= 4 and str(t[1]).upper() == 'BUY']
                sell_trades = [(t[0], t[2], t[3]) for t in trades if len(t) >= 4 and str(t[1]).upper() == 'SELL']
                # Match pairs in order
                for i, (buy_date, buy_price, buy_shares) in enumerate(buy_trades):
                    if i < len(sell_trades):
                        sell_date, sell_price, sell_shares = sell_trades[i]
                        profit = (sell_price - buy_price) * min(buy_shares, sell_shares)
                        profits.append(profit)
            else:
                # Dict format with profit/pnl keys
                for t in trades:
                    p = get_trade_profit(t)
                    if p is not None:
                        profits.append(p)
            
            winning_trades = [p for p in profits if p > 0]
            losing_trades = [p for p in profits if p < 0]
            
            metrics['winning_trades'] = len(winning_trades)
            metrics['losing_trades'] = len(losing_trades)
            metrics['win_rate'] = (len(winning_trades) / len(profits)) * 100 if profits else 0
            
            if winning_trades:
                avg_win = np.mean(winning_trades)
                metrics['avg_win'] = avg_win
            
            if losing_trades:
                avg_loss = np.mean(losing_trades)
                metrics['avg_loss'] = avg_loss
            
            if losing_trades and winning_trades:
                metrics['profit_factor'] = abs(sum(winning_trades) / sum(losing_trades))
        except Exception as e:
            metrics['calculation_error'] = str(e)
        
        # Equity curve metrics
        try:
            if len(equity_curve) > 1:
                returns = equity_curve.pct_change().dropna()
                
                if len(returns) > 0:
                    # Sharpe ratio (assuming 252 trading days, 2% risk-free rate)
                    excess_returns = returns - 0.02/252
                    if returns.std() > 0:
                        metrics['sharpe_ratio'] = np.sqrt(252) * excess_returns.mean() / returns.std()
                    
                    # Max drawdown
                    cumulative = equity_curve / equity_curve.cummax()
                    drawdown = (cumulative - 1) * 100
                    metrics['max_drawdown_pct'] = drawdown.min()
                    
                    # Volatility
                    metrics['volatility'] = returns.std() * np.sqrt(252) * 100
        
        except Exception as e:
            metrics['equity_error'] = str(e)
        
        return metrics
    
    def run_multiple_strategies(self,
                               strategies: List[Any],
                               symbol: str,
                               start_date: datetime,
                               end_date: datetime,
                               initial_capital: float = 100000) -> List[BacktestResult]:
        """Run multiple strategies and return results"""
        
        results = []
        for strategy in strategies:
            result = self.run_backtest(
                strategy=strategy,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital
            )
            results.append(result)
        
        return results
    
    def compare_strategies(self, results: List[BacktestResult]) -> pd.DataFrame:
        """Create comparison table of multiple strategy results"""
        
        comparison_data = []
        for result in results:
            comparison_data.append({
                'Strategy': result.strategy_name,
                'Symbol': result.symbol,
                'Total Return %': result.total_return,
                'Final Value': result.final_value,
                'Trades': len(result.trades),
                'Win Rate %': result.metrics.get('win_rate', 0),
                'Sharpe Ratio': result.metrics.get('sharpe_ratio', 0),
                'Max DD %': result.metrics.get('max_drawdown_pct', 0),
            })
        
        df = pd.DataFrame(comparison_data)
        return df.sort_values('Total Return %', ascending=False)
    
    def export_results(self, result: BacktestResult, filename: str):
        """Export backtest results to file"""
        import json
        
        export_data = {
            'result': result.to_dict(),
            'trades': result.trades,
            'equity_curve': result.equity_curve.to_dict() if not result.equity_curve.empty else {}
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"✓ Results exported to {filename}")
