"""
Core Configuration Module
Centralized configuration for all lookback windows, price series choices, and calculation parameters
"""

from dataclasses import dataclass
from typing import Optional

# =============================================================================
# CENTRALIZED VERSION - Import this everywhere for consistency
# =============================================================================
PLATFORM_VERSION = "V0.20"
PLATFORM_NAME = "Trading Platform"
PLATFORM_BUILD_DATE = "2025-12-25"


def get_version_string() -> str:
    """Get formatted version string for display"""
    return f"{PLATFORM_NAME} {PLATFORM_VERSION}"


def get_version_info() -> dict:
    """Get version info dict for API responses and persistence"""
    return {
        "version": PLATFORM_VERSION,
        "name": PLATFORM_NAME,
        "build_date": PLATFORM_BUILD_DATE
    }

@dataclass
class DataConfig:
    """Data fetching and preprocessing configuration"""
    
    # Price series selection (prioritize adjusted close)
    PRICE_COLUMN: str = 'Adj Close'
    FALLBACK_PRICE_COLUMN: str = 'Close'
    
    # Volume normalization
    VOLUME_COLUMN: str = 'Volume'
    
    @classmethod
    def get_canonical_price_col(cls, available_cols) -> str:
        """Return the canonical price column to use for all calculations"""
        if cls.PRICE_COLUMN in available_cols:
            return cls.PRICE_COLUMN
        return cls.FALLBACK_PRICE_COLUMN


@dataclass
class IndicatorConfig:
    """Technical indicator configuration with standard periods"""
    
    # RSI (Wilder's method)
    RSI_PERIOD: int = 14
    RSI_MIN: float = 0.0
    RSI_MAX: float = 100.0
    
    # Stochastic
    STOCH_K_PERIOD: int = 14
    STOCH_D_PERIOD: int = 3
    STOCH_MIN: float = 0.0
    STOCH_MAX: float = 100.0
    
    # MACD
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9
    
    # ADX (Wilder's method)
    ADX_PERIOD: int = 14
    ADX_MIN: float = 0.0
    ADX_MAX: float = 100.0
    
    # Moving averages
    SMA_SHORT: int = 20
    SMA_LONG: int = 50
    EMA_SHORT: int = 12
    EMA_LONG: int = 26
    
    # Bollinger Bands
    BB_PERIOD: int = 20
    BB_STD_DEV: float = 2.0
    
    # ATR
    ATR_PERIOD: int = 14


@dataclass
class LevelConfig:
    """Support/resistance and key level configuration"""
    
    # Support/resistance detection
    SR_LOOKBACK: int = 100  # days
    SR_WINDOW: int = 20     # window for local extrema
    SR_CLUSTER_THRESHOLD: float = 0.02  # 2% clustering
    SR_PROXIMITY_FILTER: float = 0.20   # 20% from current price
    
    # Fibonacci retracements
    FIB_LOOKBACK: int = 100  # days
    FIB_LEVELS: tuple = (0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0)


@dataclass
class RegimeConfig:
    """Market regime detection configuration"""
    
    # Regime classification
    REGIME_LOOKBACK: int = 50  # days for regime detection
    REGIME_VOL_WINDOW: int = 20  # rolling volatility window
    
    # Trend thresholds
    TREND_THRESHOLD: float = 0.02  # 2% for SMA crossover
    
    # Volatility thresholds (ANNUALIZED, as decimal)
    # Typical equity vol: 10-20% = 0.10-0.20
    # Low vol regime: < 12% annualized
    # High vol regime: > 25% annualized
    VOL_LOW_THRESHOLD: float = 0.12   # 12% annualized
    VOL_HIGH_THRESHOLD: float = 0.25  # 25% annualized
    
    # ADX thresholds
    ADX_STRONG_TREND: float = 25.0
    ADX_WEAK_TREND: float = 20.0


@dataclass
class RiskConfig:
    """Risk metrics configuration"""
    
    # Time periods
    TRADING_DAYS_PER_YEAR: int = 252
    HOURS_PER_DAY: int = 6.5
    
    # Risk-free rate (annual)
    RISK_FREE_RATE: float = 0.02  # 2%
    
    # VaR/CVaR
    VAR_CONFIDENCE: float = 0.95
    VAR_HORIZON_DAYS: int = 1  # 1-day VaR
    
    # Drawdown
    DD_LOOKBACK: int = 252  # 1 year
    
    # Volatility windows
    VOL_SHORT_WINDOW: int = 20   # ~1 month
    VOL_LONG_WINDOW: int = 60    # ~3 months
    
    # Labels for clarity
    @staticmethod
    def label_volatility(vol: float, is_annualized: bool) -> str:
        """Return a labeled volatility string"""
        if is_annualized:
            return f"{vol*100:.2f}% (annualized)"
        return f"{vol*100:.2f}% (daily)"
    
    @staticmethod
    def annualize_volatility(daily_vol: float) -> float:
        """Convert daily to annualized volatility"""
        return daily_vol * (RiskConfig.TRADING_DAYS_PER_YEAR ** 0.5)
    
    @staticmethod
    def daily_volatility(annualized_vol: float) -> float:
        """Convert annualized to daily volatility"""
        return annualized_vol / (RiskConfig.TRADING_DAYS_PER_YEAR ** 0.5)


@dataclass
class PortfolioConfig:
    """Portfolio allocation and trading configuration"""
    
    # Fractional shares
    FRACTIONAL_SHARES_ALLOWED: bool = True
    MIN_POSITION_VALUE: float = 1.0  # minimum $1 position
    
    # Transaction costs
    COMMISSION_PER_SHARE: float = 0.0  # $0 commission (modern brokers)
    COMMISSION_PERCENT: float = 0.0    # 0% commission
    SLIPPAGE_BPS: float = 5.0          # 5 basis points slippage
    
    # Position sizing
    MAX_POSITION_WEIGHT: float = 0.25  # 25% max per position
    MIN_CASH_BUFFER: float = 0.02      # 2% cash buffer
    
    # Rebalancing
    REBALANCE_THRESHOLD: float = 0.05  # 5% drift triggers rebalance
    
    @staticmethod
    def calculate_slippage(price: float, shares: float) -> float:
        """Calculate slippage cost"""
        return price * abs(shares) * (PortfolioConfig.SLIPPAGE_BPS / 10000.0)
    
    @staticmethod
    def calculate_commission(price: float, shares: float) -> float:
        """Calculate commission cost"""
        share_cost = abs(shares) * PortfolioConfig.COMMISSION_PER_SHARE
        percent_cost = price * abs(shares) * PortfolioConfig.COMMISSION_PERCENT
        return share_cost + percent_cost


# Global configuration instances
DATA_CFG = DataConfig()
INDICATOR_CFG = IndicatorConfig()
LEVEL_CFG = LevelConfig()
REGIME_CFG = RegimeConfig()
RISK_CFG = RiskConfig()
PORTFOLIO_CFG = PortfolioConfig()
