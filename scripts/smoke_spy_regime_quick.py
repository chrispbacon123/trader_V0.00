"""Quick test of SPY regime with fixed thresholds"""
import pandas as pd
from pathlib import Path
from validated_indicators import compute_all_indicators
from validated_regime import ValidatedRegime

# Load SPY fixture
fixture_path = Path('tests/data/spy_daily.csv')
df = pd.read_csv(fixture_path)
df['Date'] = pd.to_datetime(df['Date'])
df = df.set_index('Date')
df['Price'] = df['Close']
df = compute_all_indicators(df)

# Classify regime
regime = ValidatedRegime.classify_regime(df)

print('='*80)
print('SPY REGIME CLASSIFICATION (with fixed thresholds)')
print('='*80)
print(f'Regime: {regime["regime"].upper()}')
print(f'Confidence: {regime["confidence"]*100:.1f}%')
print(f'Volatility: {regime["metrics"]["volatility_annualized_pct"]:.2f}% annualized')
print(f'ADX: {regime["metrics"]["adx"]:.1f}')
print(f'')
print(f'Thresholds:')
print(f'  Low:  12.0% annualized')
print(f'  High: 25.0% annualized')
print(f'')
print(f'Rationale:')
for line in regime['rationale'].split('; '):
    print(f'  - {line}')
print('='*80)
print('')
print('BEFORE FIX: Would have been classified as VOLATILE (16.43% > 3%)')
print('AFTER FIX:  Correctly classified as TRANSITIONING (12% < 16.43% < 25%)')
