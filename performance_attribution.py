"""
Performance Attribution - Comprehensive analysis of strategy returns
"""

import numpy as np
import pandas as pd
from scipy import stats
from datetime import datetime, timedelta


class PerformanceAttribution:
    """Detailed performance attribution and analysis"""
    
    def __init__(self):
        self.risk_free_rate = 0.02  # 2% annual
        
    def calculate_returns_metrics(self, returns, benchmark_returns=None):
        """Calculate comprehensive return metrics"""
        if len(returns) == 0:
            return {}
        
        returns_clean = returns.dropna()
        
        metrics = {
            'total_return': (1 + returns_clean).prod() - 1,
            'annualized_return': self.annualize_return(returns_clean),
            'volatility': returns_clean.std() * np.sqrt(252),
            'sharpe_ratio': self.calculate_sharpe(returns_clean),
            'sortino_ratio': self.calculate_sortino(returns_clean),
            'calmar_ratio': self.calculate_calmar(returns_clean),
            'max_drawdown': self.calculate_max_drawdown(returns_clean),
            'win_rate': (returns_clean > 0).sum() / len(returns_clean),
            'profit_factor': self.calculate_profit_factor(returns_clean),
            'skewness': stats.skew(returns_clean),
            'kurtosis': stats.kurtosis(returns_clean),
            'var_95': returns_clean.quantile(0.05),
            'cvar_95': returns_clean[returns_clean <= returns_clean.quantile(0.05)].mean(),
        }
        
        # Add benchmark comparison if provided
        if benchmark_returns is not None and len(benchmark_returns) > 0:
            benchmark_clean = benchmark_returns.dropna()
            aligned_returns, aligned_benchmark = returns_clean.align(benchmark_clean, join='inner')
            
            if len(aligned_returns) > 0:
                metrics['alpha'] = self.calculate_alpha(aligned_returns, aligned_benchmark)
                metrics['beta'] = self.calculate_beta(aligned_returns, aligned_benchmark)
                metrics['information_ratio'] = self.calculate_information_ratio(aligned_returns, aligned_benchmark)
                metrics['tracking_error'] = (aligned_returns - aligned_benchmark).std() * np.sqrt(252)
        
        return metrics
    
    def annualize_return(self, returns):
        """Annualize returns"""
        if len(returns) == 0:
            return 0
        total_return = (1 + returns).prod() - 1
        years = len(returns) / 252
        if years > 0:
            return (1 + total_return) ** (1 / years) - 1
        return 0
    
    def calculate_sharpe(self, returns, risk_free_rate=None):
        """Calculate Sharpe ratio"""
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        if returns.std() == 0:
            return 0
        
        excess_returns = returns - risk_free_rate / 252
        return np.sqrt(252) * excess_returns.mean() / returns.std()
    
    def calculate_sortino(self, returns, risk_free_rate=None):
        """Calculate Sortino ratio (downside deviation)"""
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0
        
        excess_returns = returns - risk_free_rate / 252
        return np.sqrt(252) * excess_returns.mean() / downside_returns.std()
    
    def calculate_calmar(self, returns):
        """Calculate Calmar ratio (return / max drawdown)"""
        max_dd = abs(self.calculate_max_drawdown(returns))
        if max_dd == 0:
            return 0
        
        ann_return = self.annualize_return(returns)
        return ann_return / max_dd
    
    def calculate_max_drawdown(self, returns):
        """Calculate maximum drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def calculate_profit_factor(self, returns):
        """Calculate profit factor (gross profits / gross losses)"""
        profits = returns[returns > 0].sum()
        losses = abs(returns[returns < 0].sum())
        
        if losses == 0:
            return np.inf if profits > 0 else 0
        
        return profits / losses
    
    def calculate_alpha(self, returns, benchmark_returns):
        """Calculate Jensen's alpha"""
        beta = self.calculate_beta(returns, benchmark_returns)
        
        strategy_return = self.annualize_return(returns)
        benchmark_return = self.annualize_return(benchmark_returns)
        
        alpha = strategy_return - (self.risk_free_rate + beta * (benchmark_return - self.risk_free_rate))
        return alpha
    
    def calculate_beta(self, returns, benchmark_returns):
        """Calculate beta relative to benchmark"""
        if len(returns) < 2 or len(benchmark_returns) < 2:
            return 1.0
        
        covariance = returns.cov(benchmark_returns)
        benchmark_variance = benchmark_returns.var()
        
        if benchmark_variance == 0:
            return 1.0
        
        return covariance / benchmark_variance
    
    def calculate_information_ratio(self, returns, benchmark_returns):
        """Calculate information ratio"""
        active_returns = returns - benchmark_returns
        
        if active_returns.std() == 0:
            return 0
        
        return np.sqrt(252) * active_returns.mean() / active_returns.std()
    
    def decompose_returns(self, returns, factors):
        """Decompose returns into factor contributions"""
        if factors.empty:
            return {'unexplained': returns.sum()}
        
        # Simple linear regression attribution
        factor_contributions = {}
        
        for factor_name in factors.columns:
            factor_values = factors[factor_name]
            aligned_returns, aligned_factor = returns.align(factor_values, join='inner')
            
            if len(aligned_returns) > 1 and aligned_factor.std() > 0:
                # Calculate correlation-based contribution
                correlation = aligned_returns.corr(aligned_factor)
                contribution = correlation * aligned_factor.std() * aligned_returns.std()
                factor_contributions[factor_name] = contribution
        
        # Calculate unexplained portion
        total_explained = sum(factor_contributions.values())
        factor_contributions['unexplained'] = returns.std() - total_explained
        
        return factor_contributions
    
    def calculate_rolling_metrics(self, returns, window=60):
        """Calculate rolling performance metrics"""
        rolling_metrics = pd.DataFrame(index=returns.index)
        
        rolling_metrics['rolling_return'] = returns.rolling(window).sum()
        rolling_metrics['rolling_vol'] = returns.rolling(window).std() * np.sqrt(252)
        rolling_metrics['rolling_sharpe'] = (
            returns.rolling(window).mean() / returns.rolling(window).std() * np.sqrt(252)
        )
        
        # Rolling max drawdown
        cumulative = (1 + returns).cumprod()
        rolling_max = cumulative.rolling(window, min_periods=1).max()
        rolling_metrics['rolling_drawdown'] = (cumulative - rolling_max) / rolling_max
        
        return rolling_metrics
    
    def analyze_drawdowns(self, returns):
        """Detailed drawdown analysis"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        
        # Find drawdown periods
        is_dd = drawdown < 0
        dd_periods = []
        
        in_dd = False
        start_idx = None
        
        for idx, value in is_dd.items():
            if value and not in_dd:
                # Start of drawdown
                start_idx = idx
                in_dd = True
            elif not value and in_dd:
                # End of drawdown
                dd_periods.append({
                    'start': start_idx,
                    'end': idx,
                    'depth': drawdown[start_idx:idx].min(),
                    'length': len(returns[start_idx:idx])
                })
                in_dd = False
        
        # Sort by depth
        dd_periods.sort(key=lambda x: x['depth'])
        
        return {
            'max_drawdown': drawdown.min(),
            'avg_drawdown': drawdown[drawdown < 0].mean() if (drawdown < 0).any() else 0,
            'num_drawdowns': len(dd_periods),
            'top_5_drawdowns': dd_periods[:5],
            'avg_recovery_time': np.mean([dd['length'] for dd in dd_periods]) if dd_periods else 0
        }
    
    def calculate_regime_performance(self, returns, market_returns):
        """Analyze performance in different market regimes"""
        # Define regimes based on market performance
        regimes = pd.Series('NEUTRAL', index=returns.index)
        
        market_vol = market_returns.rolling(20).std()
        vol_median = market_vol.median()
        
        # Volatility regimes
        regimes[market_vol > vol_median * 1.5] = 'HIGH_VOL'
        regimes[market_vol < vol_median * 0.5] = 'LOW_VOL'
        
        # Trend regimes
        market_sma = market_returns.rolling(50).mean()
        regimes[market_sma > 0.001] = 'BULL'
        regimes[market_sma < -0.001] = 'BEAR'
        
        # Calculate performance by regime
        regime_performance = {}
        
        for regime in regimes.unique():
            regime_returns = returns[regimes == regime]
            if len(regime_returns) > 0:
                regime_performance[regime] = {
                    'return': regime_returns.mean() * 252,
                    'volatility': regime_returns.std() * np.sqrt(252),
                    'sharpe': self.calculate_sharpe(regime_returns),
                    'num_periods': len(regime_returns)
                }
        
        return regime_performance
    
    def trade_level_attribution(self, trades_df):
        """Attribute performance to individual trades"""
        if trades_df.empty or 'pnl' not in trades_df.columns:
            return {}
        
        winning_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] < 0]
        
        attribution = {
            'num_trades': len(trades_df),
            'num_winners': len(winning_trades),
            'num_losers': len(losing_trades),
            'win_rate': len(winning_trades) / len(trades_df) if len(trades_df) > 0 else 0,
            'avg_win': winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0,
            'avg_loss': losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0,
            'largest_win': winning_trades['pnl'].max() if len(winning_trades) > 0 else 0,
            'largest_loss': losing_trades['pnl'].min() if len(losing_trades) > 0 else 0,
            'avg_hold_time': trades_df.get('hold_time', pd.Series()).mean() if 'hold_time' in trades_df.columns else 0
        }
        
        # Win/loss ratio
        if attribution['avg_loss'] != 0:
            attribution['win_loss_ratio'] = abs(attribution['avg_win'] / attribution['avg_loss'])
        else:
            attribution['win_loss_ratio'] = np.inf if attribution['avg_win'] > 0 else 0
        
        # Expectancy
        attribution['expectancy'] = (
            attribution['win_rate'] * attribution['avg_win'] +
            (1 - attribution['win_rate']) * attribution['avg_loss']
        )
        
        return attribution
    
    def print_performance_report(self, returns, benchmark_returns=None, trades_df=None):
        """Print comprehensive performance report"""
        print("\n" + "="*80)
        print("PERFORMANCE ATTRIBUTION REPORT")
        print("="*80)
        
        # Overall metrics
        metrics = self.calculate_returns_metrics(returns, benchmark_returns)
        
        print("\n📊 RETURN METRICS")
        print(f"  Total Return:        {metrics.get('total_return', 0)*100:>8.2f}%")
        print(f"  Annualized Return:   {metrics.get('annualized_return', 0)*100:>8.2f}%")
        print(f"  Volatility:          {metrics.get('volatility', 0)*100:>8.2f}%")
        
        print("\n📈 RISK-ADJUSTED METRICS")
        print(f"  Sharpe Ratio:        {metrics.get('sharpe_ratio', 0):>8.2f}")
        print(f"  Sortino Ratio:       {metrics.get('sortino_ratio', 0):>8.2f}")
        print(f"  Calmar Ratio:        {metrics.get('calmar_ratio', 0):>8.2f}")
        
        print("\n⚠️  RISK METRICS")
        print(f"  Max Drawdown:        {metrics.get('max_drawdown', 0)*100:>8.2f}%")
        print(f"  VaR (95%):          {metrics.get('var_95', 0)*100:>8.2f}%")
        print(f"  CVaR (95%):         {metrics.get('cvar_95', 0)*100:>8.2f}%")
        
        print("\n🎯 TRADE STATISTICS")
        print(f"  Win Rate:            {metrics.get('win_rate', 0)*100:>8.2f}%")
        print(f"  Profit Factor:       {metrics.get('profit_factor', 0):>8.2f}")
        
        if benchmark_returns is not None:
            print("\n🏁 BENCHMARK COMPARISON")
            print(f"  Alpha:               {metrics.get('alpha', 0)*100:>8.2f}%")
            print(f"  Beta:                {metrics.get('beta', 0):>8.2f}")
            print(f"  Information Ratio:   {metrics.get('information_ratio', 0):>8.2f}")
            print(f"  Tracking Error:      {metrics.get('tracking_error', 0)*100:>8.2f}%")
        
        # Drawdown analysis
        dd_analysis = self.analyze_drawdowns(returns)
        print("\n📉 DRAWDOWN ANALYSIS")
        print(f"  Max Drawdown:        {dd_analysis['max_drawdown']*100:>8.2f}%")
        print(f"  Average Drawdown:    {dd_analysis['avg_drawdown']*100:>8.2f}%")
        print(f"  Number of Drawdowns: {dd_analysis['num_drawdowns']:>8}")
        print(f"  Avg Recovery Time:   {dd_analysis['avg_recovery_time']:>8.1f} days")
        
        # Trade-level attribution
        if trades_df is not None and not trades_df.empty:
            trade_attr = self.trade_level_attribution(trades_df)
            print("\n💰 TRADE-LEVEL ATTRIBUTION")
            print(f"  Total Trades:        {trade_attr['num_trades']:>8}")
            print(f"  Winners:             {trade_attr['num_winners']:>8}")
            print(f"  Losers:              {trade_attr['num_losers']:>8}")
            print(f"  Avg Win:            ${trade_attr['avg_win']:>8.2f}")
            print(f"  Avg Loss:           ${trade_attr['avg_loss']:>8.2f}")
            print(f"  Win/Loss Ratio:      {trade_attr['win_loss_ratio']:>8.2f}")
            print(f"  Expectancy:         ${trade_attr['expectancy']:>8.2f}")
        
        print("\n" + "="*80)
