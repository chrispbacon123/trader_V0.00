"""
Advanced Risk Management Module
Implements institutional-grade risk controls and portfolio risk metrics
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import json
from core_config import PORTFOLIO_CFG

class RiskManager:
    """Comprehensive risk management for trading strategies"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.max_position_size = self.config.get('max_position_size', 0.25)  # 25% max per position
        self.max_portfolio_var = self.config.get('max_portfolio_var', 0.02)  # 2% daily VaR
        self.max_drawdown = self.config.get('max_drawdown', 0.20)  # 20% max drawdown
        self.max_leverage = self.config.get('max_leverage', 1.0)
        self.stop_loss_pct = self.config.get('stop_loss_pct', 0.05)  # 5% stop loss
        self.take_profit_pct = self.config.get('take_profit_pct', 0.15)  # 15% take profit
        
    def calculate_position_size(self, capital: float, price: float, 
                               volatility: float, risk_per_trade: float = 0.02) -> float:
        """Calculate optimal position size using volatility-adjusted Kelly criterion
        
        Returns:
            float: Number of shares (float if fractional enabled, int otherwise)
        """
        # Kelly fraction adjusted for risk
        kelly_fraction = risk_per_trade / (volatility ** 2) if volatility > 0 else 0.01
        kelly_fraction = min(kelly_fraction, self.max_position_size)
        
        # Position size in shares
        position_value = capital * kelly_fraction
        shares = position_value / price
        
        # Apply fractional share logic
        if not PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED:
            shares = int(shares)
        
        return max(shares, 0)
    
    def calculate_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """Calculate Value at Risk (VaR) using historical simulation"""
        if len(returns) < 2:
            return 0.0
        return np.percentile(returns, (1 - confidence) * 100)
    
    def calculate_cvar(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """Calculate Conditional Value at Risk (CVaR/Expected Shortfall)"""
        if len(returns) < 2:
            return 0.0
        var = self.calculate_var(returns, confidence)
        return returns[returns <= var].mean()
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate annualized Sharpe ratio"""
        if len(returns) < 2 or returns.std() == 0:
            return 0.0
        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
        return np.sqrt(252) * excess_returns.mean() / returns.std()
    
    def calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio (uses downside deviation)"""
        if len(returns) < 2:
            return 0.0
        excess_returns = returns - risk_free_rate / 252
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        return np.sqrt(252) * excess_returns.mean() / downside_returns.std()
    
    def calculate_max_drawdown(self, equity_curve: pd.Series) -> Tuple[float, datetime, datetime]:
        """Calculate maximum drawdown and its dates"""
        if len(equity_curve) < 2:
            return 0.0, None, None
        
        cumulative = equity_curve.cummax()
        drawdown = (equity_curve - cumulative) / cumulative
        max_dd = drawdown.min()
        
        end_date = drawdown.idxmin()
        start_date = equity_curve[:end_date].idxmax()
        
        return abs(max_dd), start_date, end_date
    
    def calculate_calmar_ratio(self, returns: pd.Series, equity_curve: pd.Series) -> float:
        """Calculate Calmar ratio (annual return / max drawdown)"""
        if len(returns) < 2:
            return 0.0
        
        annual_return = (1 + returns.mean()) ** 252 - 1
        max_dd, _, _ = self.calculate_max_drawdown(equity_curve)
        
        if max_dd == 0:
            return 0.0
        return annual_return / max_dd
    
    def check_risk_limits(self, portfolio_value: float, positions: Dict, 
                         equity_curve: pd.Series) -> Dict[str, bool]:
        """Check if current portfolio violates any risk limits"""
        violations = {}
        
        # Check max drawdown
        if len(equity_curve) > 1:
            max_dd, _, _ = self.calculate_max_drawdown(equity_curve)
            violations['max_drawdown_exceeded'] = max_dd > self.max_drawdown
        
        # Check position concentration
        for symbol, position in positions.items():
            position_pct = abs(position.get('value', 0)) / portfolio_value if portfolio_value > 0 else 0
            if position_pct > self.max_position_size:
                violations[f'{symbol}_position_size_exceeded'] = True
        
        # Check leverage
        total_exposure = sum(abs(p.get('value', 0)) for p in positions.values())
        leverage = total_exposure / portfolio_value if portfolio_value > 0 else 0
        violations['leverage_exceeded'] = leverage > self.max_leverage
        
        return violations
    
    def generate_risk_report(self, returns: pd.Series, equity_curve: pd.Series, 
                            positions: Dict) -> Dict:
        """Generate comprehensive risk report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'sharpe_ratio': self.calculate_sharpe_ratio(returns),
            'sortino_ratio': self.calculate_sortino_ratio(returns),
            'var_95': self.calculate_var(returns, 0.95),
            'cvar_95': self.calculate_cvar(returns, 0.95),
            'calmar_ratio': self.calculate_calmar_ratio(returns, equity_curve),
        }
        
        if len(equity_curve) > 1:
            max_dd, start, end = self.calculate_max_drawdown(equity_curve)
            report['max_drawdown'] = max_dd
            report['max_drawdown_start'] = start.isoformat() if start else None
            report['max_drawdown_end'] = end.isoformat() if end else None
        
        return report
    
    def should_stop_trading(self, equity_curve: pd.Series, initial_capital: float) -> bool:
        """Determine if trading should be halted due to risk limits"""
        if len(equity_curve) < 2:
            return False
        
        current_value = equity_curve.iloc[-1]
        max_dd, _, _ = self.calculate_max_drawdown(equity_curve)
        
        # Stop if max drawdown exceeded
        if max_dd > self.max_drawdown:
            return True
        
        # Stop if portfolio value dropped below critical threshold
        if current_value < initial_capital * (1 - self.max_drawdown * 1.5):
            return True
        
        return False


class PositionSizer:
    """Advanced position sizing strategies"""
    
    @staticmethod
    def fixed_fractional(capital: float, price: float, risk_pct: float = 0.02) -> float:
        """Fixed fractional position sizing
        
        Returns:
            float: Number of shares (float if fractional enabled, int otherwise)
        """
        position_value = capital * risk_pct
        shares = position_value / price
        if not PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED:
            shares = int(shares)
        return shares
    
    @staticmethod
    def volatility_adjusted(capital: float, price: float, volatility: float, 
                           target_risk: float = 0.02) -> float:
        """Position size adjusted for volatility
        
        Returns:
            float: Number of shares (float if fractional enabled, int otherwise)
        """
        if volatility == 0:
            return 0
        position_value = capital * (target_risk / volatility)
        shares = position_value / price
        if not PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED:
            shares = int(shares)
        return shares
    
    @staticmethod
    def kelly_criterion(capital: float, price: float, win_rate: float, 
                       avg_win: float, avg_loss: float) -> float:
        """Kelly criterion position sizing
        
        Returns:
            float: Number of shares (float if fractional enabled, int otherwise)
        """
        if avg_loss == 0:
            return 0
        kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_loss
        kelly = max(0, min(kelly, 0.25))  # Cap at 25%
        position_value = capital * kelly
        shares = position_value / price
        if not PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED:
            shares = int(shares)
        return shares
    
    @staticmethod
    def optimal_f(capital: float, price: float, trade_history: List[float]) -> float:
        """Optimal f position sizing
        
        Returns:
            float: Number of shares (float if fractional enabled, int otherwise)
        """
        if not trade_history:
            return 0
        
        max_loss = abs(min(trade_history))
        if max_loss == 0:
            return 0
        
        # Find optimal f that maximizes geometric mean
        best_f = 0.01
        best_geom_mean = 0
        
        for f in np.arange(0.01, 0.26, 0.01):
            hpr = [1 + (trade * f / max_loss) for trade in trade_history]
            geom_mean = np.exp(np.mean(np.log(hpr)))
            if geom_mean > best_geom_mean:
                best_geom_mean = geom_mean
                best_f = f
        
        position_value = capital * best_f
        shares = position_value / price
        if not PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED:
            shares = int(shares)
        return shares


class PortfolioAnalyzer:
    """Advanced portfolio analytics and attribution"""
    
    @staticmethod
    def calculate_beta(returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate portfolio beta vs benchmark"""
        if len(returns) < 2 or len(benchmark_returns) < 2:
            return 1.0
        covariance = np.cov(returns, benchmark_returns)[0][1]
        benchmark_variance = np.var(benchmark_returns)
        return covariance / benchmark_variance if benchmark_variance > 0 else 1.0
    
    @staticmethod
    def calculate_alpha(returns: pd.Series, benchmark_returns: pd.Series, 
                       risk_free_rate: float = 0.02) -> float:
        """Calculate Jensen's alpha"""
        if len(returns) < 2:
            return 0.0
        beta = PortfolioAnalyzer.calculate_beta(returns, benchmark_returns)
        portfolio_return = returns.mean() * 252
        benchmark_return = benchmark_returns.mean() * 252
        rf_rate = risk_free_rate
        return portfolio_return - (rf_rate + beta * (benchmark_return - rf_rate))
    
    @staticmethod
    def calculate_information_ratio(returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate information ratio"""
        if len(returns) < 2:
            return 0.0
        active_returns = returns - benchmark_returns
        tracking_error = active_returns.std()
        return active_returns.mean() / tracking_error if tracking_error > 0 else 0.0
    
    @staticmethod
    def performance_attribution(portfolio_returns: Dict[str, pd.Series], 
                               weights: Dict[str, float]) -> Dict:
        """Performance attribution by asset"""
        attribution = {}
        for symbol, returns in portfolio_returns.items():
            if len(returns) > 0:
                weight = weights.get(symbol, 0)
                contribution = returns.mean() * weight * 252
                attribution[symbol] = {
                    'weight': weight,
                    'return': returns.mean() * 252,
                    'contribution': contribution,
                    'volatility': returns.std() * np.sqrt(252)
                }
        return attribution


def save_risk_config(config: Dict, filename: str = 'risk_config.json'):
    """Save risk configuration to file"""
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)


def load_risk_config(filename: str = 'risk_config.json') -> Dict:
    """Load risk configuration from file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
