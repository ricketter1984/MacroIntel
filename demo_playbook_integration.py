#!/usr/bin/env python3
"""
Demonstration script for playbook loader integration
"""

import os
import json
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and display results"""
    print(f"\n🔧 {description}")
    print(f"Command: {cmd}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ Command completed successfully")
        else:
            print(f"❌ Command failed with return code {result.returncode}")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def test_playbook_loader_direct():
    """Test playbook loader directly"""
    print("\n🧪 Testing playbook loader directly...")
    
    try:
        from playbook_loader import get_playbook_loader, get_strategy_conditions, get_available_strategies
        
        # Get loader instance
        loader = get_playbook_loader()
        
        # Test basic functionality
        print(f"📋 Version: {loader.get_version()}")
        print(f"📅 Last Updated: {loader.get_config().get('last_updated', 'Unknown')}")
        
        # Test strategy access
        strategies = get_available_strategies()
        print(f"🎯 Available strategies: {', '.join(strategies)}")
        
        # Test strategy details
        for strategy in strategies:
            config = loader.get_strategy_config(strategy)
            print(f"\n📊 {strategy}:")
            print(f"   Description: {config.get('description', 'N/A')}")
            print(f"   Threshold: {config.get('regime_score_threshold', 'N/A')}")
            print(f"   Risk: {config.get('risk_allocation', 'N/A')}")
            print(f"   Instruments: {', '.join(config.get('instruments', []))}")
        
        # Test conditions
        tier1_conditions = get_strategy_conditions("Tier 1")
        print(f"\n🔍 Tier 1 Conditions Categories: {list(tier1_conditions.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct test failed: {e}")
        return False

def test_visual_query_integration():
    """Test visual query tool integration"""
    print("\n🧪 Testing visual query tool integration...")
    
    # Test various conditions
    conditions = [
        ("strategy == 'Tier 1'", "Tier 1 strategy condition"),
        ("strategy in ['Tier 1', 'Tier 2']", "Multiple strategy condition"),
        ("asset in ['MYM', 'MES']", "Asset condition"),
        ("regime > 70", "Regime score condition"),
        ("risk > 20", "Risk allocation condition")
    ]
    
    success_count = 0
    for condition, description in conditions:
        cmd = f'python visual_query_tool.py --assets "BTCUSD,XAUUSD,QQQ" --condition "{condition}" --save'
        if run_command(cmd, description):
            success_count += 1
    
    print(f"\n📊 Visual query integration: {success_count}/{len(conditions)} tests passed")
    return success_count == len(conditions)

def test_playbook_config_structure():
    """Test playbook configuration structure"""
    print("\n🧪 Testing playbook configuration structure...")
    
    try:
        with open("playbook_config.json", 'r') as f:
            config = json.load(f)
        
        # Check structure
        required_sections = ["version", "strategies", "defaults", "metadata"]
        for section in required_sections:
            if section not in config:
                print(f"❌ Missing required section: {section}")
                return False
        
        # Check strategies
        strategies = config.get("strategies", {})
        if not strategies:
            print("❌ No strategies defined")
            return False
        
        # Check each strategy
        for strategy_name, strategy_config in strategies.items():
            print(f"\n📋 Strategy: {strategy_name}")
            
            # Check required fields
            required_fields = ["description", "regime_score_threshold", "risk_allocation", "instruments", "conditions"]
            for field in required_fields:
                if field not in strategy_config:
                    print(f"   ❌ Missing field: {field}")
                    return False
                else:
                    print(f"   ✅ {field}: {str(strategy_config[field])[:50]}...")
            
            # Check conditions structure
            conditions = strategy_config.get("conditions", {})
            expected_categories = [
                "volatility_environment", "market_structure", "volume_breadth",
                "momentum_indicators", "institutional_positioning"
            ]
            
            for category in expected_categories:
                if category in conditions:
                    print(f"   ✅ {category} conditions present")
                else:
                    print(f"   ⚠️ {category} conditions missing")
        
        print("\n✅ Configuration structure is valid")
        return True
        
    except Exception as e:
        print(f"❌ Configuration structure test failed: {e}")
        return False

def test_error_handling():
    """Test error handling scenarios"""
    print("\n🧪 Testing error handling...")
    
    try:
        from playbook_loader import PlaybookLoader, PlaybookConfigError
        
        # Test with non-existent strategy
        loader = PlaybookLoader()
        
        try:
            loader.get_strategy_config("NonExistentStrategy")
            print("❌ Should have raised error for non-existent strategy")
            return False
        except PlaybookConfigError as e:
            print("✅ Correctly handled non-existent strategy")
        
        # Test with invalid strategy name
        try:
            loader.get_strategy_conditions("")
            print("❌ Should have raised error for empty strategy name")
            return False
        except PlaybookConfigError:
            print("✅ Correctly handled empty strategy name")
        
        # Test singleton pattern
        loader1 = PlaybookLoader()
        loader2 = PlaybookLoader()
        if loader1 is loader2:
            print("✅ Singleton pattern working correctly")
        else:
            print("❌ Singleton pattern not working")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_integration_scenarios():
    """Test real-world integration scenarios"""
    print("\n🧪 Testing integration scenarios...")
    
    try:
        from playbook_loader import get_playbook_loader
        
        loader = get_playbook_loader()
        
        # Scenario 1: Get strategy for high regime score
        print("\n📊 Scenario 1: High regime score strategy selection")
        regime_score = 75
        suitable_strategies = []
        
        for strategy in loader.get_available_strategies():
            threshold = loader.get_strategy_threshold(strategy)
            if regime_score >= threshold:
                suitable_strategies.append(strategy)
        
        print(f"   Regime score: {regime_score}")
        print(f"   Suitable strategies: {', '.join(suitable_strategies)}")
        
        # Scenario 2: Get instruments for a strategy
        print("\n📊 Scenario 2: Strategy instrument selection")
        strategy_name = "Tier 1"
        instruments = loader.get_strategy_instruments(strategy_name)
        risk_allocation = loader.get_strategy_risk_allocation(strategy_name)
        
        print(f"   Strategy: {strategy_name}")
        print(f"   Instruments: {', '.join(instruments)}")
        print(f"   Risk allocation: {risk_allocation}")
        
        # Scenario 3: Get conditions for strategy
        print("\n📊 Scenario 3: Strategy conditions")
        conditions = loader.get_strategy_conditions(strategy_name)
        for category, category_conditions in conditions.items():
            print(f"   {category}: {len(category_conditions)} sub-conditions")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration scenarios test failed: {e}")
        return False

def main():
    """Run the demonstration"""
    print("🚀 Playbook Loader Integration Demonstration")
    print("=" * 60)
    
    # Check if required files exist
    required_files = ["playbook_config.json", "playbook_loader.py", "visual_query_tool.py"]
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            return
    
    # Run tests
    tests = [
        test_playbook_loader_direct,
        test_playbook_config_structure,
        test_error_handling,
        test_integration_scenarios,
        test_visual_query_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n" + "=" * 60)
    print("📊 DEMONSTRATION SUMMARY")
    print("=" * 60)
    
    print(f"📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Playbook loader integration is working correctly.")
        print("\n📋 Integration Features:")
        print("   • Configuration loading and validation")
        print("   • Strategy-based condition parsing")
        print("   • Asset validation against strategy instruments")
        print("   • Enhanced visual query tool integration")
        print("   • Error handling and graceful fallbacks")
        print("   • Singleton pattern for efficiency")
        print("   • Comprehensive strategy management")
        
        print("\n🔧 Usage Examples:")
        print("   • python visual_query_tool.py --assets 'BTCUSD,QQQ' --condition 'strategy == \"Tier 1\"'")
        print("   • python visual_query_tool.py --assets 'ES,MYM' --condition 'asset in [\"MYM\", \"MES\"]'")
        print("   • python visual_query_tool.py --assets 'SPY' --condition 'regime > 70' --save")
        
        print("\n📁 Generated Files:")
        output_dir = Path("output")
        if output_dir.exists():
            visual_files = list(output_dir.glob("visual_query_*.png"))
            for file in sorted(visual_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
                size_kb = file.stat().st_size // 1024
                print(f"   • {file.name} ({size_kb} KB)")
    else:
        print("⚠️ Some tests failed. Please review the implementation.")

if __name__ == "__main__":
    main() 