#!/usr/bin/env python3
"""
Interactive Trading Strategy CLI
Run, compare, and manage trading strategies
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import json

# Import strategies
from simple_strategy import SimpleMeanReversionStrategy
from ml_strategy import MLTradingStrategy
from optimized_ml_strategy import OptimizedMLStrategy

class TradingCLI:
    def __init__(self):
        self.results_history = []
        self.load_history()
        
    def load_history(self):
        """Load previous results from history file"""
        history_file = 'strategy_history.json'
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    self.results_history = json.load(f)
            except:
                self.results_history = []
    
    def save_history(self):
        """Save results to history file"""
        with open('strategy_history.json', 'w') as f:
            json.dump(self.results_history, f, indent=2, default=str)
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def print_header(self):
        """Print CLI header"""
        self.clear_screen()
        print("=" * 70)
        print("🚀 ALGORITHMIC TRADING STRATEGY MANAGER")
        print("=" * 70)
        print()
    
    def print_menu(self):
        """Print main menu"""
        print("MAIN MENU:")
        print("-" * 70)
        print("1. Run Simple Mean Reversion Strategy")
        print("2. Run ML-Powered Strategy (Single Model)")
        print("3. Run Optimized ML Ensemble Strategy")
        print("4. Compare All Strategies")
        print("5. View Results History")
        print("6. Custom Strategy Run (Choose symbol, dates)")
        print("7. Export Results to CSV")
        print("8. Clear History")
        print("0. Exit")
        print("-" * 70)
        print()
    
    def run_simple_strategy(self, symbol='SPY', days=365):
        """Run simple mean reversion strategy"""
        print("\n" + "="*70)
        print(f"RUNNING: Simple Mean Reversion Strategy ({symbol})")
        print("="*70 + "\n")
        
        strategy = SimpleMeanReversionStrategy(symbol=symbol, lookback=20, std_dev=2)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        data, trades, final_value = strategy.backtest(start_date, end_date)
        strategy.print_results(final_value, trades)
        
        # Save results
        result = {
            'timestamp': datetime.now().isoformat(),
            'strategy': 'Simple Mean Reversion',
            'symbol': symbol,
            'period_days': days,
            'initial_capital': 100000,
            'final_value': final_value,
            'return_pct': ((final_value - 100000) / 100000) * 100,
            'total_trades': len(trades)
        }
        self.results_history.append(result)
        self.save_history()
        
        return result
    
    def run_ml_strategy(self, symbol='SPY', days=730):
        """Run ML-powered strategy"""
        print("\n" + "="*70)
        print(f"RUNNING: ML-Powered Strategy ({symbol})")
        print("="*70 + "\n")
        
        strategy = MLTradingStrategy(symbol=symbol, lookback=60, prediction_horizon=5)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        df_test, trades, final_value, equity_curve = strategy.backtest(start_date, end_date)
        strategy.print_results(final_value, trades, equity_curve)
        
        # Calculate metrics
        equity_df = pd.DataFrame(equity_curve)
        if len(equity_df) > 1:
            equity_df['Returns'] = equity_df['Value'].pct_change()
            sharpe = (equity_df['Returns'].mean() / equity_df['Returns'].std()) * (252**0.5)
            max_dd = ((equity_df['Value'].cummax() - equity_df['Value']) / equity_df['Value'].cummax()).max() * 100
        else:
            sharpe, max_dd = 0, 0
        
        wins = sum(1 for i in range(0, len(trades)-1, 2) if i+1 < len(trades) and trades[i+1][2] > trades[i][2])
        win_rate = (wins / (len(trades)//2) * 100) if len(trades) > 0 else 0
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'strategy': 'ML Single Model',
            'symbol': symbol,
            'period_days': days,
            'initial_capital': 100000,
            'final_value': final_value,
            'return_pct': ((final_value - 100000) / 100000) * 100,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'total_trades': len(trades),
            'win_rate': win_rate
        }
        self.results_history.append(result)
        self.save_history()
        
        return result
    
    def run_optimized_strategy(self, symbol='SPY', days=730, n_trials=20):
        """Run optimized ML ensemble strategy"""
        print("\n" + "="*70)
        print(f"RUNNING: Optimized ML Ensemble Strategy ({symbol})")
        print("="*70 + "\n")
        
        strategy = OptimizedMLStrategy(symbol=symbol, lookback=60, prediction_horizon=5)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        df_test, trades, final_value, equity = strategy.backtest(
            start_date, end_date, optimize_params=True, n_trials=n_trials
        )
        strategy.print_results(final_value, trades, equity)
        
        # Calculate metrics
        equity_df = pd.DataFrame(equity)
        if len(equity_df) > 1:
            equity_df['Returns'] = equity_df['Value'].pct_change()
            sharpe = (equity_df['Returns'].mean() / equity_df['Returns'].std()) * (252**0.5)
            max_dd = ((equity_df['Value'].cummax() - equity_df['Value']) / equity_df['Value'].cummax()).max() * 100
        else:
            sharpe, max_dd = 0, 0
        
        wins = sum(1 for i in range(0, len(trades)-1, 2) if i+1 < len(trades) and trades[i+1][2] > trades[i][2])
        win_rate = (wins / (len(trades)//2) * 100) if len(trades) > 0 else 0
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'strategy': 'Optimized Ensemble',
            'symbol': symbol,
            'period_days': days,
            'initial_capital': 100000,
            'final_value': final_value,
            'return_pct': ((final_value - 100000) / 100000) * 100,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'total_trades': len(trades),
            'win_rate': win_rate,
            'n_trials': n_trials
        }
        self.results_history.append(result)
        self.save_history()
        
        return result
    
    def compare_all_strategies(self, symbol='SPY', days=730):
        """Run and compare all three strategies"""
        print("\n" + "="*70)
        print("RUNNING ALL STRATEGIES FOR COMPARISON")
        print("="*70 + "\n")
        
        results = []
        
        # Run all strategies
        print("Running Simple Strategy...")
        results.append(self.run_simple_strategy(symbol, days))
        input("\nPress Enter to continue to next strategy...")
        
        print("\nRunning ML Strategy...")
        results.append(self.run_ml_strategy(symbol, days))
        input("\nPress Enter to continue to next strategy...")
        
        print("\nRunning Optimized Ensemble...")
        results.append(self.run_optimized_strategy(symbol, days, n_trials=15))
        
        # Print comparison
        self.print_comparison(results)
        
    def print_comparison(self, results=None):
        """Print comparison table of strategies"""
        if results is None:
            results = self.results_history[-3:] if len(self.results_history) >= 3 else self.results_history
        
        if not results:
            print("\nNo results to compare yet. Run some strategies first!")
            return
        
        print("\n" + "="*70)
        print("STRATEGY COMPARISON")
        print("="*70)
        
        # Create comparison table
        print(f"\n{'Strategy':<25} {'Return':>10} {'Sharpe':>8} {'MaxDD':>8} {'Trades':>8} {'WinRate':>8}")
        print("-" * 70)
        
        for r in results:
            strategy_name = r['strategy']
            return_pct = r.get('return_pct', 0)
            sharpe = r.get('sharpe_ratio', 'N/A')
            max_dd = r.get('max_drawdown', 'N/A')
            trades = r.get('total_trades', 0)
            win_rate = r.get('win_rate', 'N/A')
            
            sharpe_str = f"{sharpe:.2f}" if isinstance(sharpe, (int, float)) else str(sharpe)
            max_dd_str = f"{max_dd:.2f}%" if isinstance(max_dd, (int, float)) else str(max_dd)
            win_rate_str = f"{win_rate:.1f}%" if isinstance(win_rate, (int, float)) else str(win_rate)
            
            print(f"{strategy_name:<25} {return_pct:>9.2f}% {sharpe_str:>8} {max_dd_str:>8} {trades:>8} {win_rate_str:>8}")
        
        print("="*70)
        
        # Highlight winner
        if len(results) > 0:
            best_return = max(results, key=lambda x: x.get('return_pct', 0))
            best_sharpe = max([r for r in results if isinstance(r.get('sharpe_ratio'), (int, float))], 
                            key=lambda x: x.get('sharpe_ratio', 0), default=None)
            
            print(f"\n🏆 Best Return: {best_return['strategy']} ({best_return['return_pct']:.2f}%)")
            if best_sharpe:
                print(f"🏆 Best Sharpe: {best_sharpe['strategy']} ({best_sharpe['sharpe_ratio']:.2f})")
    
    def view_history(self):
        """View results history"""
        print("\n" + "="*70)
        print("RESULTS HISTORY")
        print("="*70)
        
        if not self.results_history:
            print("\nNo history yet. Run some strategies first!")
            return
        
        print(f"\nTotal runs: {len(self.results_history)}")
        print("\nRecent runs:")
        print("-" * 70)
        
        for i, r in enumerate(self.results_history[-10:], 1):
            timestamp = datetime.fromisoformat(r['timestamp']).strftime('%Y-%m-%d %H:%M')
            print(f"{i}. [{timestamp}] {r['strategy']} on {r['symbol']}: {r['return_pct']:.2f}% return")
        
        print()
    
    def custom_run(self):
        """Custom strategy run with user inputs"""
        print("\n" + "="*70)
        print("CUSTOM STRATEGY RUN")
        print("="*70)
        
        # Get strategy choice
        print("\nChoose strategy:")
        print("1. Simple Mean Reversion")
        print("2. ML Single Model")
        print("3. Optimized Ensemble")
        
        strategy_choice = input("\nEnter strategy number (1-3): ").strip()
        
        # Get symbol
        symbol = input("Enter symbol (default: SPY): ").strip().upper() or 'SPY'
        
        # Get time period
        days = input("Enter lookback period in days (default: 730): ").strip()
        days = int(days) if days.isdigit() else 730
        
        # Run selected strategy
        if strategy_choice == '1':
            self.run_simple_strategy(symbol, days)
        elif strategy_choice == '2':
            self.run_ml_strategy(symbol, days)
        elif strategy_choice == '3':
            n_trials = input("Enter number of optimization trials (default: 20): ").strip()
            n_trials = int(n_trials) if n_trials.isdigit() else 20
            self.run_optimized_strategy(symbol, days, n_trials)
        else:
            print("Invalid choice!")
    
    def export_results(self):
        """Export results to CSV"""
        if not self.results_history:
            print("\nNo results to export!")
            return
        
        df = pd.DataFrame(self.results_history)
        filename = f"strategy_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        print(f"\n✅ Results exported to: {filename}")
    
    def clear_history(self):
        """Clear results history"""
        confirm = input("\n⚠️  Are you sure you want to clear all history? (yes/no): ").strip().lower()
        if confirm == 'yes':
            self.results_history = []
            self.save_history()
            print("\n✅ History cleared!")
        else:
            print("\nCancelled.")
    
    def run(self):
        """Main CLI loop"""
        while True:
            self.print_header()
            self.print_menu()
            
            choice = input("Enter your choice (0-8): ").strip()
            
            if choice == '0':
                print("\nExiting... Good luck with your trading! 🚀\n")
                break
            elif choice == '1':
                self.run_simple_strategy()
                input("\nPress Enter to continue...")
            elif choice == '2':
                self.run_ml_strategy()
                input("\nPress Enter to continue...")
            elif choice == '3':
                self.run_optimized_strategy()
                input("\nPress Enter to continue...")
            elif choice == '4':
                self.compare_all_strategies()
                input("\nPress Enter to continue...")
            elif choice == '5':
                self.view_history()
                input("\nPress Enter to continue...")
            elif choice == '6':
                self.custom_run()
                input("\nPress Enter to continue...")
            elif choice == '7':
                self.export_results()
                input("\nPress Enter to continue...")
            elif choice == '8':
                self.clear_history()
                input("\nPress Enter to continue...")
            else:
                print("\n❌ Invalid choice! Please try again.")
                input("\nPress Enter to continue...")

if __name__ == "__main__":
    cli = TradingCLI()
    cli.run()
