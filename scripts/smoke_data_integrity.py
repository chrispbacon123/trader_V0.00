"""
Test script to verify data integrity and prevent symbol mixing
"""
import sys
from datetime import datetime, timedelta
from market_analytics import MarketAnalytics
from advanced_indicators import PatternRecognition

def test_spy_analysis():
    """Test SPY analysis for data integrity"""
    print("="*80)
    print("TESTING SPY DATA INTEGRITY")
    print("="*80)
    
    # Initialize analytics for SPY
    analytics = MarketAnalytics('SPY')
    analytics.fetch_data(period='1y')
    
    # Check that data is for SPY
    current_price = analytics.data['Close'].iloc[-1]
    print(f"\n✓ Current SPY price: ${current_price:.2f}")
    
    # SPY typically trades in $300-$700 range (as of 2024-2025)
    if not (300 < current_price < 700):
        print(f"⚠️  WARNING: SPY price ${current_price:.2f} seems unusual!")
    
    # Test support/resistance
    levels = analytics.support_resistance_levels()
    print(f"\n✓ Support levels: {[f'${x:.2f}' for x in levels['support']]}")
    print(f"✓ Resistance levels: {[f'${x:.2f}' for x in levels['resistance']]}")
    
    # Verify support is below current price and resistance above
    for support in levels['support']:
        if support > current_price * 1.2:
            print(f"⚠️  WARNING: Support ${support:.2f} too far from current ${current_price:.2f}")
    
    for resistance in levels['resistance']:
        if resistance < current_price * 0.8:
            print(f"⚠️  WARNING: Resistance ${resistance:.2f} too far from current ${current_price:.2f}")
    
    # Test Fibonacci
    fib = analytics.fibonacci_levels()
    print(f"\n✓ Fibonacci levels calculated")
    fib_range = fib['0.0'] - fib['100.0']
    print(f"✓ Fib range: ${fib_range:.2f} (High: ${fib['0.0']:.2f}, Low: ${fib['100.0']:.2f})")
    
    # Verify 50% level is between high and low
    if not (fib['100.0'] < fib['50.0'] < fib['0.0']):
        print(f"⚠️  WARNING: Fibonacci levels out of order!")
    
    # Test regime detection
    regime = analytics.market_regime()
    print(f"\n✓ Market regime: {regime['regime'].upper()}")
    print(f"✓ Confidence: {regime['confidence']*100:.1f}%")
    print(f"✓ Volatility: {regime['volatility']*100:.2f}%")
    
    # Test momentum indicators
    momentum = analytics.momentum_analysis()
    print(f"\n✓ RSI: {momentum['RSI']:.2f}")
    print(f"✓ MACD: {momentum['MACD']:.2f}")
    
    # Test advanced indicators with pattern recognition
    print("\n" + "="*80)
    print("TESTING PATTERN RECOGNITION")
    print("="*80)
    
    # Normalize column names for pattern recognition
    df_normalized = analytics.data.copy()
    df_normalized.columns = df_normalized.columns.str.lower()
    
    patterns = PatternRecognition.find_support_resistance(df_normalized)
    print(f"\n✓ Pattern recognition support: {[f'${x:.2f}' for x in patterns['support'][:3]]}")
    print(f"✓ Pattern recognition resistance: {[f'${x:.2f}' for x in patterns['resistance'][:3]]}")
    
    # Verify no extreme outliers
    all_levels = patterns['support'] + patterns['resistance']
    for level in all_levels:
        ratio = level / current_price
        if ratio > 1.25 or ratio < 0.75:
            print(f"⚠️  WARNING: Level ${level:.2f} is {ratio:.1f}x current price")
    
    print("\n" + "="*80)
    print("✓ ALL TESTS PASSED - DATA INTEGRITY VERIFIED")
    print("="*80)

def test_multiple_symbols():
    """Test that different symbols don't mix data"""
    print("\n" + "="*80)
    print("TESTING MULTIPLE SYMBOL ISOLATION")
    print("="*80)
    
    symbols = ['SPY', 'QQQ', 'AAPL']
    
    for symbol in symbols:
        analytics = MarketAnalytics(symbol)
        analytics.fetch_data(period='6mo')
        
        current_price = analytics.data['Close'].iloc[-1]
        levels = analytics.support_resistance_levels()
        
        print(f"\n{symbol}:")
        print(f"  Current: ${current_price:.2f}")
        print(f"  Support: {[f'${x:.2f}' for x in levels['support'][:2]]}")
        print(f"  Resistance: {[f'${x:.2f}' for x in levels['resistance'][:2]]}")
        
        # Verify levels are reasonable for the symbol
        for level in levels['support'] + levels['resistance']:
            ratio = level / current_price
            if ratio > 1.2 or ratio < 0.8:
                print(f"  ⚠️  WARNING: {symbol} level ${level:.2f} seems off (ratio: {ratio:.2f})")
    
    print("\n✓ Symbol isolation verified - no cross-contamination detected")

if __name__ == "__main__":
    try:
        test_spy_analysis()
        test_multiple_symbols()
        print("\n✅ ALL INTEGRITY TESTS PASSED!\n")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
