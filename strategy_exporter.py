"""
Strategy Export System
Export strategies for live trading with real capital
"""

import json
import pickle
import os
from datetime import datetime
from pathlib import Path

class StrategyExporter:
    """Handles exporting strategies for deployment"""
    
    def __init__(self, export_dir='/Users/jonathanbrooks/lean-trading/live_strategies'):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
    
    def export_strategy_config(self, strategy_name, strategy_type, parameters, 
                              backtest_results=None, model_path=None):
        """Export strategy configuration for live deployment"""
        
        config = {
            'strategy_name': strategy_name,
            'strategy_type': strategy_type,
            'parameters': parameters,
            'created_at': datetime.now().isoformat(),
            'backtest_results': backtest_results or {},
            'model_path': model_path,
            'status': 'ready_for_deployment',
            'risk_parameters': {
                'max_position_size': parameters.get('max_position_size', 0.95),
                'stop_loss': parameters.get('stop_loss', None),
                'take_profit': parameters.get('take_profit', None),
            }
        }
        
        # Save as JSON for easy reading
        json_path = self.export_dir / f"{strategy_name}_{strategy_type}_config.json"
        with open(json_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Exported config to: {json_path}")
        return json_path
    
    def export_ml_model(self, strategy_name, model, feature_names=None):
        """Export trained ML model for deployment"""
        
        model_dir = self.export_dir / 'models'
        model_dir.mkdir(exist_ok=True)
        
        model_path = model_dir / f"{strategy_name}_model.pkl"
        
        export_data = {
            'model': model,
            'feature_names': feature_names or [],
            'exported_at': datetime.now().isoformat(),
            'model_type': type(model).__name__
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(export_data, f)
        
        print(f"✅ Exported model to: {model_path}")
        return model_path
    
    def create_deployment_package(self, strategy_name, strategy_obj, 
                                 backtest_results=None):
        """Create complete deployment package"""
        
        package_dir = self.export_dir / strategy_name
        package_dir.mkdir(exist_ok=True)
        
        # 1. Export configuration
        params = {
            'symbol': getattr(strategy_obj, 'symbol', 'SPY'),
            'lookback': getattr(strategy_obj, 'lookback', 20),
            'initial_capital': getattr(strategy_obj, 'initial_capital', 100000),
        }
        
        # Add strategy-specific params
        if hasattr(strategy_obj, 'std_dev'):
            params['std_dev'] = strategy_obj.std_dev
        if hasattr(strategy_obj, 'prediction_horizon'):
            params['prediction_horizon'] = strategy_obj.prediction_horizon
        
        config_path = self.export_strategy_config(
            strategy_name=strategy_name,
            strategy_type=type(strategy_obj).__name__,
            parameters=params,
            backtest_results=backtest_results
        )
        
        # 2. Export model if ML strategy
        model_path = None
        if hasattr(strategy_obj, 'model') and strategy_obj.model is not None:
            feature_names = getattr(strategy_obj, 'feature_names', None)
            model_path = self.export_ml_model(strategy_name, strategy_obj.model, feature_names)
        
        # 3. Create deployment script
        deployment_script = f'''#!/usr/bin/env python3
"""
Live Trading Script for {strategy_name}
Generated: {datetime.now().isoformat()}

WARNING: This script is for live trading with real capital.
Always paper trade first and verify performance.
"""

import json
import pickle
from pathlib import Path

def load_strategy():
    """Load strategy configuration and model"""
    config_path = Path(__file__).parent / "{strategy_name}_{type(strategy_obj).__name__}_config.json"
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    print(f"Loaded strategy: {{config['strategy_name']}}")
    print(f"Type: {{config['strategy_type']}}")
    print(f"Parameters: {{config['parameters']}}")
    
    return config

def load_model():
    """Load trained ML model if available"""
    model_path = Path(__file__).parent / "models" / "{strategy_name}_model.pkl"
    
    if model_path.exists():
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        print(f"Loaded model: {{model_data['model_type']}}")
        return model_data['model'], model_data['feature_names']
    
    return None, None

def run_live_trading():
    """Main live trading loop"""
    print("="*60)
    print("LIVE TRADING - {strategy_name}")
    print("="*60)
    
    config = load_strategy()
    model, features = load_model()
    
    # TODO: Implement your broker integration here
    # Example: Interactive Brokers, Alpaca, TD Ameritrade, etc.
    
    print("\\n⚠️  Configure your broker API before running live!")
    print("See: https://www.quantconnect.com/docs/v2/cloud-platform/live-trading")

if __name__ == '__main__':
    run_live_trading()
'''
        
        script_path = package_dir / f"deploy_{strategy_name}.py"
        with open(script_path, 'w') as f:
            f.write(deployment_script)
        os.chmod(script_path, 0o755)
        
        # 4. Create README
        readme = f'''# {strategy_name} - Deployment Package

Generated: {datetime.now().isoformat()}

## Contents

- `{strategy_name}_{type(strategy_obj).__name__}_config.json`: Strategy configuration
- `models/{strategy_name}_model.pkl`: Trained ML model (if applicable)
- `deploy_{strategy_name}.py`: Deployment script template

## Backtest Results

{json.dumps(backtest_results or {}, indent=2)}

## Deployment Steps

1. **Paper Trade First**: Always test with paper trading before live deployment
2. **Configure Broker**: Set up your broker API credentials
3. **Risk Management**: Review and adjust risk parameters
4. **Monitor**: Set up monitoring and alerts
5. **Start Small**: Begin with small position sizes

## Risk Warning

Trading involves substantial risk. This strategy has been backtested but past 
performance does not guarantee future results. Only trade with capital you can 
afford to lose.

## Broker Integration

Popular options:
- QuantConnect LEAN (cloud or local)
- Interactive Brokers API
- Alpaca Markets
- TD Ameritrade API
- MetaTrader (forex)

## Support

For issues or questions, review the main trading interface documentation.
'''
        
        readme_path = package_dir / 'README.md'
        with open(readme_path, 'w') as f:
            f.write(readme)
        
        print("\n" + "="*60)
        print(f"✅ DEPLOYMENT PACKAGE CREATED")
        print("="*60)
        print(f"Location: {package_dir}")
        print(f"\nContents:")
        print(f"  • Configuration: {config_path.name}")
        if model_path:
            print(f"  • ML Model: models/{model_path.name}")
        print(f"  • Deployment Script: deploy_{strategy_name}.py")
        print(f"  • Documentation: README.md")
        print("="*60)
        
        return package_dir
    
    def list_exported_strategies(self):
        """List all exported strategies"""
        
        configs = list(self.export_dir.glob("*_config.json"))
        packages = [d for d in self.export_dir.iterdir() if d.is_dir() and d.name != 'models']
        
        print("\n" + "="*60)
        print("EXPORTED STRATEGIES")
        print("="*60)
        
        if configs:
            print("\nConfiguration Files:")
            for config_path in sorted(configs):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                print(f"\n  📄 {config_path.name}")
                print(f"     Type: {config['strategy_type']}")
                print(f"     Created: {config['created_at'][:10]}")
                if config.get('backtest_results'):
                    results = config['backtest_results']
                    if 'return_pct' in results:
                        print(f"     Backtest Return: {results['return_pct']:.2f}%")
        
        if packages:
            print("\nDeployment Packages:")
            for pkg_dir in sorted(packages):
                print(f"  📦 {pkg_dir.name}/")
                files = list(pkg_dir.iterdir())
                print(f"     Files: {len(files)}")
        
        if not configs and not packages:
            print("\n  No exported strategies yet.")
            print("  Use the interface to create and export strategies.")
        
        print("="*60)

if __name__ == '__main__':
    # Demo
    exporter = StrategyExporter()
    exporter.list_exported_strategies()
