"""
Centralized Position Sizing Module
Handles share calculations with fractional share support
"""

import numpy as np
from typing import Tuple
from core_config import PORTFOLIO_CFG


def calculate_shares(
    target_value: float,
    price: float,
    fractional_allowed: bool = None,
    min_position_value: float = None
) -> Tuple[float, float]:
    """
    Calculate number of shares to buy given target value and price.
    
    Args:
        target_value: Dollar amount to allocate
        price: Current price per share
        fractional_allowed: Whether fractional shares are allowed (None = use config)
        min_position_value: Minimum position value (None = use config)
    
    Returns:
        tuple: (shares, cash_residual)
            shares: Number of shares (float if fractional, int if whole)
            cash_residual: Unallocated cash due to rounding
    
    Example:
        >>> shares, residual = calculate_shares(10000, 457.23, fractional_allowed=True)
        >>> shares  # 21.8723...
        >>> residual  # 0.0 (fully allocated)
        
        >>> shares, residual = calculate_shares(10000, 457.23, fractional_allowed=False)
        >>> shares  # 21.0 (whole shares)
        >>> residual  # 348.17 (leftover cash)
    """
    # Use config defaults if not provided
    if fractional_allowed is None:
        fractional_allowed = PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED
    if min_position_value is None:
        min_position_value = PORTFOLIO_CFG.MIN_POSITION_VALUE
    
    # Validate inputs
    if target_value <= 0:
        return 0.0, target_value
    if price <= 0:
        raise ValueError(f"Price must be positive, got {price}")
    
    # Calculate ideal shares
    ideal_shares = target_value / price
    
    # Apply fractional share logic
    if fractional_allowed:
        shares = ideal_shares
        cash_residual = 0.0  # Fully allocated
    else:
        shares = np.floor(ideal_shares)  # Round down to whole shares
        position_value = shares * price
        cash_residual = target_value - position_value
    
    # Check minimum position value
    position_value = shares * price
    if position_value < min_position_value:
        return 0.0, target_value  # Position too small, return all cash
    
    return shares, cash_residual


def calculate_shares_from_weight(
    total_equity: float,
    target_weight: float,
    price: float,
    fractional_allowed: bool = None,
    min_position_value: float = None
) -> Tuple[float, float]:
    """
    Calculate shares from target portfolio weight.
    
    Args:
        total_equity: Total portfolio value
        target_weight: Target weight (0.0 to 1.0)
        price: Current price per share
        fractional_allowed: Whether fractional shares are allowed
        min_position_value: Minimum position value
    
    Returns:
        tuple: (shares, cash_residual)
    """
    target_value = total_equity * target_weight
    return calculate_shares(target_value, price, fractional_allowed, min_position_value)


def format_shares(shares: float, fractional_allowed: bool = None) -> str:
    """
    Format shares for display based on fractional flag.
    
    Args:
        shares: Number of shares
        fractional_allowed: Whether fractional shares are allowed
    
    Returns:
        Format specifier string for use in f-strings
    
    Example:
        >>> fmt = format_shares(21.8723, fractional_allowed=True)
        >>> f"{shares:{fmt}}"  # "21.8723"
        
        >>> fmt = format_shares(21.0, fractional_allowed=False)
        >>> f"{shares:{fmt}}"  # "21"
    """
    if fractional_allowed is None:
        fractional_allowed = PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED
    
    return '.4f' if fractional_allowed else '.0f'


def calculate_transaction_costs(
    shares: float,
    price: float,
    include_slippage: bool = True,
    include_commission: bool = True
) -> dict:
    """
    Calculate transaction costs for a trade.
    
    Args:
        shares: Number of shares
        price: Price per share
        include_slippage: Whether to include slippage
        include_commission: Whether to include commission
    
    Returns:
        dict with breakdown of costs
    """
    costs = {
        'slippage': 0.0,
        'commission': 0.0,
        'total': 0.0,
        'position_value': shares * price
    }
    
    if include_slippage:
        costs['slippage'] = PORTFOLIO_CFG.calculate_slippage(price, shares)
    
    if include_commission:
        costs['commission'] = PORTFOLIO_CFG.calculate_commission(price, shares)
    
    costs['total'] = costs['slippage'] + costs['commission']
    costs['total_cost_bps'] = (costs['total'] / costs['position_value']) * 10000 if costs['position_value'] > 0 else 0
    
    return costs
