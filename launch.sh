#!/bin/bash
# Quick launcher for Trading CLI

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

echo "🚀 Launching Trading Strategy CLI..."
echo ""
python advanced_trading_interface.py
