"""
Custom Strategy Builder - Create, test, and export custom trading strategies
"""
import json
import os
import re
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Any

def sanitize_identifier(name: str) -> str:
    """
    Sanitize a string to be a valid Python identifier
    
    Rules:
    - Must start with letter or underscore
    - Can only contain letters, numbers, underscore
    - Cannot be empty
    
    Args:
        name: Input string
        
    Returns:
        Valid Python identifier
    """
    # Remove spaces and special chars, keep only alphanumeric and underscore
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '', name.replace(' ', '_'))
    
    # Ensure doesn't start with digit
    if cleaned and cleaned[0].isdigit():
        cleaned = 'Algo_' + cleaned
    
    # If empty after cleaning, use default
    if not cleaned:
        cleaned = 'CustomAlgorithm'
    
    return cleaned


def sanitize_export_basename(name: str, timestamp: str) -> str:
    """
    Create a safe export filename base that will never match pytest's test_*.py pattern.
    
    Always prefixes with 'export_' to prevent pytest collection issues.
    
    Args:
        name: Strategy name (will be sanitized)
        timestamp: Timestamp string
        
    Returns:
        Safe filename base like 'export_MyStrategy_20251225_120000'
    """
    sanitized_name = sanitize_identifier(name)
    return f"export_{sanitized_name}_{timestamp}"


class StrategyBuilder:
    """Interactive strategy builder with export capabilities"""
    
    def __init__(self):
        self.strategies_dir = "custom_strategies"
        self.exports_dir = "strategy_exports"
        os.makedirs(self.strategies_dir, exist_ok=True)
        os.makedirs(self.exports_dir, exist_ok=True)
    
    def create_custom_strategy(self) -> Dict[str, Any]:
        """Interactive custom strategy creation"""
        print("\n" + "="*60)
        print("CUSTOM STRATEGY BUILDER")
        print("="*60)
        
        strategy = {
            'name': '',
            'description': '',
            'type': '',
            'parameters': {},
            'indicators': [],
            'entry_rules': [],
            'exit_rules': [],
            'risk_management': {},
            'created': datetime.now().isoformat()
        }
        
        # Basic info
        strategy['name'] = input("\n[INPUT] Strategy Name: ").strip()
        strategy['description'] = input("[INPUT] Description: ").strip()
        
        # Strategy type
        print("\n🎯 Strategy Type:")
        print("1. Trend Following")
        print("2. Mean Reversion")
        print("3. Momentum")
        print("4. Breakout")
        print("5. ML-Based")
        print("6. Hybrid")
        
        type_choice = input("\nSelect type (1-6): ").strip()
        types = {
            '1': 'trend_following',
            '2': 'mean_reversion',
            '3': 'momentum',
            '4': 'breakout',
            '5': 'ml_based',
            '6': 'hybrid'
        }
        strategy['type'] = types.get(type_choice, 'custom')
        
        # Technical indicators
        print("\n[INFO] Add Technical Indicators (comma separated):")
        print("Available: SMA, EMA, RSI, MACD, Bollinger, ATR, Stochastic, Volume, OBV")
        indicators_input = input("Indicators: ").strip()
        if indicators_input:
            strategy['indicators'] = [ind.strip() for ind in indicators_input.split(',')]
        
        # Parameters
        print("\n⚙️  Strategy Parameters:")
        strategy['parameters']['lookback_period'] = int(input("Lookback period (days): ") or "20")
        strategy['parameters']['holding_period'] = int(input("Max holding period (days): ") or "5")
        
        # Entry rules
        print("\n[ENTRY] Entry Rules (type 'done' when finished):")
        rule_num = 1
        while True:
            rule = input(f"Rule {rule_num}: ").strip()
            if rule.lower() == 'done' or not rule:
                break
            strategy['entry_rules'].append(rule)
            rule_num += 1
        
        # Exit rules
        print("\n[EXIT] Exit Rules (type 'done' when finished):")
        rule_num = 1
        while True:
            rule = input(f"Rule {rule_num}: ").strip()
            if rule.lower() == 'done' or not rule:
                break
            strategy['exit_rules'].append(rule)
            rule_num += 1
        
        # Risk management
        print("\n[RISK] Risk Management:")
        strategy['risk_management']['position_size_pct'] = float(input("Position size (% of capital, default 10): ") or "10")
        strategy['risk_management']['stop_loss_pct'] = float(input("Stop loss (%, default 5): ") or "5")
        strategy['risk_management']['take_profit_pct'] = float(input("Take profit (%, default 15): ") or "15")
        strategy['risk_management']['max_positions'] = int(input("Max concurrent positions (default 5): ") or "5")
        
        # Save strategy
        self.save_strategy(strategy)
        
        print(f"\n[OK] Strategy '{strategy['name']}' created successfully!")
        return strategy
    
    def save_strategy(self, strategy: Dict[str, Any]):
        """Save strategy to JSON file"""
        filename = f"{self.strategies_dir}/{strategy['name'].replace(' ', '_')}.json"
        with open(filename, 'w') as f:
            json.dump(strategy, f, indent=2)
        print(f"[SAVED] Saved to: {filename}")
    
    def load_strategy(self, name: str) -> Dict[str, Any]:
        """Load strategy from JSON file"""
        filename = f"{self.strategies_dir}/{name.replace(' ', '_')}.json"
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return None
    
    def list_strategies(self) -> List[str]:
        """List all saved strategies"""
        if not os.path.exists(self.strategies_dir):
            return []
        files = [f.replace('.json', '').replace('_', ' ') 
                for f in os.listdir(self.strategies_dir) if f.endswith('.json')]
        return sorted(files)
    
    def export_for_live_trading(self, strategy_name: str, export_format: str = 'python'):
        """Export strategy for live trading implementation"""
        strategy = self.load_strategy(strategy_name)
        if not strategy:
            print(f"❌ Strategy '{strategy_name}' not found")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if export_format == 'python':
            self._export_python_class(strategy, timestamp)
        elif export_format == 'json':
            self._export_json_config(strategy, timestamp)
        elif export_format == 'lean':
            self._export_lean_algorithm(strategy, timestamp)
        else:
            print(f"❌ Unknown format: {export_format}")
    
    def _export_python_class(self, strategy: Dict[str, Any], timestamp: str):
        """Export as standalone Python class"""
        # Sanitize name to be a valid Python identifier
        name = sanitize_identifier(strategy['name'])
        # Use export_ prefix to avoid pytest collection
        basename = sanitize_export_basename(strategy['name'], timestamp)
        filename = f"{self.exports_dir}/{basename}.py"
        
        code = f'''"""
{strategy['name']} - {strategy['description']}
Auto-generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

import pandas as pd
import numpy as np
from datetime import datetime

class {name}Strategy:
    """
    Type: {strategy['type']}
    Indicators: {', '.join(strategy['indicators'])}
    """
    
    def __init__(self, symbol: str, initial_capital: float = 100000):
        self.symbol = symbol
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.position = 0
        self.trades = []
        
        # Strategy parameters
        self.lookback = {strategy['parameters'].get('lookback_period', 20)}
        self.holding_period = {strategy['parameters'].get('holding_period', 5)}
        
        # Risk management
        self.position_size_pct = {strategy['risk_management'].get('position_size_pct', 10)} / 100
        self.stop_loss_pct = {strategy['risk_management'].get('stop_loss_pct', 5)} / 100
        self.take_profit_pct = {strategy['risk_management'].get('take_profit_pct', 15)} / 100
        self.max_positions = {strategy['risk_management'].get('max_positions', 5)}
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        # Add your indicator calculations here
        indicators = {strategy['indicators']}
        
        if 'SMA' in indicators:
            df['SMA'] = df['close'].rolling(window=self.lookback).mean()
        
        if 'EMA' in indicators:
            df['EMA'] = df['close'].ewm(span=self.lookback).mean()
        
        if 'RSI' in indicators:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
        
        if 'MACD' in indicators:
            ema12 = df['close'].ewm(span=12).mean()
            ema26 = df['close'].ewm(span=26).mean()
            df['MACD'] = ema12 - ema26
            df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
        
        if 'Bollinger' in indicators:
            df['BB_middle'] = df['close'].rolling(window=20).mean()
            df['BB_std'] = df['close'].rolling(window=20).std()
            df['BB_upper'] = df['BB_middle'] + (2 * df['BB_std'])
            df['BB_lower'] = df['BB_middle'] - (2 * df['BB_std'])
        
        return df
    
    def check_entry_signal(self, df: pd.DataFrame, idx: int) -> bool:
        """
        Entry Rules:
{chr(10).join([f'        # {rule}' for rule in strategy['entry_rules']])}
        """
        # Implement your entry logic here
        return False
    
    def check_exit_signal(self, df: pd.DataFrame, idx: int, entry_price: float, days_held: int) -> bool:
        """
        Exit Rules:
{chr(10).join([f'        # {rule}' for rule in strategy['exit_rules']])}
        """
        current_price = df.iloc[idx]['close']
        
        # Stop loss
        if current_price <= entry_price * (1 - self.stop_loss_pct):
            return True
        
        # Take profit
        if current_price >= entry_price * (1 + self.take_profit_pct):
            return True
        
        # Max holding period
        if days_held >= self.holding_period:
            return True
        
        # Implement your exit logic here
        return False
    
    def backtest(self, data: pd.DataFrame, start_date: str, end_date: str):
        """Run backtest on historical data"""
        df = self.calculate_indicators(data.copy())
        df = df.dropna()
        
        # Filter date range
        df = df[(df.index >= start_date) & (df.index <= end_date)]
        
        equity_curve = []
        entry_price = None
        entry_idx = None
        
        for idx in range(len(df)):
            current_price = df.iloc[idx]['close']
            
            # Check exit
            if self.position > 0 and entry_price:
                days_held = idx - entry_idx
                if self.check_exit_signal(df, idx, entry_price, days_held):
                    # Sell
                    self.cash += self.position * current_price
                    pnl = (current_price - entry_price) * self.position
                    self.trades.append({{
                        'entry_date': df.index[entry_idx],
                        'exit_date': df.index[idx],
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'shares': self.position,
                        'pnl': pnl
                    }})
                    self.position = 0
                    entry_price = None
                    entry_idx = None
            
            # Check entry
            elif self.position == 0:
                if self.check_entry_signal(df, idx):
                    # Buy with fractional share support
                    from sizing import calculate_shares
                    position_value = self.cash * self.position_size_pct
                    shares, _ = calculate_shares(position_value, current_price)
                    if shares > 0:
                        cost = shares * current_price
                        self.cash -= cost
                        self.position = shares
                        entry_price = current_price
                        entry_idx = idx
            
            # Track equity
            portfolio_value = self.cash + (self.position * current_price)
            equity_curve.append(portfolio_value)
        
        # Close any open position
        if self.position > 0:
            final_price = df.iloc[-1]['close']
            self.cash += self.position * final_price
            pnl = (final_price - entry_price) * self.position
            self.trades.append({{
                'entry_date': df.index[entry_idx],
                'exit_date': df.index[-1],
                'entry_price': entry_price,
                'exit_price': final_price,
                'shares': self.position,
                'pnl': pnl
            }})
            self.position = 0
        
        final_value = self.cash
        return df, self.trades, final_value, equity_curve

# Strategy metadata
STRATEGY_INFO = {{
    'name': '{strategy['name']}',
    'type': '{strategy['type']}',
    'created': '{strategy.get('created', 'N/A')}',
    'description': '{strategy['description']}'
}}
'''
        
        with open(filename, 'w') as f:
            f.write(code)
        
        print(f"[OK] Exported Python class to: {filename}")
        print(f"[INPUT] Import with: from {basename} import {name}Strategy")
    
    def _export_json_config(self, strategy: Dict[str, Any], timestamp: str):
        """Export as JSON configuration"""
        # Use export_ prefix to avoid pytest collection
        basename = sanitize_export_basename(strategy['name'], timestamp)
        filename = f"{self.exports_dir}/{basename}_config.json"
        
        config = {
            'strategy': strategy,
            'export_info': {
                'exported_at': datetime.now().isoformat(),
                'format': 'json_config',
                'ready_for_live': True
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"[OK] Exported JSON config to: {filename}")
    
    def _export_lean_algorithm(self, strategy: Dict[str, Any], timestamp: str):
        """Export as QuantConnect LEAN algorithm"""
        # Sanitize name to be a valid Python identifier
        name = sanitize_identifier(strategy['name'])
        # Use export_ prefix to avoid pytest collection
        basename = sanitize_export_basename(strategy['name'], timestamp)
        filename = f"{self.exports_dir}/{basename}_lean.py"
        
        code = f'''"""
{strategy['name']} - LEAN Algorithm
{strategy['description']}
Auto-generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

from AlgorithmImports import *

class {name}Algorithm(QCAlgorithm):
    """
    Type: {strategy['type']}
    Indicators: {', '.join(strategy['indicators'])}
    """
    
    def Initialize(self):
        # Set dates and cash
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)
        
        # Add equity
        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        
        # Strategy parameters
        self.lookback = {strategy['parameters'].get('lookback_period', 20)}
        self.position_size = {strategy['risk_management'].get('position_size_pct', 10)} / 100
        self.stop_loss = {strategy['risk_management'].get('stop_loss_pct', 5)} / 100
        self.take_profit = {strategy['risk_management'].get('take_profit_pct', 15)} / 100
        
        # Initialize indicators
        self.InitializeIndicators()
        
        # Schedule function
        self.Schedule.On(
            self.DateRules.EveryDay(self.symbol),
            self.TimeRules.AfterMarketOpen(self.symbol, 30),
            self.RebalancePortfolio
        )
    
    def InitializeIndicators(self):
        """Initialize technical indicators"""
        indicators = {strategy['indicators']}
        
        if 'SMA' in indicators:
            self.sma = self.SMA(self.symbol, self.lookback)
        
        if 'EMA' in indicators:
            self.ema = self.EMA(self.symbol, self.lookback)
        
        if 'RSI' in indicators:
            self.rsi = self.RSI(self.symbol, 14)
        
        if 'MACD' in indicators:
            self.macd = self.MACD(self.symbol, 12, 26, 9)
        
        if 'Bollinger' in indicators:
            self.bb = self.BB(self.symbol, 20, 2)
    
    def RebalancePortfolio(self):
        """Main trading logic"""
        if not self.IsMarketOpen(self.symbol):
            return
        
        # Entry Rules:
{chr(10).join([f'        # {rule}' for rule in strategy['entry_rules']])}
        
        # Exit Rules:
{chr(10).join([f'        # {rule}' for rule in strategy['exit_rules']])}
        
        holdings = self.Portfolio[self.symbol]
        
        # Implement your trading logic here
        if not holdings.Invested:
            # Check entry signal
            if self.CheckEntrySignal():
                # Use SetHoldings for fractional share support
                self.SetHoldings(self.symbol, self.position_size)
                self.Debug(f"BUY: Set holdings to {{self.position_size*100}}% at {{self.Securities[self.symbol].Price}}")
        else:
            # Check exit signal
            if self.CheckExitSignal():
                self.Liquidate(self.symbol)
                self.Debug(f"SELL: Liquidated at {{self.Securities[self.symbol].Price}}")
    
    def CheckEntrySignal(self) -> bool:
        """Check if entry conditions are met"""
        # Implement entry logic
        return False
    
    def CheckExitSignal(self) -> bool:
        """Check if exit conditions are met"""
        holdings = self.Portfolio[self.symbol]
        current_price = self.Securities[self.symbol].Price
        
        # Stop loss
        if current_price <= holdings.AveragePrice * (1 - self.stop_loss):
            return True
        
        # Take profit
        if current_price >= holdings.AveragePrice * (1 + self.take_profit):
            return True
        
        # Implement exit logic
        return False
    
    def OnData(self, data: Slice):
        """OnData event"""
        pass

# Strategy metadata
# Type: {strategy['type']}
# Created: {strategy.get('created', 'N/A')}
'''
        
        with open(filename, 'w') as f:
            f.write(code)
        
        print(f"[OK] Exported LEAN algorithm to: {filename}")
        print(f"    Upload to QuantConnect or run locally with LEAN CLI")
    
    def compare_strategies(self, strategy_names: List[str], symbol: str, start_date: str, end_date: str):
        """Compare multiple strategies side by side"""
        print(f"\n[INFO] Comparing {len(strategy_names)} strategies on {symbol}")
        print(f"Period: {start_date} to {end_date}")
        print("="*80)
        
        results = []
        for name in strategy_names:
            strategy = self.load_strategy(name)
            if strategy:
                # Would implement backtest here
                print(f"✓ {name}: Type={strategy['type']}, Indicators={len(strategy['indicators'])}")
                results.append(strategy)
        
        return results
