"""
Validated Key Levels Module
Support/Resistance and Fibonacci with explicit anchors and verification
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from datetime import datetime

from core_config import LEVEL_CFG


class ValidatedKeyLevels:
    """
    Key levels with self-verifying outputs:
    - Explicit lookback windows
    - Anchor dates/prices printed
    - Proximity filtering
    - No far-off outliers
    """
    
    @staticmethod
    def support_resistance(
        df: pd.DataFrame,
        lookback: int = None,
        window: int = None,
        proximity_filter: float = None
    ) -> Dict[str, List[float]]:
        """
        Calculate support and resistance levels with validation
        
        Args:
            df: DataFrame with High/Low/Price columns and DateTimeIndex
            lookback: Number of days to analyze (default from config)
            window: Window for local extrema detection
            proximity_filter: Filter levels within X% of current price
            
        Returns:
            Dict with 'support', 'resistance', and metadata
        """
        if lookback is None:
            lookback = LEVEL_CFG.SR_LOOKBACK
        if window is None:
            window = LEVEL_CFG.SR_WINDOW
        if proximity_filter is None:
            proximity_filter = LEVEL_CFG.SR_PROXIMITY_FILTER
        
        # Subset to lookback window
        recent_df = df.iloc[-min(lookback, len(df)):].copy()
        
        if len(recent_df) < window * 2:
            # Not enough data
            current_price = recent_df['Price'].iloc[-1]
            return {
                'support': [recent_df['Low'].min()],
                'resistance': [recent_df['High'].max()],
                'anchor_start': recent_df.index[0],
                'anchor_end': recent_df.index[-1],
                'current_price': current_price,
                'lookback_days': len(recent_df),
                'warning': 'Insufficient data for local extrema'
            }
        
        current_price = recent_df['Price'].iloc[-1]
        
        # Find local minima (support) and maxima (resistance)
        support_levels = []
        resistance_levels = []
        
        for i in range(window, len(recent_df) - window):
            # Support: local minimum
            if recent_df['Low'].iloc[i] == recent_df['Low'].iloc[i-window:i+window+1].min():
                level = recent_df['Low'].iloc[i]
                # Proximity filter
                if level > current_price * (1 - proximity_filter):
                    support_levels.append(level)
            
            # Resistance: local maximum
            if recent_df['High'].iloc[i] == recent_df['High'].iloc[i-window:i+window+1].max():
                level = recent_df['High'].iloc[i]
                # Proximity filter
                if level < current_price * (1 + proximity_filter):
                    resistance_levels.append(level)
        
        # Cluster nearby levels
        support_levels = ValidatedKeyLevels._cluster_levels(
            support_levels, LEVEL_CFG.SR_CLUSTER_THRESHOLD
        )
        resistance_levels = ValidatedKeyLevels._cluster_levels(
            resistance_levels, LEVEL_CFG.SR_CLUSTER_THRESHOLD
        )
        
        # Fallback if no levels found
        if not support_levels:
            support_levels = [recent_df['Low'].iloc[-20:].min()]
        if not resistance_levels:
            resistance_levels = [recent_df['High'].iloc[-20:].max()]
        
        return {
            'support': sorted(support_levels),
            'resistance': sorted(resistance_levels, reverse=True),
            'anchor_start': recent_df.index[0],
            'anchor_end': recent_df.index[-1],
            'current_price': current_price,
            'lookback_days': len(recent_df),
            'window': window,
            'proximity_filter_pct': proximity_filter * 100
        }
    
    @staticmethod
    def _cluster_levels(levels: List[float], threshold: float) -> List[float]:
        """Cluster nearby levels using threshold"""
        if not levels:
            return []
        
        levels = sorted(levels)
        if len(levels) == 1:
            return levels
        
        clustered = []
        current_cluster = [levels[0]]
        
        for level in levels[1:]:
            # Check if within threshold of cluster
            if abs(level - np.mean(current_cluster)) / np.mean(current_cluster) < threshold:
                current_cluster.append(level)
            else:
                # Save cluster mean and start new cluster
                clustered.append(np.mean(current_cluster))
                current_cluster = [level]
        
        # Add last cluster
        if current_cluster:
            clustered.append(np.mean(current_cluster))
        
        return clustered
    
    @staticmethod
    def fibonacci_retracements(
        df: pd.DataFrame,
        lookback: int = None
    ) -> Dict[str, float]:
        """
        Calculate Fibonacci retracement levels with explicit anchors
        
        Guarantees:
        - High/Low from intended lookback window
        - Anchor dates/prices in output
        - Self-verifying
        
        Returns:
            Dict with levels and metadata
        """
        if lookback is None:
            lookback = LEVEL_CFG.FIB_LOOKBACK
        
        # Subset to lookback window
        recent_df = df.iloc[-min(lookback, len(df)):].copy()
        
        # Find high and low
        high_idx = recent_df['High'].idxmax()
        low_idx = recent_df['Low'].idxmin()
        
        high_price = recent_df.loc[high_idx, 'High']
        low_price = recent_df.loc[low_idx, 'Low']
        
        # Calculate Fibonacci levels
        diff = high_price - low_price
        
        levels = {}
        for ratio in LEVEL_CFG.FIB_LEVELS:
            level_name = f"{ratio*100:.1f}%"
            level_value = high_price - (ratio * diff)
            levels[level_name] = level_value
            # Also add programmatic key for tests
            prog_key = f"fib_{ratio}"
            levels[prog_key] = level_value
        
        # Add metadata for verification
        metadata = {
            'anchor_high_date': high_idx,
            'anchor_high_price': high_price,
            'anchor_low_date': low_idx,
            'anchor_low_price': low_price,
            'lookback_start': recent_df.index[0],
            'lookback_end': recent_df.index[-1],
            'lookback_days': len(recent_df),
            'range': diff
        }
        
        return {**levels, **metadata}
    
    @staticmethod
    def print_support_resistance(sr_dict: Dict):
        """Print support/resistance with metadata"""
        print(f"\n{'='*80}")
        print("SUPPORT & RESISTANCE LEVELS")
        print(f"{'='*80}")
        print(f"Analysis Window:  {sr_dict['anchor_start'].date()} to {sr_dict['anchor_end'].date()}")
        print(f"Lookback Days:    {sr_dict['lookback_days']}")
        print(f"Current Price:    ${sr_dict['current_price']:.2f}")
        print(f"Proximity Filter: ±{sr_dict['proximity_filter_pct']:.0f}%")
        print(f"\nResistance Levels:")
        for level in sr_dict['resistance'][:3]:
            pct_diff = ((level - sr_dict['current_price']) / sr_dict['current_price']) * 100
            print(f"  ${level:>8.2f}  (+{pct_diff:.1f}%)")
        print(f"\nSupport Levels:")
        for level in sr_dict['support'][:3]:
            pct_diff = ((sr_dict['current_price'] - level) / sr_dict['current_price']) * 100
            print(f"  ${level:>8.2f}  (-{pct_diff:.1f}%)")
        print(f"{'='*80}\n")
    
    @staticmethod
    def print_fibonacci(fib_dict: Dict):
        """Print Fibonacci levels with anchors"""
        print(f"\n{'='*80}")
        print("FIBONACCI RETRACEMENT LEVELS")
        print(f"{'='*80}")
        print(f"Analysis Window:  {fib_dict['lookback_start'].date()} to {fib_dict['lookback_end'].date()}")
        print(f"Lookback Days:    {fib_dict['lookback_days']}")
        print(f"\nAnchor High:      ${fib_dict['anchor_high_price']:.2f} on {fib_dict['anchor_high_date'].date()}")
        print(f"Anchor Low:       ${fib_dict['anchor_low_price']:.2f} on {fib_dict['anchor_low_date'].date()}")
        print(f"Range:            ${fib_dict['range']:.2f}")
        print(f"\nFibonacci Levels:")
        
        # Print levels in order
        for ratio in LEVEL_CFG.FIB_LEVELS:
            level_name = f"{ratio*100:.1f}%"
            if level_name in fib_dict:
                print(f"  {level_name:>6s}:  ${fib_dict[level_name]:>8.2f}")
        
        print(f"{'='*80}\n")
    
    @staticmethod
    def volume_profile(
        df: pd.DataFrame,
        lookback: int = None,
        bins: int = 20
    ) -> pd.DataFrame:
        """
        Calculate volume profile (Volume-by-Price)
        
        Returns DataFrame with price bins and volume
        """
        if lookback is None:
            lookback = LEVEL_CFG.SR_LOOKBACK
        
        recent_df = df.iloc[-min(lookback, len(df)):].copy()
        
        # Create price bins
        price_range = recent_df['High'].max() - recent_df['Low'].min()
        bin_size = price_range / bins
        
        # Assign each row to a price bin
        recent_df['Price_Bin'] = (
            (recent_df['Price'] - recent_df['Low'].min()) / bin_size
        ).astype(int)
        
        # Aggregate volume by bin
        volume_profile = recent_df.groupby('Price_Bin').agg({
            'Volume': 'sum',
            'Price': 'mean'
        }).sort_values('Volume', ascending=False)
        
        volume_profile.columns = ['Total_Volume', 'Avg_Price']
        
        return volume_profile.head(10)


# Convenience function
def compute_all_levels(df: pd.DataFrame, verbose: bool = True) -> Dict:
    """
    Compute all key levels
    
    Returns dict with support/resistance, Fibonacci, and volume profile
    """
    sr = ValidatedKeyLevels.support_resistance(df)
    fib = ValidatedKeyLevels.fibonacci_retracements(df)
    vol_profile = ValidatedKeyLevels.volume_profile(df)
    
    if verbose:
        ValidatedKeyLevels.print_support_resistance(sr)
        ValidatedKeyLevels.print_fibonacci(fib)
    
    return {
        'support_resistance': sr,
        'fibonacci': fib,
        'volume_profile': vol_profile
    }
