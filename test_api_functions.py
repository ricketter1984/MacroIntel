#!/usr/bin/env python3
"""
Test script to verify all API functions work correctly.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(dotenv_path=project_root / "config" / ".env")

# Import the API functions
from utils.api_clients import (
    fetch_polygon_indices,
    fetch_fmp_calendar,
    fetch_messari_metrics,
    fetch_twelve_data_chart
)

def test_polygon_indices():
    """Test Polygon indices function."""
    print("Testing fetch_polygon_indices()...")
    try:
        result = fetch_polygon_indices("SPY")
        if result:
            print(f"✅ Polygon indices: {result}")
            return True
        else:
            print("❌ Polygon indices: No data returned")
            return False
    except Exception as e:
        print(f"❌ Polygon indices error: {e}")
        return False

def test_fmp_calendar():
    """Test FMP calendar function."""
    print("Testing fetch_fmp_calendar()...")
    try:
        result = fetch_fmp_calendar()
        if result:
            print(f"✅ FMP calendar: {len(result)} events")
            return True
        else:
            print("❌ FMP calendar: No data returned")
            return False
    except Exception as e:
        print(f"❌ FMP calendar error: {e}")
        return False

def test_messari_metrics():
    """Test Messari metrics function."""
    print("Testing fetch_messari_metrics()...")
    try:
        result = fetch_messari_metrics("bitcoin")
        if result:
            print(f"✅ Messari metrics: {result}")
            return True
        else:
            print("❌ Messari metrics: No data returned")
            return False
    except Exception as e:
        print(f"❌ Messari metrics error: {e}")
        return False

def test_twelve_data_chart():
    """Test Twelve Data chart function."""
    print("Testing fetch_twelve_data_chart()...")
    try:
        result = fetch_twelve_data_chart("BTC/USD", interval="1day", outputsize=5)
        if result is not None:
            print(f"✅ Twelve Data chart: {len(result)} data points")
            print(f"   Columns: {list(result.columns)}")
            return True
        else:
            print("❌ Twelve Data chart: No data returned")
            return False
    except Exception as e:
        print(f"❌ Twelve Data chart error: {e}")
        return False

def main():
    """Test all API functions."""
    print("🧪 Testing API Functions")
    print("=" * 50)
    
    # Check API keys
    api_keys = {
        "POLYGON_API_KEY": os.getenv("POLYGON_API_KEY"),
        "FMP_API_KEY": os.getenv("FMP_API_KEY"),
        "MESSARI_API_KEY": os.getenv("MESSARI_API_KEY"),
        "TWELVE_DATA_API_KEY": os.getenv("TWELVE_DATA_API_KEY")
    }
    
    print("🔑 API Keys Status:")
    for key_name, key_value in api_keys.items():
        status = "✅ Present" if key_value else "❌ Missing"
        print(f"   {key_name}: {status}")
    
    print("\n📊 Testing Functions:")
    
    # Test each function
    results = {
        "polygon_indices": test_polygon_indices(),
        "fmp_calendar": test_fmp_calendar(),
        "messari_metrics": test_messari_metrics(),
        "twelve_data_chart": test_twelve_data_chart()
    }
    
    print("\n📋 Test Results Summary:")
    for function_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {function_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("✅ All API functions are working correctly!")
    else:
        print("⚠️ Some API functions need attention (missing API keys or API issues)")

if __name__ == "__main__":
    main() 