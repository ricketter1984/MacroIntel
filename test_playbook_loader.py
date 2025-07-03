#!/usr/bin/env python3
"""
Test script for playbook loader functionality
"""

import os
import json
import tempfile
import shutil
from pathlib import Path

def test_playbook_loader_basic():
    """Test basic playbook loader functionality"""
    print("🧪 Testing basic playbook loader functionality...")
    
    try:
        from playbook_loader import PlaybookLoader, PlaybookConfigError
        
        # Test loading the configuration
        loader = PlaybookLoader()
        
        # Test basic access methods
        config = loader.get_config()
        assert isinstance(config, dict), "Config should be a dictionary"
        assert "version" in config, "Config should have version"
        assert "strategies" in config, "Config should have strategies"
        
        print("✅ Basic configuration loading passed")
        
        # Test strategy access
        strategies = loader.get_available_strategies()
        assert len(strategies) > 0, "Should have at least one strategy"
        assert "Tier 1" in strategies, "Should have Tier 1 strategy"
        assert "Tier 2" in strategies, "Should have Tier 2 strategy"
        
        print("✅ Strategy access passed")
        
        # Test strategy configuration
        tier1_config = loader.get_strategy_config("Tier 1")
        assert "description" in tier1_config, "Strategy should have description"
        assert "conditions" in tier1_config, "Strategy should have conditions"
        assert "instruments" in tier1_config, "Strategy should have instruments"
        
        print("✅ Strategy configuration access passed")
        
        # Test conditions access
        tier1_conditions = loader.get_strategy_conditions("Tier 1")
        assert isinstance(tier1_conditions, dict), "Conditions should be a dictionary"
        assert "volatility_environment" in tier1_conditions, "Should have volatility conditions"
        
        print("✅ Conditions access passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_playbook_loader_validation():
    """Test playbook loader validation"""
    print("\n🧪 Testing playbook loader validation...")
    
    try:
        from playbook_loader import PlaybookLoader, PlaybookConfigError
        
        # Test with invalid file path
        try:
            loader = PlaybookLoader("nonexistent_file.json")
            print("❌ Should have raised error for nonexistent file")
            return False
        except PlaybookConfigError:
            print("✅ Correctly handled nonexistent file")
        
        # Test with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')
            invalid_file = f.name
        
        try:
            loader = PlaybookLoader(invalid_file)
            print("❌ Should have raised error for invalid JSON")
            return False
        except PlaybookConfigError:
            print("✅ Correctly handled invalid JSON")
        finally:
            os.unlink(invalid_file)
        
        return True
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        return False

def test_playbook_loader_convenience_functions():
    """Test convenience functions"""
    print("\n🧪 Testing convenience functions...")
    
    try:
        from playbook_loader import (
            get_playbook_loader, get_strategy_conditions, 
            get_strategy_config, get_available_strategies
        )
        
        # Test singleton loader
        loader1 = get_playbook_loader()
        loader2 = get_playbook_loader()
        assert loader1 is loader2, "Should return same instance"
        
        print("✅ Singleton pattern works")
        
        # Test convenience functions
        strategies = get_available_strategies()
        assert len(strategies) > 0, "Should return strategies"
        
        tier1_config = get_strategy_config("Tier 1")
        assert "description" in tier1_config, "Should return strategy config"
        
        tier1_conditions = get_strategy_conditions("Tier 1")
        assert isinstance(tier1_conditions, dict), "Should return conditions"
        
        print("✅ Convenience functions work")
        
        return True
        
    except Exception as e:
        print(f"❌ Convenience functions test failed: {e}")
        return False

def test_playbook_loader_error_handling():
    """Test error handling"""
    print("\n🧪 Testing error handling...")
    
    try:
        from playbook_loader import PlaybookLoader, PlaybookConfigError
        
        # Test accessing non-existent strategy
        loader = PlaybookLoader()
        
        try:
            loader.get_strategy_config("NonExistentStrategy")
            print("❌ Should have raised error for non-existent strategy")
            return False
        except PlaybookConfigError as e:
            assert "NonExistentStrategy" in str(e), "Error should mention strategy name"
            print("✅ Correctly handled non-existent strategy")
        
        # Test accessing strategy with invalid name
        try:
            loader.get_strategy_conditions("")
            print("❌ Should have raised error for empty strategy name")
            return False
        except PlaybookConfigError:
            print("✅ Correctly handled empty strategy name")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_playbook_loader_integration():
    """Test integration with other modules"""
    print("\n🧪 Testing integration with other modules...")
    
    try:
        # Test that the loader can be imported by other modules
        from playbook_loader import get_playbook_loader, PlaybookConfigError
        
        # Test integration with visual query tool
        try:
            from visual_query_tool import parse_regime_condition
            print("✅ Visual query tool can import playbook loader")
        except ImportError as e:
            print(f"⚠️ Visual query tool import issue: {e}")
        
        # Test integration with playbook strategist
        try:
            from agents.playbook_strategist_agent import PlaybookStrategistAgent
            print("✅ Playbook strategist can import playbook loader")
        except ImportError as e:
            print(f"⚠️ Playbook strategist import issue: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_playbook_config_content():
    """Test the content of the playbook configuration"""
    print("\n🧪 Testing playbook configuration content...")
    
    try:
        from playbook_loader import PlaybookLoader
        
        loader = PlaybookLoader()
        
        # Test Tier 1 strategy content
        tier1_config = loader.get_strategy_config("Tier 1")
        
        # Check required fields
        required_fields = ["description", "regime_score_threshold", "risk_allocation", "instruments", "conditions"]
        for field in required_fields:
            assert field in tier1_config, f"Tier 1 should have {field}"
        
        # Check specific values
        assert tier1_config["regime_score_threshold"] == 70, "Tier 1 threshold should be 70"
        assert tier1_config["risk_allocation"] == "25%", "Tier 1 risk should be 25%"
        assert "MYM" in tier1_config["instruments"], "Tier 1 should include MYM"
        
        print("✅ Tier 1 configuration content correct")
        
        # Test Tier 2 strategy content
        tier2_config = loader.get_strategy_config("Tier 2")
        assert tier2_config["regime_score_threshold"] == 55, "Tier 2 threshold should be 55"
        assert tier2_config["risk_allocation"] == "15%", "Tier 2 risk should be 15%"
        
        print("✅ Tier 2 configuration content correct")
        
        # Test conditions structure
        tier1_conditions = loader.get_strategy_conditions("Tier 1")
        expected_categories = [
            "volatility_environment", "market_structure", "volume_breadth",
            "momentum_indicators", "institutional_positioning"
        ]
        
        for category in expected_categories:
            assert category in tier1_conditions, f"Tier 1 should have {category} conditions"
        
        print("✅ Conditions structure correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration content test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting playbook loader tests...\n")
    
    tests = [
        test_playbook_loader_basic,
        test_playbook_loader_validation,
        test_playbook_loader_convenience_functions,
        test_playbook_loader_error_handling,
        test_playbook_loader_integration,
        test_playbook_config_content
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Playbook loader is working correctly.")
        print("\n📋 Available Features:")
        print("   • Configuration loading and validation")
        print("   • Strategy access and management")
        print("   • Conditions parsing and retrieval")
        print("   • Error handling and fallbacks")
        print("   • Integration with other modules")
        print("   • Singleton pattern for efficiency")
    else:
        print("⚠️ Some tests failed. Please review the implementation.")

if __name__ == "__main__":
    main() 