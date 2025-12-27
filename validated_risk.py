"""
Validated Risk Metrics
Clear daily vs annualized labels, consistent annualization, documented VaR/CVaR
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from scipy import stats

from core_config import RISK_CFG


class ValidatedRiskMetrics:
    """
    Risk metrics with:
    - Explicit daily vs annualized labels
    - Consistent annualization (sqrt(252))
    - Clear VaR/CVaR horizon and method
    - Self-documenting outputs
    """
    
    @staticmethod
    def calculate_returns(prices: pd.Series) -> pd.Series:
        """
        Calculate log returns for better mathematical properties
        
        Returns:
            Series with NaN for first value (downstream must dropna())
        
        Note:
            First return is NaN (NOT filled). This is mathematically correct.
        """
        return np.log(prices / prices.shift(1))
    
    @staticmethod
    def volatility(returns: pd.Series, annualize: bool = True) -> Dict:
        """
        Calculate volatility with explicit labeling
        
        Returns dict with both daily and annualized values
        """
        returns_clean = returns.dropna()
        
        if len(returns_clean) < 2:
            return {
                'volatility_daily': 0.0,
                'volatility_annualized': 0.0,
                'method': 'std_dev',
                'sample_size': 0
            }
        
        vol_daily = returns_clean.std()
        vol_annual = RISK_CFG.annualize_volatility(vol_daily)
        
        return {
            'volatility_daily': vol_daily,
            'volatility_annualized': vol_annual,
            'volatility_daily_pct': vol_daily * 100,
            'volatility_annualized_pct': vol_annual * 100,
            'method': 'standard_deviation',
            'sample_size': len(returns_clean),
            'annualization_factor': RISK_CFG.TRADING_DAYS_PER_YEAR ** 0.5
        }
    
    @staticmethod
    def downside_deviation(returns: pd.Series, annualize: bool = True) -> Dict:
        """
        Calculate downside deviation (for Sortino ratio)
        
        Only considers negative returns
        """
        returns_clean = returns.dropna()
        downside_returns = returns_clean[returns_clean < 0]
        
        if len(downside_returns) < 2:
            return {
                'downside_dev_daily': 0.0,
                'downside_dev_annualized': 0.0,
                'negative_periods': 0
            }
        
        dd_daily = downside_returns.std()
        dd_annual = RISK_CFG.annualize_volatility(dd_daily)
        
        return {
            'downside_dev_daily': dd_daily,
            'downside_dev_annualized': dd_annual,
            'downside_dev_daily_pct': dd_daily * 100,
            'downside_dev_annualized_pct': dd_annual * 100,
            'negative_periods': len(downside_returns),
            'total_periods': len(returns_clean),
            'negative_ratio': len(downside_returns) / len(returns_clean)
        }
    
    @staticmethod
    def value_at_risk(
        returns: pd.Series,
        confidence: float = None,
        method: str = 'historical'
    ) -> Dict:
        """
        Calculate Value at Risk with explicit method and horizon
        
        Args:
            returns: Daily returns
            confidence: Confidence level (default 0.95)
            method: 'historical', 'parametric', or 'cornish_fisher'
            
        Returns:
            Dict with VaR and metadata
        """
        if confidence is None:
            confidence = RISK_CFG.VAR_CONFIDENCE
        
        returns_clean = returns.dropna()
        
        if len(returns_clean) < 2:
            return {
                'var': 0.0,
                'method': method,
                'confidence': confidence,
                'horizon_days': RISK_CFG.VAR_HORIZON_DAYS,
                'error': 'insufficient_data'
            }
        
        if method == 'historical':
            var = np.percentile(returns_clean, (1 - confidence) * 100)
        
        elif method == 'parametric':
            mu = returns_clean.mean()
            sigma = returns_clean.std()
            z_score = stats.norm.ppf(1 - confidence)
            var = mu + sigma * z_score
        
        elif method == 'cornish_fisher':
            mu = returns_clean.mean()
            sigma = returns_clean.std()
            skew = stats.skew(returns_clean)
            kurt = stats.kurtosis(returns_clean)
            
            z = stats.norm.ppf(1 - confidence)
            z_cf = (z + (z**2 - 1) * skew / 6 +
                   (z**3 - 3*z) * kurt / 24 -
                   (2*z**3 - 5*z) * skew**2 / 36)
            
            var = mu + sigma * z_cf
        
        else:
            raise ValueError(f"Unknown VaR method: {method}")
        
        return {
            'var': var,
            'var_pct': var * 100,
            'var_dollar_per_1k': var * 1000,  # Loss per $1000 invested
            'method': method,
            'confidence': confidence,
            'confidence_pct': confidence * 100,
            'horizon_days': RISK_CFG.VAR_HORIZON_DAYS,
            'sample_size': len(returns_clean),
            'interpretation': f"With {confidence*100:.0f}% confidence, expect loss <= {abs(var)*100:.2f}% per day"
        }
    
    @staticmethod
    def conditional_var(
        returns: pd.Series,
        confidence: float = None
    ) -> Dict:
        """
        Calculate Conditional VaR (Expected Shortfall)
        
        Average of returns worse than VaR
        """
        if confidence is None:
            confidence = RISK_CFG.VAR_CONFIDENCE
        
        var_dict = ValidatedRiskMetrics.value_at_risk(returns, confidence, 'historical')
        var_threshold = var_dict['var']
        
        returns_clean = returns.dropna()
        tail_returns = returns_clean[returns_clean <= var_threshold]
        
        if len(tail_returns) == 0:
            cvar = var_threshold
            tail_count = 0
        else:
            cvar = tail_returns.mean()
            tail_count = len(tail_returns)
        
        return {
            'cvar': cvar,
            'cvar_pct': cvar * 100,
            'cvar_dollar_per_1k': cvar * 1000,
            'var': var_threshold,
            'confidence': confidence,
            'tail_observations': tail_count,
            'interpretation': f"Average loss in worst {(1-confidence)*100:.0f}% of days: {abs(cvar)*100:.2f}%"
        }
    
    @staticmethod
    def sharpe_ratio(returns: pd.Series, risk_free_rate: float = None) -> Dict:
        """
        Calculate Sharpe ratio with explicit annualization
        
        Formula: (Mean Return - Risk Free) / Std Dev
        All annualized
        """
        if risk_free_rate is None:
            risk_free_rate = RISK_CFG.RISK_FREE_RATE
        
        returns_clean = returns.dropna()
        
        if len(returns_clean) < 2:
            return {'sharpe_ratio': 0.0, 'error': 'insufficient_data'}
        
        # Annualize returns
        mean_return_daily = returns_clean.mean()
        mean_return_annual = mean_return_daily * RISK_CFG.TRADING_DAYS_PER_YEAR
        
        # Annualize volatility
        std_daily = returns_clean.std()
        std_annual = RISK_CFG.annualize_volatility(std_daily)
        
        if std_annual == 0:
            return {'sharpe_ratio': 0.0, 'error': 'zero_volatility'}
        
        excess_return = mean_return_annual - risk_free_rate
        sharpe = excess_return / std_annual
        
        return {
            'sharpe_ratio': sharpe,
            'mean_return_annual_pct': mean_return_annual * 100,
            'volatility_annual_pct': std_annual * 100,
            'risk_free_rate_pct': risk_free_rate * 100,
            'excess_return_pct': excess_return * 100,
            'method': 'annualized',
            'interpretation': 'Higher is better; >1 good, >2 excellent'
        }
    
    @staticmethod
    def sortino_ratio(returns: pd.Series, risk_free_rate: float = None) -> Dict:
        """
        Calculate Sortino ratio (uses downside deviation)
        
        Like Sharpe but only penalizes downside volatility
        """
        if risk_free_rate is None:
            risk_free_rate = RISK_CFG.RISK_FREE_RATE
        
        returns_clean = returns.dropna()
        
        if len(returns_clean) < 2:
            return {'sortino_ratio': 0.0, 'error': 'insufficient_data'}
        
        # Annualize returns
        mean_return_daily = returns_clean.mean()
        mean_return_annual = mean_return_daily * RISK_CFG.TRADING_DAYS_PER_YEAR
        
        # Downside deviation
        dd_dict = ValidatedRiskMetrics.downside_deviation(returns_clean)
        dd_annual = dd_dict['downside_dev_annualized']
        
        if dd_annual == 0:
            return {'sortino_ratio': 0.0, 'error': 'zero_downside_volatility'}
        
        excess_return = mean_return_annual - risk_free_rate
        sortino = excess_return / dd_annual
        
        return {
            'sortino_ratio': sortino,
            'mean_return_annual_pct': mean_return_annual * 100,
            'downside_dev_annual_pct': dd_annual * 100,
            'risk_free_rate_pct': risk_free_rate * 100,
            'method': 'annualized',
            'interpretation': 'Like Sharpe but only penalizes downside; >1 good, >2 excellent'
        }
    
    @staticmethod
    def calmar_ratio(returns: pd.Series) -> Dict:
        """
        Calculate Calmar ratio (Annual Return / Max Drawdown)
        """
        returns_clean = returns.dropna()
        
        if len(returns_clean) < 2:
            return {'calmar_ratio': 0.0, 'error': 'insufficient_data'}
        
        # Annual return
        mean_return_daily = returns_clean.mean()
        mean_return_annual = mean_return_daily * RISK_CFG.TRADING_DAYS_PER_YEAR
        
        # Max drawdown
        cumulative = (1 + returns_clean).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_dd = abs(drawdown.min())
        
        if max_dd == 0:
            return {'calmar_ratio': 0.0, 'error': 'zero_drawdown'}
        
        calmar = mean_return_annual / max_dd
        
        return {
            'calmar_ratio': calmar,
            'annual_return_pct': mean_return_annual * 100,
            'max_drawdown_pct': max_dd * 100,
            'method': 'annualized',
            'interpretation': 'Return per unit of max drawdown; >1 good'
        }
    
    @staticmethod
    def max_drawdown_analysis(returns: pd.Series) -> Dict:
        """
        Complete drawdown analysis
        """
        returns_clean = returns.dropna()
        
        if len(returns_clean) < 2:
            return {'max_drawdown': 0.0, 'error': 'insufficient_data'}
        
        cumulative = (1 + returns_clean).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        
        max_dd = drawdown.min()
        max_dd_idx = drawdown.idxmin()
        
        # Find recovery
        recovery_idx = drawdown[max_dd_idx:][drawdown >= 0].index
        if len(recovery_idx) > 0:
            recovery_date = recovery_idx[0]
            recovery_days = len(drawdown[max_dd_idx:recovery_date])
        else:
            recovery_date = None
            recovery_days = len(drawdown) - drawdown.index.get_loc(max_dd_idx)
        
        # Current drawdown
        current_dd = drawdown.iloc[-1]
        
        return {
            'max_drawdown': max_dd,
            'max_drawdown_pct': max_dd * 100,
            'max_dd_date': max_dd_idx,
            'recovery_date': recovery_date,
            'recovery_days': recovery_days,
            'current_drawdown': current_dd,
            'current_drawdown_pct': current_dd * 100,
            'interpretation': f"Worst peak-to-trough decline: {abs(max_dd)*100:.2f}%"
        }
    
    @staticmethod
    def comprehensive_risk_report(returns: pd.Series) -> Dict:
        """
        Generate complete risk metrics report
        """
        vol = ValidatedRiskMetrics.volatility(returns)
        dd = ValidatedRiskMetrics.downside_deviation(returns)
        var = ValidatedRiskMetrics.value_at_risk(returns)
        cvar = ValidatedRiskMetrics.conditional_var(returns)
        sharpe = ValidatedRiskMetrics.sharpe_ratio(returns)
        sortino = ValidatedRiskMetrics.sortino_ratio(returns)
        calmar = ValidatedRiskMetrics.calmar_ratio(returns)
        mdd = ValidatedRiskMetrics.max_drawdown_analysis(returns)
        
        return {
            'volatility': vol,
            'downside_deviation': dd,
            'var': var,
            'cvar': cvar,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            'max_drawdown': mdd
        }
    
    @staticmethod
    def print_risk_report(risk_dict: Dict):
        """Print comprehensive risk report"""
        print(f"\n{'='*80}")
        print("RISK METRICS REPORT")
        print(f"{'='*80}")
        
        print(f"\nVOLATILITY:")
        vol = risk_dict['volatility']
        print(f"  Daily:       {vol['volatility_daily_pct']:.4f}%")
        print(f"  Annualized:  {vol['volatility_annualized_pct']:.2f}%")
        print(f"  Sample Size: {vol['sample_size']} days")
        
        print(f"\nDOWNSIDE DEVIATION:")
        dd = risk_dict['downside_deviation']
        print(f"  Daily:       {dd['downside_dev_daily_pct']:.4f}%")
        print(f"  Annualized:  {dd['downside_dev_annualized_pct']:.2f}%")
        print(f"  Neg Periods: {dd['negative_periods']}/{dd['total_periods']} ({dd['negative_ratio']*100:.1f}%)")
        
        print(f"\nVALUE AT RISK (VaR):")
        var = risk_dict['var']
        print(f"  {var['confidence_pct']:.0f}% VaR:   {var['var_pct']:.4f}%")
        print(f"  Method:      {var['method']}")
        print(f"  Horizon:     {var['horizon_days']} day(s)")
        print(f"  {var['interpretation']}")
        
        print(f"\nCONDITIONAL VaR (CVaR):")
        cvar = risk_dict['cvar']
        print(f"  CVaR:        {cvar['cvar_pct']:.4f}%")
        print(f"  {cvar['interpretation']}")
        
        print(f"\nRISK-ADJUSTED RETURNS:")
        sharpe = risk_dict['sharpe_ratio']
        print(f"  Sharpe:      {sharpe['sharpe_ratio']:.4f}")
        sortino = risk_dict['sortino_ratio']
        print(f"  Sortino:     {sortino['sortino_ratio']:.4f}")
        calmar = risk_dict['calmar_ratio']
        print(f"  Calmar:      {calmar['calmar_ratio']:.4f}")
        
        print(f"\nDRAWDOWN ANALYSIS:")
        mdd = risk_dict['max_drawdown']
        print(f"  Max DD:      {mdd['max_drawdown_pct']:.2f}%")
        print(f"  DD Date:     {mdd['max_dd_date'].date() if hasattr(mdd['max_dd_date'], 'date') else mdd['max_dd_date']}")
        print(f"  Recovery:    {mdd['recovery_days']} days")
        print(f"  Current DD:  {mdd['current_drawdown_pct']:.2f}%")
        
        print(f"{'='*80}\n")


def compute_risk_metrics(returns: pd.Series, verbose: bool = True) -> Dict:
    """
    Convenience function to compute and optionally print risk metrics
    """
    risk_report = ValidatedRiskMetrics.comprehensive_risk_report(returns)
    
    if verbose:
        ValidatedRiskMetrics.print_risk_report(risk_report)
    
    return risk_report


# ============================================================================
# BACKWARDS COMPATIBILITY WRAPPER
# ============================================================================

class ValidatedRisk:
    """
    Compatibility wrapper for tests expecting ValidatedRisk interface.
    Routes to ValidatedRiskMetrics.
    """
    
    @staticmethod
    def compute_risk_metrics(returns: pd.Series) -> Dict:
        """
        Compute comprehensive risk metrics.
        Wrapper for ValidatedRiskMetrics.comprehensive_risk_report()
        
        Args:
            returns: Series of returns (first value should be NaN; will be dropped)
        
        Returns:
            Dict with risk metrics (volatility, VaR, CVaR, etc.)
        """
        return ValidatedRiskMetrics.comprehensive_risk_report(returns)

