"""
Advanced Performance Analytics Module
Provides institutional-grade performance metrics and analysis
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class PerformanceAnalytics:
    """Advanced performance analytics for trading strategies"""
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
        
    def calculate_returns(self, equity_curve: pd.Series) -> pd.Series:
        """Calculate returns from equity curve"""
        return equity_curve.pct_change().fillna(0)
    
    def sharpe_ratio(self, returns: pd.Series, periods_per_year: int = 252) -> float:
        """Calculate annualized Sharpe ratio"""
        if len(returns) < 2 or returns.std() == 0:
            return 0.0
        excess_returns = returns - self.risk_free_rate / periods_per_year
        return np.sqrt(periods_per_year) * excess_returns.mean() / returns.std()
    
    def sortino_ratio(self, returns: pd.Series, periods_per_year: int = 252) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        if len(returns) < 2:
            return 0.0
        excess_returns = returns - self.risk_free_rate / periods_per_year
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        return np.sqrt(periods_per_year) * excess_returns.mean() / downside_returns.std()
    
    def calmar_ratio(self, returns: pd.Series, periods_per_year: int = 252) -> float:
        """Calculate Calmar ratio (return/max drawdown)"""
        if len(returns) < 2:
            return 0.0
        annual_return = (1 + returns.mean()) ** periods_per_year - 1
        max_dd = self.max_drawdown(returns)
        if max_dd == 0:
            return 0.0
        return annual_return / abs(max_dd)
    
    def max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        if len(returns) == 0:
            return 0.0
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def value_at_risk(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """Calculate Value at Risk (VaR)"""
        if len(returns) < 2:
            return 0.0
        return np.percentile(returns, (1 - confidence) * 100)
    
    def conditional_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """Calculate Conditional Value at Risk (CVaR/Expected Shortfall)"""
        if len(returns) < 2:
            return 0.0
        var = self.value_at_risk(returns, confidence)
        return returns[returns <= var].mean()
    
    def omega_ratio(self, returns: pd.Series, threshold: float = 0.0) -> float:
        """Calculate Omega ratio"""
        if len(returns) < 2:
            return 1.0
        excess = returns - threshold
        gains = excess[excess > 0].sum()
        losses = -excess[excess < 0].sum()
        if losses == 0:
            return np.inf if gains > 0 else 1.0
        return gains / losses
    
    def win_rate(self, returns: pd.Series) -> float:
        """Calculate win rate percentage"""
        if len(returns) == 0:
            return 0.0
        return (returns > 0).sum() / len(returns)
    
    def profit_factor(self, returns: pd.Series) -> float:
        """Calculate profit factor"""
        if len(returns) == 0:
            return 0.0
        gains = returns[returns > 0].sum()
        losses = -returns[returns < 0].sum()
        if losses == 0:
            return np.inf if gains > 0 else 0.0
        return gains / losses
    
    def tail_ratio(self, returns: pd.Series) -> float:
        """Calculate tail ratio (95th percentile / 5th percentile)"""
        if len(returns) < 2:
            return 1.0
        right_tail = np.percentile(returns, 95)
        left_tail = np.percentile(returns, 5)
        if left_tail == 0:
            return np.inf if right_tail > 0 else 1.0
        return abs(right_tail / left_tail)
    
    def information_ratio(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate information ratio vs benchmark"""
        if len(returns) < 2 or len(benchmark_returns) < 2:
            return 0.0
        active_returns = returns - benchmark_returns
        if active_returns.std() == 0:
            return 0.0
        return active_returns.mean() / active_returns.std()
    
    def generate_report(self, equity_curve: pd.Series, 
                       benchmark: Optional[pd.Series] = None) -> Dict:
        """Generate comprehensive performance report"""
        returns = self.calculate_returns(equity_curve)
        
        if len(returns) < 2:
            return {
                'total_return': 0.0,
                'annual_return': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0
            }
        
        periods_per_year = 252
        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
        n_periods = len(returns)
        years = n_periods / periods_per_year
        
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        volatility = returns.std() * np.sqrt(periods_per_year)
        
        report = {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': self.sharpe_ratio(returns),
            'sortino_ratio': self.sortino_ratio(returns),
            'calmar_ratio': self.calmar_ratio(returns),
            'max_drawdown': self.max_drawdown(returns),
            'var_95': self.value_at_risk(returns),
            'cvar_95': self.conditional_var(returns),
            'omega_ratio': self.omega_ratio(returns),
            'win_rate': self.win_rate(returns),
            'profit_factor': self.profit_factor(returns),
            'tail_ratio': self.tail_ratio(returns),
            'total_trades': n_periods,
            'avg_return': returns.mean(),
            'median_return': returns.median(),
            'best_day': returns.max(),
            'worst_day': returns.min(),
            'positive_days': (returns > 0).sum(),
            'negative_days': (returns < 0).sum(),
        }
        
        if benchmark is not None and len(benchmark) > 0:
            benchmark_returns = self.calculate_returns(benchmark)
            if len(benchmark_returns) == len(returns):
                report['information_ratio'] = self.information_ratio(returns, benchmark_returns)
                report['beta'] = self.calculate_beta(returns, benchmark_returns)
                report['alpha'] = self.calculate_alpha(returns, benchmark_returns, report['beta'])
        
        return report
    
    def calculate_beta(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate beta vs benchmark"""
        if len(returns) < 2 or len(benchmark_returns) < 2:
            return 1.0
        covariance = returns.cov(benchmark_returns)
        benchmark_variance = benchmark_returns.var()
        if benchmark_variance == 0:
            return 1.0
        return covariance / benchmark_variance
    
    def calculate_alpha(self, returns: pd.Series, benchmark_returns: pd.Series, 
                       beta: float, periods_per_year: int = 252) -> float:
        """Calculate alpha vs benchmark"""
        if len(returns) < 2:
            return 0.0
        strategy_return = returns.mean() * periods_per_year
        benchmark_return = benchmark_returns.mean() * periods_per_year
        return strategy_return - (self.risk_free_rate + beta * (benchmark_return - self.risk_free_rate))
    
    def rolling_sharpe(self, returns: pd.Series, window: int = 60) -> pd.Series:
        """Calculate rolling Sharpe ratio"""
        if len(returns) < window:
            return pd.Series([0] * len(returns), index=returns.index)
        
        rolling_mean = returns.rolling(window).mean()
        rolling_std = returns.rolling(window).std()
        
        excess_returns = rolling_mean - self.risk_free_rate / 252
        sharpe = np.sqrt(252) * excess_returns / rolling_std
        return sharpe.fillna(0)
    
    def drawdown_analysis(self, equity_curve: pd.Series) -> Dict:
        """Analyze drawdown characteristics"""
        returns = self.calculate_returns(equity_curve)
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        
        # Find all drawdown periods
        is_drawdown = drawdown < 0
        drawdown_starts = is_drawdown & ~is_drawdown.shift(1, fill_value=False)
        drawdown_ends = ~is_drawdown & is_drawdown.shift(1, fill_value=False)
        
        max_dd = drawdown.min()
        avg_dd = drawdown[is_drawdown].mean() if is_drawdown.any() else 0.0
        
        # Calculate recovery time for max drawdown
        max_dd_idx = drawdown.idxmin()
        recovery_idx = drawdown[max_dd_idx:][drawdown >= 0].index
        recovery_days = len(drawdown[max_dd_idx:recovery_idx[0]]) if len(recovery_idx) > 0 else len(drawdown) - drawdown.index.get_loc(max_dd_idx)
        
        return {
            'max_drawdown': max_dd,
            'avg_drawdown': avg_dd,
            'max_drawdown_duration': recovery_days,
            'current_drawdown': drawdown.iloc[-1],
            'drawdown_periods': drawdown_starts.sum()
        }
