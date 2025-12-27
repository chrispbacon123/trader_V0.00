"""
Test execution algorithms (TWAP, VWAP, Iceberg) with fractional shares
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from order_execution import (
    Order, OrderType, OrderSide, OrderStatus,
    TWAPAlgorithm, VWAPAlgorithm, IcebergOrder
)
from core_config import PORTFOLIO_CFG


@pytest.fixture
def sample_market_data():
    """Create sample market data"""
    dates = pd.date_range('2024-01-01', periods=20, freq='5min')
    data = pd.DataFrame({
        'Close': np.random.uniform(100, 110, 20),
        'Volume': np.random.uniform(1e6, 10e6, 20)
    }, index=dates)
    return data


class TestTWAPAlgorithm:
    """Test TWAP execution algorithm"""
    
    def test_twap_fractional_enabled(self, sample_market_data):
        """Test TWAP with fractional shares enabled"""
        # Temporarily enable fractional
        original = PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED
        PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = True
        
        try:
            order = Order(
                symbol='SPY',
                side=OrderSide.BUY,
                quantity=100.5,  # Fractional quantity
                order_type=OrderType.TWAP
            )
            
            twap = TWAPAlgorithm(order, num_slices=10)
            child_orders = twap.generate_child_orders(sample_market_data)
            
            # Should have 10 slices
            assert len(child_orders) == 10
            
            # Each slice should be fractional (10.05)
            for child in child_orders:
                assert child.quantity == 10.05
            
            # Total should equal parent quantity
            total = sum(child.quantity for child in child_orders)
            assert np.isclose(total, 100.5)
            
        finally:
            PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = original
    
    def test_twap_fractional_disabled(self, sample_market_data):
        """Test TWAP with fractional shares disabled"""
        # Temporarily disable fractional
        original = PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED
        PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = False
        
        try:
            order = Order(
                symbol='SPY',
                side=OrderSide.BUY,
                quantity=105,  # Whole number
                order_type=OrderType.TWAP
            )
            
            twap = TWAPAlgorithm(order, num_slices=10)
            child_orders = twap.generate_child_orders(sample_market_data)
            
            # Should have 10 slices
            assert len(child_orders) == 10
            
            # All slices should be whole numbers
            for child in child_orders:
                assert child.quantity == int(child.quantity)
            
            # Total should equal parent (105)
            total = sum(child.quantity for child in child_orders)
            assert total == 105
            
            # First 5 slices get 11, last 5 get 10 (105 = 10*10 + 5*1)
            assert child_orders[0].quantity == 11
            assert child_orders[5].quantity == 10
            
        finally:
            PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = original


class TestVWAPAlgorithm:
    """Test VWAP execution algorithm"""
    
    def test_vwap_fractional_enabled(self, sample_market_data):
        """Test VWAP with fractional shares enabled"""
        original = PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED
        PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = True
        
        try:
            # Create volume profile
            volume_profile = pd.Series([1e6, 2e6, 3e6, 2e6, 1e6])
            
            order = Order(
                symbol='SPY',
                side=OrderSide.BUY,
                quantity=100.5,
                order_type=OrderType.VWAP
            )
            
            vwap = VWAPAlgorithm(order, historical_volume=volume_profile)
            child_orders = vwap.generate_child_orders(sample_market_data)
            
            # Should create child orders
            assert len(child_orders) > 0
            
            # At least one should be fractional
            has_fractional = any(
                child.quantity != int(child.quantity) 
                for child in child_orders
            )
            assert has_fractional, "VWAP should produce fractional quantities when enabled"
            
            # Total should be close to parent quantity
            total = sum(child.quantity for child in child_orders)
            assert np.isclose(total, 100.5, atol=0.01)
            
        finally:
            PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = original
    
    def test_vwap_fractional_disabled(self, sample_market_data):
        """Test VWAP with fractional shares disabled"""
        original = PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED
        PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = False
        
        try:
            volume_profile = pd.Series([1e6, 2e6, 3e6, 2e6, 1e6])
            
            order = Order(
                symbol='SPY',
                side=OrderSide.BUY,
                quantity=100,
                order_type=OrderType.VWAP
            )
            
            vwap = VWAPAlgorithm(order, historical_volume=volume_profile)
            child_orders = vwap.generate_child_orders(sample_market_data)
            
            # All quantities should be whole numbers
            for child in child_orders:
                assert child.quantity == int(child.quantity), \
                    f"VWAP child quantity {child.quantity} should be whole number"
            
        finally:
            PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = original


class TestIcebergOrder:
    """Test Iceberg order execution"""
    
    def test_iceberg_fractional_enabled(self, sample_market_data):
        """Test Iceberg with fractional shares enabled"""
        original = PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED
        PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = True
        
        try:
            order = Order(
                symbol='SPY',
                side=OrderSide.BUY,
                quantity=100.5,
                order_type=OrderType.ICEBERG
            )
            
            iceberg = IcebergOrder(order, visible_quantity=10.5)
            child_orders = iceberg.generate_child_orders(sample_market_data)
            
            # Should create multiple slices
            assert len(child_orders) > 1
            
            # Most slices should be 10.5
            for child in child_orders[:-1]:
                assert np.isclose(child.quantity, 10.5)
            
            # Total should equal parent
            total = sum(child.quantity for child in child_orders)
            assert np.isclose(total, 100.5)
            
        finally:
            PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = original
    
    def test_iceberg_fractional_disabled_whole_numbers(self, sample_market_data):
        """Test Iceberg with whole numbers when fractional disabled"""
        original = PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED
        PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = False
        
        try:
            order = Order(
                symbol='SPY',
                side=OrderSide.BUY,
                quantity=100,
                order_type=OrderType.ICEBERG
            )
            
            iceberg = IcebergOrder(order, visible_quantity=10)
            child_orders = iceberg.generate_child_orders(sample_market_data)
            
            # Should create 10 slices of 10 each
            assert len(child_orders) == 10
            
            for child in child_orders:
                assert child.quantity == 10
                assert child.quantity == int(child.quantity)
            
        finally:
            PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = original
    
    def test_iceberg_fractional_disabled_rejects_fractional(self, sample_market_data):
        """Test Iceberg rejects fractional quantities when disabled"""
        original = PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED
        PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = False
        
        try:
            order = Order(
                symbol='SPY',
                side=OrderSide.BUY,
                quantity=100.5,  # Fractional when not allowed
                order_type=OrderType.ICEBERG
            )
            
            iceberg = IcebergOrder(order, visible_quantity=10)
            
            # Should raise ValueError
            with pytest.raises(ValueError, match="IcebergOrder requires whole shares"):
                child_orders = iceberg.generate_child_orders(sample_market_data)
            
        finally:
            PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = original


class TestExecutionConsistency:
    """Test execution algorithms respect fractional flag consistently"""
    
    def test_no_silent_int_casts_when_fractional_enabled(self, sample_market_data):
        """Ensure no silent integer casts occur when fractional is enabled"""
        original = PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED
        PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = True
        
        try:
            # Test TWAP
            order_twap = Order('SPY', OrderSide.BUY, 100.7, OrderType.TWAP)
            twap = TWAPAlgorithm(order_twap, num_slices=10)
            children = twap.generate_child_orders(sample_market_data)
            
            total_twap = sum(c.quantity for c in children)
            assert np.isclose(total_twap, 100.7), \
                f"TWAP lost precision: {total_twap} != 100.7"
            
            # Test VWAP
            volume_profile = pd.Series([1e6, 2e6, 3e6])
            order_vwap = Order('SPY', OrderSide.BUY, 50.3, OrderType.VWAP)
            vwap = VWAPAlgorithm(order_vwap, historical_volume=volume_profile)
            children_vwap = vwap.generate_child_orders(sample_market_data)
            
            total_vwap = sum(c.quantity for c in children_vwap)
            # VWAP may have small rounding but should be close
            assert abs(total_vwap - 50.3) < 0.1, \
                f"VWAP lost too much precision: {total_vwap} vs 50.3"
            
        finally:
            PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = original
