"""
Example Usage of Refactored Trading System
Demonstrates all key capabilities
"""

from datetime import datetime, timedelta
from master_analyzer import ANALYZER
from validated_portfolio import ValidatedPortfolio

def example_1_basic_analysis():
    """Example 1: Basic symbol analysis"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Symbol Analysis")
    print("="*80)
    
    # Analyze SPY for the last year
    results = ANALYZER.quick_analysis('SPY', days=252, verbose=True)
    
    # Access specific components
    print("\n--- Quick Access ---")
    print(f"Current Price: ${results['data']['Price'].iloc[-1]:.2f}")
    print(f"RSI: {results['indicators']['RSI']:.2f}")
    print(f"Market Regime: {results['regime']['regime']}")
    print(f"Sharpe Ratio: {results['risk']['sharpe_ratio']['sharpe_ratio']:.4f}")
    
    return results


def example_2_compare_etfs():
    """Example 2: Compare multiple ETFs"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Compare Multiple ETFs")
    print("="*80)
    
    # Compare major index ETFs
    symbols = ['SPY', 'QQQ', 'IWM', 'DIA']
    comparison = ANALYZER.compare_symbols(symbols, days=252, verbose=True)
    
    # Get comparison table
    df = comparison['comparison_table']
    
    # Sort by Sharpe ratio
    df_sorted = df.sort_values('sharpe', ascending=False)
    print("\n--- Ranked by Sharpe Ratio ---")
    print(df_sorted[['symbol', 'sharpe', 'volatility_pct', 'max_dd_pct']].to_string(index=False))
    
    return comparison


def example_3_portfolio_allocation():
    """Example 3: Portfolio allocation with fractional shares"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Portfolio Allocation")
    print("="*80)
    
    # Initialize portfolio
    portfolio = ValidatedPortfolio(
        equity=100000,
        fractional_allowed=True,
        slippage_bps=5.0
    )
    
    # Define target allocation
    target_weights = {
        'SPY': 0.40,   # 40% Large Cap
        'QQQ': 0.30,   # 30% Tech
        'IWM': 0.20,   # 20% Small Cap
        'TLT': 0.10    # 10% Bonds
    }
    
    # Current prices (in production, fetch from market data)
    prices = {
        'SPY': 687.96,
        'QQQ': 622.11,
        'IWM': 230.50,
        'TLT': 90.75
    }
    
    # Allocate
    summary = portfolio.allocate(target_weights, prices)
    ValidatedPortfolio.print_allocation(summary)
    
    # Simulate rebalancing
    print("\n--- Simulating Rebalancing ---")
    
    # Prices change
    new_prices = {
        'SPY': 700.00,  # +1.7%
        'QQQ': 640.00,  # +2.9%
        'IWM': 228.00,  # -1.1%
        'TLT': 89.00    # -1.9%
    }
    
    rebalance_result = portfolio.rebalance(target_weights, new_prices, threshold=0.05)
    
    if rebalance_result['rebalanced']:
        print("Portfolio was rebalanced!")
        print(f"Max drift was {rebalance_result['max_drift']*100:.2f}%")
    else:
        print(rebalance_result['message'])
    
    return summary


def example_4_key_levels():
    """Example 4: Support/Resistance and Fibonacci"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Key Levels Analysis")
    print("="*80)
    
    from canonical_data import FETCHER
    from validated_indicators import compute_all_indicators
    from validated_levels import ValidatedKeyLevels
    
    # Get data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    df, metadata = FETCHER.fetch_data('AAPL', start_date, end_date)
    df = compute_all_indicators(df)
    
    # Compute support/resistance
    sr = ValidatedKeyLevels.support_resistance(df, lookback=100)
    ValidatedKeyLevels.print_support_resistance(sr)
    
    # Compute Fibonacci
    fib = ValidatedKeyLevels.fibonacci_retracements(df, lookback=100)
    ValidatedKeyLevels.print_fibonacci(fib)
    
    return {'support_resistance': sr, 'fibonacci': fib}


def example_5_risk_analysis():
    """Example 5: Comprehensive risk analysis"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Risk Analysis")
    print("="*80)
    
    from canonical_data import FETCHER
    from validated_risk import ValidatedRiskMetrics
    
    # Get data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    df, metadata = FETCHER.fetch_data('SPY', start_date, end_date)
    returns = FETCHER.get_returns(df)
    
    # Compute comprehensive risk metrics
    risk_report = ValidatedRiskMetrics.comprehensive_risk_report(returns)
    ValidatedRiskMetrics.print_risk_report(risk_report)
    
    # Access specific metrics
    print("\n--- Key Risk Metrics ---")
    print(f"Annual Volatility: {risk_report['volatility']['volatility_annualized_pct']:.2f}%")
    print(f"Sharpe Ratio: {risk_report['sharpe_ratio']['sharpe_ratio']:.4f}")
    print(f"Max Drawdown: {risk_report['max_drawdown']['max_drawdown_pct']:.2f}%")
    print(f"VaR (95%): {risk_report['var']['var_pct']:.4f}%")
    print(f"CVaR (95%): {risk_report['cvar']['cvar_pct']:.4f}%")
    
    return risk_report


def example_6_regime_analysis():
    """Example 6: Market regime detection"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Market Regime Analysis")
    print("="*80)
    
    from canonical_data import FETCHER
    from validated_indicators import compute_all_indicators
    from validated_regime import ValidatedRegime
    
    # Get data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    df, metadata = FETCHER.fetch_data('SPY', start_date, end_date)
    df = compute_all_indicators(df)
    
    # Single horizon regime
    regime = ValidatedRegime.classify_regime(df, lookback=50)
    ValidatedRegime.print_regime(regime)
    
    # Multi-horizon analysis
    print("\n--- Multi-Horizon Analysis ---")
    multi = ValidatedRegime.multi_horizon_regime(df)
    
    for horizon, data in multi.items():
        if data['regime'] != 'insufficient_data':
            print(f"{horizon:15s}: {data['regime']:15s} (ADX: {data['adx']:.1f}, Vol: {data['volatility_pct']:.2f}%)")
    
    return regime


def run_all_examples():
    """Run all examples"""
    print("\n" + "="*80)
    print("REFACTORED TRADING SYSTEM - USAGE EXAMPLES")
    print("="*80)
    
    try:
        # Example 1
        example_1_basic_analysis()
        
        # Example 2
        example_2_compare_etfs()
        
        # Example 3
        example_3_portfolio_allocation()
        
        # Example 4
        example_4_key_levels()
        
        # Example 5
        example_5_risk_analysis()
        
        # Example 6
        example_6_regime_analysis()
        
        print("\n" + "="*80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*80)
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run individual examples or all
    
    # Single example:
    # example_1_basic_analysis()
    
    # All examples:
    run_all_examples()
