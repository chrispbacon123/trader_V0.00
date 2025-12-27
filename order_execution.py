"""
Advanced Order Execution Engine
Supports multiple order types and execution algorithms
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
from core_config import PORTFOLIO_CFG

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"
    ICEBERG = "ICEBERG"
    TWAP = "TWAP"
    VWAP = "VWAP"
    
class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"
    
class OrderStatus(Enum):
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class Order:
    """Order object with full details"""
    
    def __init__(self, symbol: str, side: OrderSide, quantity: float, 
                 order_type: OrderType, price: Optional[float] = None,
                 stop_price: Optional[float] = None, time_in_force: str = "GTC",
                 metadata: Dict = None):
        self.id = f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        self.symbol = symbol
        self.side = side
        self.quantity = quantity  # float to support fractional shares
        self.order_type = order_type
        self.price = price
        self.stop_price = stop_price
        self.time_in_force = time_in_force  # GTC, DAY, IOC, FOK
        self.status = OrderStatus.PENDING
        self.filled_quantity = 0.0  # float to support fractional fills
        self.avg_fill_price = 0.0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.fills = []
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict:
        """Convert order to dictionary"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side.value,
            'quantity': self.quantity,
            'order_type': self.order_type.value,
            'price': self.price,
            'stop_price': self.stop_price,
            'time_in_force': self.time_in_force,
            'status': self.status.value,
            'filled_quantity': self.filled_quantity,
            'avg_fill_price': self.avg_fill_price,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'fills': self.fills,
            'metadata': self.metadata
        }

class ExecutionAlgorithm:
    """Base class for execution algorithms"""
    
    def __init__(self, order: Order):
        self.order = order
        self.child_orders = []
        
    def generate_child_orders(self, market_data: pd.DataFrame) -> List[Order]:
        """Generate child orders for execution"""
        raise NotImplementedError

class TWAPAlgorithm(ExecutionAlgorithm):
    """Time-Weighted Average Price execution"""
    
    def __init__(self, order: Order, num_slices: int = 10, interval_minutes: int = 5):
        super().__init__(order)
        self.num_slices = num_slices
        self.interval_minutes = interval_minutes
        
    def generate_child_orders(self, market_data: pd.DataFrame) -> List[Order]:
        """Split order into equal time slices"""
        # Handle fractional vs whole shares
        if PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED:
            # Fractional mode: split evenly as floats
            slice_size = self.order.quantity / self.num_slices
            child_orders = []
            
            for i in range(self.num_slices):
                child_order = Order(
                    symbol=self.order.symbol,
                    side=self.order.side,
                    quantity=slice_size,
                    order_type=OrderType.MARKET,
                    metadata={'parent_id': self.order.id, 'slice': i}
                )
                child_orders.append(child_order)
        else:
            # Integer mode: distribute remainder across first slices
            slice_size = int(self.order.quantity) // self.num_slices
            remainder = int(self.order.quantity) % self.num_slices
            
            child_orders = []
            for i in range(self.num_slices):
                quantity = slice_size + (1 if i < remainder else 0)
                child_order = Order(
                    symbol=self.order.symbol,
                    side=self.order.side,
                    quantity=quantity,
                    order_type=OrderType.MARKET,
                    metadata={'parent_id': self.order.id, 'slice': i}
                )
                child_orders.append(child_order)
        
        return child_orders

class VWAPAlgorithm(ExecutionAlgorithm):
    """Volume-Weighted Average Price execution"""
    
    def __init__(self, order: Order, historical_volume: pd.Series):
        super().__init__(order)
        self.historical_volume = historical_volume
        
    def generate_child_orders(self, market_data: pd.DataFrame) -> List[Order]:
        """Split order based on historical volume profile"""
        # Calculate volume distribution
        total_volume = self.historical_volume.sum()
        volume_pcts = self.historical_volume / total_volume
        
        child_orders = []
        remaining = self.order.quantity
        
        for i, pct in enumerate(volume_pcts):
            if remaining <= 0:
                break
            quantity = self.order.quantity * pct
            # Apply fractional logic
            if not PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED:
                quantity = int(quantity)
            quantity = min(quantity, remaining)
            
            if quantity > 0:
                child_order = Order(
                    symbol=self.order.symbol,
                    side=self.order.side,
                    quantity=quantity,
                    order_type=OrderType.MARKET,
                    metadata={'parent_id': self.order.id, 'slice': i}
                )
                child_orders.append(child_order)
                remaining -= quantity
        
        return child_orders

class IcebergOrder(ExecutionAlgorithm):
    """Iceberg order - only show small portion of total order"""
    
    def __init__(self, order: Order, visible_quantity: float):
        """
        Initialize Iceberg order
        
        Args:
            order: Parent order
            visible_quantity: Visible quantity per slice (can be fractional)
        """
        super().__init__(order)
        self.visible_quantity = visible_quantity
        
    def generate_child_orders(self, market_data: pd.DataFrame) -> List[Order]:
        """Generate child orders with limited visibility"""
        # Check if fractional shares allowed
        if not PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED:
            # Iceberg requires whole shares in integer mode
            if self.order.quantity != int(self.order.quantity) or \
               self.visible_quantity != int(self.visible_quantity):
                raise ValueError(
                    "IcebergOrder requires whole shares when FRACTIONAL_SHARES_ALLOWED=False. "
                    f"Got order qty={self.order.quantity}, visible_qty={self.visible_quantity}"
                )
        
        # Calculate number of slices
        if PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED:
            # Fractional mode: use ceil to ensure we cover full quantity
            import math
            num_slices = math.ceil(self.order.quantity / self.visible_quantity)
        else:
            # Integer mode
            num_slices = (int(self.order.quantity) + int(self.visible_quantity) - 1) // int(self.visible_quantity)
        
        child_orders = []
        remaining = self.order.quantity
        
        for i in range(num_slices):
            quantity = min(self.visible_quantity, remaining)
            
            child_order = Order(
                symbol=self.order.symbol,
                side=self.order.side,
                quantity=quantity,
                order_type=self.order.order_type,
                price=self.order.price,
                metadata={'parent_id': self.order.id, 'slice': i, 'hidden_qty': remaining - quantity}
            )
            child_orders.append(child_order)
            remaining -= quantity
            
            if remaining <= 0:
                break
        
        return child_orders

class OrderExecutor:
    """Main order execution engine"""
    
    def __init__(self):
        self.active_orders = {}
        self.order_history = []
        self.execution_costs = []
        
    def submit_order(self, order: Order) -> str:
        """Submit order for execution"""
        self.active_orders[order.id] = order
        return order.id
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel active order"""
        if order_id in self.active_orders:
            order = self.active_orders[order_id]
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now()
            self.order_history.append(order)
            del self.active_orders[order_id]
            return True
        return False
    
    def execute_market_order(self, order: Order, current_price: float, 
                            slippage_pct: float = 0.001) -> bool:
        """Execute market order with slippage"""
        # Simulate slippage
        if order.side == OrderSide.BUY:
            fill_price = current_price * (1 + slippage_pct)
        else:
            fill_price = current_price * (1 - slippage_pct)
        
        # Record fill
        fill = {
            'timestamp': datetime.now().isoformat(),
            'quantity': order.quantity,
            'price': fill_price
        }
        order.fills.append(fill)
        order.filled_quantity = order.quantity
        order.avg_fill_price = fill_price
        order.status = OrderStatus.FILLED
        order.updated_at = datetime.now()
        
        # Calculate execution cost
        ideal_value = order.quantity * current_price
        actual_value = order.quantity * fill_price
        cost = abs(actual_value - ideal_value)
        self.execution_costs.append({
            'order_id': order.id,
            'cost': cost,
            'cost_pct': cost / ideal_value if ideal_value > 0 else 0
        })
        
        return True
    
    def execute_limit_order(self, order: Order, current_price: float) -> bool:
        """Execute limit order if price conditions met"""
        can_fill = False
        
        if order.side == OrderSide.BUY and current_price <= order.price:
            can_fill = True
        elif order.side == OrderSide.SELL and current_price >= order.price:
            can_fill = True
        
        if can_fill:
            fill = {
                'timestamp': datetime.now().isoformat(),
                'quantity': order.quantity,
                'price': order.price
            }
            order.fills.append(fill)
            order.filled_quantity = order.quantity
            order.avg_fill_price = order.price
            order.status = OrderStatus.FILLED
            order.updated_at = datetime.now()
            return True
        
        return False
    
    def execute_stop_order(self, order: Order, current_price: float) -> Optional[Order]:
        """Convert stop order to market order if triggered"""
        triggered = False
        
        if order.side == OrderSide.BUY and current_price >= order.stop_price:
            triggered = True
        elif order.side == OrderSide.SELL and current_price <= order.stop_price:
            triggered = True
        
        if triggered:
            # Convert to market order
            market_order = Order(
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                order_type=OrderType.MARKET,
                metadata={'parent_stop_order': order.id}
            )
            return market_order
        
        return None
    
    def update_trailing_stop(self, order: Order, current_price: float, 
                            trail_pct: float = 0.05) -> Optional[Order]:
        """Update trailing stop order"""
        if order.side == OrderSide.SELL:
            # Update stop price if current price increases
            new_stop = current_price * (1 - trail_pct)
            if order.stop_price is None or new_stop > order.stop_price:
                order.stop_price = new_stop
                order.updated_at = datetime.now()
            
            # Check if triggered
            if current_price <= order.stop_price:
                return self.execute_stop_order(order, current_price)
        else:
            # Buy trailing stop
            new_stop = current_price * (1 + trail_pct)
            if order.stop_price is None or new_stop < order.stop_price:
                order.stop_price = new_stop
                order.updated_at = datetime.now()
            
            if current_price >= order.stop_price:
                return self.execute_stop_order(order, current_price)
        
        return None
    
    def process_orders(self, market_data: Dict[str, float]) -> List[Order]:
        """Process all active orders"""
        filled_orders = []
        triggered_orders = []
        
        for order_id, order in list(self.active_orders.items()):
            if order.symbol not in market_data:
                continue
            
            current_price = market_data[order.symbol]
            
            if order.order_type == OrderType.MARKET:
                if self.execute_market_order(order, current_price):
                    filled_orders.append(order)
                    del self.active_orders[order_id]
                    
            elif order.order_type == OrderType.LIMIT:
                if self.execute_limit_order(order, current_price):
                    filled_orders.append(order)
                    del self.active_orders[order_id]
                    
            elif order.order_type == OrderType.STOP:
                triggered = self.execute_stop_order(order, current_price)
                if triggered:
                    triggered_orders.append(triggered)
                    del self.active_orders[order_id]
                    
            elif order.order_type == OrderType.TRAILING_STOP:
                trail_pct = order.metadata.get('trail_pct', 0.05)
                triggered = self.update_trailing_stop(order, current_price, trail_pct)
                if triggered:
                    triggered_orders.append(triggered)
                    del self.active_orders[order_id]
        
        # Submit triggered stop orders
        for triggered in triggered_orders:
            self.submit_order(triggered)
        
        # Move filled orders to history
        self.order_history.extend(filled_orders)
        
        return filled_orders
    
    def get_execution_report(self) -> Dict:
        """Generate execution quality report"""
        if not self.execution_costs:
            return {'avg_cost': 0, 'total_cost': 0, 'avg_cost_pct': 0}
        
        total_cost = sum(c['cost'] for c in self.execution_costs)
        avg_cost = total_cost / len(self.execution_costs)
        avg_cost_pct = sum(c['cost_pct'] for c in self.execution_costs) / len(self.execution_costs)
        
        return {
            'avg_cost': avg_cost,
            'total_cost': total_cost,
            'avg_cost_pct': avg_cost_pct,
            'num_orders': len(self.execution_costs)
        }
    
    def export_orders(self, filename: str):
        """Export order history to JSON"""
        orders_data = [order.to_dict() for order in self.order_history]
        with open(filename, 'w') as f:
            json.dump(orders_data, f, indent=2)
    
    def get_fill_rate(self) -> float:
        """Calculate order fill rate"""
        if not self.order_history:
            return 0.0
        filled = sum(1 for o in self.order_history if o.status == OrderStatus.FILLED)
        return filled / len(self.order_history)
