#!/usr/bin/env python3
"""
Playbook Loader for MacroIntel
Loads and validates playbook configuration from JSON file.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PlaybookConfigError(Exception):
    """Custom exception for playbook configuration errors"""
    pass

class PlaybookLoader:
    """
    Loader for playbook configuration files.
    Provides easy access to strategy conditions and rules.
    """
    
    def __init__(self, config_path: str = "playbook_config.json"):
        """
        Initialize the playbook loader.
        
        Args:
            config_path: Path to the playbook configuration file
        """
        self.config_path = Path(config_path)
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """
        Load and validate the playbook configuration file.
        
        Raises:
            PlaybookConfigError: If file is missing or invalid
        """
        try:
            # Check if file exists
            if not self.config_path.exists():
                raise PlaybookConfigError(
                    f"Playbook configuration file not found: {self.config_path}\n"
                    f"Please ensure 'playbook_config.json' exists in the root directory."
                )
            
            # Load JSON file
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            
            # Validate configuration structure
            self._validate_config()
            
            logging.info(f"✅ Loaded playbook configuration: {self.config_path}")
            logging.info(f"📋 Version: {self._config.get('version', 'Unknown')}")
            logging.info(f"📅 Last Updated: {self._config.get('last_updated', 'Unknown')}")
            
        except json.JSONDecodeError as e:
            raise PlaybookConfigError(
                f"Invalid JSON in playbook configuration file: {e}\n"
                f"Please check the syntax of {self.config_path}"
            )
        except Exception as e:
            raise PlaybookConfigError(f"Error loading playbook configuration: {e}")
    
    def _validate_config(self) -> None:
        """
        Validate the configuration structure and required fields.
        
        Raises:
            PlaybookConfigError: If configuration is invalid
        """
        if not isinstance(self._config, dict):
            raise PlaybookConfigError("Configuration must be a JSON object")
        
        # Check required top-level keys
        required_keys = ['version', 'strategies', 'defaults']
        for key in required_keys:
            if key not in self._config:
                raise PlaybookConfigError(f"Missing required key: {key}")
        
        # Validate strategies
        strategies = self._config.get('strategies', {})
        if not isinstance(strategies, dict) or not strategies:
            raise PlaybookConfigError("Strategies section must be a non-empty object")
        
        # Validate each strategy
        for strategy_name, strategy_config in strategies.items():
            self._validate_strategy(strategy_name, strategy_config)
    
    def _validate_strategy(self, strategy_name: str, strategy_config: Dict[str, Any]) -> None:
        """
        Validate a single strategy configuration.
        
        Args:
            strategy_name: Name of the strategy
            strategy_config: Strategy configuration dictionary
            
        Raises:
            PlaybookConfigError: If strategy configuration is invalid
        """
        if not isinstance(strategy_config, dict):
            raise PlaybookConfigError(f"Strategy '{strategy_name}' must be an object")
        
        # Check required strategy fields
        required_fields = ['description', 'regime_score_threshold', 'risk_allocation', 'instruments', 'conditions']
        for field in required_fields:
            if field not in strategy_config:
                raise PlaybookConfigError(f"Strategy '{strategy_name}' missing required field: {field}")
        
        # Validate regime score threshold
        threshold = strategy_config.get('regime_score_threshold')
        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 100:
            raise PlaybookConfigError(f"Strategy '{strategy_name}' regime_score_threshold must be 0-100")
        
        # Validate instruments list
        instruments = strategy_config.get('instruments', [])
        if not isinstance(instruments, list) or not instruments:
            raise PlaybookConfigError(f"Strategy '{strategy_name}' instruments must be a non-empty list")
        
        # Validate conditions structure
        conditions = strategy_config.get('conditions', {})
        if not isinstance(conditions, dict):
            raise PlaybookConfigError(f"Strategy '{strategy_name}' conditions must be an object")
        
        # Validate each condition category
        expected_categories = [
            'volatility_environment', 'market_structure', 'volume_breadth',
            'momentum_indicators', 'institutional_positioning'
        ]
        
        for category in expected_categories:
            if category in conditions:
                category_config = conditions[category]
                if not isinstance(category_config, dict):
                    raise PlaybookConfigError(f"Strategy '{strategy_name}' {category} must be an object")
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the complete configuration dictionary.
        
        Returns:
            Complete configuration dictionary
        """
        return self._config.copy()
    
    def get_strategy_conditions(self, strategy_name: str) -> Dict[str, Any]:
        """
        Get the conditions block for a specific strategy.
        
        Args:
            strategy_name: Name of the strategy (e.g., 'Tier 1', 'Tier 2')
            
        Returns:
            Strategy conditions dictionary
            
        Raises:
            PlaybookConfigError: If strategy is not found
        """
        strategies = self._config.get('strategies', {})
        
        if strategy_name not in strategies:
            available_strategies = list(strategies.keys())
            raise PlaybookConfigError(
                f"Strategy '{strategy_name}' not found in playbook configuration.\n"
                f"Available strategies: {', '.join(available_strategies)}"
            )
        
        strategy_config = strategies[strategy_name]
        return strategy_config.get('conditions', {})
    
    def get_strategy_config(self, strategy_name: str) -> Dict[str, Any]:
        """
        Get the complete configuration for a specific strategy.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Complete strategy configuration dictionary
            
        Raises:
            PlaybookConfigError: If strategy is not found
        """
        strategies = self._config.get('strategies', {})
        
        if strategy_name not in strategies:
            available_strategies = list(strategies.keys())
            raise PlaybookConfigError(
                f"Strategy '{strategy_name}' not found in playbook configuration.\n"
                f"Available strategies: {', '.join(available_strategies)}"
            )
        
        return strategies[strategy_name].copy()
    
    def get_available_strategies(self) -> List[str]:
        """
        Get list of available strategy names.
        
        Returns:
            List of strategy names
        """
        return list(self._config.get('strategies', {}).keys())
    
    def get_strategy_threshold(self, strategy_name: str) -> int:
        """
        Get the regime score threshold for a strategy.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Regime score threshold
            
        Raises:
            PlaybookConfigError: If strategy is not found
        """
        strategy_config = self.get_strategy_config(strategy_name)
        return strategy_config.get('regime_score_threshold', 50)
    
    def get_strategy_instruments(self, strategy_name: str) -> List[str]:
        """
        Get the recommended instruments for a strategy.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            List of instrument symbols
            
        Raises:
            PlaybookConfigError: If strategy is not found
        """
        strategy_config = self.get_strategy_config(strategy_name)
        return strategy_config.get('instruments', [])
    
    def get_strategy_risk_allocation(self, strategy_name: str) -> str:
        """
        Get the risk allocation for a strategy.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Risk allocation percentage as string
            
        Raises:
            PlaybookConfigError: If strategy is not found
        """
        strategy_config = self.get_strategy_config(strategy_name)
        return strategy_config.get('risk_allocation', '5%')
    
    def get_defaults(self) -> Dict[str, Any]:
        """
        Get the default configuration values.
        
        Returns:
            Default configuration dictionary
        """
        return self._config.get('defaults', {}).copy()
    
    def get_version(self) -> str:
        """
        Get the playbook version.
        
        Returns:
            Playbook version string
        """
        return self._config.get('version', 'Unknown')
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get the metadata information.
        
        Returns:
            Metadata dictionary
        """
        return self._config.get('metadata', {}).copy()
    
    def is_strategy_available(self, strategy_name: str) -> bool:
        """
        Check if a strategy is available in the configuration.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            True if strategy exists, False otherwise
        """
        return strategy_name in self._config.get('strategies', {})
    
    def get_strategy_description(self, strategy_name: str) -> str:
        """
        Get the description for a strategy.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Strategy description
            
        Raises:
            PlaybookConfigError: If strategy is not found
        """
        strategy_config = self.get_strategy_config(strategy_name)
        return strategy_config.get('description', 'No description available')
    
    def reload_config(self) -> None:
        """
        Reload the configuration from file.
        Useful for development or when config file is updated.
        """
        logging.info("🔄 Reloading playbook configuration...")
        self._load_config()

# Global instance for easy access
_playbook_loader = None

def get_playbook_loader(config_path: str = "playbook_config.json") -> PlaybookLoader:
    """
    Get a singleton instance of the playbook loader.
    
    Args:
        config_path: Path to the playbook configuration file
        
    Returns:
        PlaybookLoader instance
    """
    global _playbook_loader
    
    if _playbook_loader is None:
        _playbook_loader = PlaybookLoader(config_path)
    
    return _playbook_loader

def get_strategy_conditions(strategy_name: str) -> Dict[str, Any]:
    """
    Convenience function to get strategy conditions.
    
    Args:
        strategy_name: Name of the strategy
        
    Returns:
        Strategy conditions dictionary
    """
    loader = get_playbook_loader()
    return loader.get_strategy_conditions(strategy_name)

def get_strategy_config(strategy_name: str) -> Dict[str, Any]:
    """
    Convenience function to get complete strategy configuration.
    
    Args:
        strategy_name: Name of the strategy
        
    Returns:
        Complete strategy configuration dictionary
    """
    loader = get_playbook_loader()
    return loader.get_strategy_config(strategy_name)

def get_available_strategies() -> List[str]:
    """
    Convenience function to get available strategies.
    
    Returns:
        List of available strategy names
    """
    loader = get_playbook_loader()
    return loader.get_available_strategies()

# Example usage and testing
if __name__ == "__main__":
    try:
        # Test the loader
        loader = PlaybookLoader()
        
        print("🎯 Playbook Loader Test")
        print("=" * 50)
        
        # Test basic functionality
        print(f"Version: {loader.get_version()}")
        print(f"Available strategies: {loader.get_available_strategies()}")
        
        # Test strategy access
        for strategy in loader.get_available_strategies():
            print(f"\n📋 Strategy: {strategy}")
            print(f"   Description: {loader.get_strategy_description(strategy)}")
            print(f"   Threshold: {loader.get_strategy_threshold(strategy)}")
            print(f"   Risk Allocation: {loader.get_strategy_risk_allocation(strategy)}")
            print(f"   Instruments: {loader.get_strategy_instruments(strategy)}")
        
        # Test conditions access
        tier1_conditions = loader.get_strategy_conditions("Tier 1")
        print(f"\n🔍 Tier 1 Conditions Categories: {list(tier1_conditions.keys())}")
        
        print("\n✅ All tests passed!")
        
    except PlaybookConfigError as e:
        print(f"❌ Configuration Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}") 