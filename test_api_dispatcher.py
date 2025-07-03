#!/usr/bin/env python3
"""
Test script for the API Dispatcher System

This script demonstrates how to use the modular API dispatcher to run
Benzinga and Polygon API tasks in isolated virtual environments.
"""

import json
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api_dispatcher import dispatch_api_task, get_api_status, cleanup_dispatcher

def test_api_dispatcher():
    """Test the API dispatcher functionality."""
    
    print("🚀 Testing MacroIntel API Dispatcher System")
    print("=" * 50)
    
    # Check API status
    print("\n📊 Checking API Status:")
    status = get_api_status()
    print(json.dumps(status, indent=2))
    
    # Test Benzinga API
    print("\n🔍 Testing Benzinga API:")
    benzinga_result = dispatch_api_task("benzinga", "test/test_benzinga.py")
    
    print("Benzinga Result:")
    print(f"  Success: {benzinga_result['success']}")
    print(f"  Return Code: {benzinga_result.get('return_code', 'N/A')}")
    if benzinga_result['success']:
        print("  ✅ Benzinga API test completed successfully")
        if benzinga_result.get('stdout'):
            print(f"  Output: {benzinga_result['stdout'][:500]}...")
    else:
        print(f"  ❌ Benzinga API test failed: {benzinga_result.get('error', 'Unknown error')}")
        if benzinga_result.get('stderr'):
            print(f"  Error: {benzinga_result['stderr']}")
    
    # Test Polygon API
    print("\n🔍 Testing Polygon API:")
    polygon_result = dispatch_api_task("polygon", "test/test_polygon.py --symbol AAPL --type news")
    
    print("Polygon Result:")
    print(f"  Success: {polygon_result['success']}")
    print(f"  Return Code: {polygon_result.get('return_code', 'N/A')}")
    if polygon_result['success']:
        print("  ✅ Polygon API test completed successfully")
        if polygon_result.get('stdout'):
            print(f"  Output: {polygon_result['stdout'][:500]}...")
    else:
        print(f"  ❌ Polygon API test failed: {polygon_result.get('error', 'Unknown error')}")
        if polygon_result.get('stderr'):
            print(f"  Error: {polygon_result['stderr']}")
    
    # Summary
    print("\n📋 Test Summary:")
    print(f"  Benzinga: {'✅ PASS' if benzinga_result['success'] else '❌ FAIL'}")
    print(f"  Polygon: {'✅ PASS' if polygon_result['success'] else '❌ FAIL'}")
    
    # Cleanup
    cleanup_dispatcher()
    
    return benzinga_result['success'] and polygon_result['success']

def test_individual_apis():
    """Test individual API dispatches."""
    
    print("\n🧪 Testing Individual API Dispatches")
    print("=" * 40)
    
    # Test Benzinga only
    print("\n📰 Testing Benzinga News API:")
    result = dispatch_api_task("benzinga", "test/test_benzinga.py")
    print(f"Result: {'✅ Success' if result['success'] else '❌ Failed'}")
    
    # Test Polygon only
    print("\n📊 Testing Polygon News API:")
    result = dispatch_api_task("polygon", "test/test_polygon.py --symbol BTC-USD --type news")
    print(f"Result: {'✅ Success' if result['success'] else '❌ Failed'}")

if __name__ == "__main__":
    try:
        # Run comprehensive test
        success = test_api_dispatcher()
        
        # Run individual tests
        test_individual_apis()
        
        if success:
            print("\n🎉 All tests completed successfully!")
            sys.exit(0)
        else:
            print("\n⚠️  Some tests failed. Check the output above for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        cleanup_dispatcher()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        cleanup_dispatcher()
        sys.exit(1) 