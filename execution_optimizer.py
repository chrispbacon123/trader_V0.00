"""
Execution Optimizer - Smart order execution and slippage modeling
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


class ExecutionOptimizer:
    """Optimize trade execution to minimize costs and slippage"""
    
    def __init__(self, model='linear'):
        self.model = model
        self.slippage_params = {
            'linear': 0.0005,  # 5 bps per 1% of volume
            'sqrt': 0.001,     # Square root model
            'fixed': 0.0001    # Fixed 1bp
        }
        
    def estimate_slippage(self, order_size, avg_volume, volatility, spread=0.0001):
        """Estimate market impact and slippage"""
        if avg_volume <= 0:
            return 0.01  # 1% default if no volume data
        
        volume_participation = abs(order_size) / avg_volume
        
        if self.model == 'linear':
            # Linear market impact model
            impact = self.slippage_params['linear'] * volume_participation
        
        elif self.model == 'sqrt':
            # Square-root market impact model (more realistic)
            impact = self.slippage_params['sqrt'] * np.sqrt(volume_participation)
        
        elif self.model == 'fixed':
            # Fixed slippage
            impact = self.slippage_params['fixed']
        
        else:
            impact = 0.0
        
        # Add spread cost
        total_cost = impact + spread / 2
        
        # Add volatility component
        vol_cost = volatility * np.sqrt(volume_participation) * 0.1
        
        return total_cost + vol_cost
    
    def optimize_execution_schedule(self, total_size, duration_minutes=390, vwap_target=True):
        """Create optimal execution schedule (e.g., TWAP, VWAP)"""
        if duration_minutes <= 0:
            return [total_size]
        
        num_slices = min(duration_minutes // 5, 20)  # 5-minute slices, max 20
        
        if vwap_target:
            # VWAP-weighted schedule (U-shaped volume pattern)
            time_points = np.linspace(0, 1, num_slices)
            # U-shape: higher volume at open and close
            weights = 1 + np.sin(time_points * np.pi) * 0.5
            weights = weights / weights.sum()
        else:
            # TWAP - equal slices
            weights = np.ones(num_slices) / num_slices
        
        schedule = weights * total_size
        return schedule
    
    def calculate_optimal_limit_price(self, current_price, signal_strength, 
                                      volatility, is_buy=True, urgency=0.5):
        """Calculate optimal limit price based on signal and market conditions"""
        # Base adjustment on volatility
        vol_adjustment = volatility * (1 - urgency)
        
        # Adjust for signal strength
        signal_adjustment = abs(signal_strength) * 0.002  # Up to 20 bps for strong signals
        
        if is_buy:
            # For buy orders, limit slightly above market for urgency
            limit_price = current_price * (1 + signal_adjustment - vol_adjustment * urgency)
        else:
            # For sell orders, limit slightly below market
            limit_price = current_price * (1 - signal_adjustment + vol_adjustment * urgency)
        
        return limit_price
    
    def estimate_fill_probability(self, limit_price, current_price, volatility, 
                                  time_horizon_minutes=5):
        """Estimate probability of limit order fill"""
        price_diff = abs(limit_price - current_price) / current_price
        
        # Use normal distribution assumption
        expected_move = volatility * np.sqrt(time_horizon_minutes / (252 * 390))
        
        if expected_move > 0:
            z_score = price_diff / expected_move
            # Probability price reaches limit
            fill_prob = 1 - stats.norm.cdf(z_score)
        else:
            fill_prob = 0.5
        
        return max(0, min(1, fill_prob))
    
    def transaction_cost_analysis(self, trades_df):
        """Analyze transaction costs from executed trades"""
        if trades_df.empty:
            return {}
        
        analysis = {
            'total_trades': len(trades_df),
            'total_commission': trades_df.get('commission', 0).sum(),
            'avg_slippage': trades_df.get('slippage', 0).mean(),
            'total_cost_bps': 0
        }
        
        if 'entry_price' in trades_df.columns and 'exit_price' in trades_df.columns:
            # Calculate realized slippage
            expected_pnl = trades_df.get('shares', 0) * (trades_df['exit_price'] - trades_df['entry_price'])
            actual_pnl = trades_df.get('pnl', expected_pnl)
            slippage_cost = expected_pnl - actual_pnl
            analysis['slippage_cost'] = slippage_cost.sum()
        
        return analysis


class SmartOrderRouter:
    """Route orders intelligently based on market conditions"""
    
    def __init__(self):
        self.order_types = ['MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT', 'TWAP', 'VWAP']
        
    def select_order_type(self, signal_strength, volatility, liquidity_score, urgency=0.5):
        """Select best order type based on conditions"""
        # High urgency + strong signal = market order
        if urgency > 0.8 and abs(signal_strength) > 0.7:
            return 'MARKET'
        
        # Low volatility + good liquidity = limit order
        if volatility < 0.02 and liquidity_score > 0.7:
            return 'LIMIT'
        
        # High volatility = stop limit for protection
        if volatility > 0.04:
            return 'STOP_LIMIT'
        
        # Large orders = VWAP algo
        if liquidity_score < 0.3:
            return 'VWAP'
        
        # Default to limit
        return 'LIMIT'
    
    def calculate_urgency_score(self, signal_alpha, signal_decay, time_in_position=0):
        """Calculate how urgently to execute the trade"""
        # Higher decay = more urgent
        # Stronger signal = more urgent
        # Longer in position = less urgent (already positioned)
        
        urgency = abs(signal_alpha) * 0.5
        urgency += signal_decay * 0.3
        urgency -= min(time_in_position / 100, 0.3)
        
        return max(0, min(1, urgency))


class RiskLimitManager:
    """Manage position and risk limits in real-time"""
    
    def __init__(self, max_position_pct=0.1, max_sector_pct=0.3, max_leverage=1.0):
        self.max_position_pct = max_position_pct
        self.max_sector_pct = max_sector_pct
        self.max_leverage = max_leverage
        self.current_positions = {}
        self.sector_exposure = {}
        
    def check_position_limit(self, symbol, proposed_size, portfolio_value):
        """Check if proposed position violates limits"""
        current_size = self.current_positions.get(symbol, 0)
        new_size = current_size + proposed_size
        
        position_pct = abs(new_size) / portfolio_value if portfolio_value > 0 else 0
        
        if position_pct > self.max_position_pct:
            # Reduce to max allowed
            allowed_size = self.max_position_pct * portfolio_value * np.sign(new_size)
            return allowed_size - current_size
        
        return proposed_size
    
    def check_sector_limit(self, sector, proposed_exposure, total_value):
        """Check sector concentration limits"""
        current_exposure = self.sector_exposure.get(sector, 0)
        new_exposure = current_exposure + proposed_exposure
        
        sector_pct = abs(new_exposure) / total_value if total_value > 0 else 0
        
        if sector_pct > self.max_sector_pct:
            allowed_exposure = self.max_sector_pct * total_value * np.sign(new_exposure)
            return allowed_exposure - current_exposure
        
        return proposed_exposure
    
    def check_leverage(self, gross_exposure, net_exposure, capital):
        """Check leverage limits"""
        leverage = gross_exposure / capital if capital > 0 else 0
        
        if leverage > self.max_leverage:
            return False, f"Leverage {leverage:.2f}x exceeds limit {self.max_leverage}x"
        
        return True, "OK"
    
    def update_positions(self, symbol, size, sector=None):
        """Update position tracking"""
        self.current_positions[symbol] = self.current_positions.get(symbol, 0) + size
        
        if sector and size != 0:
            self.sector_exposure[sector] = self.sector_exposure.get(sector, 0) + size
    
    def get_available_capacity(self, symbol, portfolio_value):
        """Get remaining capacity for a symbol"""
        current_size = abs(self.current_positions.get(symbol, 0))
        max_size = self.max_position_pct * portfolio_value
        return max(0, max_size - current_size)
