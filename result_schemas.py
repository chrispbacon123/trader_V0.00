"""
Canonical Result Schemas
Defines stable, typed schemas for all API responses
Prevents KeyError/NoneType crashes by enforcing required fields
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime


# =============================================================================
# MARKET ANALYSIS SCHEMAS
# =============================================================================

@dataclass
class DataSummary:
    """Summary of analyzed data"""
    rows: int = 0
    date_range_start: str = ""
    date_range_end: str = ""
    price_source: str = "Close"
    
    @classmethod
    def from_dict(cls, d: dict) -> 'DataSummary':
        return cls(
            rows=d.get('rows', 0),
            date_range_start=str(d.get('date_range_start', '')),
            date_range_end=str(d.get('date_range_end', '')),
            price_source=d.get('price_source', 'Close')
        )


@dataclass
class RegimeResult:
    """Market regime classification result"""
    type: str = "unknown"
    confidence: float = 0.0
    volatility_annualized: float = 0.0
    adx: float = 0.0
    rationale: str = ""
    error: Optional[str] = None
    
    @classmethod
    def from_dict(cls, d: dict) -> 'RegimeResult':
        if not d or 'error' in d:
            return cls(error=d.get('error', 'No data'))
        return cls(
            type=d.get('type', 'unknown'),
            confidence=d.get('confidence', 0.0),
            volatility_annualized=d.get('volatility_annualized', 0.0),
            adx=d.get('adx', 0.0),
            rationale=d.get('rationale', '')
        )


@dataclass
class KeyLevelsResult:
    """Support/resistance levels result"""
    resistance: List[float] = field(default_factory=list)
    support: List[float] = field(default_factory=list)
    current_price: Optional[float] = None
    lookback_days: int = 0
    error: Optional[str] = None
    
    @classmethod
    def from_dict(cls, d: dict) -> 'KeyLevelsResult':
        if not d or 'error' in d:
            return cls(error=d.get('error', 'No data'))
        return cls(
            resistance=d.get('resistance', []),
            support=d.get('support', []),
            current_price=d.get('current_price'),
            lookback_days=d.get('lookback_days', 0)
        )


@dataclass
class FibonacciResult:
    """Fibonacci retracements result"""
    levels: Dict[str, float] = field(default_factory=dict)
    anchor_high: Optional[float] = None
    anchor_low: Optional[float] = None
    lookback_days: int = 0
    error: Optional[str] = None
    
    @classmethod
    def from_dict(cls, d: dict) -> 'FibonacciResult':
        if not d or 'error' in d:
            return cls(error=d.get('error', 'No data'))
        return cls(
            levels=d.get('levels', {}),
            anchor_high=d.get('anchor_high'),
            anchor_low=d.get('anchor_low'),
            lookback_days=d.get('lookback_days', 0)
        )


@dataclass
class MomentumResult:
    """Momentum indicators result"""
    RSI: Optional[float] = None
    Stochastic_K: Optional[float] = None
    Stochastic_D: Optional[float] = None
    MACD: Optional[float] = None
    MACD_Signal: Optional[float] = None
    MACD_Histogram: Optional[float] = None
    ADX: Optional[float] = None
    Plus_DI: Optional[float] = None
    Minus_DI: Optional[float] = None
    error: Optional[str] = None
    
    @classmethod
    def from_dict(cls, d: dict) -> 'MomentumResult':
        if not d or 'error' in d:
            return cls(error=d.get('error', 'No data'))
        return cls(
            RSI=d.get('RSI'),
            Stochastic_K=d.get('Stochastic_K'),
            Stochastic_D=d.get('Stochastic_D'),
            MACD=d.get('MACD'),
            MACD_Signal=d.get('MACD_Signal'),
            MACD_Histogram=d.get('MACD_Histogram'),
            ADX=d.get('ADX'),
            Plus_DI=d.get('Plus_DI'),
            Minus_DI=d.get('Minus_DI')
        )


@dataclass
class RiskResult:
    """Risk metrics result"""
    volatility_daily: float = 0.0
    volatility_annualized: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    var_95: float = 0.0
    error: Optional[str] = None
    
    @classmethod
    def from_dict(cls, d: dict) -> 'RiskResult':
        if not d or 'error' in d:
            return cls(error=d.get('error', 'No data'))
        return cls(
            volatility_daily=d.get('volatility_daily', 0.0),
            volatility_annualized=d.get('volatility_annualized', 0.0),
            sharpe_ratio=d.get('sharpe_ratio', 0.0),
            max_drawdown=d.get('max_drawdown', 0.0),
            var_95=d.get('var_95', 0.0)
        )


@dataclass
class MarketAnalysisResult:
    """Complete market analysis result"""
    success: bool = True
    symbol: str = ""
    period_start: str = ""
    period_end: str = ""
    period_days: int = 0
    data_summary: DataSummary = field(default_factory=DataSummary)
    regime: RegimeResult = field(default_factory=RegimeResult)
    key_levels: KeyLevelsResult = field(default_factory=KeyLevelsResult)
    fibonacci: FibonacciResult = field(default_factory=FibonacciResult)
    momentum: MomentumResult = field(default_factory=MomentumResult)
    risk: RiskResult = field(default_factory=RiskResult)
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None
    platform_version: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, d: dict) -> 'MarketAnalysisResult':
        """Create from API response dict"""
        period = d.get('period', {})
        return cls(
            success=d.get('success', False),
            symbol=d.get('symbol', ''),
            period_start=period.get('start', ''),
            period_end=period.get('end', ''),
            period_days=period.get('days', 0),
            data_summary=DataSummary.from_dict(d.get('data_summary', {})),
            regime=RegimeResult.from_dict(d.get('regime', {})),
            key_levels=KeyLevelsResult.from_dict(d.get('key_levels', {})),
            fibonacci=FibonacciResult.from_dict(d.get('fibonacci', {})),
            momentum=MomentumResult.from_dict(d.get('momentum', {})),
            risk=RiskResult.from_dict(d.get('risk', {})),
            warnings=d.get('warnings', []),
            error=d.get('error'),
            platform_version=d.get('platform_version', '')
        )


# =============================================================================
# BACKTEST SCHEMAS
# =============================================================================

@dataclass
class BacktestResult:
    """Backtest result with stable schema"""
    success: bool = True
    symbol: str = ""
    strategy: str = ""
    start_date: str = ""
    end_date: str = ""
    initial_capital: float = 0.0
    final_value: float = 0.0
    return_pct: float = 0.0
    num_trades: int = 0
    win_rate: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, d: dict) -> 'BacktestResult':
        return cls(
            success=d.get('success', True),
            symbol=d.get('symbol', ''),
            strategy=d.get('strategy', ''),
            start_date=d.get('start_date', ''),
            end_date=d.get('end_date', ''),
            initial_capital=d.get('initial_capital', 0.0),
            final_value=d.get('final_value', 0.0),
            return_pct=d.get('return_pct', d.get('total_return', 0.0)),
            num_trades=d.get('num_trades', 0),
            win_rate=d.get('win_rate', 0.0),
            sharpe_ratio=d.get('sharpe_ratio', 0.0),
            max_drawdown=d.get('max_drawdown', 0.0),
            profit_factor=d.get('profit_factor', 0.0),
            avg_win=d.get('avg_win', 0.0),
            avg_loss=d.get('avg_loss', 0.0),
            warnings=d.get('warnings', []),
            error=d.get('error')
        )


# =============================================================================
# OPTIMIZATION SCHEMAS
# =============================================================================

@dataclass
class OptimizationResult:
    """Strategy optimization result with stable schema"""
    success: bool = False
    best_params: Dict[str, Any] = field(default_factory=dict)
    best_score: Optional[float] = None
    tested: int = 0
    valid: int = 0
    failures: int = 0
    skipped: int = 0
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    failure_summary: Dict[str, int] = field(default_factory=dict)
    example_failures: List[str] = field(default_factory=list)
    top_results: List[Dict] = field(default_factory=list)
    platform_version: str = ""
    optimization_date: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, d: dict) -> 'OptimizationResult':
        return cls(
            success=d.get('success', False),
            best_params=d.get('best_params', {}),
            best_score=d.get('best_score'),
            tested=d.get('tested', 0),
            valid=d.get('valid', 0),
            failures=d.get('failures', 0),
            skipped=d.get('skipped', 0),
            error=d.get('error'),
            warnings=d.get('warnings', []),
            failure_summary=d.get('failure_summary', {}),
            example_failures=d.get('example_failures', []),
            top_results=d.get('top_results', []),
            platform_version=d.get('platform_version', ''),
            optimization_date=d.get('optimization_date', '')
        )
    
    def print_summary(self):
        """Print a human-readable summary"""
        status = "[OK]" if self.success else "[FAIL]"
        print(f"\n{status} Optimization Summary")
        print(f"  Tested: {self.tested} | Valid: {self.valid} | Failed: {self.failures}")
        
        if self.success:
            print(f"  Best Score: {self.best_score:.4f}")
            print(f"  Best Params: {self.best_params}")
        else:
            print(f"  Error: {self.error}")
            if self.failure_summary:
                print(f"  Failure categories:")
                for cat, count in sorted(self.failure_summary.items(), key=lambda x: -x[1])[:3]:
                    print(f"    {cat}: {count}")
            if self.example_failures:
                print(f"  Example failures:")
                for reason in self.example_failures[:3]:
                    print(f"    - {reason[:80]}")


# =============================================================================
# PORTFOLIO SCHEMAS
# =============================================================================

@dataclass
class PositionResult:
    """Individual position in portfolio"""
    symbol: str = ""
    shares: float = 0.0
    price: float = 0.0
    value: float = 0.0
    weight_pct: float = 0.0


@dataclass
class PortfolioAllocationResult:
    """Portfolio allocation result"""
    success: bool = True
    total_equity: float = 0.0
    total_invested: float = 0.0
    cash_remaining: float = 0.0
    cash_pct: float = 0.0
    transaction_costs: float = 0.0
    transaction_costs_pct: float = 0.0
    num_positions: int = 0
    fractional_allowed: bool = True
    positions: Dict[str, PositionResult] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        # Convert PositionResult to dict
        result['positions'] = {
            k: asdict(v) for k, v in self.positions.items()
        }
        return result


# =============================================================================
# HISTORY/PERSISTENCE SCHEMAS
# =============================================================================

@dataclass
class HistoryRecord:
    """Normalized history record"""
    timestamp: str = ""
    symbol: str = "UNKNOWN"
    strategy: str = "Unknown Strategy"
    return_pct: float = 0.0
    initial_capital: float = 100000.0
    final_value: Optional[float] = None
    num_trades: int = 0
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    
    @classmethod
    def from_dict(cls, d: dict) -> 'HistoryRecord':
        """Create from raw dict (handles schema drift)"""
        return cls(
            timestamp=d.get('timestamp') or d.get('date') or datetime.now().isoformat(),
            symbol=d.get('symbol') or d.get('ticker') or 'UNKNOWN',
            strategy=d.get('strategy') or d.get('strategy_name') or d.get('type') or 'Unknown',
            return_pct=d.get('return_pct') or d.get('total_return') or 0.0,
            initial_capital=d.get('initial_capital', 100000.0),
            final_value=d.get('final_value') or d.get('final_portfolio_value'),
            num_trades=d.get('num_trades') or d.get('trades', 0),
            sharpe_ratio=d.get('sharpe_ratio'),
            max_drawdown=d.get('max_drawdown') or d.get('max_dd'),
            win_rate=d.get('win_rate')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

def ensure_optimization_schema(d: dict) -> dict:
    """
    Ensure optimization result has all required fields.
    Use this before accessing any fields to prevent KeyError.
    """
    defaults = OptimizationResult().to_dict()
    for key, default_value in defaults.items():
        if key not in d:
            d[key] = default_value
    # Ensure best_params is never None
    if d.get('best_params') is None:
        d['best_params'] = {}
    return d


def ensure_backtest_schema(d: dict) -> dict:
    """Ensure backtest result has all required fields."""
    defaults = BacktestResult().to_dict()
    for key, default_value in defaults.items():
        if key not in d:
            d[key] = default_value
    return d


def ensure_history_schema(d: dict) -> dict:
    """Ensure history record has all required fields."""
    return HistoryRecord.from_dict(d).to_dict()
