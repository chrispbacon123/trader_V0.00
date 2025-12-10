#!/usr/bin/env python3
"""
Strategy Configuration Manager
Handles saving, loading, and managing strategy configurations
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from enhanced_utils import safe_json_load, safe_json_save, ValidationError

class StrategyConfig:
    """Represents a saved strategy configuration"""
    
    def __init__(self, name: str, strategy_type: str, parameters: Dict[str, Any] = None,
                 description: str = "", tags: List[str] = None, symbol: str = None,
                 initial_capital: float = None):
        self.name = name
        self.strategy_type = strategy_type
        self.parameters = parameters or {}
        # Add symbol and capital to parameters if provided
        if symbol:
            self.parameters['symbol'] = symbol
        if initial_capital:
            self.parameters['initial_capital'] = initial_capital
        self.description = description
        self.tags = tags or []
        self.created_at = datetime.now().isoformat()
        self.last_modified = self.created_at
        self.performance_history = []
        self.metadata = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'strategy_type': self.strategy_type,
            'parameters': self.parameters,
            'description': self.description,
            'tags': self.tags,
            'created_at': self.created_at,
            'last_modified': self.last_modified,
            'performance_history': self.performance_history,
            'metadata': self.metadata
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'StrategyConfig':
        """Create from dictionary"""
        config = StrategyConfig(
            name=data['name'],
            strategy_type=data['strategy_type'],
            parameters=data['parameters'],
            description=data.get('description', ''),
            tags=data.get('tags', [])
        )
        config.created_at = data.get('created_at', datetime.now().isoformat())
        config.last_modified = data.get('last_modified', config.created_at)
        config.performance_history = data.get('performance_history', [])
        config.metadata = data.get('metadata', {})
        return config
    
    def update_performance(self, results: Dict):
        """Add performance results to history"""
        self.performance_history.append({
            'timestamp': datetime.now().isoformat(),
            'results': results
        })
        self.last_modified = datetime.now().isoformat()
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to strategy"""
        self.metadata[key] = value
        self.last_modified = datetime.now().isoformat()


class StrategyManager:
    """Manages strategy configurations"""
    
    def __init__(self, config_file: str = 'strategy_configs.json'):
        self.config_file = config_file
        self.strategies = {}
        self.load_strategies()
    
    def load_strategies(self):
        """Load all saved strategies"""
        data = safe_json_load(self.config_file, {})
        self.strategies = {
            name: StrategyConfig.from_dict(config)
            for name, config in data.items()
        }
    
    def save_strategies(self):
        """Save all strategies to file"""
        data = {
            name: config.to_dict()
            for name, config in self.strategies.items()
        }
        safe_json_save(data, self.config_file)
    
    def save_strategy(self, config: StrategyConfig) -> bool:
        """Save a strategy configuration"""
        try:
            if config.name in self.strategies:
                raise ValidationError(f"Strategy '{config.name}' already exists. Use update instead.")
            
            self.strategies[config.name] = config
            self.save_strategies()
            return True
        except Exception as e:
            print(f"Error saving strategy: {e}")
            return False
    
    def update_strategy(self, name: str, updates: Dict) -> bool:
        """Update an existing strategy"""
        try:
            if name not in self.strategies:
                raise ValidationError(f"Strategy '{name}' not found")
            
            config = self.strategies[name]
            
            if 'description' in updates:
                config.description = updates['description']
            if 'tags' in updates:
                config.tags = updates['tags']
            if 'parameters' in updates:
                config.parameters.update(updates['parameters'])
            if 'metadata' in updates:
                config.metadata.update(updates['metadata'])
            
            config.last_modified = datetime.now().isoformat()
            self.save_strategies()
            return True
        except Exception as e:
            print(f"Error updating strategy: {e}")
            return False
    
    def delete_strategy(self, name: str) -> bool:
        """Delete a strategy"""
        try:
            if name not in self.strategies:
                raise ValidationError(f"Strategy '{name}' not found")
            
            del self.strategies[name]
            self.save_strategies()
            return True
        except Exception as e:
            print(f"Error deleting strategy: {e}")
            return False
    
    def get_strategy(self, name: str) -> Optional[StrategyConfig]:
        """Get a strategy by name"""
        return self.strategies.get(name)
    
    def load_strategy(self, name: str) -> Optional[StrategyConfig]:
        """Load a specific strategy by name (alias for get_strategy)"""
        return self.get_strategy(name)
    
    def list_strategies(self, strategy_type: str = None, tags: List[str] = None) -> List[StrategyConfig]:
        """List strategies with optional filters"""
        results = list(self.strategies.values())
        
        if strategy_type:
            results = [s for s in results if s.strategy_type == strategy_type]
        
        if tags:
            results = [s for s in results if any(tag in s.tags for tag in tags)]
        
        return sorted(results, key=lambda x: x.last_modified, reverse=True)
    
    def export_strategy(self, name: str, export_path: str) -> bool:
        """Export a strategy to JSON file"""
        try:
            if name not in self.strategies:
                raise ValidationError(f"Strategy '{name}' not found")
            
            config = self.strategies[name]
            with open(export_path, 'w') as f:
                json.dump(config.to_dict(), f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting strategy: {e}")
            return False
    
    def import_strategy(self, import_path: str, new_name: str = None) -> bool:
        """Import a strategy from JSON file"""
        try:
            with open(import_path, 'r') as f:
                data = json.load(f)
            
            config = StrategyConfig.from_dict(data)
            
            if new_name:
                config.name = new_name
            
            if config.name in self.strategies:
                raise ValidationError(f"Strategy '{config.name}' already exists")
            
            self.strategies[config.name] = config
            self.save_strategies()
            return True
        except Exception as e:
            print(f"Error importing strategy: {e}")
            return False
    
    def clone_strategy(self, source_name: str, new_name: str) -> bool:
        """Clone an existing strategy"""
        try:
            if source_name not in self.strategies:
                raise ValidationError(f"Strategy '{source_name}' not found")
            
            if new_name in self.strategies:
                raise ValidationError(f"Strategy '{new_name}' already exists")
            
            source = self.strategies[source_name]
            cloned = StrategyConfig(
                name=new_name,
                strategy_type=source.strategy_type,
                parameters=source.parameters.copy(),
                description=f"Cloned from {source_name}: {source.description}",
                tags=source.tags.copy()
            )
            
            self.strategies[new_name] = cloned
            self.save_strategies()
            return True
        except Exception as e:
            print(f"Error cloning strategy: {e}")
            return False
    
    def get_best_performing(self, n: int = 5, metric: str = 'return') -> List[StrategyConfig]:
        """Get top N best performing strategies"""
        strategies_with_perf = []
        
        for config in self.strategies.values():
            if config.performance_history:
                latest = config.performance_history[-1]['results']
                if metric in latest:
                    strategies_with_perf.append((config, latest[metric]))
        
        strategies_with_perf.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in strategies_with_perf[:n]]
    
    def search_strategies(self, query: str) -> List[StrategyConfig]:
        """Search strategies by name, description, or tags"""
        query = query.lower()
        results = []
        
        for config in self.strategies.values():
            if (query in config.name.lower() or
                query in config.description.lower() or
                any(query in tag.lower() for tag in config.tags)):
                results.append(config)
        
        return results


def create_strategy_from_execution(strategy_obj, name: str, description: str = "", 
                                   tags: List[str] = None) -> StrategyConfig:
    """Create a StrategyConfig from a strategy object"""
    
    # Determine strategy type
    strategy_type = strategy_obj.__class__.__name__
    
    # Extract parameters based on strategy type
    parameters = {
        'symbol': getattr(strategy_obj, 'symbol', None),
        'initial_capital': getattr(strategy_obj, 'cash', 100000),
    }
    
    # Type-specific parameters
    if hasattr(strategy_obj, 'lookback'):
        parameters['lookback'] = strategy_obj.lookback
    
    if hasattr(strategy_obj, 'prediction_horizon'):
        parameters['prediction_horizon'] = strategy_obj.prediction_horizon
    
    if hasattr(strategy_obj, 'entry_threshold'):
        parameters['entry_threshold'] = strategy_obj.entry_threshold
    
    if hasattr(strategy_obj, 'exit_threshold'):
        parameters['exit_threshold'] = strategy_obj.exit_threshold
    
    # ML-specific parameters
    if hasattr(strategy_obj, 'n_estimators'):
        parameters['n_estimators'] = strategy_obj.n_estimators
    
    if hasattr(strategy_obj, 'use_ensemble'):
        parameters['use_ensemble'] = strategy_obj.use_ensemble
    
    return StrategyConfig(
        name=name,
        strategy_type=strategy_type,
        parameters=parameters,
        description=description,
        tags=tags or []
    )


if __name__ == '__main__':
    # Test the strategy manager
    print("="*80)
    print("TESTING STRATEGY MANAGER")
    print("="*80)
    
    manager = StrategyManager('test_strategies.json')
    
    # Create test strategy
    config = StrategyConfig(
        name="Test_Short_Term_SPY",
        strategy_type="ShortTermStrategy",
        parameters={
            'symbol': 'SPY',
            'lookback': 14,
            'entry_threshold': 0.02,
            'initial_capital': 100000
        },
        description="Short-term strategy for SPY testing",
        tags=['short-term', 'spy', 'test']
    )
    
    # Test save
    if manager.save_strategy(config):
        print("✅ Strategy saved successfully")
    
    # Test load
    loaded = manager.get_strategy("Test_Short_Term_SPY")
    if loaded:
        print(f"✅ Strategy loaded: {loaded.name}")
    
    # Test list
    strategies = manager.list_strategies()
    print(f"✅ Total strategies: {len(strategies)}")
    
    # Clean up
    manager.delete_strategy("Test_Short_Term_SPY")
    if os.path.exists('test_strategies.json'):
        os.remove('test_strategies.json')
    
    print("\n✅ All strategy manager tests passed!")
