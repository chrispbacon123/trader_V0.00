"""
Advanced Market Analytics and Indicators
Comprehensive technical analysis, market regime detection, and correlation analysis
Now using validated modules for accuracy and consistency
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Import validated modules
from canonical_data import CanonicalDataFetcher
from validated_indicators import ValidatedIndicators, compute_all_indicators
from validated_levels import ValidatedKeyLevels
from validated_regime import ValidatedRegime
from validated_risk import ValidatedRiskMetrics
from core_config import INDICATOR_CFG, LEVEL_CFG, REGIME_CFG, RISK_CFG
from data_normalization import DataNormalizer, DataContractError


class MarketAnalytics:
    """
    Advanced market analysis tools using validated modules
    
    All calculations now use:
    - Canonical price series (auto-adjusted Close)
    - Wilder's RSI and ADX implementations
    - Explicit lookback windows
    - Self-verifying outputs
    """
    
    def __init__(self, symbol: str = None):
        self.symbol = symbol
        self.data = None
        self.metadata = None
        self.fetcher = CanonicalDataFetcher()
    
    def analyze(
        self,
        df: pd.DataFrame,
        symbol: str = None,
        lookbacks: Dict[str, int] = None
    ) -> Dict:
        """
        Comprehensive market analysis on PRE-FETCHED data.
        
        This is the canonical entry point for analysis - it NEVER re-fetches data.
        Use this instead of fetch_data() when you already have normalized data.
        
        Args:
            df: Normalized DataFrame with Price column and DatetimeIndex
            symbol: Optional symbol override
            lookbacks: Optional custom lookback periods
                {
                    'regime': 50,
                    'support_resistance': 100,
                    'fibonacci': 100
                }
        
        Returns:
            Dict with stable schema:
            {
                'success': bool,
                'symbol': str,
                'data_summary': {
                    'rows': int,
                    'date_range_start': str,
                    'date_range_end': str,
                    'price_source': str
                },
                'regime': {...},
                'key_levels': {...},
                'fibonacci': {...},
                'momentum': {...},
                'risk': {...},
                'warnings': list[str],
                'error': str | None
            }
        """
        # Use passed symbol or instance symbol
        sym = symbol or self.symbol or 'UNKNOWN'
        
        # Default lookbacks
        lookbacks = lookbacks or {}
        regime_lookback = lookbacks.get('regime', REGIME_CFG.REGIME_LOOKBACK)
        sr_lookback = lookbacks.get('support_resistance', LEVEL_CFG.SR_LOOKBACK)
        fib_lookback = lookbacks.get('fibonacci', LEVEL_CFG.FIB_LOOKBACK)
        
        warnings_list = []
        
        # Validate input
        if df is None or len(df) == 0:
            return {
                'success': False,
                'symbol': sym,
                'data_summary': {},
                'regime': {},
                'key_levels': {},
                'fibonacci': {},
                'momentum': {},
                'risk': {},
                'warnings': [],
                'error': 'Input DataFrame is None or empty'
            }
        
        # Normalize data if needed
        try:
            df, metadata = DataNormalizer.normalize_market_data(
                df, symbol=sym, require_ohlc=False
            )
        except DataContractError as e:
            return {
                'success': False,
                'symbol': sym,
                'data_summary': {},
                'regime': {},
                'key_levels': {},
                'fibonacci': {},
                'momentum': {},
                'risk': {},
                'warnings': [],
                'error': f'Data normalization failed: {str(e)}'
            }
        
        # Store in instance for other methods
        self.data = df
        self.symbol = sym
        self.metadata = metadata
        
        # Compute indicators
        self.data = compute_all_indicators(self.data)
        
        # Build result with stable schema
        result = {
            'success': True,
            'symbol': sym,
            'data_summary': {
                'rows': len(df),
                'date_range_start': str(df.index[0]),
                'date_range_end': str(df.index[-1]),
                'price_source': metadata.get('price_source', 'Unknown')
            },
            'warnings': warnings_list,
            'error': None
        }
        
        # REGIME ANALYSIS
        if len(df) >= regime_lookback:
            try:
                regime_result = ValidatedRegime.classify_regime(df, lookback=regime_lookback)
                regime_type = regime_result.get('regime', 'unknown')
                if hasattr(regime_type, 'value'):
                    regime_type = regime_type.value
                result['regime'] = {
                    'type': regime_type,
                    'confidence': regime_result.get('confidence', 0.0),
                    'volatility_annualized': regime_result.get('metrics', {}).get('volatility_annualized_pct', 0.0),
                    'adx': regime_result.get('metrics', {}).get('adx', 0.0),
                    'rationale': regime_result.get('rationale', '')
                }
            except Exception as e:
                result['regime'] = {'error': str(e)}
                warnings_list.append(f'Regime analysis failed: {e}')
        else:
            result['regime'] = {'error': f'Insufficient data ({len(df)} rows, need {regime_lookback})'}
        
        # KEY LEVELS (Support/Resistance)
        if len(df) >= sr_lookback:
            try:
                sr = ValidatedKeyLevels.support_resistance(df, lookback=sr_lookback)
                result['key_levels'] = {
                    'resistance': sr.get('resistance', []),
                    'support': sr.get('support', []),
                    'current_price': sr.get('current_price'),
                    'lookback_days': sr.get('lookback_days', sr_lookback)
                }
            except Exception as e:
                result['key_levels'] = {'error': str(e)}
                warnings_list.append(f'Key levels failed: {e}')
        else:
            result['key_levels'] = {'error': f'Insufficient data ({len(df)} rows, need {sr_lookback})'}
        
        # FIBONACCI RETRACEMENTS
        if len(df) >= fib_lookback:
            try:
                fib = ValidatedKeyLevels.fibonacci_retracements(df, lookback=fib_lookback)
                # Filter to just the levels (not metadata)
                fib_levels = {}
                for k, v in fib.items():
                    if k.endswith('%') or k.startswith('fib_'):
                        fib_levels[k] = v
                result['fibonacci'] = {
                    'levels': fib_levels,
                    'anchor_high': fib.get('anchor_high_price'),
                    'anchor_low': fib.get('anchor_low_price'),
                    'lookback_days': fib.get('lookback_days', fib_lookback)
                }
            except Exception as e:
                result['fibonacci'] = {'error': str(e)}
                warnings_list.append(f'Fibonacci failed: {e}')
        else:
            result['fibonacci'] = {'error': f'Insufficient data ({len(df)} rows, need {fib_lookback})'}
        
        # MOMENTUM INDICATORS
        try:
            result['momentum'] = {
                'RSI': float(self.data['RSI'].iloc[-1]) if 'RSI' in self.data else None,
                'Stochastic_K': float(self.data['Stoch_K'].iloc[-1]) if 'Stoch_K' in self.data else None,
                'Stochastic_D': float(self.data['Stoch_D'].iloc[-1]) if 'Stoch_D' in self.data else None,
                'MACD': float(self.data['MACD'].iloc[-1]) if 'MACD' in self.data else None,
                'MACD_Signal': float(self.data['MACD_Signal'].iloc[-1]) if 'MACD_Signal' in self.data else None,
                'MACD_Histogram': float(self.data['MACD_Hist'].iloc[-1]) if 'MACD_Hist' in self.data else None,
                'ADX': float(self.data['ADX'].iloc[-1]) if 'ADX' in self.data else None,
                'Plus_DI': float(self.data['Plus_DI'].iloc[-1]) if 'Plus_DI' in self.data else None,
                'Minus_DI': float(self.data['Minus_DI'].iloc[-1]) if 'Minus_DI' in self.data else None
            }
        except Exception as e:
            result['momentum'] = {'error': str(e)}
            warnings_list.append(f'Momentum calculation failed: {e}')
        
        # RISK METRICS
        try:
            returns = df['Price'].pct_change().dropna()
            if len(returns) >= 2:
                vol = ValidatedRiskMetrics.volatility(returns)
                sharpe = ValidatedRiskMetrics.sharpe_ratio(returns)
                var = ValidatedRiskMetrics.value_at_risk(returns)
                mdd = ValidatedRiskMetrics.max_drawdown_analysis(returns)
                
                result['risk'] = {
                    'volatility_daily': vol.get('volatility_daily', 0.0),
                    'volatility_annualized': vol.get('volatility_annualized', 0.0),
                    'sharpe_ratio': sharpe.get('sharpe_ratio', 0.0),
                    'max_drawdown': mdd.get('max_drawdown', 0.0),
                    'var_95': var.get('var', 0.0)
                }
            else:
                result['risk'] = {'error': 'Insufficient returns data'}
        except Exception as e:
            result['risk'] = {'error': str(e)}
            warnings_list.append(f'Risk calculation failed: {e}')
        
        return result
        
    def fetch_data(self, period: str = '1y', start_date: datetime = None, end_date: datetime = None):
        """
        Fetch market data using canonical data fetcher
        
        Args:
            period: Period string (e.g., '1y', '6mo') OR
            start_date/end_date: Explicit date range
        """
        if start_date is None or end_date is None:
            # Convert period to dates
            end_date = datetime.now()
            if period == '1y':
                start_date = end_date - timedelta(days=365)
            elif period == '6mo':
                start_date = end_date - timedelta(days=180)
            elif period == '3mo':
                start_date = end_date - timedelta(days=90)
            elif period == '1mo':
                start_date = end_date - timedelta(days=30)
            else:
                # Default to 1 year
                start_date = end_date - timedelta(days=365)
        
        # Fetch using canonical fetcher
        self.data, self.metadata = self.fetcher.fetch_data(
            self.symbol, start_date, end_date
        )
        
        # Compute all indicators
        self.data = compute_all_indicators(self.data)
        
        return self.data
    
    def detect_market_regime(self, data: pd.DataFrame = None) -> Dict:
        """
        Detect current market regime using ValidatedRegime
        Returns: trending_up, trending_down, ranging, volatile, transitioning
        """
        df = data if data is not None else self.data
        if df is None or len(df) < 50:
            return {
                'regime': 'unknown',
                'confidence': 0,
                'rationale': 'Insufficient data'
            }
        
        # Normalize data to ensure consistent schema
        try:
            df, _ = DataNormalizer.normalize_market_data(df, symbol=self.symbol, require_ohlc=False)
        except DataContractError as e:
            return {
                'regime': 'error',
                'confidence': 0,
                'rationale': f'Data normalization failed: {str(e)}'
            }
        
        # Use ValidatedRegime for consistency with ADX
        regime_result = ValidatedRegime.classify_regime(df, lookback=REGIME_CFG.REGIME_LOOKBACK)
        
        return regime_result
    
    def market_regime(self) -> Dict:
        """
        Detect current market regime using self.data
        Returns: trending_up, trending_down, ranging, volatile, transitioning
        """
        if self.data is None or len(self.data) < 50:
            return {
                'regime': 'unknown',
                'confidence': 0,
                'rationale': 'Insufficient data'
            }
        
        return self.detect_market_regime(self.data)
    
    def support_resistance_levels(self, lookback: int = None) -> Dict[str, List[float]]:
        """
        Find key support and resistance levels using ValidatedKeyLevels
        
        Args:
            lookback: Number of days to analyze (default from config)
        """
        if self.data is None or len(self.data) < 40:
            return {'support': [], 'resistance': []}
        
        if lookback is None:
            lookback = LEVEL_CFG.SR_LOOKBACK
        
        # Use ValidatedKeyLevels for consistent calculation
        sr_result = ValidatedKeyLevels.support_resistance(
            self.data,
            lookback=lookback
        )
        
        return {
            'support': sr_result['support'],
            'resistance': sr_result['resistance'],
            'metadata': {
                'lookback_days': sr_result['lookback_days'],
                'anchor_start': sr_result['anchor_start'],
                'anchor_end': sr_result['anchor_end'],
                'current_price': sr_result['current_price']
            }
        }
    
    def fibonacci_levels(self, lookback: int = None) -> Dict[str, float]:
        """
        Calculate Fibonacci retracement levels using ValidatedKeyLevels
        
        Args:
            lookback: Number of days to analyze (default from config)
        """
        if self.data is None or len(self.data) < 20:
            return {}
        
        if lookback is None:
            lookback = LEVEL_CFG.FIB_LOOKBACK
        
        # Use ValidatedKeyLevels for consistent, anchored calculation
        fib_result = ValidatedKeyLevels.fibonacci_retracements(
            self.data,
            lookback=lookback
        )
        
        # Return just the levels (metadata available in fib_result)
        levels = {}
        for ratio in LEVEL_CFG.FIB_LEVELS:
            level_name = f"{ratio*100:.1f}%"
            if level_name in fib_result:
                levels[level_name] = fib_result[level_name]
        
        # Store metadata for printing
        self._fib_metadata = {
            'anchor_high_date': fib_result.get('anchor_high_date'),
            'anchor_high_price': fib_result.get('anchor_high_price'),
            'anchor_low_date': fib_result.get('anchor_low_date'),
            'anchor_low_price': fib_result.get('anchor_low_price'),
            'lookback_days': fib_result.get('lookback_days'),
            'lookback_start': fib_result.get('lookback_start'),
            'lookback_end': fib_result.get('lookback_end')
        }
        
        return levels
    
    def _cluster_levels(self, levels: List[float], num_clusters: int) -> List[float]:
        """Cluster nearby price levels"""
        if len(levels) == 0:
            return []
        
        levels = sorted(levels)
        if len(levels) <= num_clusters:
            return levels
        
        # Simple clustering by grouping nearby levels
        clustered = []
        current_cluster = [levels[0]]
        threshold = np.std(levels) * 0.5
        
        for level in levels[1:]:
            if level - current_cluster[-1] < threshold:
                current_cluster.append(level)
            else:
                clustered.append(np.mean(current_cluster))
                current_cluster = [level]
        
        if current_cluster:
            clustered.append(np.mean(current_cluster))
        
        return clustered
    
    def momentum_analysis(self) -> Dict[str, float]:
        """
        Comprehensive momentum indicators using ValidatedIndicators
        
        Returns RSI, Stochastic, MACD, ADX with correct implementations
        """
        if self.data is None or len(self.data) < 50:
            return {}
        
        # All indicators already computed by compute_all_indicators()
        # Just extract the latest values
        indicators = {
            f'RSI({INDICATOR_CFG.RSI_PERIOD})': self.data['RSI'].iloc[-1],
            f'Stochastic_K({INDICATOR_CFG.STOCH_K_PERIOD})': self.data['Stoch_K'].iloc[-1],
            f'Stochastic_D({INDICATOR_CFG.STOCH_D_PERIOD})': self.data['Stoch_D'].iloc[-1],
            f'MACD({INDICATOR_CFG.MACD_FAST}/{INDICATOR_CFG.MACD_SLOW})': self.data['MACD'].iloc[-1],
            'MACD_Signal': self.data['MACD_Signal'].iloc[-1],
            'MACD_Histogram': self.data['MACD_Hist'].iloc[-1],
            f'ADX({INDICATOR_CFG.ADX_PERIOD})': self.data['ADX'].iloc[-1],
            'Plus_DI': self.data['Plus_DI'].iloc[-1],
            'Minus_DI': self.data['Minus_DI'].iloc[-1]
        }
        
        return indicators
    
    def volume_profile(self, bins: int = 20) -> pd.DataFrame:
        """Calculate volume profile"""
        if self.data is None:
            return pd.DataFrame()
        
        df = self.data.copy()
        
        # Create price bins
        price_range = df['High'].max() - df['Low'].min()
        bin_size = price_range / bins
        
        # Calculate volume at each price level
        df['Price_Bin'] = ((df['Price'] - df['Low'].min()) / bin_size).astype(int)
        volume_profile = df.groupby('Price_Bin').agg({
            'Volume': 'sum',
            'Price': 'mean'
        }).sort_values('Volume', ascending=False)
        
        volume_profile.columns = ['Total_Volume', 'Avg_Price']
        
        return volume_profile.head(10)
    
    def correlation_matrix(self, symbols: List[str], period: str = '3mo') -> pd.DataFrame:
        """Calculate correlation matrix for multiple symbols"""
        data_dict = {}
        
        for symbol in symbols:
            try:
                df = yf.download(symbol, period=period, progress=False)
                if not df.empty:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.droplevel(1)
                    data_dict[symbol] = df['Close'].pct_change()
            except:
                continue
        
        if len(data_dict) < 2:
            return pd.DataFrame()
        
        # Combine data
        combined = pd.DataFrame(data_dict).dropna()
        
        # Calculate correlation
        corr_matrix = combined.corr()
        
        return corr_matrix
    
    def risk_metrics(self) -> Dict[str, float]:
        """
        Calculate comprehensive risk metrics using ValidatedRiskMetrics
        
        Uses canonical Price column for returns calculation
        
        Returns dict with both detailed keys and backward-compatible aliases:
        - volatility, volatility_daily, volatility_annualized
        - var_95, var_95_1day, cvar_95, cvar_95_1day
        - downside_deviation, max_drawdown, calmar_ratio, sortino_ratio
        """
        if self.data is None or len(self.data) < 30:
            return {}
        
        # Calculate returns from canonical Price column (not raw Close)
        returns = self.fetcher.get_returns(self.data)
        
        # Use ValidatedRiskMetrics for consistent calculations
        vol = ValidatedRiskMetrics.volatility(returns)
        dd = ValidatedRiskMetrics.downside_deviation(returns)
        var = ValidatedRiskMetrics.value_at_risk(returns, method='historical')
        cvar = ValidatedRiskMetrics.conditional_var(returns)
        sortino = ValidatedRiskMetrics.sortino_ratio(returns)
        calmar = ValidatedRiskMetrics.calmar_ratio(returns)
        mdd = ValidatedRiskMetrics.max_drawdown_analysis(returns)
        
        return {
            # Detailed keys (new format)
            'volatility_daily': vol['volatility_daily'],
            'volatility_annualized': vol['volatility_annualized'],
            'var_95_1day': var['var'],  # 1-day VaR at 95% confidence
            'var_method': var['method'],  # 'historical'
            'cvar_95_1day': cvar['cvar'],  # 1-day CVaR at 95% confidence
            # Backward-compatible aliases (for UI)
            'volatility': vol['volatility_annualized'],  # alias for UI
            'var_95': var['var'],  # alias for UI
            'cvar_95': cvar['cvar'],  # alias for UI
            # Common keys
            'downside_deviation': dd['downside_dev_annualized'],
            'max_drawdown': mdd['max_drawdown'],
            'calmar_ratio': calmar['calmar_ratio'],
            'sortino_ratio': sortino['sortino_ratio']
        }
    
    def print_comprehensive_analysis(self):
        """
        Print complete market analysis using validated modules
        
        All calculations now use:
        - Canonical price series from CanonicalDataFetcher
        - ValidatedIndicators (Wilder's RSI/ADX)
        - ValidatedKeyLevels (with anchors)
        - ValidatedRegime (reconciled with ADX)
        - ValidatedRiskMetrics (labeled daily vs annualized)
        """
        print(f"\n{'═'*90}")
        print(f"COMPREHENSIVE MARKET ANALYSIS: {self.symbol}")
        print(f"{'═'*90}")
        
        # Data summary (NEW: explicit date span and price source)
        if self.metadata:
            print(f"\n📅 DATA SUMMARY")
            print(f"   Date Range:  {self.metadata['actual_start']} to {self.metadata['actual_end']}")
            print(f"   Rows:        {self.metadata['num_rows']}")
            print(f"   Price Source: {self.metadata['price_source']}")
        
        # Market Regime (using ValidatedRegime)
        regime = self.market_regime()
        print(f"\n📊 MARKET REGIME (lookback={REGIME_CFG.REGIME_LOOKBACK}d)")
        print(f"   Current Regime: {regime['regime'].upper().replace('_', ' ')}")
        print(f"   Confidence: {regime['confidence']*100:.1f}%")
        if 'metrics' in regime:
            vol_ann = regime['metrics'].get('volatility_annualized_pct', 0)
            adx = regime['metrics'].get('adx', 0)
            print(f"   Volatility: {vol_ann:.2f}% (annualized)")
            print(f"   ADX({INDICATOR_CFG.ADX_PERIOD}): {adx:.2f}")
        if 'rationale' in regime:
            print(f"   Rationale: {regime['rationale'][:100]}...")
        
        # Support/Resistance (using ValidatedKeyLevels)
        levels = self.support_resistance_levels()
        print(f"\n🎯 KEY LEVELS (lookback={LEVEL_CFG.SR_LOOKBACK}d)")
        if 'metadata' in levels:
            meta = levels['metadata']
            print(f"   Analysis Window: {meta['anchor_start'].date()} to {meta['anchor_end'].date()}")
            print(f"   Current Price: ${meta['current_price']:.2f}")
        print(f"   Resistance: {', '.join([f'${x:.2f}' for x in levels['resistance']])}")
        print(f"   Support: {', '.join([f'${x:.2f}' for x in levels['support']])}")
        
        # Fibonacci (using ValidatedKeyLevels with anchors)
        fib = self.fibonacci_levels()
        if fib:
            print(f"\n📐 FIBONACCI RETRACEMENTS (lookback={LEVEL_CFG.FIB_LOOKBACK}d)")
            if hasattr(self, '_fib_metadata'):
                meta = self._fib_metadata
                print(f"   Anchor High: ${meta['anchor_high_price']:.2f} on {meta['anchor_high_date'].date()}")
                print(f"   Anchor Low:  ${meta['anchor_low_price']:.2f} on {meta['anchor_low_date'].date()}")
            for level, price in fib.items():
                print(f"   {level:>6s}: ${price:.2f}")
        
        # Momentum (using ValidatedIndicators)
        momentum = self.momentum_analysis()
        if momentum:
            print(f"\n⚡ MOMENTUM INDICATORS")
            for name, value in momentum.items():
                print(f"   {name:25s}: {value:.2f}")
        
        # Risk Metrics (using ValidatedRiskMetrics)
        risk = self.risk_metrics()
        if risk:
            print(f"\n🛡️  RISK METRICS")
            print(f"   {'volatility (daily)':20s}: {risk['volatility_daily']*100:.4f}%")
            print(f"   {'volatility (annualized)':20s}: {risk['volatility_annualized']*100:.2f}%")
            print(f"   {'downside_deviation':20s}: {risk['downside_deviation']*100:.2f}% (annualized)")
            print(f"   {'var_95 (1-day)':20s}: {risk['var_95_1day']*100:.4f}% ({risk['var_method']})")
            print(f"   {'cvar_95 (1-day)':20s}: {risk['cvar_95_1day']*100:.4f}%")
            print(f"   {'max_drawdown':20s}: {risk['max_drawdown']*100:.2f}%")
            print(f"   {'calmar_ratio':20s}: {risk['calmar_ratio']:.4f} (annualized)")
            print(f"   {'sortino_ratio':20s}: {risk['sortino_ratio']:.4f} (annualized)")
        
        print(f"\n{'═'*90}\n")
