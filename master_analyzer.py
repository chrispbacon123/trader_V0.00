"""
Master Integration Module
Clean, well-factored pipeline for all analysis
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import pandas as pd

from canonical_data import FETCHER
from validated_indicators import compute_all_indicators
from validated_levels import compute_all_levels
from validated_regime import compute_regime
from validated_risk import compute_risk_metrics
from validated_portfolio import ValidatedPortfolio


class TradingAnalyzer:
    """
    Master analyzer with deterministic, reproducible pipeline:
    1. fetch_data
    2. compute_indicators
    3. compute_levels
    4. compute_risk
    5. classify_regime
    6. allocate_portfolio (optional)
    """
    
    def __init__(self):
        self.fetcher = FETCHER
        self.data = None
        self.metadata = None
        self.symbol = None
    
    def analyze(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        verbose: bool = True
    ) -> Dict:
        """
        Complete analysis pipeline
        
        Returns comprehensive results dict
        """
        # Step 1: Fetch data
        if verbose:
            print(f"\n{'='*80}")
            print(f"TRADING ANALYSIS: {symbol}")
            print(f"{'='*80}\n")
            print("Step 1: Fetching data...")
        
        self.data, self.metadata = self.fetcher.fetch_data(
            symbol, start_date, end_date
        )
        self.symbol = symbol
        
        if verbose:
            self.fetcher.print_data_summary(self.data, self.metadata)
        
        # Step 2: Compute indicators
        if verbose:
            print("Step 2: Computing indicators...")
        
        self.data = compute_all_indicators(self.data)
        
        # Step 3: Compute key levels
        if verbose:
            print("Step 3: Computing key levels...")
        
        levels = compute_all_levels(self.data, verbose=verbose)
        
        # Step 4: Classify regime
        if verbose:
            print("Step 4: Classifying market regime...")
        
        regime = compute_regime(self.data, verbose=verbose)
        
        # Step 5: Compute risk metrics
        if verbose:
            print("Step 5: Computing risk metrics...")
        
        returns = self.fetcher.get_returns(self.data)
        risk = compute_risk_metrics(returns, verbose=verbose)
        
        # Compile results
        results = {
            'symbol': symbol,
            'metadata': self.metadata,
            'data': self.data,
            'returns': returns,
            'indicators': {
                'RSI': self.data['RSI'].iloc[-1],
                'MACD': self.data['MACD'].iloc[-1],
                'MACD_Signal': self.data['MACD_Signal'].iloc[-1],
                'MACD_Hist': self.data['MACD_Hist'].iloc[-1],
                'ADX': self.data['ADX'].iloc[-1],
                'Stoch_K': self.data['Stoch_K'].iloc[-1],
                'Stoch_D': self.data['Stoch_D'].iloc[-1]
            },
            'levels': levels,
            'regime': regime,
            'risk': risk
        }
        
        if verbose:
            self._print_summary(results)
        
        return results
    
    def quick_analysis(
        self,
        symbol: str,
        days: int = 252,
        verbose: bool = True
    ) -> Dict:
        """Convenience method with days instead of dates"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return self.analyze(symbol, start_date, end_date, verbose)
    
    def _print_summary(self, results: Dict):
        """Print executive summary"""
        print(f"\n{'='*80}")
        print("EXECUTIVE SUMMARY")
        print(f"{'='*80}")
        
        ind = results['indicators']
        print(f"\nTechnical Indicators:")
        print(f"  RSI:         {ind['RSI']:.2f}")
        print(f"  MACD:        {ind['MACD']:.2f}")
        print(f"  MACD Signal: {ind['MACD_Signal']:.2f}")
        print(f"  MACD Hist:   {ind['MACD_Hist']:.2f}")
        print(f"  ADX:         {ind['ADX']:.2f}")
        print(f"  Stoch %K:    {ind['Stoch_K']:.2f}")
        print(f"  Stoch %D:    {ind['Stoch_D']:.2f}")
        
        regime = results['regime']
        print(f"\nMarket Regime:")
        print(f"  Classification: {regime['regime'].upper().replace('_', ' ')}")
        print(f"  Confidence:     {regime['confidence']*100:.1f}%")
        
        risk = results['risk']
        print(f"\nRisk Summary:")
        print(f"  Volatility:     {risk['volatility']['volatility_annualized_pct']:.2f}% (ann)")
        print(f"  Sharpe Ratio:   {risk['sharpe_ratio']['sharpe_ratio']:.4f}")
        print(f"  Max Drawdown:   {risk['max_drawdown']['max_drawdown_pct']:.2f}%")
        print(f"  VaR (95%):      {risk['var']['var_pct']:.4f}%")
        
        print(f"{'='*80}\n")
    
    def compare_symbols(
        self,
        symbols: list,
        days: int = 252,
        verbose: bool = False
    ) -> Dict:
        """
        Compare multiple symbols
        
        Returns comparison table
        """
        results = {}
        
        for symbol in symbols:
            try:
                result = self.quick_analysis(symbol, days, verbose=False)
                results[symbol] = result
            except Exception as e:
                print(f"Error analyzing {symbol}: {e}")
                continue
        
        # Build comparison table
        comparison = {
            'symbol': [],
            'current_price': [],
            'volatility_pct': [],
            'sharpe': [],
            'max_dd_pct': [],
            'var_95_pct': [],
            'regime': [],
            'rsi': [],
            'adx': []
        }
        
        for symbol, result in results.items():
            comparison['symbol'].append(symbol)
            comparison['current_price'].append(result['data']['Price'].iloc[-1])
            comparison['volatility_pct'].append(
                result['risk']['volatility']['volatility_annualized_pct']
            )
            comparison['sharpe'].append(
                result['risk']['sharpe_ratio']['sharpe_ratio']
            )
            comparison['max_dd_pct'].append(
                abs(result['risk']['max_drawdown']['max_drawdown_pct'])
            )
            comparison['var_95_pct'].append(
                abs(result['risk']['var']['var_pct'])
            )
            comparison['regime'].append(
                result['regime']['regime']
            )
            comparison['rsi'].append(
                result['indicators']['RSI']
            )
            comparison['adx'].append(
                result['indicators']['ADX']
            )
        
        df = pd.DataFrame(comparison)
        
        if verbose:
            print(f"\n{'='*80}")
            print("SYMBOL COMPARISON")
            print(f"{'='*80}\n")
            print(df.to_string(index=False))
            print(f"\n{'='*80}\n")
        
        return {
            'comparison_table': df,
            'detailed_results': results
        }
    
    def backtest_strategy(
        self,
        symbol: str,
        strategy_func,
        days: int = 252,
        initial_capital: float = 100000
    ) -> Dict:
        """
        Backtest a trading strategy
        
        Args:
            symbol: Symbol to trade
            strategy_func: Function that takes df and returns signals
            days: Lookback period
            initial_capital: Starting capital
            
        Returns:
            Backtest results
        """
        # Get data
        result = self.quick_analysis(symbol, days, verbose=False)
        df = result['data'].copy()
        
        # Generate signals
        signals = strategy_func(df)
        
        # Simple backtest
        positions = []
        cash = initial_capital
        shares = 0
        
        for i in range(len(df)):
            price = df['Price'].iloc[i]
            signal = signals.iloc[i] if i < len(signals) else 0
            
            if signal > 0 and shares == 0:  # Buy
                shares = cash / price
                cash = 0
                positions.append({'date': df.index[i], 'action': 'BUY', 'price': price, 'shares': shares})
            
            elif signal < 0 and shares > 0:  # Sell
                cash = shares * price
                positions.append({'date': df.index[i], 'action': 'SELL', 'price': price, 'shares': shares})
                shares = 0
        
        # Final value
        final_price = df['Price'].iloc[-1]
        final_value = cash + (shares * final_price)
        total_return = (final_value - initial_capital) / initial_capital
        
        return {
            'initial_capital': initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'trades': positions,
            'num_trades': len(positions)
        }


# Convenience instance
ANALYZER = TradingAnalyzer()
