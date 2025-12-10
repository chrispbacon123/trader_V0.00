#!/bin/bash
# Run all trading strategies and compare results

echo "======================================"
echo "RUNNING ALL TRADING STRATEGIES"
echo "======================================"
echo ""

cd "$(dirname "$0")"

echo "1. Simple Mean Reversion Strategy"
echo "-----------------------------------"
python3 simple_strategy.py
echo ""
echo ""

echo "2. ML-Powered Strategy"
echo "-----------------------------------"
python3 ml_strategy.py
echo ""
echo ""

echo "3. Optimized ML Ensemble Strategy"
echo "-----------------------------------"
python3 optimized_ml_strategy.py
echo ""
echo ""

echo "======================================"
echo "ALL STRATEGIES COMPLETED"
echo "======================================"
echo ""
echo "See STRATEGY_COMPARISON.md for detailed analysis"
