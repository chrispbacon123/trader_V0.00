#!/bin/bash
# Safe startup script with system checks

cd "$(dirname "$0")"

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║          🚀 TRADING INTERFACE - STARTING SYSTEM CHECKS 🚀            ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
echo "1. Checking Python..."
if command -v python3 &> /dev/null; then
    echo "   ✅ Python found: $(python3 --version)"
else
    echo "   ❌ Python 3 not found!"
    exit 1
fi

# Check required files
echo ""
echo "2. Checking required files..."
required_files=(
    "simple_strategy.py"
    "ml_strategy.py"
    "optimized_ml_strategy.py"
    "short_term_strategy.py"
    "advanced_trading_interface.py"
    "robust_utils.py"
)

missing=0
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ Missing: $file"
        missing=1
    fi
done

if [ $missing -eq 1 ]; then
    echo ""
    echo "❌ Missing required files. Cannot start."
    exit 1
fi

# Test imports
echo ""
echo "3. Testing Python imports..."
python3 << 'EOF'
try:
    import yfinance
    import pandas
    import numpy
    import xgboost
    import sklearn
    import optuna
    print("   ✅ All packages available")
    exit(0)
except ImportError as e:
    print(f"   ❌ Missing package: {e}")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Missing Python packages. Run: pip install yfinance pandas numpy xgboost scikit-learn optuna"
    exit 1
fi

# Quick functionality test
echo ""
echo "4. Testing core functionality..."
python3 << 'EOF'
try:
    from short_term_strategy import ShortTermStrategy
    from datetime import datetime, timedelta
    
    # Quick test
    strategy = ShortTermStrategy('SPY')
    end = datetime.now()
    start = end - timedelta(days=30)
    data, trades, final, equity = strategy.backtest(start, end)
    
    print(f"   ✅ System test passed ({len(data)} days data)")
    exit(0)
except Exception as e:
    print(f"   ❌ System test failed: {str(e)[:60]}")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ System test failed. Please check error messages above."
    exit 1
fi

# All checks passed
echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║               ✅ ALL CHECKS PASSED - STARTING INTERFACE ✅            ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
sleep 1

# Launch interface
python3 advanced_trading_interface.py
