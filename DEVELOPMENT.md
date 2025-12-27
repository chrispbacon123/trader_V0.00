# Development Guide

**Version:** V0.20  
**Last Updated:** December 2024

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Modules](#core-modules)
3. [Configuration](#configuration)
4. [Data Pipeline](#data-pipeline)
5. [Strategy Development](#strategy-development)
6. [Testing](#testing)
7. [Contributing](#contributing)

---

## Architecture Overview

### Platform Structure

```
trader_V0.00/
├── Core Configuration
│   └── core_config.py              # Centralized configuration
├── Data Layer
│   ├── canonical_data.py           # Data fetching and normalization
│   ├── data_handler.py             # Data management
│   ├── data_manager.py             # Data caching
│   └── data_normalization.py       # Data preprocessing
├── Validated Modules
│   ├── validated_indicators.py     # Technical indicators
│   ├── validated_levels.py         # Support/resistance/Fibonacci
│   ├── validated_regime.py         # Market regime detection
│   ├── validated_risk.py           # Risk metrics
│   └── validated_portfolio.py      # Portfolio allocation
├── Strategy Layer
│   ├── simple_strategy.py          # Mean reversion strategy
│   ├── ml_strategy.py              # ML-based strategy
│   ├── optimized_ml_strategy.py    # Ensemble ML strategy
│   ├── short_term_strategy.py      # Short-term trading
│   └── strategy_builder.py         # Custom strategy builder
├── Execution Layer
│   ├── order_execution.py          # Order execution algorithms
│   ├── execution_optimizer.py      # Execution optimization
│   └── unified_backtest_engine.py  # Backtesting engine
├── Analytics Layer
│   ├── market_analytics.py         # Market analysis
│   ├── performance_analytics.py    # Performance metrics
│   ├── performance_attribution.py  # Attribution analysis
│   ├── advanced_risk_analytics.py  # Advanced risk metrics
│   └── master_analyzer.py          # Comprehensive analysis
├── Management Layer
│   ├── strategy_manager.py         # Strategy management
│   ├── strategy_optimizer.py       # Parameter optimization
│   ├── strategy_exporter.py        # Strategy export
│   ├── risk_manager.py             # Risk management
│   └── persistence.py              # Data persistence
└── Interface Layer
    ├── advanced_trading_interface.py  # Interactive UI
    ├── trading_cli.py                 # Command-line interface
    └── platform_api.py                # Programmatic API
```

---

## Core Modules

### 1. Core Configuration (core_config.py)

**Purpose:** Centralized configuration for all platform parameters

**Key Components:**

```python
# Version information
PLATFORM_VERSION = "V0.20"
PLATFORM_NAME = "Trading Platform"
PLATFORM_BUILD_DATE = "2025-12-25"

# Configuration classes
@dataclass
class DataConfig:
    PRICE_COLUMN: str = 'Adj Close'
    FALLBACK_PRICE_COLUMN: str = 'Close'
    
@dataclass
class IndicatorConfig:
    RSI_PERIOD: int = 14
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    # ... more indicators
    
@dataclass
class RegimeConfig:
    VOL_LOW_THRESHOLD: float = 0.12   # 12% annualized
    VOL_HIGH_THRESHOLD: float = 0.25  # 25% annualized
    
@dataclass
class PortfolioConfig:
    FRACTIONAL_SHARES_ALLOWED: bool = True
```

**Usage:**
```python
from core_config import PLATFORM_VERSION, INDICATOR_CFG, REGIME_CFG

# Access configuration
rsi_period = INDICATOR_CFG.RSI_PERIOD
vol_threshold = REGIME_CFG.VOL_LOW_THRESHOLD
```

---

### 2. Canonical Data (canonical_data.py)

**Purpose:** Single source of truth for price data

**Key Features:**
- Fetches data from yfinance
- Normalizes to standard OHLCV format
- No MultiIndex columns
- Consistent price column selection

**API:**
```python
from canonical_data import get_canonical_price_series, fetch_stock_data

# Fetch data
df = fetch_stock_data(symbol="SPY", period="365d")

# Get canonical price series
prices = get_canonical_price_series(df)
```

**Guarantees:**
- Returns pandas DataFrame with DatetimeIndex
- Columns: Open, High, Low, Close, Adj Close, Volume
- No missing required columns
- Prices are positive
- High >= Low

---

### 3. Validated Indicators (validated_indicators.py)

**Purpose:** Technical indicators with guaranteed properties

**Indicators Provided:**
- RSI (Relative Strength Index) - bounded [0, 100]
- MACD (Moving Average Convergence Divergence)
- ADX (Average Directional Index) - bounded [0, 100]
- Stochastic Oscillator - bounded [0, 100]
- Bollinger Bands
- ATR (Average True Range)

**API:**
```python
from validated_indicators import calculate_rsi, calculate_macd

# Calculate RSI
rsi = calculate_rsi(prices, period=14)
assert (rsi >= 0).all() and (rsi <= 100).all()

# Calculate MACD
macd, signal, histogram = calculate_macd(prices)
assert np.allclose(histogram, macd - signal)
```

**Guarantees:**
- RSI in [0, 100]
- Stochastic in [0, 100]
- ADX in [0, 100]
- MACD histogram = MACD - Signal
- All use Wilder's smoothing where appropriate

---

### 4. Validated Levels (validated_levels.py)

**Purpose:** Support/Resistance and Fibonacci levels

**Key Features:**
- Fibonacci retracements from defined lookback
- Support/Resistance with proximity filtering
- Auditable anchor points

**API:**
```python
from validated_levels import calculate_fibonacci_levels, find_support_resistance

# Fibonacci levels
fib_levels = calculate_fibonacci_levels(prices, lookback=100)
# Returns: {0.0, 0.236, 0.382, 0.5, 0.618, 1.0}

# Support/Resistance
sr_levels = find_support_resistance(prices, window=100, proximity=0.20)
# Returns levels within 20% of current price
```

**Guarantees:**
- Fibonacci anchors within lookback window
- S/R levels within proximity filter
- Levels sorted and unique

---

### 5. Validated Regime (validated_regime.py)

**Purpose:** Market regime classification

**Regimes:**
- Bull: Uptrend + Low volatility
- Bear: Downtrend + High volatility
- Sideways: No clear trend

**API:**
```python
from validated_regime import detect_market_regime

regime = detect_market_regime(prices, returns)
# Returns: {"regime": "bull", "rationale": "...", "metrics": {...}}
```

**Guarantees:**
- Uses ADX for trend strength
- Realistic volatility thresholds (12% / 25%)
- Clear rationale provided

---

### 6. Validated Risk (validated_risk.py)

**Purpose:** Risk metrics with proper annualization

**Metrics:**
- Volatility (daily and annualized)
- Value at Risk (VaR)
- Conditional VaR (CVaR/Expected Shortfall)
- Sharpe Ratio
- Sortino Ratio
- Maximum Drawdown

**API:**
```python
from validated_risk import calculate_risk_metrics

risk = calculate_risk_metrics(returns)
# Returns labeled metrics (daily vs annualized)
```

**Guarantees:**
- Annualized volatility = daily × √252
- CVaR ≤ VaR (more negative)
- All metrics properly labeled
- No synthetic zero returns

---

### 7. Validated Portfolio (validated_portfolio.py)

**Purpose:** Portfolio allocation with fractional share support

**Key Features:**
- Fractional share allocation (when enabled)
- Whole share enforcement (when disabled)
- Cash residual tracking
- Transaction costs

**API:**
```python
from validated_portfolio import allocate_portfolio

allocation = allocate_portfolio(
    capital=100000,
    prices=prices_dict,
    weights={"SPY": 0.6, "QQQ": 0.4},
    fractional_allowed=True
)
```

**Guarantees:**
- Fractional shares when enabled
- Integer shares when disabled
- Cash residuals tracked explicitly
- No silent int() casts

---

## Configuration

### Enabling Fractional Shares

```python
# In core_config.py
PORTFOLIO_CFG.FRACTIONAL_SHARES_ALLOWED = True
```

**Impact:**
- Shares allocated as floats (e.g., 132.4567)
- Reduces cash drag by 0.5-2%
- More accurate backtests

### Setting Regime Thresholds

```python
# In core_config.py
REGIME_CFG.VOL_LOW_THRESHOLD = 0.12   # 12% annualized
REGIME_CFG.VOL_HIGH_THRESHOLD = 0.25  # 25% annualized
```

**Impact:**
- Controls market regime classification
- Realistic thresholds avoid false signals

### Adjusting Indicator Parameters

```python
# In core_config.py
INDICATOR_CFG.RSI_PERIOD = 14
INDICATOR_CFG.MACD_FAST = 12
INDICATOR_CFG.MACD_SLOW = 26
INDICATOR_CFG.MACD_SIGNAL = 9
```

---

## Data Pipeline

### Data Flow

1. **Fetch:** `canonical_data.fetch_stock_data()`
2. **Normalize:** Ensure OHLCV format
3. **Validate:** Check data quality
4. **Cache:** Store in memory/disk
5. **Process:** Calculate indicators and levels
6. **Analyze:** Generate signals and metrics

### Caching

The platform uses multi-level caching:
- **Memory cache:** Fast access to recent data
- **Disk cache:** Persistent storage
- **Expiration:** Configurable TTL

```python
from cache_manager import CacheManager

cache = CacheManager(ttl=3600)  # 1 hour
data = cache.get_or_fetch(symbol, fetch_func)
```

---

## Strategy Development

### Creating a Custom Strategy

**Template:**

```python
class MyStrategy:
    def __init__(self):
        self.name = "My Strategy"
    
    def generate_signals(self, df):
        """Generate buy/sell signals
        
        Args:
            df: DataFrame with OHLCV and indicators
            
        Returns:
            Series with 1 (buy), -1 (sell), 0 (hold)
        """
        signals = pd.Series(0, index=df.index)
        
        # Your logic here
        # Example: Buy when RSI < 30, Sell when RSI > 70
        signals[df['RSI'] < 30] = 1
        signals[df['RSI'] > 70] = -1
        
        return signals
    
    def backtest(self, symbol, start_date, end_date):
        """Run backtest"""
        # Fetch data
        df = fetch_stock_data(symbol, start=start_date, end=end_date)
        
        # Calculate indicators
        df['RSI'] = calculate_rsi(df['Close'])
        
        # Generate signals
        signals = self.generate_signals(df)
        
        # Calculate returns
        returns = df['Close'].pct_change()
        strategy_returns = returns * signals.shift(1)
        
        return {
            'total_return': (1 + strategy_returns).prod() - 1,
            'sharpe_ratio': strategy_returns.mean() / strategy_returns.std() * np.sqrt(252),
            'max_drawdown': (strategy_returns.cumsum() - strategy_returns.cumsum().cummax()).min()
        }
```

### Integrating with Platform

1. Place in repository root or `custom_strategies/`
2. Import in `strategy_manager.py`
3. Add to strategy registry
4. Test with `unified_backtest_engine.py`

---

## Testing

### Test Structure

See [TESTING.md](TESTING.md) for complete details.

**Quick reference:**

```bash
# Run all tests
pytest

# Run specific suite
pytest tests/test_comprehensive.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

### Writing Tests

Use the validated modules test suite as reference:

```python
def test_my_feature():
    """Test my feature"""
    # Arrange
    data = create_test_data()
    
    # Act
    result = my_function(data)
    
    # Assert
    assert result is not None
    assert len(result) == len(data)
    assert result.min() >= 0
```

---

## Result Schemas

The platform uses typed result objects for consistency:

```python
from result_schemas import BacktestResult

result = BacktestResult(
    total_return=0.15,
    sharpe_ratio=1.2,
    max_drawdown=-0.10,
    win_rate=0.55,
    total_trades=100
)
```

**Guarantees:**
- All results have guaranteed keys
- No KeyError crashes
- Type hints for IDE support

---

## Persistence

Strategy results are persisted to:
- `strategy_history.json` - Historical results
- `runs/` - Individual run outputs
- `live_strategies/` - Exported strategies

```python
from persistence import save_result, load_results

# Save result
save_result({
    'strategy': 'ML Strategy',
    'symbol': 'SPY',
    'return': 0.15,
    'sharpe': 1.2
})

# Load all results
results = load_results()
```

---

## Contributing

### Development Setup

1. Clone repository
2. Create virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Run tests: `pytest`

### Code Style

- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Keep functions focused and small

### Pull Request Process

1. Create feature branch
2. Make changes
3. Add/update tests
4. Run test suite
5. Update documentation
6. Submit PR

---

## API Reference

### Platform API (platform_api.py)

Programmatic access to platform:

```python
from platform_api import PlatformAPI

api = PlatformAPI()

# Run backtest
result = api.run_backtest(
    strategy='ml_strategy',
    symbol='SPY',
    start='2023-01-01',
    end='2024-01-01'
)

# Optimize strategy
best_params = api.optimize_strategy(
    strategy='ml_strategy',
    symbol='SPY',
    trials=30
)

# Get market analytics
analytics = api.get_market_analytics(symbol='SPY')
```

---

## Performance Optimization

### Tips for Faster Backtests

1. **Use caching:** Enable data caching
2. **Reduce trials:** Fewer optimization trials
3. **Vectorize:** Use pandas vectorized operations
4. **Parallel:** Run multiple backtests in parallel
5. **Sample:** Use data sampling for initial tests

### Memory Management

```python
# Clear cache
cache_manager.clear()

# Limit data size
df = df.tail(1000)  # Only use recent data

# Delete unused variables
del large_dataframe
import gc; gc.collect()
```

---

## Troubleshooting

### Common Development Issues

**Import Errors:**
```python
# Use absolute imports
from validated_indicators import calculate_rsi

# Not relative imports
# from .validated_indicators import calculate_rsi
```

**Data Issues:**
```python
# Always validate data
assert not df.empty
assert 'Close' in df.columns
assert not df['Close'].isnull().all()
```

**Type Errors:**
```python
# Use type hints
def my_function(data: pd.DataFrame) -> pd.Series:
    return data['Close']
```

---

## Advanced Topics

### Custom Indicators

```python
def my_custom_indicator(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate custom indicator
    
    Args:
        prices: Price series
        period: Lookback period
        
    Returns:
        Indicator values
    """
    # Your calculation here
    result = prices.rolling(period).mean()
    
    # Validate output
    assert len(result) == len(prices)
    
    return result
```

### ML Model Integration

```python
from sklearn.ensemble import RandomForestClassifier

def train_ml_model(X_train, y_train):
    """Train ML model"""
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42
    )
    model.fit(X_train, y_train)
    return model
```

### Walk-Forward Analysis

```python
def walk_forward_analysis(strategy, data, train_size=0.7):
    """Perform walk-forward analysis"""
    results = []
    
    for i in range(len(data) - train_size):
        train = data[i:i+train_size]
        test = data[i+train_size:i+train_size+test_size]
        
        # Train on in-sample
        params = strategy.optimize(train)
        
        # Test on out-of-sample
        result = strategy.backtest(test, params)
        results.append(result)
    
    return results
```

---

## Version Management

Current version is defined in `core_config.py`:

```python
PLATFORM_VERSION = "V0.20"
```

To update version:
1. Update `core_config.py`
2. Update `README.md`
3. Update `CHANGELOG.md`
4. Tag release in git

---

**Version:** V0.20  
**Platform Status:** Production-Ready  
**Last Updated:** December 2024
