"""
Test refactored MarketAnalytics
"""

from market_analytics import MarketAnalytics

# Test with SPY
print("Testing refactored MarketAnalytics with SPY...")
print("="*80)

ma = MarketAnalytics('SPY')
ma.fetch_data(period='1y')

# Print comprehensive analysis
ma.print_comprehensive_analysis()

print("\nTest completed successfully!")
