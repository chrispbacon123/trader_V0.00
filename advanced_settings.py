"""
Advanced Settings and Configuration Manager
Manages advanced trading parameters, risk settings, and optimization options
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from datetime import datetime

@dataclass
class RiskSettings:
    """Risk management parameters"""
    max_position_size: float = 0.2  # Max % of capital per position
    max_portfolio_risk: float = 0.02  # Max % loss per trade
    stop_loss_pct: float = 0.05  # Stop loss percentage
    take_profit_pct: float = 0.15  # Take profit percentage
    max_drawdown: float = 0.15  # Max acceptable drawdown
    diversification_min: int = 5  # Min number of positions
    leverage: float = 1.0  # Leverage multiplier
    
@dataclass
class MLSettings:
    """Machine Learning parameters"""
    model_type: str = 'xgboost'  # xgboost, random_forest, lgbm
    n_estimators: int = 100
    max_depth: int = 5
    learning_rate: float = 0.1
    lookback_period: int = 60
    prediction_horizon: int = 5
    train_test_split: float = 0.8
    cv_folds: int = 5
    feature_selection: bool = True
    min_samples: int = 50
    
@dataclass
class BacktestSettings:
    """Backtesting parameters"""
    commission: float = 0.001  # 0.1% per trade
    slippage: float = 0.0005  # 0.05% slippage
    min_holding_period: int = 1  # Min days to hold
    max_holding_period: int = 30  # Max days to hold
    rebalance_frequency: str = 'daily'  # daily, weekly, monthly
    benchmark: str = 'SPY'
    
@dataclass
class DataSettings:
    """Data fetching and processing"""
    data_source: str = 'yfinance'
    cache_data: bool = True
    cache_duration: int = 3600  # seconds
    min_data_points: int = 50
    handle_missing: str = 'ffill'  # ffill, drop, interpolate
    outlier_detection: bool = True
    
@dataclass
class OptimizationSettings:
    """Strategy optimization parameters"""
    optimize_params: bool = False
    optimization_metric: str = 'sharpe_ratio'  # sharpe_ratio, total_return, win_rate
    param_search_method: str = 'grid'  # grid, random, bayesian
    max_iterations: int = 100
    parallel_jobs: int = 4


class AdvancedSettingsManager:
    """Manages all advanced settings"""
    
    def __init__(self, settings_file='advanced_settings.json'):
        self.settings_file = settings_file
        self.risk = RiskSettings()
        self.ml = MLSettings()
        self.backtest = BacktestSettings()
        self.data = DataSettings()
        self.optimization = OptimizationSettings()
        self.load_settings()
        
    def load_settings(self):
        """Load settings from file"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    
                if 'risk' in data:
                    self.risk = RiskSettings(**data['risk'])
                if 'ml' in data:
                    self.ml = MLSettings(**data['ml'])
                if 'backtest' in data:
                    self.backtest = BacktestSettings(**data['backtest'])
                if 'data' in data:
                    self.data = DataSettings(**data['data'])
                if 'optimization' in data:
                    self.optimization = OptimizationSettings(**data['optimization'])
            except Exception as e:
                print(f"Warning: Could not load advanced settings: {e}")
                
    def save_settings(self):
        """Save settings to file"""
        data = {
            'risk': asdict(self.risk),
            'ml': asdict(self.ml),
            'backtest': asdict(self.backtest),
            'data': asdict(self.data),
            'optimization': asdict(self.optimization),
            'last_updated': datetime.now().isoformat()
        }
        
        with open(self.settings_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as dictionary"""
        return {
            'risk': asdict(self.risk),
            'ml': asdict(self.ml),
            'backtest': asdict(self.backtest),
            'data': asdict(self.data),
            'optimization': asdict(self.optimization)
        }
        
    def update_risk_settings(self, **kwargs):
        """Update risk settings"""
        for key, value in kwargs.items():
            if hasattr(self.risk, key):
                setattr(self.risk, key, value)
        self.save_settings()
        
    def update_ml_settings(self, **kwargs):
        """Update ML settings"""
        for key, value in kwargs.items():
            if hasattr(self.ml, key):
                setattr(self.ml, key, value)
        self.save_settings()
        
    def update_backtest_settings(self, **kwargs):
        """Update backtest settings"""
        for key, value in kwargs.items():
            if hasattr(self.backtest, key):
                setattr(self.backtest, key, value)
        self.save_settings()
        
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.risk = RiskSettings()
        self.ml = MLSettings()
        self.backtest = BacktestSettings()
        self.data = DataSettings()
        self.optimization = OptimizationSettings()
        self.save_settings()
        
    def print_settings(self):
        """Print all current settings"""
        print("\n" + "═"*90)
        print("ADVANCED SETTINGS")
        print("═"*90)
        
        print("\n🛡️  RISK MANAGEMENT")
        for key, value in asdict(self.risk).items():
            print(f"  {key:25s}: {value}")
            
        print("\n🤖 MACHINE LEARNING")
        for key, value in asdict(self.ml).items():
            print(f"  {key:25s}: {value}")
            
        print("\n📊 BACKTESTING")
        for key, value in asdict(self.backtest).items():
            print(f"  {key:25s}: {value}")
            
        print("\n💾 DATA MANAGEMENT")
        for key, value in asdict(self.data).items():
            print(f"  {key:25s}: {value}")
            
        print("\n⚡ OPTIMIZATION")
        for key, value in asdict(self.optimization).items():
            print(f"  {key:25s}: {value}")
