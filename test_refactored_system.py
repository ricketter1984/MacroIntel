#!/usr/bin/env python3
"""
Test script for the refactored MacroIntel system using API dispatcher.
"""

import sys
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_api_dispatcher_import():
    """Test that the API dispatcher can be imported."""
    try:
        from api_dispatcher import dispatch_api_task, get_api_status
        print("✅ API dispatcher imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import API dispatcher: {e}")
        return False

def test_scripts_exist():
    """Test that the required scripts exist."""
    scripts = [
        "scripts/fetch_benzinga_news.py",
        "scripts/fetch_polygon_data.py"
    ]
    
    all_exist = True
    for script in scripts:
        if Path(script).exists():
            print(f"✅ {script} exists")
        else:
            print(f"❌ {script} missing")
            all_exist = False
    
    return all_exist

def test_run_macrointel_import():
    """Test that the refactored run_macrointel.py functions can be imported."""
    try:
        # Import the functions from run_macrointel
        import run_macrointel
        
        # Test that the functions exist
        if hasattr(run_macrointel, 'fetch_benzinga_news'):
            print("✅ fetch_benzinga_news function exists")
        else:
            print("❌ fetch_benzinga_news function missing")
            return False
            
        if hasattr(run_macrointel, 'fetch_polygon_indices'):
            print("✅ fetch_polygon_indices function exists")
        else:
            print("❌ fetch_polygon_indices function missing")
            return False
            
        if hasattr(run_macrointel, 'run_scheduled_tasks'):
            print("✅ run_scheduled_tasks function exists")
        else:
            print("❌ run_scheduled_tasks function missing")
            return False
            
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import run_macrointel: {e}")
        return False

def test_api_status():
    """Test the API status functionality."""
    try:
        from api_dispatcher import get_api_status
        
        status = get_api_status()
        print("✅ API status retrieved successfully")
        print("📊 API Status:")
        for source, info in status.items():
            status_icon = "✅" if info["ready"] else "❌"
            print(f"  {status_icon} {source}: {'Ready' if info['ready'] else 'Not Ready'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to get API status: {e}")
        return False

def test_scheduler_import():
    """Test that the schedule library can be imported."""
    try:
        import schedule
        print("✅ Schedule library imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import schedule library: {e}")
        return False

def test_logging_setup():
    """Test that logging can be set up."""
    try:
        import logging
        from pathlib import Path
        
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "test.log"),
                logging.StreamHandler()
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info("Test log message")
        
        print("✅ Logging setup successful")
        return True
        
    except Exception as e:
        print(f"❌ Failed to setup logging: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Refactored MacroIntel System")
    print("=" * 50)
    
    tests = [
        ("API Dispatcher Import", test_api_dispatcher_import),
        ("Scripts Exist", test_scripts_exist),
        ("Run MacroIntel Import", test_run_macrointel_import),
        ("API Status", test_api_status),
        ("Scheduler Import", test_scheduler_import),
        ("Logging Setup", test_logging_setup),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASS")
            else:
                print(f"❌ {test_name}: FAIL")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
    
    print(f"\n📋 Test Summary:")
    print("=" * 30)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Refactored system is ready.")
        print("\n💡 Next steps:")
        print("  1. Run: python run_macrointel.py --test")
        print("  2. Run: python run_macrointel.py --benzinga")
        print("  3. Run: python run_macrointel.py --polygon")
        print("  4. Run: python run_macrointel.py --schedule")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 