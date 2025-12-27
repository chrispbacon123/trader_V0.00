"""
Advanced Risk Management Module
Implements position sizing, risk controls, and portfolio constraints
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from enum import Enum
from core_config import PORTFOLIO_CFG


class PositionSizeMethod(Enum):
    FIXED = "fixed"
    PERCENT_EQUITY = "percent_equity"
    KELLY = "kelly"
    VOLATILITY_TARGET = "volatility_target"
    RISK_PARITY = "risk_parity"


class RiskManager:
    """Advanced risk management for trading strategies"""
    
    def __init__(self, 
                 initial_capital: float = 100000,
                 max_position_size: float = 0.2,
                 max_portfolio_risk: float = 0.02,
                 max_drawdown_limit: float = 0.25,
                 max_leverage: float = 1.0,
                 stop_loss_pct: float = 0.05,
                 take_profit_pct: float = 0.10):
        
        self.initial_capital = initial_capital
        self.max_position_size = max_position_size
        self.max_portfolio_risk = max_portfolio_risk
        self.max_drawdown_limit = max_drawdown_limit
        self.max_leverage = max_leverage
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        
        self.current_positions = {}
        self.equity_history = [initial_capital]
        self.peak_equity = initial_capital
        
    def calculate_position_size(self, 
                               symbol: str,
                               price: float,
                               current_equity: float,
                               volatility: float = 0.02,
                               method: PositionSizeMethod = PositionSizeMethod.PERCENT_EQUITY,
                               win_rate: float = 0.5,
                               avg_win: float = 0.02,
                               avg_loss: float = 0.01) -> float:
        """Calculate optimal position size based on risk parameters
        
        Returns:
            float: Number of shares (float if fractional enabled, int otherwise)
        """
        
        if method == PositionSizeMethod.FIXED:
            max_shares = current_equity * self.max_position_size / price
            
        elif method == PositionSizeMethod.PERCENT_EQUITY:
            risk_amount = current_equity * self.max_portfolio_risk
            shares_at_risk = risk_amount / (price * self.stop_loss_pct)
            max_shares = min(shares_at_risk, current_equity * self.max_position_size / price)
            
        elif method == PositionSizeMethod.KELLY:
            # Kelly Criterion: f = (p*b - q) / b where p=win rate, q=loss rate, b=win/loss ratio
            if avg_loss == 0:
                kelly_fraction = 0.25
            else:
                b = avg_win / avg_loss
                kelly_fraction = (win_rate * b - (1 - win_rate)) / b
                kelly_fraction = max(0, min(kelly_fraction * 0.5, 0.25))  # Half Kelly with cap
            
            max_shares = current_equity * kelly_fraction / price
            
        elif method == PositionSizeMethod.VOLATILITY_TARGET:
            target_vol = 0.15  # 15% annual volatility target
            position_vol_contribution = volatility * np.sqrt(252)
            if position_vol_contribution == 0:
                max_shares = 0
            else:
                position_fraction = target_vol / position_vol_contribution
                position_fraction = min(position_fraction, self.max_position_size)
                max_shares = current_equity * position_fraction / price
                
        else:  # RISK_PARITY
            # Equal risk contribution
            if volatility == 0:
                max_shares = 0
            else:
                risk_budget = current_equity * self.max_portfolio_risk
                max_shares = risk_budget / (price * volatility * np.sqrt(252))
        
        # Apply leverage limit
        max_exposure = current_equity * self.max_leverage
        max_shares = min(max_shares, max_exposure / price)
        
        # Apply fractional share logic
        if not PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED:
            max_shares = int(max_shares)  # Floor to whole shares
        
        return max(0, max_shares)
    
    def check_risk_limits(self, current_equity: float, positions: Dict) -> Tuple[bool, str]:
        """Check if current portfolio meets risk limits"""
        
        # Check drawdown limit
        self.peak_equity = max(self.peak_equity, current_equity)
        current_drawdown = (current_equity - self.peak_equity) / self.peak_equity
        
        if current_drawdown < -self.max_drawdown_limit:
            return False, f"Max drawdown exceeded: {current_drawdown:.2%}"
        
        # Check total exposure
        total_exposure = sum(abs(pos['shares'] * pos['price']) for pos in positions.values())
        if total_exposure > current_equity * self.max_leverage:
            return False, f"Leverage limit exceeded: {total_exposure/current_equity:.2f}x"
        
        # Check position concentration
        for symbol, pos in positions.items():
            position_value = abs(pos['shares'] * pos['price'])
            if position_value > current_equity * self.max_position_size:
                return False, f"Position size limit exceeded for {symbol}"
        
        return True, "All risk limits OK"
    
    def calculate_stop_loss(self, entry_price: float, position_type: str = 'long') -> float:
        """Calculate stop loss price"""
        if position_type == 'long':
            return entry_price * (1 - self.stop_loss_pct)
        else:
            return entry_price * (1 + self.stop_loss_pct)
    
    def calculate_take_profit(self, entry_price: float, position_type: str = 'long') -> float:
        """Calculate take profit price"""
        if position_type == 'long':
            return entry_price * (1 + self.take_profit_pct)
        else:
            return entry_price * (1 - self.take_profit_pct)
    
    def update_stops(self, symbol: str, current_price: float, 
                    entry_price: float, position_type: str = 'long') -> Dict:
        """Update trailing stops"""
        
        if position_type == 'long':
            # Trailing stop: move up as price increases
            profit_pct = (current_price - entry_price) / entry_price
            if profit_pct > self.take_profit_pct / 2:
                # Lock in some profit
                new_stop = entry_price * (1 + profit_pct * 0.5 - self.stop_loss_pct)
                return {'stop_loss': new_stop, 'trailing': True}
            else:
                return {'stop_loss': self.calculate_stop_loss(entry_price, 'long'), 'trailing': False}
        else:
            profit_pct = (entry_price - current_price) / entry_price
            if profit_pct > self.take_profit_pct / 2:
                new_stop = entry_price * (1 - profit_pct * 0.5 + self.stop_loss_pct)
                return {'stop_loss': new_stop, 'trailing': True}
            else:
                return {'stop_loss': self.calculate_stop_loss(entry_price, 'short'), 'trailing': False}
    
    def calculate_portfolio_var(self, positions: Dict, returns_history: pd.DataFrame,
                               confidence: float = 0.95) -> float:
        """Calculate portfolio Value at Risk"""
        if len(returns_history) < 10:
            return 0.0
        
        # Calculate portfolio returns
        portfolio_returns = []
        for date in returns_history.index:
            daily_return = 0
            for symbol, pos in positions.items():
                if symbol in returns_history.columns:
                    daily_return += pos.get('weight', 0) * returns_history.loc[date, symbol]
            portfolio_returns.append(daily_return)
        
        if len(portfolio_returns) == 0:
            return 0.0
        
        var = np.percentile(portfolio_returns, (1 - confidence) * 100)
        return var
    
    def diversification_score(self, positions: Dict) -> float:
        """Calculate portfolio diversification score (0-1)"""
        if len(positions) == 0:
            return 0.0
        
        # Calculate Herfindahl index
        weights = [abs(pos.get('weight', 0)) for pos in positions.values()]
        total_weight = sum(weights)
        
        if total_weight == 0:
            return 0.0
        
        normalized_weights = [w / total_weight for w in weights]
        herfindahl = sum(w ** 2 for w in normalized_weights)
        
        # Convert to diversification score (1 = fully diversified, 0 = concentrated)
        n = len(positions)
        diversification = (1 - herfindahl) / (1 - 1/n) if n > 1 else 0.0
        
        return diversification
    
    def rebalance_portfolio(self, current_positions: Dict, 
                           target_weights: Dict,
                           current_prices: Dict,
                           current_equity: float) -> Dict:
        """Calculate trades needed to rebalance to target weights"""
        
        rebalance_trades = {}
        
        for symbol, target_weight in target_weights.items():
            target_value = current_equity * target_weight
            current_value = 0
            
            if symbol in current_positions:
                current_value = current_positions[symbol]['shares'] * current_prices.get(symbol, 0)
            
            value_diff = target_value - current_value
            price = current_prices.get(symbol, 0)
            
            if price > 0:
                shares_diff = value_diff / price
                # Apply fractional share logic
                if not PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED:
                    shares_diff = int(shares_diff)
                if abs(shares_diff) > 0:
                    rebalance_trades[symbol] = shares_diff
        
        return rebalance_trades
