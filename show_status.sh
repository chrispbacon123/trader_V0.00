#!/bin/bash
# Quick system status and launch helper

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║           ADVANCED TRADING PLATFORM - STATUS CHECK                ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if we're in the right directory
if [ ! -f "advanced_trading_interface.py" ]; then
    echo "❌ Not in lean-trading directory"
    echo "Run: cd ~/lean-trading"
    exit 1
fi

echo "✅ Location: $(pwd)"
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "✅ Python: $PYTHON_VERSION"
else
    echo "❌ Python3 not found"
    exit 1
fi

echo ""
echo "📊 SYSTEM STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Run status check
python3 system_status.py 2>&1 | tail -20

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 QUICK REFERENCE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 LAUNCH PLATFORM"
echo "   python3 advanced_trading_interface.py"
echo ""
echo "📖 READ DOCUMENTATION"
echo "   cat START_HERE_FINAL.md"
echo "   cat QUICK_START_GUIDE.md"
echo ""
echo "🔧 RUN TESTS"
echo "   python3 comprehensive_test.py"
echo ""
echo "📊 CHECK EXPORTS"
echo "   ls -la live_strategies/"
echo "   ls -la strategy_exports/"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 FIRST TIME? Try this:"
echo "   1. Launch: python3 advanced_trading_interface.py"
echo "   2. Choose Option 2 (Compare All Strategies)"
echo "   3. Enter: SPY"
echo "   4. Enter: 365"
echo "   5. Review results!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Offer to launch
read -p "🚀 Launch platform now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Launching..."
    python3 advanced_trading_interface.py
fi
