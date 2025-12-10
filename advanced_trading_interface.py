#!/usr/bin/env python3
"""
Advanced Trading Portfolio Manager
Full-featured interface for portfolio management, strategy comparison, and technical analysis
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Optional
from itertools import product
import pandas as pd
import numpy as np
import json
import yfinance as yf
from collections import defaultdict

# Import strategies
from simple_strategy import SimpleMeanReversionStrategy
from ml_strategy import MLTradingStrategy
from optimized_ml_strategy import OptimizedMLStrategy
from short_term_strategy import ShortTermStrategy

# Import enhanced utilities
from enhanced_utils import (
    validate_symbol, validate_days, validate_capital, validate_percentage,
    validate_portfolio_name, check_internet_connection, safe_json_load,
    safe_json_save, calculate_metrics_safe, ProgressTracker, ValidationError,
    NetworkError, download_data_with_retry
)

# Import unified backtest engine
from unified_backtest_engine import UnifiedBacktestEngine

# Import strategy exporter
try:
    from strategy_exporter import StrategyExporter
except ImportError:
    StrategyExporter = None  # Graceful degradation

# Import strategy manager
from strategy_manager import StrategyManager, StrategyConfig, create_strategy_from_execution

# Import new modules
from advanced_settings import AdvancedSettingsManager
from market_analytics import MarketAnalytics
from strategy_optimizer import StrategyOptimizer
from strategy_builder import StrategyBuilder


class Portfolio:
    """Portfolio management class"""
    def __init__(self, name, initial_capital=100000, target_return=None, strategy_allocations=None):
        self.name = name
        self.initial_capital = initial_capital
        self.target_return = target_return
        self.strategy_allocations = strategy_allocations or {}
        self.holdings = {}
        self.performance = []
        self.created_at = datetime.now().isoformat()
        
    def to_dict(self):
        return {
            'name': self.name,
            'initial_capital': self.initial_capital,
            'target_return': self.target_return,
            'strategy_allocations': self.strategy_allocations,
            'holdings': self.holdings,
            'performance': self.performance,
            'created_at': self.created_at
        }
    
    @staticmethod
    def from_dict(data):
        portfolio = Portfolio(
            data['name'],
            data['initial_capital'],
            data.get('target_return'),
            data.get('strategy_allocations', {})
        )
        portfolio.holdings = data.get('holdings', {})
        portfolio.performance = data.get('performance', [])
        portfolio.created_at = data.get('created_at', datetime.now().isoformat())
        return portfolio


class AdvancedTradingInterface:
    def __init__(self):
        self.portfolios = {}
        self.results_history = []
        self.sector_data = self.load_sector_data()
        self.strategy_manager = StrategyManager()
        self.advanced_settings = AdvancedSettingsManager()
        self.strategy_builder = StrategyBuilder()
        self.backtest_engine = UnifiedBacktestEngine()
        self.load_all_data()
        
    def load_sector_data(self):
        """Load sector/industry classifications"""
        return {
            'Technology': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMD', 'INTC'],
            'Finance': ['JPM', 'BAC', 'GS', 'MS', 'C', 'WFC'],
            'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'CVS'],
            'Consumer': ['AMZN', 'TSLA', 'WMT', 'HD', 'NKE', 'SBUX'],
            'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG'],
            'ETFs': ['SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VOO', 'VEA', 'VWO'],
            'Crypto': ['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'ADA-USD']
        }
    
    def load_all_data(self):
        """Load portfolios and history"""
        # Load portfolios
        if os.path.exists('portfolios.json'):
            try:
                with open('portfolios.json', 'r') as f:
                    data = json.load(f)
                    self.portfolios = {name: Portfolio.from_dict(p) for name, p in data.items()}
            except:
                self.portfolios = {}
        
        # Load history
        if os.path.exists('strategy_history.json'):
            try:
                with open('strategy_history.json', 'r') as f:
                    self.results_history = json.load(f)
            except:
                self.results_history = []
    
    def save_all_data(self):
        """Save portfolios and history"""
        # Save portfolios
        portfolio_data = {name: p.to_dict() for name, p in self.portfolios.items()}
        with open('portfolios.json', 'w') as f:
            json.dump(portfolio_data, f, indent=2, default=str)
        
        # Save history
        with open('strategy_history.json', 'w') as f:
            json.dump(self.results_history, f, indent=2, default=str)
    
    def save_portfolio(self, portfolio: Portfolio):
        """Save a single portfolio to file"""
        # Create directory if doesn't exist
        os.makedirs('saved_portfolios', exist_ok=True)
        
        # Save to individual file
        filename = f'saved_portfolios/{portfolio.name}.json'
        with open(filename, 'w') as f:
            json.dump(portfolio.to_dict(), f, indent=2, default=str)
        
        # Also update main portfolios dict and save
        self.portfolios[portfolio.name] = portfolio
        self.save_all_data()
    
    def load_portfolio(self, name: str) -> Optional[Portfolio]:
        """Load a portfolio by name"""
        # Try from memory first
        if name in self.portfolios:
            return self.portfolios[name]
        
        # Try from file
        filename = f'saved_portfolios/{name}.json'
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                portfolio = Portfolio.from_dict(data)
                self.portfolios[name] = portfolio
                return portfolio
            except:
                pass
        
        return None
    
    def clear_screen(self):
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def print_header(self):
        self.clear_screen()
        print("╔" + "═"*88 + "╗")
        print("║" + " "*88 + "║")
        print("║" + "    🚀 ADVANCED TRADING PORTFOLIO MANAGER & STRATEGY ANALYZER 🚀".center(88) + "║")
        print("║" + " "*88 + "║")
        print("╚" + "═"*88 + "╝")
        print()
    
    def print_main_menu(self):
        print("═" * 90)
        print("QUANTITATIVE TRADING PLATFORM - MAIN MENU")
        print("═" * 90)
        print()
        print("📊 CORE STRATEGY OPERATIONS")
        print("  1. Run Single Strategy Backtest")
        print("  2. Run Portfolio Backtest")
        print("  3. Compare Multiple Strategies")
        print("  4. Technical Analysis Dashboard")
        print()
        print("🔨 STRATEGY DEVELOPMENT")
        print("  5. Create Custom Strategy")
        print("  6. Optimize Strategy Parameters")
        print("  7. Market Analytics & Screening")
        print()
        print("💾 MANAGEMENT")
        print("  8. Manage Saved Portfolios")
        print("  9. Manage Saved Strategies")
        print(" 10. Advanced Settings")
        print()
        print("🚀 DEPLOYMENT & REPORTING")
        print(" 11. Export Strategy for Live Trading")
        print(" 12. View Performance Reports")
        print(" 13. Help & Documentation")
        print()
        print("  0. Exit")
        print("═" * 90)
        print()
    
    def get_asset_info(self, symbol):
        """Get basic asset information"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                'name': info.get('longName', symbol),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'price': info.get('currentPrice', 'N/A')
            }
        except:
            return {'name': symbol, 'sector': 'N/A', 'industry': 'N/A', 'price': 'N/A'}
    
    def run_single_strategy(self):
        """Run a strategy on a single asset"""
        print("\n" + "═"*90)
        print("RUN STRATEGY ON SINGLE ASSET")
        print("═"*90)
        
        # Get symbol
        symbol = input("\nEnter symbol (e.g., SPY, AAPL, BTC-USD): ").strip().upper()
        if not symbol:
            return
        
        # Show asset info
        print(f"\n🔍 Fetching info for {symbol}...")
        info = self.get_asset_info(symbol)
        print(f"\n📊 Asset: {info['name']}")
        print(f"   Sector: {info['sector']} | Industry: {info['industry']}")
        
        # Validate data availability first
        try:
            test_data = yf.download(symbol, period='1mo', progress=False)
            if test_data.empty:
                print(f"\n❌ No data available for {symbol}. Please check the symbol and try again.")
                return
        except Exception as e:
            print(f"\n❌ Error fetching data for {symbol}: {e}")
            return
        
        # Choose strategy
        print("\nChoose Strategy:")
        print("1. Simple Mean Reversion")
        print("2. ML Single Model")
        print("3. Optimized Ensemble")
        print("4. Short-Term (7-90 days) ⚡ NEW")
        strategy_choice = input("\nEnter choice (1-4): ").strip()
        
        # Get parameters with strategy-specific minimums (calendar days)
        if strategy_choice == '1':
            min_days = 45  # Simple needs ~30 trading days
            default_days = 180
            note = "(~30 trading days)"
        elif strategy_choice == '2':
            min_days = 130  # ML needs ~90 trading days
            default_days = 365
            note = "(~90 trading days)"
        elif strategy_choice == '3':
            min_days = 250  # Optimized needs many samples after feature creation
            default_days = 730
            note = "(needs extensive data)"
        else:  # Short-term
            min_days = 21  # Short-term needs ~14 trading days
            default_days = 45
            note = "(~14 trading days)"
        
        days = input(f"Lookback period in CALENDAR days (default: {default_days}, min: {min_days} {note}): ").strip()
        days = int(days) if days.isdigit() else default_days
        days = max(min_days, days)  # Ensure minimum period
        
        capital = input("Starting capital (default: 100000): ").strip()
        capital = float(capital) if capital else 100000
        
        # Run strategy
        print(f"\n🔄 Running strategy with {days} days of data...")
        print("⏳ This may take 1-5 minutes depending on the strategy...")
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            if strategy_choice == '1':
                strategy = SimpleMeanReversionStrategy(symbol=symbol, lookback=20, std_dev=2)
                strategy.cash = capital
                data, trades, final_value, equity = strategy.backtest(start_date, end_date)
                strategy.print_results(final_value, trades)
                
                result = {
                    'timestamp': datetime.now().isoformat(),
                    'strategy': 'Simple Mean Reversion',
                    'symbol': symbol,
                    'sector': info['sector'],
                    'period_days': days,
                    'initial_capital': capital,
                    'final_value': final_value,
                    'return_pct': ((final_value - capital) / capital) * 100,
                    'total_trades': len(trades)
                }
                
            elif strategy_choice == '2':
                strategy = MLTradingStrategy(symbol=symbol, lookback=60, prediction_horizon=5)
                strategy.cash = capital
                df_test, trades, final_value, equity = strategy.backtest(start_date, end_date)
                strategy.print_results(final_value, trades, equity)
                
                equity_df = pd.DataFrame(equity)
                if len(equity_df) > 1:
                    equity_df['Returns'] = equity_df['Value'].pct_change()
                    sharpe = (equity_df['Returns'].mean() / equity_df['Returns'].std()) * np.sqrt(252)
                    max_dd = ((equity_df['Value'].cummax() - equity_df['Value']) / equity_df['Value'].cummax()).max() * 100
                else:
                    sharpe, max_dd = 0, 0
                
                wins = sum(1 for i in range(0, len(trades)-1, 2) if i+1 < len(trades) and trades[i+1][2] > trades[i][2])
                win_rate = (wins / (len(trades)//2) * 100) if len(trades) > 0 else 0
                
                result = {
                    'timestamp': datetime.now().isoformat(),
                    'strategy': 'ML Single Model',
                    'symbol': symbol,
                    'sector': info['sector'],
                    'period_days': days,
                    'initial_capital': capital,
                    'final_value': final_value,
                    'return_pct': ((final_value - capital) / capital) * 100,
                    'sharpe_ratio': sharpe,
                    'max_drawdown': max_dd,
                    'total_trades': len(trades),
                    'win_rate': win_rate
                }
                
            elif strategy_choice == '3':
                n_trials = input("Number of optimization trials (default: 20): ").strip()
                n_trials = int(n_trials) if n_trials.isdigit() else 20
                
                strategy = OptimizedMLStrategy(symbol=symbol, lookback=60, prediction_horizon=5)
                strategy.cash = capital
                strategy.initial_cash = capital
                df_test, trades, final_value, equity = strategy.backtest(
                    start_date, end_date, optimize_params=True, n_trials=n_trials
                )
                strategy.print_results(final_value, trades, equity)
                
                equity_df = pd.DataFrame(equity)
                if len(equity_df) > 1:
                    equity_df['Returns'] = equity_df['Value'].pct_change()
                    sharpe = (equity_df['Returns'].mean() / equity_df['Returns'].std()) * np.sqrt(252)
                    max_dd = ((equity_df['Value'].cummax() - equity_df['Value']) / equity_df['Value'].cummax()).max() * 100
                else:
                    sharpe, max_dd = 0, 0
                
                wins = sum(1 for i in range(0, len(trades)-1, 2) if i+1 < len(trades) and trades[i+1][2] > trades[i][2])
                win_rate = (wins / (len(trades)//2) * 100) if len(trades) > 0 else 0
                
                result = {
                    'timestamp': datetime.now().isoformat(),
                    'strategy': 'Optimized Ensemble',
                    'symbol': symbol,
                    'sector': info['sector'],
                    'period_days': days,
                    'initial_capital': capital,
                    'final_value': final_value,
                    'return_pct': ((final_value - capital) / capital) * 100,
                    'sharpe_ratio': sharpe,
                    'max_drawdown': max_dd,
                    'total_trades': len(trades),
                    'win_rate': win_rate,
                    'n_trials': n_trials
                }
                
            elif strategy_choice == '4':
                strategy = ShortTermStrategy(symbol=symbol, fast_period=5, slow_period=15)
                strategy.cash = capital
                df_test, trades, final_value, equity = strategy.backtest(start_date, end_date)
                strategy.print_results(final_value, trades, equity)
                
                equity_df = pd.DataFrame(equity)
                if len(equity_df) > 1:
                    equity_df['Returns'] = equity_df['Value'].pct_change()
                    sharpe = (equity_df['Returns'].mean() / equity_df['Returns'].std()) * np.sqrt(252)
                    max_dd = ((equity_df['Value'].cummax() - equity_df['Value']) / equity_df['Value'].cummax()).max() * 100
                else:
                    sharpe, max_dd = 0, 0
                
                wins = sum(1 for i in range(0, len(trades)-1, 2) if i+1 < len(trades) and trades[i+1][2] > trades[i][2])
                win_rate = (wins / (len(trades)//2) * 100) if len(trades) > 0 else 0
                
                result = {
                    'timestamp': datetime.now().isoformat(),
                    'strategy': 'Short-Term',
                    'symbol': symbol,
                    'sector': info['sector'],
                    'period_days': days,
                    'initial_capital': capital,
                    'final_value': final_value,
                    'return_pct': ((final_value - capital) / capital) * 100,
                    'sharpe_ratio': sharpe,
                    'max_drawdown': max_dd,
                    'total_trades': len(trades),
                    'win_rate': win_rate
                }
            else:
                print("Invalid choice!")
                return
            
            self.results_history.append(result)
            self.save_all_data()
            
        except Exception as e:
            print(f"\n❌ Error running strategy: {e}")
    
    def compare_all_strategies(self):
        """Compare all strategies on same symbol"""
        print("\n" + "═"*90)
        print("COMPARE ALL STRATEGIES ON SAME ASSET")
        print("═"*90)
        
        # Get symbol
        symbol = input("\nEnter symbol to compare (e.g., SPY, AAPL, BTC-USD): ").strip().upper()
        if not symbol:
            return
        
        # Validate symbol
        print(f"\n🔍 Validating {symbol}...")
        try:
            test_data = yf.download(symbol, period='1mo', progress=False)
            if test_data.empty:
                print(f"❌ No data available for {symbol}")
                return
        except Exception as e:
            print(f"❌ Error: {e}")
            return
        
        # Get period
        days = input("\nTest period in calendar days (default: 180, min: 365 for Optimized): ").strip()
        days = int(days) if days.isdigit() else 180
        days = max(180, days)
        
        # Get capital
        capital = input("Starting capital (default: 100000): ").strip()
        capital = float(capital) if capital else 100000
        
        print(f"\n🔄 Comparing all strategies on {symbol}...")
        print("⏳ This will take 3-5 minutes for all 4 strategies...")
        print()
        
        results = []
        
        # Test 1: Short-Term
        print("1/4 Testing Short-Term Strategy...")
        try:
            strategy = ShortTermStrategy(symbol)
            strategy.cash = capital
            end = datetime.now()
            start = end - timedelta(days=min(days, 90))  # Cap at 90 for short-term
            
            data, trades, final, equity = strategy.backtest(start, end)
            
            metrics = self.safe_calculate_metrics(equity)
            results.append({
                'strategy': 'Short-Term',
                'final_value': final,
                'return_pct': ((final - capital) / capital) * 100,
                'sharpe': metrics.get('sharpe', 0),
                'max_dd': metrics.get('max_dd', 0),
                'trades': len(trades),
                'period': min(days, 90)
            })
            print(f"   ✅ Complete: {results[-1]['return_pct']:.2f}% return")
        except Exception as e:
            print(f"   ❌ Failed: {str(e)[:80]}")
            results.append({
                'strategy': 'Short-Term',
                'error': str(e)[:100]
            })
        
        # Test 2: Simple
        print("\n2/4 Testing Simple Mean Reversion...")
        try:
            strategy = SimpleMeanReversionStrategy(symbol, lookback=20, std_dev=2)
            strategy.cash = capital
            end = datetime.now()
            start = end - timedelta(days=days)
            
            data, trades, final, equity = strategy.backtest(start, end)
            
            # Calculate equity curve from trades
            equity_curve = []
            current_value = capital
            for i, trade in enumerate(trades):
                if i % 2 == 1:  # Sell trades
                    current_value = capital + (trade[2] - trades[i-1][2]) * trade[3]
                equity_curve.append({'Date': trade[0], 'Value': current_value})
            
            metrics = self.safe_calculate_metrics(equity_curve) if equity_curve else {'sharpe': 0, 'max_dd': 0}
            results.append({
                'strategy': 'Simple',
                'final_value': final,
                'return_pct': ((final - capital) / capital) * 100,
                'sharpe': metrics.get('sharpe', 0),
                'max_dd': metrics.get('max_dd', 0),
                'trades': len(trades),
                'period': days
            })
            print(f"   ✅ Complete: {results[-1]['return_pct']:.2f}% return")
        except Exception as e:
            print(f"   ❌ Failed: {str(e)[:80]}")
            results.append({
                'strategy': 'Simple',
                'error': str(e)[:100]
            })
        
        # Test 3: ML
        print("\n3/4 Testing ML Single Model (suppressing output)...")
        try:
            import sys, io
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            strategy = MLTradingStrategy(symbol, lookback=60, prediction_horizon=5)
            strategy.cash = capital
            end = datetime.now()
            start = end - timedelta(days=days)
            
            df_test, trades, final, equity = strategy.backtest(start, end)
            
            sys.stdout = old_stdout
            
            metrics = self.safe_calculate_metrics(equity)
            results.append({
                'strategy': 'ML Single',
                'final_value': final,
                'return_pct': ((final - capital) / capital) * 100,
                'sharpe': metrics.get('sharpe', 0),
                'max_dd': metrics.get('max_dd', 0),
                'trades': len(trades),
                'period': days
            })
            print(f"   ✅ Complete: {results[-1]['return_pct']:.2f}% return")
        except Exception as e:
            sys.stdout = old_stdout
            print(f"   ❌ Failed: {str(e)[:80]}")
            results.append({
                'strategy': 'ML Single',
                'error': str(e)[:100]
            })
        
        # Test 4: Optimized (if period allows)
        if days >= 365:
            print("\n4/4 Testing Optimized Ensemble (3 trials, suppressing output)...")
            try:
                import sys, io
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                
                strategy = OptimizedMLStrategy(symbol, lookback=60, prediction_horizon=5)
                strategy.cash = capital
                strategy.initial_cash = capital
                end = datetime.now()
                start = end - timedelta(days=days)
                
                df_test, trades, final, equity = strategy.backtest(start, end, optimize_params=True, n_trials=3)
                
                sys.stdout = old_stdout
                
                metrics = self.safe_calculate_metrics(equity)
                results.append({
                    'strategy': 'Optimized',
                    'final_value': final,
                    'return_pct': ((final - capital) / capital) * 100,
                    'sharpe': metrics.get('sharpe', 0),
                    'max_dd': metrics.get('max_dd', 0),
                    'trades': len(trades),
                    'period': days
                })
                print(f"   ✅ Complete: {results[-1]['return_pct']:.2f}% return")
            except Exception as e:
                sys.stdout = old_stdout
                print(f"   ❌ Failed: {str(e)[:80]}")
                results.append({
                    'strategy': 'Optimized',
                    'error': str(e)[:100]
                })
        else:
            print(f"\n4/4 Skipping Optimized (needs 365+ days, got {days})")
        
        # Display comparison table
        print("\n" + "═"*90)
        print(f"STRATEGY COMPARISON RESULTS - {symbol}")
        print("═"*90)
        
        successful_results = [r for r in results if 'error' not in r]
        failed_results = [r for r in results if 'error' in r]
        
        if successful_results:
            print(f"\n{'Strategy':<20} {'Return':>10} {'Sharpe':>10} {'Max DD':>10} {'Trades':>10} {'Period':>10}")
            print("-"*90)
            
            for r in sorted(successful_results, key=lambda x: x['return_pct'], reverse=True):
                print(f"{r['strategy']:<20} {r['return_pct']:>9.2f}% {r['sharpe']:>10.2f} {r['max_dd']:>9.2f}% {r['trades']:>10} {r['period']:>9}d")
            
            print("═"*90)
            
            # Highlight winner
            best = max(successful_results, key=lambda x: x['return_pct'])
            best_sharpe = max(successful_results, key=lambda x: x['sharpe'])
            
            print(f"\n🏆 Best Return:       {best['strategy']} ({best['return_pct']:.2f}%)")
            print(f"🏆 Best Risk-Adjusted: {best_sharpe['strategy']} (Sharpe: {best_sharpe['sharpe']:.2f})")
        
        if failed_results:
            print("\n❌ Failed Strategies:")
            for r in failed_results:
                print(f"   {r['strategy']}: {r['error']}")
        
        print("\n" + "═"*90)
        
        # Save comparison to history
        comparison_record = {
            'timestamp': datetime.now().isoformat(),
            'type': 'comparison',
            'symbol': symbol,
            'period_days': days,
            'capital': capital,
            'results': successful_results
        }
        self.results_history.append(comparison_record)
        self.save_all_data()
    
    def safe_calculate_metrics(self, equity_curve):
        """Safely calculate metrics"""
        try:
            if not equity_curve or len(equity_curve) < 2:
                return {'sharpe': 0, 'max_dd': 0}
            
            df = pd.DataFrame(equity_curve)
            df['Returns'] = df['Value'].pct_change()
            
            sharpe = (df['Returns'].mean() / df['Returns'].std()) * np.sqrt(252) if df['Returns'].std() > 0 else 0
            max_dd = ((df['Value'].cummax() - df['Value']) / df['Value'].cummax()).max() * 100
            
            return {
                'sharpe': float(sharpe) if not pd.isna(sharpe) else 0,
                'max_dd': float(max_dd) if not pd.isna(max_dd) else 0
            }
        except:
            return {'sharpe': 0, 'max_dd': 0}
    
    def batch_test_strategies(self):
        """Test strategies across multiple assets"""
        print("\n" + "═"*90)
        print("BATCH TEST STRATEGIES")
        print("═"*90)
        
        print("\nChoose asset selection:")
        print("1. Enter symbols manually")
        print("2. Select by sector")
        print("3. Load from watchlist")
        
        choice = input("\nChoice (1-3): ").strip()
        
        symbols = []
        if choice == '1':
            symbols_input = input("Enter symbols separated by commas (e.g., SPY,QQQ,AAPL): ").strip().upper()
            symbols = [s.strip() for s in symbols_input.split(',')]
        elif choice == '2':
            print("\nAvailable sectors:")
            for i, sector in enumerate(self.sector_data.keys(), 1):
                print(f"{i}. {sector}")
            sector_choice = input("\nChoose sector: ").strip()
            try:
                sector_name = list(self.sector_data.keys())[int(sector_choice)-1]
                symbols = self.sector_data[sector_name][:5]  # Limit to 5 for speed
                print(f"\nTesting: {', '.join(symbols)}")
            except:
                print("Invalid choice")
                return
        elif choice == '3':
            # Load from watchlist
            watchlists = safe_json_load('watchlists.json', {})
            if not watchlists:
                print("\n❌ No watchlists available. Create one first (Option 16).")
                return
            
            print("\nAvailable watchlists:")
            for i, name in enumerate(watchlists.keys(), 1):
                print(f"{i}. {name} ({len(watchlists[name])} symbols)")
            
            wl_choice = input("\nChoose watchlist: ").strip()
            try:
                wl_name = list(watchlists.keys())[int(wl_choice)-1]
                symbols = watchlists[wl_name][:10]  # Limit to 10 for performance
                print(f"\n✅ Loaded {len(symbols)} symbols from '{wl_name}'")
            except:
                print("Invalid choice")
                return
        else:
            print("Invalid choice")
            return
        
        if not symbols:
            print("❌ No symbols to test")
            return
        
        # Validate all symbols first
        print(f"\n🔍 Validating {len(symbols)} symbols...")
        valid_symbols = []
        for sym in symbols:
            try:
                sym = validate_symbol(sym)
                # Quick check if data is available
                test_data = yf.download(sym, period='5d', progress=False)
                if not test_data.empty:
                    valid_symbols.append(sym)
                else:
                    print(f"  ⚠️  {sym}: No data available")
            except ValidationError as e:
                print(f"  ❌ {sym}: {e}")
            except:
                print(f"  ⚠️  {sym}: Validation failed")
        
        if not valid_symbols:
            print("\n❌ No valid symbols to test")
            return
        
        print(f"✅ {len(valid_symbols)}/{len(symbols)} symbols valid\n")
        symbols = valid_symbols
        
        # Choose strategy for batch testing
        print("\nChoose strategy for batch test:")
        print("1. Short-Term (fast)")
        print("2. Simple (fast)")
        print("3. ML Single (medium)")
        strategy_choice = input("\nChoice (1-3, default: 1): ").strip() or '1'
        
        # Get period
        if strategy_choice == '1':
            default_days = 45
            min_days = 21
        elif strategy_choice == '2':
            default_days = 90
            min_days = 45
        else:
            default_days = 180
            min_days = 130
        
        days = input(f"\nTest period in days (default: {default_days}, min: {min_days}): ").strip()
        days = int(days) if days.isdigit() else default_days
        days = max(min_days, days)
        
        print(f"\n🔄 Testing {len(symbols)} symbols with {days}-day period...")
        print("This may take several minutes...\n")
        
        results = []
        for i, symbol in enumerate(symbols, 1):
            print(f"{i}/{len(symbols)} Testing {symbol}...")
            try:
                import sys, io
                # Suppress output for cleaner display
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                if strategy_choice == '1':
                    strategy = ShortTermStrategy(symbol)
                    strategy.cash = 100000
                    data, trades, final_value, equity = strategy.backtest(start_date, end_date)
                    
                elif strategy_choice == '2':
                    strategy = SimpleMeanReversionStrategy(symbol, lookback=20)
                    strategy.cash = 100000
                    data, trades, final_value, equity = strategy.backtest(start_date, end_date)
                    
                else:  # ML
                    strategy = MLTradingStrategy(symbol, lookback=60, prediction_horizon=5)
                    strategy.cash = 100000
                    df_test, trades, final_value, equity = strategy.backtest(start_date, end_date)
                
                sys.stdout = old_stdout
                
                equity_df = pd.DataFrame(equity)
                if len(equity_df) > 1:
                    equity_df['Returns'] = equity_df['Value'].pct_change()
                    sharpe = (equity_df['Returns'].mean() / equity_df['Returns'].std()) * np.sqrt(252)
                else:
                    sharpe = 0
                
                results.append({
                    'symbol': symbol,
                    'final_value': final_value,
                    'return_pct': ((final_value - 100000) / 100000) * 100,
                    'sharpe': sharpe,
                    'trades': len(trades)
                })
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        # Print results table
        print("\n" + "═"*90)
        print("BATCH TEST RESULTS")
        print("═"*90)
        print(f"\n{'Symbol':<10} {'Final Value':>15} {'Return':>10} {'Sharpe':>10} {'Trades':>10}")
        print("-"*90)
        
        for r in sorted(results, key=lambda x: x['return_pct'], reverse=True):
            print(f"{r['symbol']:<10} ${r['final_value']:>14,.2f} {r['return_pct']:>9.2f}% {r['sharpe']:>9.2f} {r['trades']:>10}")
        
        print("═"*90)
        
        if results:
            best = max(results, key=lambda x: x['return_pct'])
            print(f"\n🏆 Best Performer: {best['symbol']} ({best['return_pct']:.2f}% return)")
    
    def sector_analysis(self):
        """Analyze by sector/industry"""
        print("\n" + "═"*90)
        print("SECTOR/INDUSTRY ANALYSIS")
        print("═"*90)
        
        print("\nAvailable sectors:")
        for i, sector in enumerate(self.sector_data.keys(), 1):
            print(f"{i}. {sector}")
        
        choice = input("\nChoose sector to analyze: ").strip()
        try:
            sector_name = list(self.sector_data.keys())[int(choice)-1]
            symbols = self.sector_data[sector_name]
        except:
            print("Invalid choice")
            return
        
        print(f"\n📊 Analyzing {sector_name} Sector")
        print(f"Symbols: {', '.join(symbols[:10])}")
        
        # Choose analysis type
        print("\nAnalysis Options:")
        print("1. Quick Overview (3 symbols, Short-Term strategy)")
        print("2. Detailed Analysis (5 symbols, Simple strategy)")
        print("3. Full Sector Scan (all symbols, may take time)")
        
        analysis_type = input("\nChoice (1-3): ").strip() or '1'
        
        if analysis_type == '1':
            test_symbols = symbols[:3]
            days = 45
            strategy_type = 'short'
        elif analysis_type == '2':
            test_symbols = symbols[:5]
            days = 90
            strategy_type = 'simple'
        else:
            test_symbols = symbols[:10]
            days = 90
            strategy_type = 'simple'
        
        print(f"\n🔄 Testing {len(test_symbols)} symbols from {sector_name}...")
        print(f"Period: {days} days\n")
        
        results = []
        for i, symbol in enumerate(test_symbols, 1):
            print(f"{i}/{len(test_symbols)} {symbol}...", end=" ")
            try:
                import sys, io
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                
                end = datetime.now()
                start = end - timedelta(days=days)
                
                if strategy_type == 'short':
                    strategy = ShortTermStrategy(symbol)
                else:
                    strategy = SimpleMeanReversionStrategy(symbol, lookback=20)
                
                strategy.cash = 100000
                
                if strategy_type == 'short':
                    data, trades, final, equity = strategy.backtest(start, end)
                else:
                    data, trades, final, equity = strategy.backtest(start, end)
                    equity = []
                
                sys.stdout = old_stdout
                
                ret = ((final - 100000) / 100000) * 100
                results.append({
                    'symbol': symbol,
                    'return': ret,
                    'final': final,
                    'trades': len(trades)
                })
                print(f"✅ {ret:>6.2f}%")
            except Exception as e:
                sys.stdout = old_stdout
                print(f"❌ {str(e)[:30]}")
        
        # Display sector analysis
        print("\n" + "=" * 80)
        print(f"SECTOR ANALYSIS: {sector_name}")
        print("=" * 80)
        
        if results:
            print(f"\n{'Symbol':<10} {'Return':>10} {'Final Value':>15} {'Trades':>10}")
            print("-" * 80)
            
            for r in sorted(results, key=lambda x: x['return'], reverse=True):
                print(f"{r['symbol']:<10} {r['return']:>9.2f}% ${r['final']:>14,.2f} {r['trades']:>10}")
            
            # Calculate sector metrics
            avg_return = sum(r['return'] for r in results) / len(results)
            best = max(results, key=lambda x: x['return'])
            worst = min(results, key=lambda x: x['return'])
            
            print("\n" + "-" * 80)
            print(f"Sector Average:  {avg_return:>9.2f}%")
            print(f"Best Performer:  {best['symbol']:<10} ({best['return']:>6.2f}%)")
            print(f"Worst Performer: {worst['symbol']:<10} ({worst['return']:>6.2f}%)")
            print(f"Spread:          {best['return'] - worst['return']:>9.2f}%")
            
            # Sector recommendation
            print("\n" + "=" * 80)
            if avg_return > 5:
                print("💹 SECTOR OUTLOOK: Strong - Consider overweight")
            elif avg_return > 0:
                print("📊 SECTOR OUTLOOK: Positive - Consider neutral weight")
            elif avg_return > -5:
                print("⚠️  SECTOR OUTLOOK: Weak - Consider underweight")
            else:
                print("⛔ SECTOR OUTLOOK: Poor - Consider avoiding")
            
            print("=" * 80)
        else:
            print("\n❌ No successful tests in sector")
        
        # Save sector analysis
        sector_record = {
            'timestamp': datetime.now().isoformat(),
            'type': 'sector_analysis',
            'sector': sector_name,
            'period_days': days,
            'results': results,
            'average_return': avg_return if results else 0
        }
        self.results_history.append(sector_record)
        self.save_all_data()
    
    def create_portfolio(self):
        """Create a new portfolio"""
        print("\n" + "═"*90)
        print("CREATE NEW PORTFOLIO")
        print("═"*90)
        
        name = input("\nPortfolio name: ").strip()
        if not name or name in self.portfolios:
            print("Invalid or duplicate name!")
            return
        
        capital = input("Initial capital (default: 100000): ").strip()
        capital = float(capital) if capital else 100000
        
        target = input("Target return % (optional): ").strip()
        target = float(target) if target else None
        
        print("\nStrategy Allocations:")
        print("Enter percentage for each strategy (total should be 100)")
        
        simple_pct = input("Simple Mean Reversion %: ").strip()
        ml_pct = input("ML Single Model %: ").strip()
        optimized_pct = input("Optimized Ensemble %: ").strip()
        
        allocations = {
            'Simple': float(simple_pct) if simple_pct else 0,
            'ML': float(ml_pct) if ml_pct else 0,
            'Optimized': float(optimized_pct) if optimized_pct else 0
        }
        
        total = sum(allocations.values())
        if abs(total - 100) > 0.01 and total > 0:
            print(f"\n⚠️  Warning: Allocations sum to {total}%, adjusting to 100%")
            allocations = {k: (v/total)*100 for k, v in allocations.items()}
        
        portfolio = Portfolio(name, capital, target, allocations)
        self.portfolios[name] = portfolio
        self.save_all_data()
        
        print(f"\n✅ Portfolio '{name}' created!")
        print(f"   Capital: ${capital:,.2f}")
        print(f"   Allocations: {allocations}")
    
    def view_portfolios(self):
        """View all portfolios"""
        print("\n" + "═"*90)
        print("ALL PORTFOLIOS")
        print("═"*90)
        
        if not self.portfolios:
            print("\nNo portfolios yet. Create one first!")
            return
        
        for name, portfolio in self.portfolios.items():
            print(f"\n📊 {name}")
            print(f"   Capital: ${portfolio.initial_capital:,.2f}")
            print(f"   Target Return: {portfolio.target_return}%" if portfolio.target_return else "   Target Return: Not set")
            print(f"   Allocations: {portfolio.strategy_allocations}")
            print(f"   Created: {portfolio.created_at[:10]}")
    
    def run_portfolio_backtest(self):
        """Run portfolio backtest"""
        print("\n" + "═"*90)
        print("PORTFOLIO BACKTEST")
        print("═"*90)
        
        if not self.portfolios:
            print("\nNo portfolios yet. Create one first!")
            return
        
        # List portfolios
        portfolio_list = list(self.portfolios.keys())
        print("\nAvailable portfolios:")
        for i, name in enumerate(portfolio_list, 1):
            print(f"{i}. {name}")
        
        choice = input("\nChoose portfolio number: ").strip()
        try:
            portfolio_name = portfolio_list[int(choice)-1]
            portfolio = self.portfolios[portfolio_name]
        except:
            print("Invalid choice!")
            return
        
        # Get symbol and parameters
        symbol = input("Enter symbol to test (e.g., SPY): ").strip().upper() or 'SPY'
        days = input("Lookback period in days (default: 365, min: 120): ").strip()
        days = int(days) if days.isdigit() else 365
        days = max(120, days)  # Portfolio backtesting needs at least 120 days
        
        print(f"\n🔄 Running portfolio backtest on {symbol}...")
        print("⏳ This will test each strategy according to portfolio allocation...")
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            results = {}
            total_value = 0
            
            # Run each strategy with allocation
            allocations = portfolio.strategy_allocations
            
            if allocations.get('Simple', 0) > 0:
                print(f"\n→ Testing Simple strategy ({allocations['Simple']:.0f}%)...")
                capital_allocated = portfolio.initial_capital * (allocations['Simple'] / 100)
                strategy = SimpleMeanReversionStrategy(symbol=symbol, lookback=20, std_dev=2)
                
                result = self.backtest_engine.run_backtest(
                    strategy=strategy,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=capital_allocated
                )
                
                results['Simple'] = {
                    'allocation': allocations['Simple'],
                    'initial': capital_allocated,
                    'final': result.final_value,
                    'return_pct': result.total_return,
                    'trades': len(result.trades)
                }
                total_value += result.final_value
                print(f"   Result: ${capital_allocated:,.0f} → ${result.final_value:,.0f} ({result.total_return:.2f}%)")
            
            if allocations.get('ML', 0) > 0:
                print(f"\n→ Testing ML strategy ({allocations['ML']:.0f}%)...")
                capital_allocated = portfolio.initial_capital * (allocations['ML'] / 100)
                strategy = MLTradingStrategy(symbol=symbol, lookback=60, prediction_horizon=5)
                
                result = self.backtest_engine.run_backtest(
                    strategy=strategy,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=capital_allocated
                )
                
                results['ML'] = {
                    'allocation': allocations['ML'],
                    'initial': capital_allocated,
                    'final': result.final_value,
                    'return_pct': result.total_return,
                    'trades': len(result.trades)
                }
                total_value += result.final_value
                print(f"   Result: ${capital_allocated:,.0f} → ${result.final_value:,.0f} ({result.total_return:.2f}%)")
            
            if allocations.get('Optimized', 0) > 0:
                print(f"\n→ Testing Optimized strategy ({allocations['Optimized']:.0f}%)...")
                capital_allocated = portfolio.initial_capital * (allocations['Optimized'] / 100)
                strategy = OptimizedMLStrategy(symbol=symbol, lookback=60, prediction_horizon=5)
                
                result = self.backtest_engine.run_backtest(
                    strategy=strategy,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=capital_allocated,
                    optimize_params=True,
                    n_trials=10
                )
                
                results['Optimized'] = {
                    'allocation': allocations['Optimized'],
                    'initial': capital_allocated,
                    'final': result.final_value,
                    'return_pct': result.total_return,
                    'trades': len(result.trades)
                }
                total_value += result.final_value
                print(f"   Result: ${capital_allocated:,.0f} → ${result.final_value:,.0f} ({result.total_return:.2f}%)")
            
            # Print portfolio summary
            portfolio_return = ((total_value - portfolio.initial_capital) / portfolio.initial_capital) * 100
            
            print("\n" + "="*60)
            print(f"PORTFOLIO BACKTEST RESULTS - {portfolio_name}")
            print("="*60)
            print(f"\nInitial Capital: ${portfolio.initial_capital:,.2f}")
            print(f"Final Value:     ${total_value:,.2f}")
            print(f"Total Return:    {portfolio_return:.2f}%")
            
            if portfolio.target_return:
                if portfolio_return >= portfolio.target_return:
                    print(f"Target Return:   {portfolio.target_return}% ✅ ACHIEVED")
                else:
                    print(f"Target Return:   {portfolio.target_return}% ❌ Not achieved")
            
            print("\nStrategy Breakdown:")
            print("-"*60)
            for strategy_name, result in results.items():
                print(f"{strategy_name:>10}: {result['allocation']:>5.1f}% | ${result['initial']:>10,.0f} → ${result['final']:>10,.0f} | {result['return_pct']:>6.2f}%")
            
            print("="*60)
            
            # Save to portfolio performance
            portfolio.performance.append({
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'period_days': days,
                'total_return': portfolio_return,
                'final_value': total_value,
                'results': results
            })
            self.save_all_data()
            
        except Exception as e:
            print(f"\n❌ Error running portfolio backtest: {e}")
            import traceback
            traceback.print_exc()
    
    def technical_analysis_dashboard(self):
        """Technical analysis tools"""
        print("\n" + "═"*90)
        print("TECHNICAL ANALYSIS DASHBOARD")
        print("═"*90)
        
        symbol = input("\nEnter symbol to analyze: ").strip().upper()
        if not symbol:
            return
        
        print(f"\n📈 Analyzing {symbol}...")
        print("\nFetching data...")
        
        try:
            # Download data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")
            
            if hist.empty:
                print("No data available")
                return
            
            # Calculate indicators
            close = hist['Close']
            
            # Moving averages
            sma_20 = close.rolling(window=20).mean().iloc[-1]
            sma_50 = close.rolling(window=50).mean().iloc[-1]
            sma_200 = close.rolling(window=200).mean().iloc[-1]
            
            # RSI
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = (100 - (100 / (1 + rs))).iloc[-1]
            
            # Volatility
            volatility = close.pct_change().std() * np.sqrt(252) * 100
            
            # Current price
            current = close.iloc[-1]
            
            # Print analysis
            print("\n" + "="*60)
            print(f"TECHNICAL ANALYSIS - {symbol}")
            print("="*60)
            print(f"\n💰 Current Price: ${current:.2f}")
            print(f"\n📊 Moving Averages:")
            print(f"   SMA(20):  ${sma_20:.2f} | {'🟢 Above' if current > sma_20 else '🔴 Below'}")
            print(f"   SMA(50):  ${sma_50:.2f} | {'🟢 Above' if current > sma_50 else '🔴 Below'}")
            print(f"   SMA(200): ${sma_200:.2f} | {'🟢 Above' if current > sma_200 else '🔴 Below'}")
            
            print(f"\n📉 RSI(14): {rsi:.2f}")
            if rsi > 70:
                print("   🔴 Overbought")
            elif rsi < 30:
                print("   🟢 Oversold")
            else:
                print("   ⚪ Neutral")
            
            print(f"\n📊 Volatility: {volatility:.2f}%")
            
            # Price change
            day_change = ((current - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            week_change = ((current - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5]) * 100 if len(hist) >= 5 else 0
            month_change = ((current - hist['Close'].iloc[-21]) / hist['Close'].iloc[-21]) * 100 if len(hist) >= 21 else 0
            
            print(f"\n📈 Performance:")
            print(f"   1 Day:   {day_change:>6.2f}%")
            print(f"   1 Week:  {week_change:>6.2f}%")
            print(f"   1 Month: {month_change:>6.2f}%")
            
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    def view_history(self):
        """View all results history"""
        print("\n" + "═"*90)
        print("RESULTS HISTORY")
        print("═"*90)
        
        if not self.results_history:
            print("\nNo history yet!")
            return
        
        print(f"\nTotal runs: {len(self.results_history)}")
        print("\nRecent 20 runs:")
        print("-"*90)
        
        for i, r in enumerate(self.results_history[-20:], 1):
            timestamp = datetime.fromisoformat(r['timestamp']).strftime('%Y-%m-%d %H:%M')
            strategy = r['strategy'][:20]
            symbol = r['symbol']
            return_pct = r.get('return_pct', 0)
            print(f"{i:2d}. [{timestamp}] {strategy:<20} {symbol:<8} {return_pct:>7.2f}%")
    
    def compare_portfolios(self):
        """Compare portfolio performance"""
        print("\n" + "═"*90)
        print("COMPARE PORTFOLIOS")
        print("═"*90)
        
        if len(self.portfolios) < 2:
            print("\nNeed at least 2 portfolios to compare!")
            return
        
        print("\nPortfolios with performance history:")
        portfolios_with_perf = [(name, p) for name, p in self.portfolios.items() if p.performance]
        
        if not portfolios_with_perf:
            print("\nNo portfolios have been backtested yet!")
            print("Run option 7 to backtest portfolios first.")
            return
        
        for i, (name, p) in enumerate(portfolios_with_perf, 1):
            latest_perf = p.performance[-1] if p.performance else {}
            print(f"{i}. {name} - Last return: {latest_perf.get('total_return', 0):.2f}%")
        
        print("\n" + "="*60)
        print(f"{'Portfolio':<20} {'Capital':>12} {'Target':>8} {'Best Return':>12}")
        print("-"*60)
        
        for name, p in portfolios_with_perf:
            best_return = max([perf['total_return'] for perf in p.performance]) if p.performance else 0
            target_str = f"{p.target_return}%" if p.target_return else "N/A"
            print(f"{name:<20} ${p.initial_capital:>11,.0f} {target_str:>8} {best_return:>11.2f}%")
        
        print("="*60)
    
    def edit_portfolio(self):
        """Edit portfolio allocations"""
        print("\n" + "═"*90)
        print("EDIT PORTFOLIO")
        print("═"*90)
        
        if not self.portfolios:
            print("\nNo portfolios to edit!")
            return
        
        portfolio_list = list(self.portfolios.keys())
        print("\nAvailable portfolios:")
        for i, name in enumerate(portfolio_list, 1):
            print(f"{i}. {name}")
        
        choice = input("\nChoose portfolio to edit: ").strip()
        try:
            portfolio_name = portfolio_list[int(choice)-1]
            portfolio = self.portfolios[portfolio_name]
        except:
            print("Invalid choice!")
            return
        
        print(f"\nEditing: {portfolio_name}")
        print(f"Current allocations: {portfolio.strategy_allocations}")
        
        print("\nEnter new allocations (or press Enter to keep current):")
        
        simple_pct = input(f"Simple Mean Reversion % (current: {portfolio.strategy_allocations.get('Simple', 0)}): ").strip()
        ml_pct = input(f"ML Single Model % (current: {portfolio.strategy_allocations.get('ML', 0)}): ").strip()
        optimized_pct = input(f"Optimized Ensemble % (current: {portfolio.strategy_allocations.get('Optimized', 0)}): ").strip()
        
        if simple_pct or ml_pct or optimized_pct:
            allocations = {
                'Simple': float(simple_pct) if simple_pct else portfolio.strategy_allocations.get('Simple', 0),
                'ML': float(ml_pct) if ml_pct else portfolio.strategy_allocations.get('ML', 0),
                'Optimized': float(optimized_pct) if optimized_pct else portfolio.strategy_allocations.get('Optimized', 0)
            }
            
            total = sum(allocations.values())
            if abs(total - 100) > 0.01 and total > 0:
                print(f"\n⚠️  Warning: Allocations sum to {total}%, normalizing to 100%")
                allocations = {k: (v/total)*100 for k, v in allocations.items()}
            
            portfolio.strategy_allocations = allocations
            self.save_all_data()
            print(f"\n✅ Portfolio updated!")
            print(f"New allocations: {allocations}")
        else:
            print("\nNo changes made.")
    
    def delete_portfolio(self):
        """Delete a portfolio"""
        print("\n" + "═"*90)
        print("DELETE PORTFOLIO")
        print("═"*90)
        
        if not self.portfolios:
            print("\nNo portfolios to delete!")
            return
        
        portfolio_list = list(self.portfolios.keys())
        print("\nAvailable portfolios:")
        for i, name in enumerate(portfolio_list, 1):
            print(f"{i}. {name}")
        
        choice = input("\nChoose portfolio to delete: ").strip()
        try:
            portfolio_name = portfolio_list[int(choice)-1]
        except:
            print("Invalid choice!")
            return
        
        confirm = input(f"\n⚠️  Are you sure you want to delete '{portfolio_name}'? (yes/no): ").strip().lower()
        if confirm == 'yes':
            del self.portfolios[portfolio_name]
            self.save_all_data()
            print(f"\n✅ Portfolio '{portfolio_name}' deleted!")
        else:
            print("\nCancelled.")
    
    def filter_results(self):
        """Filter and search results history"""
        print("\n" + "═"*90)
        print("FILTER RESULTS")
        print("═"*90)
        
        if not self.results_history:
            print("\nNo results to filter!")
            return
        
        print(f"\nTotal results: {len(self.results_history)}")
        print("\nFilter by:")
        print("1. Symbol")
        print("2. Strategy")
        print("3. Date range")
        print("4. Return % (min/max)")
        print("5. Show all")
        
        choice = input("\nChoice (1-5): ").strip()
        
        filtered = self.results_history.copy()
        
        if choice == '1':
            symbol = input("Enter symbol to filter: ").strip().upper()
            filtered = [r for r in filtered if r.get('symbol', '').upper() == symbol]
            filter_desc = f"Symbol: {symbol}"
            
        elif choice == '2':
            print("\nStrategies:")
            print("1. Short-Term")
            print("2. Simple")
            print("3. ML Single")
            print("4. Optimized")
            strat_choice = input("Choice: ").strip()
            strategy_map = {'1': 'Short-Term', '2': 'Simple', '3': 'ML Single', '4': 'Optimized'}
            strategy_name = strategy_map.get(strat_choice, '')
            filtered = [r for r in filtered if r.get('strategy', '') == strategy_name]
            filter_desc = f"Strategy: {strategy_name}"
            
        elif choice == '3':
            days_back = input("Show results from last N days (default: 7): ").strip()
            days_back = int(days_back) if days_back.isdigit() else 7
            cutoff = datetime.now() - timedelta(days=days_back)
            filtered = [r for r in filtered if datetime.fromisoformat(r['timestamp']) > cutoff]
            filter_desc = f"Last {days_back} days"
            
        elif choice == '4':
            min_return = input("Minimum return % (default: 0): ").strip()
            min_return = float(min_return) if min_return else 0
            filtered = [r for r in filtered if r.get('return_pct', 0) >= min_return]
            filter_desc = f"Return >= {min_return}%"
            
        else:
            filter_desc = "All results"
        
        # Display filtered results
        print("\n" + "=" * 90)
        print(f"FILTERED RESULTS: {filter_desc}")
        print("=" * 90)
        print(f"Found: {len(filtered)} results\n")
        
        if not filtered:
            print("No results match filter criteria.")
            return
        
        # Show most recent 20
        for i, r in enumerate(filtered[-20:], 1):
            timestamp = datetime.fromisoformat(r['timestamp']).strftime('%Y-%m-%d %H:%M')
            symbol = r.get('symbol', 'N/A')
            strategy = r.get('strategy', r.get('type', 'N/A'))
            return_pct = r.get('return_pct', r.get('average_return', 0))
            
            print(f"{i:2d}. [{timestamp}] {strategy:<20} {symbol:<8} {return_pct:>7.2f}%")
        
        if len(filtered) > 20:
            print(f"\n... and {len(filtered) - 20} more results")
        
        # Summary stats
        returns = [r.get('return_pct', r.get('average_return', 0)) for r in filtered if 'return_pct' in r or 'average_return' in r]
        if returns:
            print("\n" + "-" * 90)
            print(f"Summary: Avg Return: {sum(returns)/len(returns):.2f}% | Best: {max(returns):.2f}% | Worst: {min(returns):.2f}%")
    
    def export_results(self):
        """Export results to CSV"""
        if not self.results_history:
            print("\nNo results to export!")
            return
        
        df = pd.DataFrame(self.results_history)
        filename = f"strategy_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        print(f"\n✅ Results exported to: {filename}")
    
    def manage_settings(self):
        """Manage default settings"""
        print("\n" + "═"*90)
        print("SETTINGS MANAGEMENT")
        print("═"*90)
        
        # Load settings
        settings_file = 'settings.json'
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
            except:
                settings = {}
        else:
            settings = {}
        
        # Show current settings
        print("\nCurrent Settings:")
        print(f"  Default Capital:      ${settings.get('default_capital', 100000):,.0f}")
        print(f"  Default Target Return: {settings.get('default_target', 15)}%")
        print(f"  Default Period:        {settings.get('default_period', 180)} days")
        
        # Update settings
        print("\nUpdate Settings (press Enter to keep current):")
        
        capital = input(f"Default Capital ({settings.get('default_capital', 100000)}): ").strip()
        if capital:
            settings['default_capital'] = float(capital)
        
        target = input(f"Default Target Return % ({settings.get('default_target', 15)}): ").strip()
        if target:
            settings['default_target'] = float(target)
        
        period = input(f"Default Period days ({settings.get('default_period', 180)}): ").strip()
        if period:
            settings['default_period'] = int(period)
        
        # Save settings
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        
        print("\n✅ Settings saved!")
        print("\nNew Settings:")
        print(f"  Default Capital:       ${settings['default_capital']:,.0f}")
        print(f"  Default Target Return: {settings['default_target']}%")
        print(f"  Default Period:        {settings['default_period']} days")
    
    def manage_watchlists(self):
        """Manage symbol watchlists"""
        print("\n" + "═"*90)
        print("WATCHLIST MANAGEMENT")
        print("═"*90)
        
        # Load watchlists
        watchlist_file = 'watchlists.json'
        if os.path.exists(watchlist_file):
            try:
                with open(watchlist_file, 'r') as f:
                    watchlists = json.load(f)
            except:
                watchlists = {}
        else:
            watchlists = {}
        
        while True:
            print("\n" + "-" * 90)
            print("WATCHLISTS")
            print("-" * 90)
            
            if watchlists:
                for name, symbols in watchlists.items():
                    print(f"  {name}: {', '.join(symbols[:5])}" + (f" ... (+{len(symbols)-5})" if len(symbols) > 5 else ""))
            else:
                print("  No watchlists yet.")
            
            print("\nOptions:")
            print("1. Create watchlist")
            print("2. Add symbols to watchlist")
            print("3. Remove symbols from watchlist")
            print("4. Delete watchlist")
            print("5. View watchlist details")
            print("0. Back to main menu")
            
            choice = input("\nChoice: ").strip()
            
            if choice == '0':
                break
                
            elif choice == '1':
                name = input("\nWatchlist name: ").strip()
                if not name:
                    continue
                if name in watchlists:
                    print(f"Watchlist '{name}' already exists!")
                    continue
                
                symbols_input = input("Enter symbols (comma-separated): ").strip().upper()
                symbols = [s.strip() for s in symbols_input.split(',') if s.strip()]
                
                if symbols:
                    watchlists[name] = symbols
                    with open(watchlist_file, 'w') as f:
                        json.dump(watchlists, f, indent=2)
                    print(f"\n✅ Watchlist '{name}' created with {len(symbols)} symbols")
                
            elif choice == '2':
                if not watchlists:
                    print("\nNo watchlists available. Create one first.")
                    continue
                
                print("\nAvailable watchlists:")
                for i, name in enumerate(watchlists.keys(), 1):
                    print(f"{i}. {name}")
                
                wl_choice = input("Choose watchlist: ").strip()
                try:
                    wl_name = list(watchlists.keys())[int(wl_choice)-1]
                except:
                    print("Invalid choice")
                    continue
                
                symbols_input = input("Enter symbols to add (comma-separated): ").strip().upper()
                new_symbols = [s.strip() for s in symbols_input.split(',') if s.strip()]
                
                if new_symbols:
                    watchlists[wl_name].extend(new_symbols)
                    watchlists[wl_name] = list(set(watchlists[wl_name]))  # Remove duplicates
                    with open(watchlist_file, 'w') as f:
                        json.dump(watchlists, f, indent=2)
                    print(f"\n✅ Added {len(new_symbols)} symbols to '{wl_name}'")
                
            elif choice == '3':
                if not watchlists:
                    print("\nNo watchlists available.")
                    continue
                
                print("\nAvailable watchlists:")
                for i, name in enumerate(watchlists.keys(), 1):
                    print(f"{i}. {name}")
                
                wl_choice = input("Choose watchlist: ").strip()
                try:
                    wl_name = list(watchlists.keys())[int(wl_choice)-1]
                except:
                    print("Invalid choice")
                    continue
                
                print(f"\nSymbols in '{wl_name}': {', '.join(watchlists[wl_name])}")
                symbols_input = input("Enter symbols to remove (comma-separated): ").strip().upper()
                remove_symbols = [s.strip() for s in symbols_input.split(',') if s.strip()]
                
                if remove_symbols:
                    for sym in remove_symbols:
                        if sym in watchlists[wl_name]:
                            watchlists[wl_name].remove(sym)
                    with open(watchlist_file, 'w') as f:
                        json.dump(watchlists, f, indent=2)
                    print(f"\n✅ Removed symbols from '{wl_name}'")
                
            elif choice == '4':
                if not watchlists:
                    print("\nNo watchlists to delete.")
                    continue
                
                print("\nAvailable watchlists:")
                for i, name in enumerate(watchlists.keys(), 1):
                    print(f"{i}. {name}")
                
                wl_choice = input("Choose watchlist to delete: ").strip()
                try:
                    wl_name = list(watchlists.keys())[int(wl_choice)-1]
                except:
                    print("Invalid choice")
                    continue
                
                confirm = input(f"Delete '{wl_name}'? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    del watchlists[wl_name]
                    with open(watchlist_file, 'w') as f:
                        json.dump(watchlists, f, indent=2)
                    print(f"\n✅ Watchlist '{wl_name}' deleted")
                
            elif choice == '5':
                if not watchlists:
                    print("\nNo watchlists available.")
                    continue
                
                print("\nAvailable watchlists:")
                for i, name in enumerate(watchlists.keys(), 1):
                    print(f"{i}. {name}")
                
                wl_choice = input("Choose watchlist: ").strip()
                try:
                    wl_name = list(watchlists.keys())[int(wl_choice)-1]
                except:
                    print("Invalid choice")
                    continue
                
                print(f"\n" + "=" * 60)
                print(f"WATCHLIST: {wl_name}")
                print("=" * 60)
                print(f"\nSymbols ({len(watchlists[wl_name])}):")
                for i, sym in enumerate(watchlists[wl_name], 1):
                    print(f"  {i:2d}. {sym}")
    
    def show_help(self):
        """Display comprehensive help and usage guide"""
        print("\n" + "═"*90)
        print("📚 HELP & USAGE GUIDE")
        print("═"*90)
        
        print("\n1️⃣  QUICK START")
        print("─" * 90)
        print("  First time? Try this workflow:")
        print("  • Option 1: Test single asset (e.g., SPY, 90 days)")
        print("  • Option 2: Compare strategies to find best performer")
        print("  • Option 5: Create portfolio with winning strategies")
        print("  • Option 7: Backtest portfolio performance")
        
        print("\n2️⃣  STRATEGIES (Min Periods)")
        print("─" * 90)
        print("  Short-Term:  21+ days  │ Fast (5-10s)  │ Recent trends")
        print("  Simple:      45+ days  │ Fast (10-20s) │ Mean reversion")
        print("  ML Single:   130+ days │ Med (30-60s)  │ Pattern learning")
        print("  Optimized:   365+ days │ Slow (2-5min) │ Multi-model ensemble")
        print()
        print("  ⚠️  Note: These are CALENDAR days. Yahoo Finance returns trading days only.")
        print("     System auto-requests 1.5x more data to compensate for weekends/holidays.")
        
        print("\n3️⃣  SUPPORTED ASSETS")
        print("─" * 90)
        print("  ✅ Stocks:  AAPL, MSFT, TSLA, any valid ticker")
        print("  ✅ ETFs:    SPY, QQQ, IWM, sector/theme ETFs")
        print("  ✅ Crypto:  BTC-USD, ETH-USD (must end in -USD)")
        
        print("\n4️⃣  KEY LIMITATIONS")
        print("─" * 90)
        print("  • Internet required (downloads data from Yahoo Finance)")
        print("  • Min capital: $100 (recommended: $10,000+)")
        print("  • Max lookback: ~10 years (data availability varies)")
        print("  • Rate limits: Be patient with batch operations")
        print("  • Optimized strategy: Needs 365+ days, takes 2-5 minutes")
        
        print("\n5️⃣  BEST PRACTICES")
        print("─" * 90)
        print("  📊 Testing:")
        print("     • Start with short periods to get quick feedback")
        print("     • Use Short-Term strategy for initial tests")
        print("     • Compare strategies (Option 2) before choosing")
        print()
        print("  💼 Portfolios:")
        print("     • Diversify: Use 2-3 strategies with different allocations")
        print("     • Set realistic targets (10-20% annual)")
        print("     • Test with same symbol for consistency")
        print("     • Export results (Option 14) for record-keeping")
        print()
        print("  🎯 Watchlists:")
        print("     • Create sector-based lists (Option 16)")
        print("     • Use for quick batch testing (Option 3)")
        print("     • Keep lists updated with current holdings")
        
        print("\n6️⃣  COMMON ISSUES & SOLUTIONS")
        print("─" * 90)
        print("  ❌ 'Insufficient data' error:")
        print("     → Increase lookback period (use minimums above)")
        print("     → Symbol may be too new (try older assets)")
        print()
        print("  ❌ 'No data available' error:")
        print("     → Check symbol spelling (case doesn't matter)")
        print("     → Crypto must end in -USD (BTC-USD, not BTC)")
        print("     → Some symbols may be delisted")
        print()
        print("  ❌ Strategy taking too long:")
        print("     → Optimized strategy is slow by design (2-5 min)")
        print("     → Use Short-Term or Simple for quick tests")
        print("     → Reduce lookback period if possible")
        print()
        print("  ❌ Portfolio backtest fails:")
        print("     → Ensure allocations sum to 100%")
        print("     → Use adequate lookback for all strategies")
        print("     → Check internet connection")
        
        print("\n7️⃣  EXAMPLES")
        print("─" * 90)
        print("  📈 Test recent Bitcoin performance (30 days):")
        print("     → Option 1 → BTC-USD → Strategy 4 (Short-Term) → 30 days")
        print()
        print("  📊 Find best tech stock (quarterly):")
        print("     → Option 3 → By Sector → Technology → 90 days")
        print()
        print("  💼 Create balanced portfolio:")
        print("     → Option 5 → Name it → Capital: 100000")
        print("     → Simple: 40% │ ML: 30% │ Optimized: 30%")
        print("     → Then Option 7 to backtest")
        print()
        print("  🔍 Find profitable trades:")
        print("     → Option 13 → Filter by Return >= 5%")
        
        print("\n8️⃣  DATA & FILES")
        print("─" * 90)
        print("  portfolios.json         - Your portfolio configurations")
        print("  strategy_history.json   - All strategy run results")
        print("  settings.json          - Default capital/targets")
        print("  watchlists.json        - Symbol watchlists")
        print("  CSV exports            - Timestamped result files")
        print()
        print("  💡 Tip: Backup these files regularly!")
        
        print("\n9️⃣  PERFORMANCE TIPS")
        print("─" * 90)
        print("  ⚡ For speed:")
        print("     • Use Short-Term or Simple strategies")
        print("     • Limit batch tests to 5-10 symbols")
        print("     • Use shorter lookback periods")
        print()
        print("  📊 For accuracy:")
        print("     • Use longer lookback periods (365+ days)")
        print("     • Use ML or Optimized strategies")
        print("     • Compare multiple strategies (Option 2)")
        print("     • Test on multiple symbols/sectors")
        
        print("\n🔟 GETTING MORE HELP")
        print("─" * 90)
        print("  📄 Documentation:")
        print("     • ALL_FEATURES_COMPLETE.md  - Complete feature list")
        print("     • PRODUCTION_READY.md       - Production deployment")
        print("     • WORKING_PERIODS.md        - Period requirements")
        print()
        print("  🧪 Testing:")
        print("     • test_new_features.py      - Automated test suite")
        print("     • ./safe_start.sh           - System health check")
        
        print("\n" + "═"*90)
        print("💡 Remember: Past performance doesn't guarantee future results.")
        print("   Use this tool for analysis and education, not as financial advice.")
        print("═"*90)
    
    def save_strategy_config(self):
        """Save a strategy configuration for reuse"""
        print("\n" + "═"*90)
        print("SAVE STRATEGY CONFIGURATION")
        print("═"*90)
        
        # Choose strategy type
        print("\nSelect strategy type to save:")
        print("1. Short-Term Strategy")
        print("2. Simple Mean Reversion")
        print("3. ML Single Model")
        print("4. Optimized Ensemble")
        
        choice = input("\nChoice (1-4): ").strip()
        
        strategy_types = {
            '1': ('ShortTermStrategy', 'Short-Term'),
            '2': ('SimpleMeanReversionStrategy', 'Simple Mean Reversion'),
            '3': ('MLTradingStrategy', 'ML Single'),
            '4': ('OptimizedMLStrategy', 'Optimized Ensemble')
        }
        
        if choice not in strategy_types:
            print("Invalid choice")
            return
        
        strategy_class, strategy_display = strategy_types[choice]
        
        # Get configuration name
        name = input("\nStrategy name (e.g., 'Aggressive_SPY_Short'): ").strip()
        if not name:
            return
        
        # Check if exists
        if self.strategy_manager.get_strategy(name):
            overwrite = input(f"Strategy '{name}' exists. Overwrite? (yes/no): ").strip().lower()
            if overwrite != 'yes':
                return
            self.strategy_manager.delete_strategy(name)
        
        # Get parameters based on strategy type
        parameters = {}
        
        # Common parameters
        symbol = input("Default symbol (optional, e.g., SPY): ").strip().upper() or None
        if symbol:
            parameters['symbol'] = symbol
        
        capital = input("Initial capital (default: 100000): ").strip()
        parameters['initial_capital'] = float(capital) if capital else 100000
        
        # Strategy-specific parameters
        if choice == '1':  # Short-Term
            lookback = input("Lookback period (default: 14): ").strip()
            parameters['lookback'] = int(lookback) if lookback else 14
            
            entry = input("Entry threshold (default: 0.02): ").strip()
            parameters['entry_threshold'] = float(entry) if entry else 0.02
            
            exit_t = input("Exit threshold (default: 0.01): ").strip()
            parameters['exit_threshold'] = float(exit_t) if exit_t else 0.01
            
        elif choice == '2':  # Simple
            lookback = input("Lookback period (default: 20): ").strip()
            parameters['lookback'] = int(lookback) if lookback else 20
            
        elif choice == '3':  # ML Single
            lookback = input("Lookback period (default: 60): ").strip()
            parameters['lookback'] = int(lookback) if lookback else 60
            
            horizon = input("Prediction horizon (default: 5): ").strip()
            parameters['prediction_horizon'] = int(horizon) if horizon else 5
            
        elif choice == '4':  # Optimized
            lookback = input("Lookback period (default: 60): ").strip()
            parameters['lookback'] = int(lookback) if lookback else 60
            
            horizon = input("Prediction horizon (default: 5): ").strip()
            parameters['prediction_horizon'] = int(horizon) if horizon else 5
            
            n_est = input("N estimators (default: 100): ").strip()
            parameters['n_estimators'] = int(n_est) if n_est else 100
        
        # Description and tags
        description = input("\nDescription (optional): ").strip()
        tags_input = input("Tags (comma-separated, e.g., 'aggressive,tech,short-term'): ").strip()
        tags = [t.strip() for t in tags_input.split(',')] if tags_input else []
        
        # Create and save
        config = StrategyConfig(
            name=name,
            strategy_type=strategy_class,
            parameters=parameters,
            description=description,
            tags=tags
        )
        
        if self.strategy_manager.save_strategy(config):
            print(f"\n✅ Strategy '{name}' saved successfully!")
            print(f"   Type: {strategy_display}")
            print(f"   Parameters: {len(parameters)} configured")
            if tags:
                print(f"   Tags: {', '.join(tags)}")
        else:
            print(f"\n❌ Failed to save strategy")
    
    def load_and_run_strategy(self):
        """Load a saved strategy and run it"""
        print("\n" + "═"*90)
        print("LOAD & RUN SAVED STRATEGY")
        print("═"*90)
        
        strategies = self.strategy_manager.list_strategies()
        
        if not strategies:
            print("\n❌ No saved strategies found. Create one first (Option 17).")
            return
        
        # Display strategies
        print(f"\nAvailable strategies ({len(strategies)}):")
        print("─" * 90)
        for i, config in enumerate(strategies, 1):
            print(f"\n{i}. {config.name}")
            print(f"   Type: {config.strategy_type}")
            print(f"   Created: {config.created_at[:10]}")
            if config.description:
                print(f"   Description: {config.description}")
            if config.tags:
                print(f"   Tags: {', '.join(config.tags)}")
            
            # Show performance if available
            if config.performance_history:
                latest = config.performance_history[-1]['results']
                if 'return' in latest:
                    print(f"   Last Return: {latest['return']:.2f}%")
        
        print("─" * 90)
        
        choice = input("\nSelect strategy (number): ").strip()
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(strategies):
                print("Invalid choice")
                return
            
            config = strategies[idx]
        except:
            print("Invalid input")
            return
        
        # Get symbol (override or use default)
        if config.parameters.get('symbol'):
            use_default = input(f"\nUse default symbol '{config.parameters['symbol']}'? (yes/no): ").strip().lower()
            if use_default == 'yes':
                symbol = config.parameters['symbol']
            else:
                symbol = input("Enter symbol: ").strip().upper()
        else:
            symbol = input("\nEnter symbol: ").strip().upper()
        
        if not symbol:
            return
        
        # Validate symbol
        try:
            symbol = validate_symbol(symbol)
        except ValidationError as e:
            print(f"\n❌ {e}")
            return
        
        # Get time period
        days = input("\nBacktest period in days (default: based on strategy): ").strip()
        if days:
            try:
                days = validate_days(days, min_days=21)
            except ValidationError as e:
                print(f"\n❌ {e}")
                return
        else:
            # Default based on strategy type
            if 'Short' in config.strategy_type:
                days = 45
            elif 'Simple' in config.strategy_type:
                days = 180
            elif 'Optimized' in config.strategy_type:
                days = 365
            else:
                days = 180
        
        # Create strategy instance
        try:
            params = config.parameters.copy()
            params['symbol'] = symbol
            
            if config.strategy_type == 'ShortTermStrategy':
                strategy = ShortTermStrategy(
                    symbol=symbol,
                    lookback=params.get('lookback', 14),
                    entry_threshold=params.get('entry_threshold', 0.02),
                    exit_threshold=params.get('exit_threshold', 0.01)
                )
            elif config.strategy_type == 'SimpleMeanReversionStrategy':
                strategy = SimpleMeanReversionStrategy(
                    symbol=symbol,
                    lookback=params.get('lookback', 20)
                )
            elif config.strategy_type == 'MLTradingStrategy':
                strategy = MLTradingStrategy(
                    symbol=symbol,
                    lookback=params.get('lookback', 60),
                    prediction_horizon=params.get('prediction_horizon', 5)
                )
            elif config.strategy_type == 'OptimizedMLStrategy':
                strategy = OptimizedMLStrategy(
                    symbol=symbol,
                    lookback=params.get('lookback', 60),
                    prediction_horizon=params.get('prediction_horizon', 5),
                    n_estimators=params.get('n_estimators', 100)
                )
            else:
                print(f"❌ Unknown strategy type: {config.strategy_type}")
                return
            
            strategy.cash = params.get('initial_capital', 100000)
            
            # Run backtest
            print(f"\n🔄 Running '{config.name}' on {symbol} for {days} days...")
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            if hasattr(strategy, 'backtest'):
                data, trades, final_value, equity = strategy.backtest(start_date, end_date)
                
                if len(results) >= 3:
                    if 'OptimizedML' in config.strategy_type or 'MLTrading' in config.strategy_type:
                        df_test, trades, final_value, equity = results
                    else:
                        data, trades, final_value = results[:3]
                        equity = results[3] if len(results) > 3 else []
                    
                    # Display results
                    print("\n" + "═"*90)
                    print(f"RESULTS: {config.name} on {symbol}")
                    print("═"*90)
                    
                    initial = params.get('initial_capital', 100000)
                    return_pct = ((final_value - initial) / initial) * 100
                    
                    print(f"\n💰 Performance:")
                    print(f"   Initial Capital:  ${initial:,.2f}")
                    print(f"   Final Value:      ${final_value:,.2f}")
                    print(f"   Total Return:     {return_pct:+.2f}%")
                    print(f"   Total Trades:     {len(trades)}")
                    
                    if equity:
                        metrics = calculate_metrics_safe(equity)
                        print(f"   Sharpe Ratio:     {metrics['sharpe']:.2f}")
                        print(f"   Max Drawdown:     {metrics['max_dd']:.2f}%")
                        print(f"   Volatility:       {metrics['volatility']:.2f}%")
                    
                    # Update performance history
                    config.update_performance({
                        'symbol': symbol,
                        'return': return_pct,
                        'final_value': final_value,
                        'trades': len(trades),
                        'days': days
                    })
                    self.strategy_manager.save_strategies()
                    
                    print("\n✅ Performance logged to strategy history")
                    
        except Exception as e:
            print(f"\n❌ Error running strategy: {e}")
            import traceback
            traceback.print_exc()
    
    def view_saved_strategies(self):
        """View all saved strategy configurations"""
        print("\n" + "═"*90)
        print("SAVED STRATEGY LIBRARY")
        print("═"*90)
        
        strategies = self.strategy_manager.list_strategies()
        
        if not strategies:
            print("\n❌ No saved strategies. Create one with Option 17.")
            return
        
        # Group by type
        by_type = {}
        for config in strategies:
            if config.strategy_type not in by_type:
                by_type[config.strategy_type] = []
            by_type[config.strategy_type].append(config)
        
        # Display grouped
        total = 0
        for strategy_type, configs in by_type.items():
            print(f"\n📊 {strategy_type} ({len(configs)})")
            print("─" * 90)
            
            for config in configs:
                total += 1
                print(f"\n  {total}. {config.name}")
                print(f"     Created: {config.created_at[:10]} | Modified: {config.last_modified[:10]}")
                
                if config.description:
                    print(f"     Description: {config.description}")
                
                if config.tags:
                    print(f"     Tags: {', '.join(config.tags)}")
                
                # Parameters
                params_str = []
                if 'lookback' in config.parameters:
                    params_str.append(f"lookback={config.parameters['lookback']}")
                if 'entry_threshold' in config.parameters:
                    params_str.append(f"entry={config.parameters['entry_threshold']}")
                if 'initial_capital' in config.parameters:
                    cap = config.parameters['initial_capital']
                    params_str.append(f"capital=${cap:,.0f}")
                
                if params_str:
                    print(f"     Parameters: {', '.join(params_str)}")
                
                # Performance history
                if config.performance_history:
                    print(f"     Runs: {len(config.performance_history)}")
                    latest = config.performance_history[-1]['results']
                    if 'return' in latest:
                        print(f"     Last Return: {latest['return']:+.2f}% on {latest.get('symbol', 'N/A')}")
        
        print("\n" + "═"*90)
        print(f"Total: {total} saved strategies")
        print("═"*90)
    
    def clone_modify_strategy(self):
        """Clone and modify an existing strategy"""
        print("\n" + "═"*90)
        print("CLONE & MODIFY STRATEGY")
        print("═"*90)
        
        strategies = self.strategy_manager.list_strategies()
        
        if not strategies:
            print("\n❌ No saved strategies. Create one first (Option 17).")
            return
        
        # Display strategies
        print(f"\nAvailable strategies ({len(strategies)}):")
        for i, config in enumerate(strategies, 1):
            print(f"{i:2d}. {config.name} ({config.strategy_type})")
        
        choice = input("\nSelect strategy to clone: ").strip()
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(strategies):
                print("Invalid choice")
                return
            source = strategies[idx]
        except:
            print("Invalid input")
            return
        
        # New name
        new_name = input(f"\nNew strategy name (cloning '{source.name}'): ").strip()
        if not new_name:
            return
        
        if self.strategy_manager.get_strategy(new_name):
            print(f"❌ Strategy '{new_name}' already exists")
            return
        
        # Clone
        if not self.strategy_manager.clone_strategy(source.name, new_name):
            print("❌ Failed to clone strategy")
            return
        
        print(f"✅ Cloned '{source.name}' to '{new_name}'")
        
        # Modify?
        modify = input("\nModify parameters? (yes/no): ").strip().lower()
        if modify == 'yes':
            cloned = self.strategy_manager.get_strategy(new_name)
            
            print("\nCurrent parameters:")
            for key, value in cloned.parameters.items():
                print(f"  {key}: {value}")
            
            print("\nEnter new values (press Enter to keep current):")
            
            updates = {}
            for key, value in cloned.parameters.items():
                new_val = input(f"  {key} [{value}]: ").strip()
                if new_val:
                    # Try to preserve type
                    if isinstance(value, int):
                        try:
                            updates[key] = int(new_val)
                        except:
                            updates[key] = new_val
                    elif isinstance(value, float):
                        try:
                            updates[key] = float(new_val)
                        except:
                            updates[key] = new_val
                    else:
                        updates[key] = new_val
            
            if updates:
                if self.strategy_manager.update_strategy(new_name, {'parameters': updates}):
                    print(f"\n✅ Updated {len(updates)} parameters")
                else:
                    print("\n❌ Failed to update parameters")
    
    def export_import_strategies(self):
        """Export or import strategy configurations"""
        print("\n" + "═"*90)
        print("EXPORT / IMPORT STRATEGIES")
        print("═"*90)
        
        print("\n1. Export strategy to file")
        print("2. Import strategy from file")
        print("3. Export all strategies")
        
        choice = input("\nChoice (1-3): ").strip()
        
        if choice == '1':
            # Export single
            strategies = self.strategy_manager.list_strategies()
            if not strategies:
                print("\n❌ No strategies to export")
                return
            
            print(f"\nAvailable strategies ({len(strategies)}):")
            for i, config in enumerate(strategies, 1):
                print(f"{i:2d}. {config.name}")
            
            sel = input("\nSelect strategy: ").strip()
            try:
                idx = int(sel) - 1
                if idx < 0 or idx >= len(strategies):
                    print("Invalid choice")
                    return
                config = strategies[idx]
            except:
                print("Invalid input")
                return
            
            filename = input(f"\nExport filename (default: {config.name}.json): ").strip()
            filename = filename if filename else f"{config.name}.json"
            
            if not filename.endswith('.json'):
                filename += '.json'
            
            if self.strategy_manager.export_strategy(config.name, filename):
                print(f"\n✅ Exported '{config.name}' to {filename}")
            else:
                print("\n❌ Export failed")
        
        elif choice == '2':
            # Import single
            filename = input("\nImport filename: ").strip()
            if not filename:
                return
            
            if not os.path.exists(filename):
                print(f"❌ File '{filename}' not found")
                return
            
            new_name = input("Import as (leave blank to keep original name): ").strip()
            
            if self.strategy_manager.import_strategy(filename, new_name or None):
                print(f"\n✅ Imported strategy from {filename}")
            else:
                print("\n❌ Import failed")
        
        elif choice == '3':
            # Export all
            strategies = self.strategy_manager.list_strategies()
            if not strategies:
                print("\n❌ No strategies to export")
                return
            
            export_dir = input("\nExport directory (default: ./strategy_exports): ").strip()
            export_dir = export_dir if export_dir else "./strategy_exports"
            
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            
            exported = 0
            for config in strategies:
                filename = os.path.join(export_dir, f"{config.name}.json")
                if self.strategy_manager.export_strategy(config.name, filename):
                    exported += 1
            
            print(f"\n✅ Exported {exported}/{len(strategies)} strategies to {export_dir}")
    
    def strategy_leaderboard(self):
        """Show best performing strategies"""
        print("\n" + "═"*90)
        print("STRATEGY PERFORMANCE LEADERBOARD")
        print("═"*90)
        
        strategies = self.strategy_manager.list_strategies()
        
        if not strategies:
            print("\n❌ No saved strategies found")
            return
        
        # Filter strategies with performance history
        with_performance = [s for s in strategies if s.performance_history]
        
        if not with_performance:
            print("\n❌ No strategies have been run yet. Run saved strategies to see leaderboard.")
            return
        
        # Calculate average returns
        strategy_stats = []
        for config in with_performance:
            returns = [run['results'].get('return', 0) for run in config.performance_history]
            avg_return = sum(returns) / len(returns)
            best_return = max(returns)
            worst_return = min(returns)
            total_runs = len(returns)
            
            strategy_stats.append({
                'name': config.name,
                'type': config.strategy_type,
                'avg_return': avg_return,
                'best_return': best_return,
                'worst_return': worst_return,
                'total_runs': total_runs,
                'latest': config.performance_history[-1]['results']
            })
        
        # Sort by average return
        strategy_stats.sort(key=lambda x: x['avg_return'], reverse=True)
        
        print(f"\n{'Rank':<5} {'Strategy':<25} {'Avg Return':>12} {'Best':>10} {'Runs':>6}")
        print("─" * 90)
        
        for i, stats in enumerate(strategy_stats, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            print(f"{emoji}{i:<4} {stats['name']:<25} {stats['avg_return']:>11.2f}% "
                  f"{stats['best_return']:>9.2f}% {stats['total_runs']:>6}")
        
        print("─" * 90)
        
        # Show top 3 details
        if len(strategy_stats) >= 1:
            print("\n🏆 TOP PERFORMER DETAILS:")
            print("─" * 90)
            top = strategy_stats[0]
            print(f"Name: {top['name']}")
            print(f"Type: {top['type']}")
            print(f"Average Return: {top['avg_return']:.2f}%")
            print(f"Best Run: {top['best_return']:.2f}%")
            print(f"Worst Run: {top['worst_return']:.2f}%")
            print(f"Total Runs: {top['total_runs']}")
            print(f"Latest Symbol: {top['latest'].get('symbol', 'N/A')}")
            print(f"Latest Return: {top['latest'].get('return', 0):.2f}%")
    
    def market_analytics_menu(self):
        """Advanced market analytics and regime detection"""
        print("\n" + "═"*90)
        print("MARKET ANALYTICS & REGIME DETECTION")
        print("═"*90)
        
        symbol = input("\nEnter symbol to analyze: ").strip().upper()
        if not symbol:
            return
        
        try:
            print(f"\n🔍 Analyzing {symbol}...")
            analytics = MarketAnalytics(symbol)
            analytics.fetch_data(period='1y')
            analytics.print_comprehensive_analysis()
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    def correlation_analysis_menu(self):
        """Correlation analysis between multiple assets"""
        print("\n" + "═"*90)
        print("CORRELATION ANALYSIS")
        print("═"*90)
        
        print("\nEnter symbols to analyze (comma-separated):")
        print("Example: SPY,QQQ,IWM,TLT,GLD")
        
        symbols_input = input("\nSymbols: ").strip().upper()
        if not symbols_input:
            return
        
        symbols = [s.strip() for s in symbols_input.split(',')]
        
        if len(symbols) < 2:
            print("\n❌ Need at least 2 symbols for correlation analysis")
            return
        
        period = input("\nAnalysis period (3mo, 6mo, 1y, default: 3mo): ").strip() or '3mo'
        
        try:
            print(f"\n🔍 Calculating correlations for {len(symbols)} symbols...")
            
            # Use first symbol's analytics
            analytics = MarketAnalytics(symbols[0])
            corr_matrix = analytics.correlation_matrix(symbols, period)
            
            if corr_matrix.empty:
                print("\n❌ Could not calculate correlations")
                return
            
            print("\n" + "═"*90)
            print("CORRELATION MATRIX")
            print("═"*90)
            print("\nValues range from -1 (perfect negative) to +1 (perfect positive)")
            print()
            print(corr_matrix.to_string())
            
            # Find highly correlated pairs
            print("\n" + "─"*90)
            print("HIGHLY CORRELATED PAIRS (>0.7):")
            print("─"*90)
            
            found_pairs = False
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_val = corr_matrix.iloc[i, j]
                    if abs(corr_val) > 0.7:
                        symbol1 = corr_matrix.columns[i]
                        symbol2 = corr_matrix.columns[j]
                        print(f"  {symbol1} <-> {symbol2}: {corr_val:+.3f}")
                        found_pairs = True
            
            if not found_pairs:
                print("  No highly correlated pairs found")
            
            print("\n" + "═"*90)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    def optimize_strategy_menu(self):
        """Optimize strategy parameters"""
        print("\n" + "═"*90)
        print("STRATEGY PARAMETER OPTIMIZATION")
        print("═"*90)
        
        print("\n⚡ Optimize strategy parameters using grid search")
        print("   This will test multiple parameter combinations to find the best")
        
        # Choose strategy
        print("\nSelect strategy to optimize:")
        print("1. Short-Term Strategy")
        print("2. Simple Mean Reversion")
        print("3. ML Single Model")
        
        choice = input("\nChoice (1-3): ").strip()
        
        strategy_map = {
            '1': (ShortTermStrategy, 'Short-Term'),
            '2': (SimpleMeanReversionStrategy, 'Simple'),
            '3': (MLTradingStrategy, 'ML Single')
        }
        
        if choice not in strategy_map:
            print("Invalid choice")
            return
        
        strategy_class, strategy_name = strategy_map[choice]
        
        # Get symbol and period
        symbol = input("\nSymbol to optimize on: ").strip().upper()
        if not symbol:
            return
        
        days = input("Backtest period in days (default: 180): ").strip()
        days = int(days) if days.isdigit() else 180
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Define parameter grids
        if choice == '1':  # Short-Term
            param_grid = {
                'lookback': [7, 14, 21],
                'entry_threshold': [0.01, 0.02, 0.03],
                'exit_threshold': [0.005, 0.01, 0.015]
            }
        elif choice == '2':  # Simple
            param_grid = {
                'lookback': [15, 20, 30],
                'std_dev': [1.5, 2.0, 2.5]
            }
        else:  # ML
            param_grid = {
                'lookback': [40, 60, 80],
                'prediction_horizon': [3, 5, 7]
            }
        
        # Choose metric
        print("\nOptimization metric:")
        print("1. Sharpe Ratio (risk-adjusted)")
        print("2. Total Return (absolute)")
        print("3. Win Rate")
        
        metric_choice = input("\nChoice (default: 1): ").strip() or '1'
        metric_map = {'1': 'sharpe_ratio', '2': 'total_return', '3': 'win_rate'}
        metric = metric_map.get(metric_choice, 'sharpe_ratio')
        
        # Run optimization
        print(f"\n🔄 Optimizing {strategy_name} on {symbol}...")
        print(f"   This will test ~{len(list(product(*param_grid.values()))[:50])} combinations...")
        print("   Please wait...")
        
        try:
            from itertools import product
            
            optimizer = StrategyOptimizer(strategy_class, metric=metric)
            results = optimizer.grid_search(
                param_grid, symbol, start_date, end_date,
                initial_capital=10000, max_combinations=50
            )
            
            print("\n" + "═"*90)
            print(f"OPTIMIZATION RESULTS - {strategy_name}")
            print("═"*90)
            print(f"\n🏆 Best Parameters:")
            for param, value in results['best_params'].items():
                print(f"   {param}: {value}")
            print(f"\n📊 Best {metric}: {results['best_score']:.4f}")
            
            # Show top 5 combinations
            if results['all_results']:
                print(f"\n📋 Top 5 Combinations:")
                print("─" * 90)
                for i, result in enumerate(results['all_results'][:5], 1):
                    print(f"\n{i}. Score: {result['score']:.4f}")
                    print(f"   Params: {result['params']}")
                    if 'metrics' in result:
                        metrics = result['metrics']
                        print(f"   Return: {metrics.get('total_return', 0):.2f}% | "
                              f"Sharpe: {metrics.get('sharpe_ratio', 0):.2f} | "
                              f"Trades: {metrics.get('num_trades', 0)}")
            
            # Save results
            save = input("\n\nSave optimization results? (yes/no): ").strip().lower()
            if save == 'yes':
                optimizer.save_results()
            
        except Exception as e:
            print(f"\n❌ Error during optimization: {e}")
            import traceback
            traceback.print_exc()
    
    def advanced_settings_menu(self):
        """Advanced settings configuration"""
        print("\n" + "═"*90)
        print("ADVANCED SETTINGS MANAGER")
        print("═"*90)
        
        self.advanced_settings.print_settings()
        
        print("\n\nOptions:")
        print("1. Update Risk Management Settings")
        print("2. Update ML Settings")
        print("3. Update Backtest Settings")
        print("4. Reset to Defaults")
        print("0. Back")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            print("\n📝 Update Risk Settings (press Enter to skip):")
            updates = {}
            
            val = input(f"Max Position Size [0-1] (current: {self.advanced_settings.risk.max_position_size}): ").strip()
            if val: updates['max_position_size'] = float(val)
            
            val = input(f"Stop Loss % [0-1] (current: {self.advanced_settings.risk.stop_loss_pct}): ").strip()
            if val: updates['stop_loss_pct'] = float(val)
            
            val = input(f"Take Profit % [0-1] (current: {self.advanced_settings.risk.take_profit_pct}): ").strip()
            if val: updates['take_profit_pct'] = float(val)
            
            if updates:
                self.advanced_settings.update_risk_settings(**updates)
                print(f"\n✅ Updated {len(updates)} risk settings")
            
        elif choice == '2':
            print("\n📝 Update ML Settings (press Enter to skip):")
            updates = {}
            
            val = input(f"Lookback Period (current: {self.advanced_settings.ml.lookback_period}): ").strip()
            if val: updates['lookback_period'] = int(val)
            
            val = input(f"Prediction Horizon (current: {self.advanced_settings.ml.prediction_horizon}): ").strip()
            if val: updates['prediction_horizon'] = int(val)
            
            val = input(f"Min Samples (current: {self.advanced_settings.ml.min_samples}): ").strip()
            if val: updates['min_samples'] = int(val)
            
            if updates:
                self.advanced_settings.update_ml_settings(**updates)
                print(f"\n✅ Updated {len(updates)} ML settings")
            
        elif choice == '3':
            print("\n📝 Update Backtest Settings (press Enter to skip):")
            updates = {}
            
            val = input(f"Commission [0-1] (current: {self.advanced_settings.backtest.commission}): ").strip()
            if val: updates['commission'] = float(val)
            
            val = input(f"Slippage [0-1] (current: {self.advanced_settings.backtest.slippage}): ").strip()
            if val: updates['slippage'] = float(val)
            
            val = input(f"Benchmark Symbol (current: {self.advanced_settings.backtest.benchmark}): ").strip()
            if val: updates['benchmark'] = val.upper()
            
            if updates:
                self.advanced_settings.update_backtest_settings(**updates)
                print(f"\n✅ Updated {len(updates)} backtest settings")
            
        elif choice == '4':
            confirm = input("\n⚠️  Reset all settings to defaults? (yes/no): ").strip().lower()
            if confirm == 'yes':
                self.advanced_settings.reset_to_defaults()
                print("\n✅ All settings reset to defaults")
    
    def risk_analysis_dashboard(self):
        """Comprehensive risk analysis"""
        print("\n" + "═"*90)
        print("RISK ANALYSIS DASHBOARD")
        print("═"*90)
        
        symbol = input("\nEnter symbol to analyze: ").strip().upper()
        if not symbol:
            return
        
        period = input("Analysis period (3mo, 6mo, 1y, 2y, default: 1y): ").strip() or '1y'
        
        try:
            print(f"\n🔍 Performing risk analysis on {symbol}...")
            
            analytics = MarketAnalytics(symbol)
            analytics.fetch_data(period=period)
            
            # Get risk metrics
            risk_metrics = analytics.risk_metrics()
            
            if not risk_metrics:
                print("\n❌ Insufficient data for risk analysis")
                return
            
            print("\n" + "═"*90)
            print(f"RISK ANALYSIS - {symbol}")
            print("═"*90)
            
            print("\n📊 VOLATILITY METRICS")
            print(f"   Annualized Volatility:    {risk_metrics['volatility']*100:.2f}%")
            print(f"   Downside Deviation:       {risk_metrics['downside_deviation']*100:.2f}%")
            
            print("\n💰 VALUE AT RISK (VaR)")
            print(f"   95% VaR:                  {risk_metrics['var_95']*100:.2f}%")
            print(f"   95% CVaR (Expected Loss): {risk_metrics['cvar_95']*100:.2f}%")
            
            print("\n📉 DRAWDOWN ANALYSIS")
            print(f"   Maximum Drawdown:         {risk_metrics['max_drawdown']*100:.2f}%")
            
            print("\n⚖️  RISK-ADJUSTED RETURNS")
            print(f"   Calmar Ratio:             {risk_metrics['calmar_ratio']:.2f}")
            print(f"   Sortino Ratio:            {risk_metrics['sortino_ratio']:.2f}")
            
            # Risk rating
            vol = risk_metrics['volatility']
            max_dd = abs(risk_metrics['max_drawdown'])
            
            print("\n🎯 RISK RATING")
            if vol < 0.15 and max_dd < 0.10:
                rating = "🟢 LOW RISK"
            elif vol < 0.25 and max_dd < 0.20:
                rating = "🟡 MODERATE RISK"
            elif vol < 0.40 and max_dd < 0.30:
                rating = "🟠 HIGH RISK"
            else:
                rating = "🔴 VERY HIGH RISK"
            
            print(f"   {rating}")
            
            print("\n" + "═"*90)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    def create_custom_strategy(self):
        """Interactive custom strategy creation"""
        try:
            print("\n" + "="*80)
            print("🔨 CUSTOM STRATEGY BUILDER")
            print("="*80)
            
            strategy = self.strategy_builder.create_custom_strategy()
            
            print("\n✅ Strategy created successfully!")
            print(f"\n📋 Strategy Summary:")
            print(f"   Name: {strategy['name']}")
            print(f"   Type: {strategy['type']}")
            print(f"   Indicators: {', '.join(strategy['indicators'])}")
            print(f"   Entry Rules: {len(strategy['entry_rules'])} rules")
            print(f"   Exit Rules: {len(strategy['exit_rules'])} rules")
            
            # Offer to export immediately
            export = input("\n💾 Export for live trading now? (y/n): ").strip().lower()
            if export == 'y':
                self.export_strategy_for_live(strategy['name'])
            
        except Exception as e:
            print(f"\n❌ Error creating strategy: {e}")
            import traceback
            traceback.print_exc()
        
        input("\nPress Enter to continue...")
    
    def export_strategy_for_live(self, strategy_name=None):
        """Export strategy for live trading"""
        try:
            print("\n" + "="*80)
            print("💾 EXPORT STRATEGY FOR LIVE TRADING")
            print("="*80)
            
            # List available strategies
            strategies = self.strategy_builder.list_strategies()
            if not strategies:
                print("\n❌ No custom strategies found. Create one first!")
                input("\nPress Enter to continue...")
                return
            
            print("\n📚 Available Strategies:")
            for i, name in enumerate(strategies, 1):
                print(f"  {i}. {name}")
            
            if not strategy_name:
                choice = input("\nSelect strategy number: ").strip()
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(strategies):
                        strategy_name = strategies[idx]
                    else:
                        print("❌ Invalid selection")
                        input("\nPress Enter to continue...")
                        return
                except ValueError:
                    print("❌ Invalid input")
                    input("\nPress Enter to continue...")
                    return
            
            print(f"\n📝 Exporting: {strategy_name}")
            print("\n🎯 Export Format:")
            print("  1. Python Class (standalone)")
            print("  2. JSON Configuration")
            print("  3. QuantConnect LEAN Algorithm")
            print("  4. All formats")
            
            format_choice = input("\nSelect format (1-4): ").strip()
            formats = {
                '1': ['python'],
                '2': ['json'],
                '3': ['lean'],
                '4': ['python', 'json', 'lean']
            }
            
            export_formats = formats.get(format_choice, ['python'])
            
            print("\n🔄 Exporting...")
            for fmt in export_formats:
                self.strategy_builder.export_for_live_trading(strategy_name, fmt)
            
            print(f"\n✅ Exported to: {self.strategy_builder.exports_dir}/")
            
            # Also create deployment package if StrategyExporter available
            if StrategyExporter and '4' in format_choice or input("\n📦 Create deployment package? (y/n): ").lower() == 'y':
                print("\n📦 Creating deployment package...")
                exporter = StrategyExporter()
                
                # Load strategy for package creation
                strategy_config = self.strategy_builder.load_strategy(strategy_name)
                
                # Create a mock strategy object for export
                class MockStrategy:
                    def __init__(self, config):
                        self.symbol = config.get('symbol', 'SPY')
                        self.lookback = config.get('lookback', 20)
                        self.initial_capital = config.get('initial_capital', 100000)
                        for key, value in config.items():
                            setattr(self, key, value)
                
                mock_strat = MockStrategy(strategy_config)
                exporter.create_deployment_package(strategy_name, mock_strat)
            
            print("\n📌 Next Steps:")
            print("  • Python: Import the class and use in your trading bot")
            print("  • JSON: Load config in your application")
            print("  • LEAN: Upload to QuantConnect or run with LEAN CLI")
            print("  • Deployment Package: See live_strategies/ directory")
            print("\n⚠️  Remember to:")
            print("  • Test thoroughly before using real capital")
            print("  • Configure API keys and broker connections")
            print("  • Set appropriate risk limits")
            
        except Exception as e:
            print(f"\n❌ Error exporting strategy: {e}")
            import traceback
            traceback.print_exc()
        
        input("\nPress Enter to continue...")
    
    def load_and_test_custom_strategy(self):
        """Load and test a custom strategy"""
        try:
            print("\n" + "="*80)
            print("🧪 LOAD & TEST CUSTOM STRATEGY")
            print("="*80)
            
            # List available strategies
            strategies = self.strategy_builder.list_strategies()
            if not strategies:
                print("\n❌ No custom strategies found. Create one first!")
                input("\nPress Enter to continue...")
                return
            
            print("\n📚 Available Strategies:")
            for i, name in enumerate(strategies, 1):
                strategy = self.strategy_builder.load_strategy(name)
                print(f"  {i}. {name}")
                print(f"      Type: {strategy['type']}, Indicators: {len(strategy['indicators'])}")
            
            choice = input("\nSelect strategy number: ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(strategies):
                    strategy_name = strategies[idx]
                else:
                    print("❌ Invalid selection")
                    input("\nPress Enter to continue...")
                    return
            except ValueError:
                print("❌ Invalid input")
                input("\nPress Enter to continue...")
                return
            
            strategy = self.strategy_builder.load_strategy(strategy_name)
            
            print(f"\n📋 Strategy: {strategy['name']}")
            print(f"📝 Description: {strategy['description']}")
            print(f"🎯 Type: {strategy['type']}")
            print(f"📊 Indicators: {', '.join(strategy['indicators'])}")
            print(f"\n📈 Entry Rules:")
            for i, rule in enumerate(strategy['entry_rules'], 1):
                print(f"   {i}. {rule}")
            print(f"\n📉 Exit Rules:")
            for i, rule in enumerate(strategy['exit_rules'], 1):
                print(f"   {i}. {rule}")
            print(f"\n🛡️  Risk Management:")
            for key, value in strategy['risk_management'].items():
                print(f"   {key}: {value}")
            
            print("\n⚠️  Note: Custom strategies require manual implementation of logic.")
            print("This shows the strategy configuration. To backtest, you need to:")
            print("  1. Export the strategy (option 31)")
            print("  2. Implement the entry/exit logic in the generated code")
            print("  3. Run backtests using the exported code")
            
        except Exception as e:
            print(f"\n❌ Error loading strategy: {e}")
            import traceback
            traceback.print_exc()
        
        input("\nPress Enter to continue...")
    
    def manage_portfolios_menu(self):
        """Portfolio management submenu"""
        while True:
            print("\n" + "═" * 60)
            print("PORTFOLIO MANAGEMENT")
            print("═" * 60)
            print("  1. Create New Portfolio")
            print("  2. View All Portfolios")
            print("  3. Compare Portfolios")
            print("  4. Edit Portfolio")
            print("  5. Delete Portfolio")
            print("  0. Back to Main Menu")
            print("═" * 60)
            
            choice = input("\nEnter choice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.create_portfolio()
            elif choice == '2':
                self.view_portfolios()
            elif choice == '3':
                self.compare_portfolios()
            elif choice == '4':
                self.edit_portfolio()
            elif choice == '5':
                self.delete_portfolio()
            else:
                print("❌ Invalid choice!")
            
            if choice != '0':
                input("\nPress Enter to continue...")
    
    def manage_strategies_menu(self):
        """Strategy management submenu"""
        while True:
            print("\n" + "═" * 60)
            print("STRATEGY MANAGEMENT")
            print("═" * 60)
            print("  1. Save Current Strategy Configuration")
            print("  2. Load & Run Saved Strategy")
            print("  3. View All Saved Strategies")
            print("  4. Clone/Modify Strategy")
            print("  5. Export/Import Strategies")
            print("  6. Strategy Performance Leaderboard")
            print("  0. Back to Main Menu")
            print("═" * 60)
            
            choice = input("\nEnter choice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.save_strategy_config()
            elif choice == '2':
                self.load_and_run_strategy()
            elif choice == '3':
                self.view_saved_strategies()
            elif choice == '4':
                self.clone_modify_strategy()
            elif choice == '5':
                self.export_import_strategies()
            elif choice == '6':
                self.strategy_leaderboard()
            else:
                print("❌ Invalid choice!")
            
            if choice != '0':
                input("\nPress Enter to continue...")
    
    def view_performance_reports(self):
        """View performance reports submenu"""
        while True:
            print("\n" + "═" * 60)
            print("PERFORMANCE REPORTS")
            print("═" * 60)
            print("  1. View All Results History")
            print("  2. Filter Results (by symbol, strategy, date)")
            print("  3. Export Results to CSV")
            print("  4. Risk Analysis Dashboard")
            print("  5. Correlation Analysis")
            print("  0. Back to Main Menu")
            print("═" * 60)
            
            choice = input("\nEnter choice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.view_history()
            elif choice == '2':
                self.filter_results()
            elif choice == '3':
                self.export_results()
            elif choice == '4':
                self.risk_analysis_dashboard()
            elif choice == '5':
                self.correlation_analysis_menu()
            else:
                print("❌ Invalid choice!")
            
            if choice != '0':
                input("\nPress Enter to continue...")
    
    def run(self):
        """Main interface loop"""
        while True:
            self.print_header()
            self.print_main_menu()
            
            choice = input("Enter your choice: ").strip()
            
            if choice == '0':
                print("\n👋 Exiting... Happy trading! 🚀\n")
                break
            elif choice == '1':
                self.run_single_strategy()
                input("\n\nPress Enter to continue...")
            elif choice == '2':
                self.run_portfolio_backtest()
                input("\n\nPress Enter to continue...")
            elif choice == '3':
                self.compare_all_strategies()
                input("\n\nPress Enter to continue...")
            elif choice == '4':
                self.technical_analysis_dashboard()
                input("\n\nPress Enter to continue...")
            elif choice == '5':
                self.create_custom_strategy()
                input("\n\nPress Enter to continue...")
            elif choice == '6':
                self.optimize_strategy_menu()
                input("\n\nPress Enter to continue...")
            elif choice == '7':
                self.market_analytics_menu()
                input("\n\nPress Enter to continue...")
            elif choice == '8':
                self.manage_portfolios_menu()
                input("\n\nPress Enter to continue...")
            elif choice == '9':
                self.manage_strategies_menu()
                input("\n\nPress Enter to continue...")
            elif choice == '10':
                self.advanced_settings_menu()
                input("\n\nPress Enter to continue...")
            elif choice == '11':
                self.export_strategy_for_live()
                input("\n\nPress Enter to continue...")
            elif choice == '12':
                self.view_performance_reports()
                input("\n\nPress Enter to continue...")
            elif choice == '13':
                self.show_help()
                input("\n\nPress Enter to continue...")
            else:
                print("\n❌ Invalid choice!")
                input("\nPress Enter to continue...")


if __name__ == "__main__":
    interface = AdvancedTradingInterface()
    interface.run()
