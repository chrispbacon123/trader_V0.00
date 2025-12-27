"""
Platform API Layer
Thin, stable API for data fetching, analysis, and optimization
Routes UI through DataManager + DataNormalizer for consistency
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import pandas as pd

from data_manager import DataManager
from data_normalization import DataNormalizer, DataContractError
from market_analytics import MarketAnalytics
from strategy_optimizer import StrategyOptimizer
from core_config import PLATFORM_VERSION, get_version_info


class PlatformAPI:
    """Unified API layer for trading platform operations"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.normalizer = DataNormalizer()
    
    def fetch(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Fetch and normalize market data
        
        Args:
            symbol: Ticker symbol
            start_date: Start date
            end_date: End date
            interval: Data interval (1d, 1h, etc.)
        
        Returns:
            (normalized_df, metadata) where df has Price + OHLC + DatetimeIndex
        
        Raises:
            DataContractError: If data is invalid or insufficient
        """
        # Fetch via DataManager
        raw_df = self.data_manager.fetch_data(
            symbol,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        if raw_df is None or len(raw_df) == 0:
            raise DataContractError(
                f"No data available for {symbol}",
                {"symbol": symbol, "start": start_date, "end": end_date}
            )
        
        # Normalize via DataNormalizer
        normalized_df, metadata = self.normalizer.normalize_market_data(
            raw_df,
            symbol=symbol,
            require_ohlc=False  # Derive from Price if missing
        )
        
        return normalized_df, metadata
    
    def analyze_market(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
        lookbacks: Optional[Dict[str, int]] = None,
        debug: bool = False,
        data: pd.DataFrame = None
    ) -> Dict:
        """
        Comprehensive market analysis
        
        IMPORTANT: If data is provided, uses that DataFrame directly (NO re-fetch).
        If data is None, fetches fresh data.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date
            end_date: End date
            interval: Data interval
            lookbacks: Custom lookback periods for analysis
            debug: Enable debug logging
            data: Optional pre-fetched DataFrame (prevents double-fetch)
        
        Returns:
            JSON-serializable dict with stable schema:
            {
                'success': bool,
                'symbol': str,
                'period': dict,
                'data_summary': dict,
                'regime': dict,
                'key_levels': dict,
                'fibonacci': dict,
                'momentum': dict,
                'risk': dict,
                'metadata': dict,
                'warnings': list[str],
                'error': str | None,
                'platform_version': str
            }
        """
        import time
        from run_logger import log_run
        
        start_time = time.time()
        
        try:
            # FETCH DATA (only if not provided)
            if data is not None:
                if debug:
                    print(f"[DEBUG] Using provided data ({len(data)} rows)")
                df = data
                # Normalize the provided data
                df, metadata = self.normalizer.normalize_market_data(
                    df,
                    symbol=symbol,
                    require_ohlc=False
                )
            else:
                if debug:
                    print(f"[DEBUG] Fetching data for {symbol} from {start_date.date()} to {end_date.date()}")
                df, metadata = self.fetch(symbol, start_date, end_date, interval)
            
            if debug:
                print(f"[DEBUG] Using {len(df)} rows, columns: {list(df.columns)}")
                print(f"[DEBUG] Date range: {df.index[0]} to {df.index[-1]}")
            
            # USE THE analyze() METHOD - NO RE-FETCH
            analytics = MarketAnalytics(symbol)
            analysis_result = analytics.analyze(df, symbol=symbol, lookbacks=lookbacks)
            
            # Build response with platform metadata
            result = {
                'success': analysis_result.get('success', True),
                'symbol': symbol,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'days': (end_date - start_date).days
                },
                'data_summary': analysis_result.get('data_summary', {
                    'rows': len(df),
                    'date_range_start': str(df.index[0]),
                    'date_range_end': str(df.index[-1]),
                    'price_source': metadata.get('price_source', 'Close')
                }),
                'regime': analysis_result.get('regime', {}),
                'key_levels': analysis_result.get('key_levels', {}),
                'fibonacci': analysis_result.get('fibonacci', {}),
                'momentum': analysis_result.get('momentum', {}),
                'risk': analysis_result.get('risk', {}),
                'metadata': metadata,
                'warnings': analysis_result.get('warnings', []),
                'error': analysis_result.get('error'),
                'platform_version': PLATFORM_VERSION
            }
            
            # Log the run
            duration = time.time() - start_time
            log_run(
                kind='analyze',
                inputs={
                    'symbol': symbol,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'interval': interval,
                    'data_injected': data is not None
                },
                outputs={
                    'success': result.get('success'),
                    'regime': result.get('regime', {}).get('type'),
                    'rows': result.get('data_summary', {}).get('rows')
                },
                warnings=result.get('warnings', []),
                error=result.get('error'),
                duration_seconds=duration
            )
            
            return result
            
        except DataContractError as e:
            duration = time.time() - start_time
            error_result = {
                'success': False,
                'symbol': symbol,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'data_summary': {},
                'regime': {},
                'key_levels': {},
                'fibonacci': {},
                'momentum': {},
                'risk': {},
                'error': str(e),
                'warnings': [],
                'metadata': e.context if hasattr(e, 'context') else {},
                'platform_version': PLATFORM_VERSION
            }
            log_run(
                kind='analyze',
                inputs={'symbol': symbol},
                error=str(e),
                failure_summary={'data_contract': 1},
                duration_seconds=duration
            )
            return error_result
        except Exception as e:
            duration = time.time() - start_time
            error_result = {
                'success': False,
                'symbol': symbol,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'data_summary': {},
                'regime': {},
                'key_levels': {},
                'fibonacci': {},
                'momentum': {},
                'risk': {},
                'error': f"Analysis error: {type(e).__name__}: {str(e)}",
                'warnings': [],
                'platform_version': PLATFORM_VERSION
            }
            log_run(
                kind='analyze',
                inputs={'symbol': symbol},
                error=f"{type(e).__name__}: {str(e)}",
                failure_summary={'analysis_exception': 1},
                duration_seconds=duration
            )
            return error_result
    
    def optimize_strategy(
        self,
        strategy_class,
        param_grid: Dict,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
        metric: str = "sharpe_ratio",
        max_combinations: int = 50,
        mode: str = "grid",
        data: Optional[pd.DataFrame] = None,
        verbose: bool = True,
        seed: int = 42
    ) -> Dict:
        """
        Optimize strategy parameters
        
        Args:
            strategy_class: Strategy class to optimize
            param_grid: Parameter grid for optimization
            symbol: Symbol to test on
            start_date: Start date
            end_date: End date
            interval: Data interval (currently unused, for future extension)
            metric: Optimization metric (sharpe_ratio, total_return, etc.)
            max_combinations: Max combinations to test
            mode: Optimization mode ("grid" or "random")
            data: Optional pre-fetched DataFrame. If provided, optimizer will
                  use this data instead of fetching (no per-combo downloads).
            verbose: Whether to print progress updates. Default True.
            seed: Random seed for deterministic sampling. Default 42.
        
        Returns:
            Consistent schema dict from StrategyOptimizer with added metadata:
            {
                'success': bool,
                'best_params': dict (never None),
                'best_score': float | None,
                'tested': int,
                'valid': int,
                'failures': int,
                'skipped': int,
                'error': str | None,
                'warnings': list[str],
                'failure_summary': dict[str, int],
                'example_failures': list[str],
                'top_results': list[dict],
                'all_results': list[dict],
                'platform_version': str,
                'optimization_date': str
            }
        """
        import time
        from run_logger import log_run
        
        start_time = time.time()
        optimizer = StrategyOptimizer(strategy_class, metric=metric)
        
        # Pre-fetch and normalize data if not provided
        normalized_data = None
        if data is not None:
            # Normalize provided data
            normalized_data, _ = self.normalizer.normalize_market_data(
                data.copy(), symbol=symbol, require_ohlc=False
            )
        
        try:
            # Choose optimization method based on mode
            if mode == "random":
                # Random search (if implemented in optimizer)
                if hasattr(optimizer, 'random_search'):
                    results = optimizer.random_search(
                        param_grid,
                        symbol,
                        start_date,
                        end_date,
                        n_iterations=max_combinations,
                        data=normalized_data,
                        verbose=verbose,
                        seed=seed
                    )
                else:
                    # Fallback to grid search
                    results = optimizer.grid_search(
                        param_grid,
                        symbol,
                        start_date,
                        end_date,
                        max_combinations=max_combinations,
                        data=normalized_data,
                        verbose=verbose,
                        seed=seed
                    )
            else:
                # Grid search (default)
                results = optimizer.grid_search(
                    param_grid,
                    symbol,
                    start_date,
                    end_date,
                    max_combinations=max_combinations,
                    data=normalized_data,
                    verbose=verbose,
                    seed=seed
                )
            
            # Add platform metadata
            results['platform_version'] = PLATFORM_VERSION
            results['optimization_date'] = datetime.now().isoformat()
            
            # Log the run
            duration = time.time() - start_time
            log_run(
                kind='optimize',
                inputs={
                    'symbol': symbol,
                    'strategy': strategy_class.__name__,
                    'metric': metric,
                    'mode': mode,
                    'max_combinations': max_combinations,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'data_injected': data is not None
                },
                outputs={
                    'success': results.get('success'),
                    'best_score': results.get('best_score'),
                    'best_params': results.get('best_params'),
                    'tested': results.get('tested'),
                    'valid': results.get('valid'),
                    'failures': results.get('failures')
                },
                warnings=results.get('warnings', []),
                failure_summary=results.get('failure_summary'),
                error=results.get('error'),
                duration_seconds=duration
            )
            
            return results
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Optimization setup error: {type(e).__name__}: {str(e)}"
            
            # Log the failed run
            log_run(
                kind='optimize',
                inputs={
                    'symbol': symbol,
                    'strategy': strategy_class.__name__ if hasattr(strategy_class, '__name__') else str(strategy_class),
                    'metric': metric,
                    'mode': mode
                },
                outputs={},
                error=error_msg,
                failure_summary={'setup_error': 1},
                duration_seconds=duration
            )
            
            # Return consistent failure schema
            return {
                'success': False,
                'best_params': {},
                'best_score': None,
                'tested': 0,
                'valid': 0,
                'failures': 1,
                'skipped': 0,
                'error': error_msg,
                'warnings': [],
                'failure_summary': {'setup_error': 1},
                'example_failures': [str(e)],
                'top_results': [],
                'all_results': [],
                'platform_version': PLATFORM_VERSION,
                'optimization_date': datetime.now().isoformat()
            }
    
    def batch_analyze(
        self,
        symbols: list,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
        data_map: Optional[Dict[str, pd.DataFrame]] = None,
        use_cache: bool = False
    ) -> list:
        """
        Analyze multiple symbols in batch
        
        Reuses fetched data per symbol (never refetches the same symbol).
        
        Args:
            symbols: List of ticker symbols
            start_date: Start date for all symbols
            end_date: End date for all symbols
            interval: Data interval
            data_map: Optional dict mapping symbol -> pre-fetched DataFrame
            use_cache: Whether to use local data cache
            
        Returns:
            List of analysis results (same schema as analyze_market)
        """
        results = []
        fetched_data = data_map or {}
        
        for symbol in symbols:
            try:
                # Reuse cached data if available
                df = fetched_data.get(symbol)
                
                result = self.analyze_market(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval,
                    data=df  # Inject data if available
                )
                
                # Cache the fetched data for potential reuse
                if df is None and result.get('success'):
                    # Data was fetched internally, can't cache without re-fetch
                    pass
                    
                results.append(result)
            except Exception as e:
                results.append({
                    'success': False,
                    'symbol': symbol,
                    'error': str(e),
                    'platform_version': PLATFORM_VERSION
                })
        
        return results
    
    def batch_optimize(
        self,
        strategy_class,
        symbols: list,
        param_grid: Dict,
        start_date: datetime,
        end_date: datetime,
        metric: str = "sharpe_ratio",
        max_combinations: int = 50,
        mode: str = "grid",
        param_grids: Optional[Dict[str, Dict]] = None,
        data_map: Optional[Dict[str, pd.DataFrame]] = None,
        verbose: bool = False,
        seed: int = 42
    ) -> list:
        """
        Optimize strategy across multiple symbols
        
        Fetches data ONCE per symbol and reuses for all parameter combinations.
        Uses verbose=False by default to reduce output clutter in batch mode.
        
        Args:
            strategy_class: Strategy class to optimize (or list of classes)
            symbols: List of ticker symbols
            param_grid: Default parameter grid for optimization
            start_date: Start date
            end_date: End date
            metric: Optimization metric
            max_combinations: Max combinations per symbol
            mode: Optimization mode ("grid" or "random")
            param_grids: Optional dict mapping symbol -> custom param_grid
            data_map: Optional dict mapping symbol -> pre-fetched DataFrame.
                      If provided, uses this data instead of fetching.
            verbose: Whether to print per-combo progress. Default False for batch.
            seed: Random seed for deterministic sampling. Default 42.
            
        Returns:
            List of optimization results with 'symbol' field, sorted by symbol
        """
        from run_logger import log_run
        import time
        
        results = []
        fetched_data = dict(data_map) if data_map else {}
        
        # Pre-fetch all symbols that aren't in data_map
        symbols_to_fetch = [s for s in symbols if s not in fetched_data]
        if symbols_to_fetch:
            print(f"Pre-fetching data for {len(symbols_to_fetch)} symbols...")
            for symbol in symbols_to_fetch:
                try:
                    df, _ = self.fetch(symbol, start_date, end_date)
                    fetched_data[symbol] = df
                except Exception as e:
                    print(f"  Warning: Failed to fetch {symbol}: {e}")
                    # Will be handled in the per-symbol loop
        
        batch_start = time.time()
        
        for symbol in symbols:
            try:
                # Use symbol-specific param_grid if provided
                grid = param_grids.get(symbol, param_grid) if param_grids else param_grid
                
                # Get pre-fetched data for this symbol
                symbol_data = fetched_data.get(symbol)
                
                result = self.optimize_strategy(
                    strategy_class=strategy_class,
                    param_grid=grid,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    metric=metric,
                    max_combinations=max_combinations,
                    mode=mode,
                    data=symbol_data,  # Pass pre-fetched data
                    verbose=verbose,   # Use batch verbose setting
                    seed=seed
                )
                result['symbol'] = symbol
                results.append(result)
            except Exception as e:
                results.append({
                    'success': False,
                    'symbol': symbol,
                    'best_params': {},
                    'error': str(e),
                    'platform_version': PLATFORM_VERSION
                })
        
        # Sort results by symbol for stable output
        results = sorted(results, key=lambda r: r.get('symbol', ''))
        
        # Log the batch run
        batch_duration = time.time() - batch_start
        successful = sum(1 for r in results if r.get('success'))
        log_run(
            kind='batch_optimize',
            inputs={
                'symbols': symbols,
                'strategy': strategy_class.__name__ if hasattr(strategy_class, '__name__') else str(strategy_class),
                'metric': metric,
                'mode': mode,
                'max_combinations': max_combinations,
                'num_symbols': len(symbols),
                'data_injected': data_map is not None
            },
            outputs={
                'total': len(results),
                'successful': successful,
                'failed': len(results) - successful
            },
            duration_seconds=batch_duration
        )
        
        return results
    
    def backtest_strategy(
        self,
        strategy_class,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        params: Optional[Dict] = None,
        data: Optional[pd.DataFrame] = None,
        debug: bool = False
    ) -> Dict:
        """
        Run strategy backtest with optional debug trace
        
        Args:
            strategy_class: Strategy class to backtest
            symbol: Ticker symbol
            start_date: Start date
            end_date: End date
            params: Strategy parameters
            data: Optional pre-fetched DataFrame
            debug: Enable debug trace for explainability
            
        Returns:
            Backtest result dict with optional decision_trace
        """
        import time
        from run_logger import log_run
        
        start_time = time.time()
        
        try:
            # Initialize strategy with parameters
            strategy_params = params or {}
            strategy = strategy_class(symbol=symbol, **strategy_params)
            
            # Fetch data if not provided
            if data is None:
                df, metadata = self.fetch(symbol, start_date, end_date)
            else:
                df = data
                df, metadata = self.normalizer.normalize_market_data(
                    df.copy(), symbol=symbol, require_ohlc=False
                )
            
            # Run backtest with data injection
            backtest_results = strategy.backtest(start_date, end_date, data=df)
            
            # Unpack results (handle different return formats)
            if len(backtest_results) == 3:
                df_result, trades, final_value = backtest_results
                equity_curve = []
            elif len(backtest_results) == 4:
                df_result, trades, final_value, equity_curve = backtest_results
            else:
                df_result = backtest_results[0]
                trades = backtest_results[1] if len(backtest_results) > 1 else []
                final_value = backtest_results[2] if len(backtest_results) > 2 else 0
                equity_curve = []
            
            # Calculate metrics
            initial_capital = strategy_params.get('initial_capital', 10000)
            return_pct = ((final_value - initial_capital) / initial_capital) * 100
            
            result = {
                'success': True,
                'symbol': symbol,
                'strategy': strategy_class.__name__,
                'params': strategy_params,
                'final_value': final_value,
                'return_pct': return_pct,
                'num_trades': len(trades),
                'trades': trades[-10:] if trades else [],  # Last 10 trades
                'platform_version': PLATFORM_VERSION
            }
            
            # Add decision trace if debug enabled
            if debug and hasattr(df_result, 'columns'):
                result['decision_trace'] = self._build_decision_trace(
                    df_result, trades, strategy_class.__name__
                )
            
            # Log the run
            duration = time.time() - start_time
            log_run(
                kind='backtest',
                inputs={
                    'symbol': symbol,
                    'strategy': strategy_class.__name__,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'params': strategy_params,
                    'data_injected': data is not None
                },
                outputs={
                    'success': True,
                    'final_value': final_value,
                    'return_pct': return_pct,
                    'num_trades': len(trades)
                },
                duration_seconds=duration
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}"
            
            log_run(
                kind='backtest',
                inputs={
                    'symbol': symbol,
                    'strategy': strategy_class.__name__ if hasattr(strategy_class, '__name__') else str(strategy_class)
                },
                error=error_msg,
                failure_summary={'backtest_exception': 1},
                duration_seconds=duration
            )
            
            return {
                'success': False,
                'symbol': symbol,
                'strategy': strategy_class.__name__ if hasattr(strategy_class, '__name__') else str(strategy_class),
                'error': error_msg,
                'platform_version': PLATFORM_VERSION
            }
    
    def _build_decision_trace(self, df: pd.DataFrame, trades: list, strategy_name: str) -> Dict:
        """
        Build decision trace for explainability
        
        Returns key indicator values and thresholds at last signal
        """
        trace = {
            'strategy': strategy_name,
            'last_signal': None,
            'last_reason': None,
            'indicator_values': {},
            'thresholds': {},
            'warnings': []
        }
        
        try:
            # Find last trade/signal
            if trades:
                last_trade = trades[-1]
                if isinstance(last_trade, dict):
                    trace['last_signal'] = last_trade.get('action', 'UNKNOWN')
                    trace['last_reason'] = last_trade.get('reason', 'Trade executed')
                elif isinstance(last_trade, tuple) and len(last_trade) >= 2:
                    trace['last_signal'] = last_trade[1]  # BUY/SELL
                    trace['last_reason'] = f"{last_trade[1]} at ${last_trade[2]:.2f}" if len(last_trade) > 2 else None
            
            # Extract indicator values from last row
            if len(df) > 0:
                last_row = df.iloc[-1]
                
                # Common indicators
                indicator_cols = ['RSI', 'RSI_7', 'RSI_14', 'EMA_Fast', 'EMA_Slow', 
                                  'SMA', 'Upper', 'Lower', 'Momentum', 'Signal',
                                  'MACD', 'MACD_Signal', 'ADX']
                
                for col in indicator_cols:
                    if col in df.columns:
                        val = last_row[col]
                        if pd.notna(val):
                            trace['indicator_values'][col] = float(val)
                
                # Strategy-specific thresholds
                if 'ShortTerm' in strategy_name:
                    trace['thresholds'] = {
                        'rsi_overbought': 70,
                        'rsi_oversold': 30,
                        'momentum_negative_threshold': -0.02
                    }
                elif 'MeanReversion' in strategy_name:
                    trace['thresholds'] = {
                        'upper_band': float(last_row.get('Upper', 0)) if 'Upper' in df.columns else None,
                        'lower_band': float(last_row.get('Lower', 0)) if 'Lower' in df.columns else None
                    }
                    
        except Exception as e:
            trace['warnings'].append(f"Trace generation error: {str(e)}")
        
        return trace


# Singleton instance for convenience
_api = None

def get_api() -> PlatformAPI:
    """Get singleton API instance"""
    global _api
    if _api is None:
        _api = PlatformAPI()
    return _api


def export_batch_analysis_csv(results: list, path: str) -> bool:
    """
    Export batch analysis results to CSV
    
    Args:
        results: List of analysis result dicts from batch_analyze
        path: Output CSV path
        
    Returns:
        True if successful
    """
    try:
        rows = []
        for r in results:
            row = {
                'symbol': r.get('symbol', ''),
                'success': r.get('success', False),
                'regime': r.get('regime', {}).get('type', ''),
                'regime_confidence': r.get('regime', {}).get('confidence', 0),
                'rsi': r.get('momentum', {}).get('RSI', None),
                'sharpe': r.get('risk', {}).get('sharpe_ratio', None),
                'volatility': r.get('risk', {}).get('volatility', None),
                'error': r.get('error', ''),
                'platform_version': r.get('platform_version', '')
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        df.to_csv(path, index=False)
        return True
    except Exception:
        return False


def export_batch_optimize_csv(results: list, path: str) -> bool:
    """
    Export batch optimization results to CSV
    
    Args:
        results: List of optimization result dicts from batch_optimize
        path: Output CSV path
        
    Returns:
        True if successful
    """
    try:
        rows = []
        for r in results:
            row = {
                'symbol': r.get('symbol', ''),
                'success': r.get('success', False),
                'best_score': r.get('best_score', None),
                'best_params': str(r.get('best_params', {})),
                'tested': r.get('tested', 0),
                'valid': r.get('valid', 0),
                'failures': r.get('failures', 0),
                'error': r.get('error', ''),
                'platform_version': r.get('platform_version', '')
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        df.to_csv(path, index=False)
        return True
    except Exception:
        return False
