"""
Alpha Generation Engine - Advanced quantitative analysis and signal generation
"""

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


class AlphaEngine:
    """Advanced alpha generation and factor analysis"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.pca = None
        
    def calculate_momentum_factors(self, df, windows=[5, 10, 20, 60]):
        """Calculate multiple momentum factors"""
        factors = pd.DataFrame(index=df.index)
        
        for window in windows:
            if len(df) >= window:
                # Price momentum
                factors[f'mom_{window}'] = df['Close'].pct_change(window)
                
                # Volume-weighted momentum
                if 'Volume' in df.columns:
                    vwap = (df['Close'] * df['Volume']).rolling(window).sum() / df['Volume'].rolling(window).sum()
                    factors[f'vwap_mom_{window}'] = (df['Close'] / vwap - 1)
                
                # Acceleration
                factors[f'accel_{window}'] = factors[f'mom_{window}'].diff()
        
        return factors
    
    def calculate_mean_reversion_factors(self, df, windows=[10, 20, 50]):
        """Calculate mean reversion indicators"""
        factors = pd.DataFrame(index=df.index)
        
        for window in windows:
            if len(df) >= window:
                # Z-score
                mean = df['Close'].rolling(window).mean()
                std = df['Close'].rolling(window).std()
                factors[f'zscore_{window}'] = (df['Close'] - mean) / std
                
                # Distance from MA
                factors[f'ma_dist_{window}'] = (df['Close'] / mean - 1)
                
                # RSI-based reversion
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
                rs = gain / loss.replace(0, 1e-10)
                factors[f'rsi_{window}'] = 100 - (100 / (1 + rs))
        
        return factors
    
    def calculate_volatility_factors(self, df, windows=[10, 20, 60]):
        """Calculate volatility-based factors"""
        factors = pd.DataFrame(index=df.index)
        
        returns = df['Close'].pct_change()
        
        for window in windows:
            if len(df) >= window:
                # Historical volatility
                factors[f'hvol_{window}'] = returns.rolling(window).std() * np.sqrt(252)
                
                # Parkinson volatility (uses high-low)
                if 'High' in df.columns and 'Low' in df.columns:
                    hl = np.log(df['High'] / df['Low'])
                    factors[f'parkinson_vol_{window}'] = hl.rolling(window).std() * np.sqrt(252 / (4 * np.log(2)))
                
                # Volatility ratio (short/long)
                if window > 10:
                    short_vol = returns.rolling(10).std()
                    long_vol = returns.rolling(window).std()
                    factors[f'vol_ratio_{window}'] = short_vol / long_vol.replace(0, 1e-10)
        
        return factors
    
    def calculate_volume_factors(self, df, windows=[10, 20]):
        """Calculate volume-based factors"""
        if 'Volume' not in df.columns:
            return pd.DataFrame(index=df.index)
        
        factors = pd.DataFrame(index=df.index)
        
        for window in windows:
            if len(df) >= window:
                # Volume trend
                factors[f'vol_ma_{window}'] = df['Volume'].rolling(window).mean()
                factors[f'vol_ratio_{window}'] = df['Volume'] / factors[f'vol_ma_{window}']
                
                # On-balance volume
                obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
                factors[f'obv_slope_{window}'] = obv.rolling(window).apply(
                    lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == window else np.nan
                )
        
        return factors
    
    def calculate_microstructure_factors(self, df):
        """Calculate market microstructure factors"""
        factors = pd.DataFrame(index=df.index)
        
        if all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
            # Amihud illiquidity
            if 'Volume' in df.columns:
                factors['amihud'] = abs(df['Close'].pct_change()) / (df['Volume'] * df['Close'] + 1e-10)
            
            # Roll spread estimate
            factors['roll_spread'] = 2 * np.sqrt(abs(df['Close'].diff().rolling(20).cov(df['Close'].diff().shift(1))))
            
            # Price impact
            factors['price_range'] = (df['High'] - df['Low']) / df['Close']
            
            # Garman-Klass volatility
            factors['gk_vol'] = np.sqrt(
                0.5 * (np.log(df['High'] / df['Low']))**2 -
                (2*np.log(2)-1) * (np.log(df['Close'] / df['Open']))**2
            )
        
        return factors
    
    def calculate_all_factors(self, df):
        """Calculate all alpha factors"""
        all_factors = pd.DataFrame(index=df.index)
        
        # Generate all factor groups
        momentum = self.calculate_momentum_factors(df)
        mean_rev = self.calculate_mean_reversion_factors(df)
        volatility = self.calculate_volatility_factors(df)
        volume = self.calculate_volume_factors(df)
        micro = self.calculate_microstructure_factors(df)
        
        # Combine all factors
        for factor_df in [momentum, mean_rev, volatility, volume, micro]:
            all_factors = pd.concat([all_factors, factor_df], axis=1)
        
        return all_factors
    
    def factor_neutralization(self, factors, method='zscore'):
        """Neutralize factors to remove common trends"""
        if factors.empty:
            return factors
        
        neutralized = factors.copy()
        
        if method == 'zscore':
            # Z-score normalization
            mean = factors.mean()
            std = factors.std().replace(0, 1)
            neutralized = (factors - mean) / std
        
        elif method == 'rank':
            # Rank normalization
            neutralized = factors.rank(pct=True) * 2 - 1
        
        elif method == 'winsorize':
            # Winsorize outliers
            lower = factors.quantile(0.01)
            upper = factors.quantile(0.99)
            neutralized = factors.clip(lower=lower, upper=upper, axis=1)
        
        return neutralized.fillna(0)
    
    def generate_composite_alpha(self, factors, weights=None):
        """Generate composite alpha signal from multiple factors"""
        if factors.empty:
            return pd.Series(0, index=factors.index)
        
        # Remove any inf or nan values
        factors_clean = factors.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        if weights is None:
            # Equal weight by default
            weights = pd.Series(1.0 / len(factors_clean.columns), index=factors_clean.columns)
        
        # Calculate composite signal
        composite = (factors_clean * weights).sum(axis=1)
        
        # Normalize to [-1, 1]
        if composite.std() > 0:
            composite = composite / composite.rolling(60, min_periods=1).std()
            composite = composite.clip(-3, 3) / 3  # Clip at 3 std devs
        
        return composite
    
    def optimize_factor_weights(self, factors, returns, lookback=252):
        """Optimize factor weights based on historical performance"""
        if factors.empty or len(factors) < lookback:
            return pd.Series(1.0 / len(factors.columns), index=factors.columns)
        
        # Use last lookback period
        factors_period = factors.iloc[-lookback:]
        returns_period = returns.iloc[-lookback:]
        
        # Calculate factor returns (IC - information coefficient)
        ic = pd.Series(index=factors_period.columns, dtype=float)
        
        for col in factors_period.columns:
            try:
                # Spearman rank correlation between factor and forward returns
                correlation = factors_period[col].corr(returns_period.shift(-1), method='spearman')
                ic[col] = correlation if not np.isnan(correlation) else 0
            except:
                ic[col] = 0
        
        # Convert IC to weights (positive IC = buy signal, negative = sell signal)
        weights = ic.abs() / ic.abs().sum() if ic.abs().sum() > 0 else ic * 0 + 1.0 / len(ic)
        
        # Apply sign
        weights = weights * np.sign(ic)
        
        return weights
    
    def calculate_factor_performance(self, factors, returns):
        """Calculate comprehensive factor performance metrics"""
        if factors.empty:
            return {}
        
        performance = {}
        
        for col in factors.columns:
            try:
                factor_series = factors[col].dropna()
                returns_aligned = returns.reindex(factor_series.index).dropna()
                
                if len(factor_series) > 30 and len(returns_aligned) > 30:
                    # Information Coefficient (IC)
                    ic = factor_series.corr(returns_aligned.shift(-1), method='spearman')
                    
                    # IC t-stat
                    ic_std = factor_series.rolling(60).corr(returns_aligned.shift(-1), method='spearman').std()
                    ic_tstat = ic / ic_std if ic_std > 0 else 0
                    
                    # Turnover
                    factor_rank = factor_series.rank(pct=True)
                    turnover = factor_rank.diff().abs().mean()
                    
                    performance[col] = {
                        'IC': ic,
                        'IC_tstat': ic_tstat,
                        'turnover': turnover,
                        'abs_IC': abs(ic)
                    }
            except:
                continue
        
        return performance
    
    def pca_factor_reduction(self, factors, n_components=5):
        """Reduce factor dimensionality using PCA"""
        if factors.empty or len(factors.columns) < n_components:
            return factors
        
        # Clean factors
        factors_clean = factors.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        # Fit PCA
        self.pca = PCA(n_components=min(n_components, len(factors_clean.columns)))
        
        try:
            components = self.pca.fit_transform(factors_clean)
            
            # Create DataFrame with principal components
            pc_df = pd.DataFrame(
                components,
                index=factors_clean.index,
                columns=[f'PC{i+1}' for i in range(components.shape[1])]
            )
            
            return pc_df
        except:
            return factors
    
    def calculate_alpha_decay(self, factor, returns, horizons=[1, 5, 10, 20]):
        """Analyze alpha signal decay over different horizons"""
        decay_analysis = {}
        
        for horizon in horizons:
            if len(returns) > horizon:
                future_returns = returns.shift(-horizon)
                ic = factor.corr(future_returns, method='spearman')
                decay_analysis[f'{horizon}d'] = ic
        
        return decay_analysis


class SignalGenerator:
    """Generate trading signals from alpha factors"""
    
    def __init__(self, threshold=0.5):
        self.threshold = threshold
        
    def generate_signal(self, alpha, method='threshold'):
        """Generate buy/sell/hold signals from alpha"""
        signals = pd.Series('HOLD', index=alpha.index)
        
        if method == 'threshold':
            signals[alpha > self.threshold] = 'BUY'
            signals[alpha < -self.threshold] = 'SELL'
        
        elif method == 'quantile':
            upper = alpha.quantile(0.7)
            lower = alpha.quantile(0.3)
            signals[alpha > upper] = 'BUY'
            signals[alpha < lower] = 'SELL'
        
        elif method == 'dynamic':
            # Dynamic threshold based on rolling statistics
            rolling_mean = alpha.rolling(60, min_periods=1).mean()
            rolling_std = alpha.rolling(60, min_periods=1).std()
            
            upper = rolling_mean + rolling_std
            lower = rolling_mean - rolling_std
            
            signals[alpha > upper] = 'BUY'
            signals[alpha < lower] = 'SELL'
        
        return signals
    
    def generate_position_sizes(self, alpha, method='proportional', max_position=1.0):
        """Generate position sizes from alpha signal"""
        positions = pd.Series(0.0, index=alpha.index)
        
        if method == 'proportional':
            # Position size proportional to signal strength
            normalized_alpha = alpha.clip(-3, 3) / 3
            positions = normalized_alpha * max_position
        
        elif method == 'binary':
            # All-in or all-out
            positions[alpha > 0] = max_position
            positions[alpha < 0] = -max_position
        
        elif method == 'kelly':
            # Kelly criterion (simplified)
            win_rate = (alpha > 0).rolling(60, min_periods=1).mean()
            positions = ((2 * win_rate - 1) * np.sign(alpha)).clip(-max_position, max_position)
        
        return positions
