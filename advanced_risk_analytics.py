"""
Advanced Risk Analytics Module
Provides sophisticated risk metrics and analysis tools
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class AdvancedRiskAnalytics:
    """Advanced risk analytics for trading strategies"""
    
    def __init__(self, returns: pd.Series, confidence_level: float = 0.95):
        """
        Initialize with return series
        
        Args:
            returns: Series of returns
            confidence_level: Confidence level for VaR/CVaR calculations
        """
        self.returns = returns.dropna()
        self.confidence_level = confidence_level
        
    def value_at_risk(self, method: str = 'historical') -> float:
        """
        Calculate Value at Risk
        
        Args:
            method: 'historical', 'parametric', or 'cornish_fisher'
        """
        if len(self.returns) == 0:
            return 0.0
            
        if method == 'historical':
            return float(np.percentile(self.returns, (1 - self.confidence_level) * 100))
        
        elif method == 'parametric':
            mu = float(self.returns.mean())
            sigma = float(self.returns.std())
            z_score = stats.norm.ppf(1 - self.confidence_level)
            return mu + sigma * z_score
        
        elif method == 'cornish_fisher':
            # Cornish-Fisher expansion for non-normal distributions
            mu = float(self.returns.mean())
            sigma = float(self.returns.std())
            skew = stats.skew(self.returns)
            kurt = stats.kurtosis(self.returns)
            
            z = stats.norm.ppf(1 - self.confidence_level)
            z_cf = (z + (z**2 - 1) * skew / 6 +
                   (z**3 - 3*z) * kurt / 24 -
                   (2*z**3 - 5*z) * skew**2 / 36)
            
            return mu + sigma * z_cf
        
        return 0.0
    
    def conditional_var(self) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        if len(self.returns) == 0:
            return 0.0
            
        var = self.value_at_risk('historical')
        return float(self.returns[self.returns <= var].mean())
    
    def maximum_drawdown_duration(self) -> int:
        """Calculate maximum drawdown duration in periods"""
        if len(self.returns) == 0:
            return 0
            
        cum_returns = (1 + self.returns).cumprod()
        running_max = cum_returns.expanding().max()
        drawdown = (cum_returns - running_max) / running_max
        
        # Find underwater periods
        is_underwater = drawdown < 0
        underwater_periods = []
        current_period = 0
        
        for underwater in is_underwater:
            if bool(underwater):
                current_period += 1
            else:
                if current_period > 0:
                    underwater_periods.append(current_period)
                current_period = 0
        
        if current_period > 0:
            underwater_periods.append(current_period)
        
        return max(underwater_periods) if underwater_periods else 0
    
    def tail_ratio(self) -> float:
        """Calculate tail ratio (95th percentile / 5th percentile)"""
        if len(self.returns) == 0:
            return 1.0
            
        right_tail = np.percentile(self.returns, 95)
        left_tail = np.percentile(self.returns, 5)
        
        if left_tail != 0:
            return abs(right_tail / left_tail)
        return 1.0
    
    def gain_to_pain_ratio(self) -> float:
        """Calculate gain to pain ratio"""
        if len(self.returns) == 0:
            return 0.0
            
        total_return = float((1 + self.returns).prod() - 1)
        pain = float(abs(self.returns[self.returns < 0].sum()))
        
        if pain != 0:
            return total_return / pain
        return 0.0
    
    def omega_ratio(self, threshold: float = 0.0) -> float:
        """
        Calculate Omega ratio
        
        Args:
            threshold: Return threshold (default 0)
        """
        if len(self.returns) == 0:
            return 1.0
            
        returns_above = self.returns[self.returns > threshold] - threshold
        returns_below = threshold - self.returns[self.returns < threshold]
        
        sum_below = float(returns_below.sum())
        sum_above = float(returns_above.sum())
        
        if sum_below != 0:
            return sum_above / sum_below
        return float('inf') if sum_above > 0 else 1.0
    
    def ulcer_index(self) -> float:
        """Calculate Ulcer Index (measure of downside volatility)"""
        if len(self.returns) == 0:
            return 0.0
            
        cum_returns = (1 + self.returns).cumprod()
        running_max = cum_returns.expanding().max()
        drawdown_pct = ((cum_returns - running_max) / running_max) * 100
        
        return np.sqrt(np.mean(drawdown_pct ** 2))
    
    def calmar_ratio(self, periods_per_year: int = 252) -> float:
        """Calculate Calmar ratio (annual return / max drawdown)"""
        if len(self.returns) == 0:
            return 0.0
            
        annual_return = (1 + self.returns.mean()) ** periods_per_year - 1
        
        cum_returns = (1 + self.returns).cumprod()
        running_max = cum_returns.expanding().max()
        drawdown = (cum_returns - running_max) / running_max
        max_dd = float(abs(drawdown.min()))
        
        if max_dd != 0:
            return float(annual_return) / max_dd
        return 0.0
    
    def burke_ratio(self, periods_per_year: int = 252) -> float:
        """Calculate Burke ratio"""
        if len(self.returns) == 0:
            return 0.0
            
        annual_return = float((1 + self.returns.mean()) ** periods_per_year - 1)
        
        cum_returns = (1 + self.returns).cumprod()
        running_max = cum_returns.expanding().max()
        drawdowns = (cum_returns - running_max) / running_max
        
        burke_denominator = float(np.sqrt(np.sum(drawdowns ** 2)))
        
        if burke_denominator != 0:
            return annual_return / burke_denominator
        return 0.0
    
    def generate_full_report(self) -> Dict[str, float]:
        """Generate comprehensive risk report"""
        return {
            'VaR (Historical)': self.value_at_risk('historical'),
            'VaR (Parametric)': self.value_at_risk('parametric'),
            'CVaR': self.conditional_var(),
            'Max DD Duration': self.maximum_drawdown_duration(),
            'Tail Ratio': self.tail_ratio(),
            'Gain/Pain Ratio': self.gain_to_pain_ratio(),
            'Omega Ratio': self.omega_ratio(),
            'Ulcer Index': self.ulcer_index(),
            'Calmar Ratio': self.calmar_ratio(),
            'Burke Ratio': self.burke_ratio(),
        }


class MonteCarloSimulator:
    """Monte Carlo simulation for strategy analysis"""
    
    def __init__(self, returns: pd.Series):
        """Initialize with historical returns"""
        self.returns = returns.dropna()
        self.mu = returns.mean()
        self.sigma = returns.std()
        
    def simulate_paths(self, num_simulations: int = 1000, 
                       periods: int = 252,
                       initial_capital: float = 100000) -> np.ndarray:
        """
        Simulate multiple price paths
        
        Args:
            num_simulations: Number of paths to simulate
            periods: Number of periods to simulate
            initial_capital: Starting capital
            
        Returns:
            Array of shape (num_simulations, periods) with simulated paths
        """
        paths = np.zeros((num_simulations, periods))
        paths[:, 0] = initial_capital
        
        for i in range(1, periods):
            random_returns = np.random.normal(self.mu, self.sigma, num_simulations)
            paths[:, i] = paths[:, i-1] * (1 + random_returns)
        
        return paths
    
    def confidence_intervals(self, paths: np.ndarray,
                            confidence_levels: List[float] = [0.05, 0.50, 0.95]) -> Dict[float, np.ndarray]:
        """Calculate confidence intervals from simulated paths"""
        percentiles = {}
        for level in confidence_levels:
            percentiles[level] = np.percentile(paths, level * 100, axis=0)
        return percentiles
    
    def probability_of_profit(self, paths: np.ndarray) -> float:
        """Calculate probability of ending with profit"""
        final_values = paths[:, -1]
        initial_value = paths[0, 0]
        return np.mean(final_values > initial_value)
    
    def expected_shortfall_simulation(self, paths: np.ndarray, 
                                     confidence_level: float = 0.95) -> float:
        """Calculate expected shortfall from simulations"""
        final_returns = (paths[:, -1] - paths[:, 0]) / paths[:, 0]
        var_threshold = np.percentile(final_returns, (1 - confidence_level) * 100)
        return final_returns[final_returns <= var_threshold].mean()


class WalkForwardOptimizer:
    """Walk-forward optimization for robust strategy testing"""
    
    def __init__(self, in_sample_periods: int = 252, 
                 out_sample_periods: int = 63):
        """
        Initialize walk-forward optimizer
        
        Args:
            in_sample_periods: Number of periods for optimization
            out_sample_periods: Number of periods for testing
        """
        self.in_sample_periods = in_sample_periods
        self.out_sample_periods = out_sample_periods
        
    def generate_windows(self, data_length: int) -> List[Tuple[int, int, int, int]]:
        """
        Generate walk-forward windows
        
        Returns:
            List of tuples: (in_start, in_end, out_start, out_end)
        """
        windows = []
        total_period = self.in_sample_periods + self.out_sample_periods
        
        position = 0
        while position + total_period <= data_length:
            in_start = position
            in_end = position + self.in_sample_periods
            out_start = in_end
            out_end = out_start + self.out_sample_periods
            
            windows.append((in_start, in_end, out_start, out_end))
            position += self.out_sample_periods
        
        return windows
    
    def efficiency_ratio(self, in_sample_results: List[float],
                        out_sample_results: List[float]) -> float:
        """
        Calculate walk-forward efficiency ratio
        
        Higher values indicate more robust strategies
        """
        if not in_sample_results or not out_sample_results:
            return 0.0
            
        avg_in = np.mean(in_sample_results)
        avg_out = np.mean(out_sample_results)
        
        if avg_in != 0:
            return avg_out / avg_in
        return 0.0


def calculate_regime_metrics(returns: pd.Series, 
                             volatility_window: int = 20) -> pd.DataFrame:
    """
    Detect market regimes based on volatility
    
    Args:
        returns: Return series
        volatility_window: Rolling window for volatility calculation
        
    Returns:
        DataFrame with regime classifications
    """
    vol = returns.rolling(volatility_window).std()
    vol_median = float(vol.median())
    
    regimes = pd.DataFrame(index=returns.index)
    regimes['volatility'] = vol.values
    regimes['regime'] = 'Normal'
    
    # Use boolean indexing properly
    high_vol_mask = vol > vol_median * 1.5
    low_vol_mask = vol < vol_median * 0.5
    
    regimes.loc[high_vol_mask, 'regime'] = 'High Volatility'
    regimes.loc[low_vol_mask, 'regime'] = 'Low Volatility'
    
    return regimes
