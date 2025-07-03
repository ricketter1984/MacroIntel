#!/usr/bin/env python3
"""
Simple Demo of the API Dispatcher System

This script demonstrates the basic functionality of the modular API dispatcher
for handling conflicting urllib3 versions in MacroIntel.
"""

import json
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api_dispatcher import dispatch_api_task, get_api_status

def main():
    """Demonstrate the API dispatcher functionality."""
    
    print("🚀 MacroIntel API Dispatcher Demo")
    print("=" * 40)
    
    # Check current status
    print("\n📊 Current API Status:")
    status = get_api_status()
    for source, info in status.items():
        status_icon = "✅" if info["ready"] else "❌"
        print(f"  {status_icon} {source}: {'Ready' if info['ready'] else 'Not Ready'}")
    
    # Demo 1: Simple API calls
    print("\n🔍 Demo 1: Simple API Calls")
    print("-" * 30)
    
    # Benzinga demo
    print("\n📰 Testing Benzinga API...")
    benzinga_result = dispatch_api_task("benzinga", "test/test_benzinga.py")
    
    if benzinga_result["success"]:
        print("  ✅ Benzinga API call successful")
        if benzinga_result.get("stdout"):
            print(f"  📝 Output preview: {benzinga_result['stdout'][:200]}...")
    else:
        print(f"  ❌ Benzinga API call failed: {benzinga_result.get('error', 'Unknown error')}")
    
    # Polygon demo
    print("\n📊 Testing Polygon API...")
    polygon_result = dispatch_api_task("polygon", "test/test_polygon.py --symbol AAPL --type news")
    
    if polygon_result["success"]:
        print("  ✅ Polygon API call successful")
        if polygon_result.get("stdout"):
            print(f"  📝 Output preview: {polygon_result['stdout'][:200]}...")
    else:
        print(f"  ❌ Polygon API call failed: {polygon_result.get('error', 'Unknown error')}")
    
    # Demo 2: Show execution details
    print("\n🔍 Demo 2: Execution Details")
    print("-" * 30)
    
    print("\n📋 Benzinga Execution Details:")
    print(f"  Return Code: {benzinga_result.get('return_code', 'N/A')}")
    print(f"  Timestamp: {benzinga_result.get('timestamp', 'N/A')}")
    print(f"  Script: {benzinga_result.get('script', 'N/A')}")
    
    print("\n📋 Polygon Execution Details:")
    print(f"  Return Code: {polygon_result.get('return_code', 'N/A')}")
    print(f"  Timestamp: {polygon_result.get('timestamp', 'N/A')}")
    print(f"  Script: {polygon_result.get('script', 'N/A')}")
    
    # Demo 3: Error handling
    print("\n🔍 Demo 3: Error Handling")
    print("-" * 30)
    
    # Test with non-existent script
    print("\n🧪 Testing with non-existent script...")
    error_result = dispatch_api_task("benzinga", "non_existent_script.py")
    
    if not error_result["success"]:
        print(f"  ✅ Error properly caught: {error_result.get('error', 'Unknown error')}")
    else:
        print("  ❌ Expected error was not caught")
    
    # Summary
    print("\n📋 Demo Summary:")
    print("=" * 40)
    
    total_tests = 3
    passed_tests = 0
    
    if benzinga_result["success"]:
        passed_tests += 1
        print("  ✅ Benzinga API: PASS")
    else:
        print("  ❌ Benzinga API: FAIL")
    
    if polygon_result["success"]:
        passed_tests += 1
        print("  ✅ Polygon API: PASS")
    else:
        print("  ❌ Polygon API: FAIL")
    
    if not error_result["success"]:
        passed_tests += 1
        print("  ✅ Error Handling: PASS")
    else:
        print("  ❌ Error Handling: FAIL")
    
    print(f"\n🎯 Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! API dispatcher is working correctly.")
        print("\n💡 Key Benefits Demonstrated:")
        print("  • ✅ Isolated virtual environments prevent urllib3 conflicts")
        print("  • ✅ Benzinga (urllib3==1.25.10) runs in separate process")
        print("  • ✅ Polygon (urllib3==2.5.0) runs in separate process")
        print("  • ✅ Robust error handling and logging")
        print("  • ✅ Automatic cleanup of temporary files")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1) 