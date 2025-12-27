"""
Validated Portfolio Allocation
Fractional shares, cash residuals, position sizing with transaction costs
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass

from core_config import PORTFOLIO_CFG


@dataclass
class Position:
    """Represents a portfolio position"""
    symbol: str
    shares: float  # Can be fractional
    price: float
    value: float
    weight: float
    
    def __repr__(self):
        return f"Position({self.symbol}: {self.shares:.4f} shares @ ${self.price:.2f} = ${self.value:.2f}, {self.weight*100:.2f}%)"


class ValidatedPortfolio:
    """
    Portfolio allocation with:
    - Fractional share support
    - Explicit cash management
    - Transaction cost modeling
    - Broker constraint handling
    """
    
    def __init__(
        self,
        equity: float,
        fractional_allowed: bool = None,
        commission_per_share: float = None,
        slippage_bps: float = None
    ):
        """
        Initialize portfolio
        
        Args:
            equity: Available capital
            fractional_allowed: Allow fractional shares (broker dependent)
            commission_per_share: Commission per share
            slippage_bps: Slippage in basis points
        """
        self.equity = equity
        self.fractional_allowed = fractional_allowed if fractional_allowed is not None else PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED
        self.commission_per_share = commission_per_share if commission_per_share is not None else PORTFOLIO_CFG.COMMISSION_PER_SHARE
        self.slippage_bps = slippage_bps if slippage_bps is not None else PORTFOLIO_CFG.SLIPPAGE_BPS
        
        self.positions: Dict[str, Position] = {}
        self.cash = equity
        self.transaction_costs = 0.0
    
    def allocate(
        self,
        target_weights: Dict[str, float],
        prices: Dict[str, float]
    ) -> Dict:
        """
        Allocate portfolio based on target weights
        
        Args:
            target_weights: Dict of symbol -> target weight (0-1)
            prices: Dict of symbol -> current price
            
        Returns:
            Dict with positions, cash, costs, and summary
        """
        # Validate weights
        total_weight = sum(target_weights.values())
        if not np.isclose(total_weight, 1.0, atol=0.01):
            raise ValueError(f"Weights must sum to 1.0, got {total_weight:.4f}")
        
        # Cap individual weights
        capped_weights = {}
        for symbol, weight in target_weights.items():
            capped_weights[symbol] = min(weight, PORTFOLIO_CFG.MAX_POSITION_WEIGHT)
        
        # Renormalize if weights were capped
        total_capped = sum(capped_weights.values())
        if total_capped < total_weight:
            scale_factor = total_weight / total_capped
            capped_weights = {s: w * scale_factor for s, w in capped_weights.items()}
        
        # Reserve cash buffer
        investable = self.equity * (1 - PORTFOLIO_CFG.MIN_CASH_BUFFER)
        
        # Calculate target values
        target_values = {s: investable * w for s, w in capped_weights.items()}
        
        # Calculate shares needed
        positions = {}
        total_cost = 0.0
        total_transaction_costs = 0.0
        
        for symbol, target_value in target_values.items():
            price = prices[symbol]
            
            # Calculate shares
            ideal_shares = target_value / price
            
            # Handle fractional shares
            if self.fractional_allowed:
                shares = ideal_shares
            else:
                shares = np.floor(ideal_shares)  # Round down
            
            # Skip if position would be too small
            if shares * price < PORTFOLIO_CFG.MIN_POSITION_VALUE:
                continue
            
            # Calculate costs
            position_value = shares * price
            slippage = PORTFOLIO_CFG.calculate_slippage(price, shares)
            commission = PORTFOLIO_CFG.calculate_commission(price, shares)
            transaction_cost = slippage + commission
            
            # Create position
            positions[symbol] = Position(
                symbol=symbol,
                shares=shares,
                price=price,
                value=position_value,
                weight=0.0  # Will calculate after
            )
            
            total_cost += position_value + transaction_cost
            total_transaction_costs += transaction_cost
        
        # Calculate actual weights
        total_invested = sum(p.value for p in positions.values())
        for position in positions.values():
            position.weight = position.value / total_invested if total_invested > 0 else 0.0
        
        # Update portfolio state
        self.positions = positions
        self.cash = self.equity - total_cost
        self.transaction_costs = total_transaction_costs
        
        # Build summary
        summary = {
            'total_equity': self.equity,
            'total_invested': total_invested,
            'cash_remaining': self.cash,
            'cash_pct': self.cash / self.equity * 100,
            'transaction_costs': total_transaction_costs,
            'transaction_costs_pct': total_transaction_costs / self.equity * 100,
            'num_positions': len(positions),
            'fractional_allowed': self.fractional_allowed,
            'positions': {s: {
                'shares': p.shares,
                'price': p.price,
                'value': p.value,
                'weight_pct': p.weight * 100
            } for s, p in positions.items()}
        }
        
        return summary
    
    def rebalance(
        self,
        target_weights: Dict[str, float],
        prices: Dict[str, float],
        threshold: float = None
    ) -> Dict:
        """
        Rebalance portfolio if drift exceeds threshold
        
        Args:
            target_weights: New target weights
            prices: Current prices
            threshold: Rebalance if any weight drifts by more than this
            
        Returns:
            Dict with rebalancing summary
        """
        if threshold is None:
            threshold = PORTFOLIO_CFG.REBALANCE_THRESHOLD
        
        # Calculate current weights
        current_values = {}
        total_value = self.cash
        
        for symbol, position in self.positions.items():
            current_price = prices.get(symbol, position.price)
            current_value = position.shares * current_price
            current_values[symbol] = current_value
            total_value += current_value
        
        current_weights = {s: v / total_value for s, v in current_values.items()}
        
        # Check if rebalancing needed
        max_drift = 0.0
        drifts = {}
        for symbol, target_weight in target_weights.items():
            current_weight = current_weights.get(symbol, 0.0)
            drift = abs(target_weight - current_weight)
            drifts[symbol] = drift
            max_drift = max(max_drift, drift)
        
        needs_rebalance = max_drift > threshold
        
        if needs_rebalance:
            # Reset and reallocate
            self.equity = total_value
            self.cash = total_value
            self.positions = {}
            allocation_summary = self.allocate(target_weights, prices)
            
            return {
                'rebalanced': True,
                'max_drift': max_drift,
                'threshold': threshold,
                'drifts': drifts,
                **allocation_summary
            }
        else:
            return {
                'rebalanced': False,
                'max_drift': max_drift,
                'threshold': threshold,
                'drifts': drifts,
                'message': f'No rebalancing needed (max drift {max_drift*100:.2f}% < threshold {threshold*100:.2f}%)'
            }
    
    @staticmethod
    def print_allocation(summary: Dict):
        """Print allocation summary"""
        print(f"\n{'='*80}")
        print("PORTFOLIO ALLOCATION")
        print(f"{'='*80}")
        print(f"Total Equity:        ${summary['total_equity']:>12,.2f}")
        print(f"Invested:            ${summary['total_invested']:>12,.2f}")
        print(f"Cash Remaining:      ${summary['cash_remaining']:>12,.2f}  ({summary['cash_pct']:.2f}%)")
        print(f"Transaction Costs:   ${summary['transaction_costs']:>12,.2f}  ({summary['transaction_costs_pct']:.2f}%)")
        print(f"Number of Positions: {summary['num_positions']}")
        print(f"Fractional Shares:   {'Allowed' if summary['fractional_allowed'] else 'Not Allowed'}")
        
        print(f"\nPositions:")
        print(f"{'Symbol':<10} {'Shares':>12} {'Price':>10} {'Value':>12} {'Weight':>10}")
        print(f"{'-'*60}")
        
        for symbol, pos in summary['positions'].items():
            print(
                f"{symbol:<10} {pos['shares']:>12.4f} "
                f"${pos['price']:>9.2f} ${pos['value']:>11,.2f} "
                f"{pos['weight_pct']:>9.2f}%"
            )
        
        print(f"{'='*80}\n")


def optimize_allocation(
    target_weights: Dict[str, float],
    prices: Dict[str, float],
    equity: float,
    expected_returns: Dict[str, float] = None,
    risk_tolerance: float = 1.0
) -> Dict[str, float]:
    """
    Optimize allocation based on expected returns and risk
    
    Simple mean-variance optimization
    For production use, consider scipy.optimize or cvxpy
    """
    # If no expected returns provided, use equal weighting
    if expected_returns is None:
        n = len(target_weights)
        return {s: 1.0/n for s in target_weights.keys()}
    
    # Scale by expected returns and risk tolerance
    scaled_weights = {}
    total = 0.0
    
    for symbol, weight in target_weights.items():
        exp_return = expected_returns.get(symbol, 0.0)
        scaled = max(0, weight + exp_return * risk_tolerance)
        scaled_weights[symbol] = scaled
        total += scaled
    
    # Normalize
    if total > 0:
        scaled_weights = {s: w / total for s, w in scaled_weights.items()}
    
    return scaled_weights
