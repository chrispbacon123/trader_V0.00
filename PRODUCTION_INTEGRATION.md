# Production Integration Plan

## Current Status
- ✓ Performance Analytics module created and tested
- ✓ Risk Manager module created and tested  
- ✓ Data Manager module created and tested
- ✓ Order Execution module exists
- ⚠️ Main application has backtest return value mismatches

## Identified Issues

### 1. Backtest Return Values (CRITICAL)
Different strategies return different tuple sizes:
- SimpleMeanReversionStrategy: returns 4 values (data, trades, final_value, equity)
- MLTradingStrategy: returns 4 values (df_test, trades, final_value, equity)
- Line 1083: `data, trades, final_value = strategy.backtest()` expects 3 values but gets 4

### 2. Solution: Unified Wrapper
Create a BacktestEngine that normalizes all strategy outputs

## Integration Steps

1. Create unified BacktestEngine
2. Update all strategy calls to use wrapper
3. Integrate new modules (analytics, risk, data)
4. Add comprehensive error handling
5. Test all features end-to-end
6. Commit to GitHub

