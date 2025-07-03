#!/usr/bin/env python3
"""
MacroIntel Startup Health Checker
Verifies all critical components are ready before running the system.
"""

import os
import sys
import importlib
from dotenv import load_dotenv
from termcolor import colored

# Load environment variables from config/.env
load_dotenv(dotenv_path="config/.env")

def check_environment_variables():
    """Check all critical environment variables."""
    print("🔑 Checking environment variables...")
    
    critical_vars = [
        "FMP_API_KEY",
        "POLYGON_API_KEY", 
        "MESSARI_API_KEY",
        "BENZINGA_API_KEY",
        "FEAR_GREED_API_KEY",
        "OPENAI_API_KEY",
        "SMTP_USER",
        "SMTP_PASSWORD"
    ]
    
    missing_vars = []
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {'*' * min(len(value), 8)}...")
        else:
            print(colored(f"  ❌ {var}: MISSING!", "red"))
            missing_vars.append(var)
    
    if missing_vars:
        print(colored(f"\n⚠️  Missing {len(missing_vars)} critical environment variables!", "yellow"))
        return False
    else:
        print(colored("✅ All environment variables are set!", "green"))
        return True

def check_directories():
    """Check and create required directories."""
    print("\n📁 Checking required directories...")
    
    required_dirs = ["output", "logs", "config"]
    missing_dirs = []
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"  ✅ {directory}/: exists")
        else:
            print(colored(f"  ❌ {directory}/: missing", "red"))
            missing_dirs.append(directory)
    
    # Create missing directories
    for directory in missing_dirs:
        try:
            os.makedirs(directory, exist_ok=True)
            print(colored(f"  ✅ {directory}/: created", "green"))
        except Exception as e:
            print(colored(f"  ❌ Failed to create {directory}/: {e}", "red"))
            return False
    
    print(colored("✅ All required directories are ready!", "green"))
    return True

def check_python_packages():
    """Check if required Python packages are installed."""
    print("\n📦 Checking Python packages...")
    
    required_packages = [
        "requests",
        "pandas", 
        "numpy",
        "matplotlib",
        "plotly",
        "openai",
        "anthropic",
        "schedule",
        "dotenv",
        "termcolor",
        "yfinance",
        "scipy",
        "sklearn"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"  ✅ {package}: installed")
        except ImportError:
            print(colored(f"  ❌ {package}: missing", "red"))
            missing_packages.append(package)
    
    if missing_packages:
        print(colored(f"\n⚠️  Missing {len(missing_packages)} packages!", "yellow"))
        print("Install missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    else:
        print(colored("✅ All required packages are installed!", "green"))
        return True

def check_api_connectivity():
    """Test basic API connectivity."""
    print("\n🌐 Testing API connectivity...")
    
    try:
        import requests
        
        # Test FMP API
        fmp_key = os.getenv("FMP_API_KEY")
        if fmp_key:
            try:
                response = requests.get(
                    "https://financialmodelingprep.com/api/v3/quote/SPY",
                    params={"apikey": fmp_key},
                    timeout=10
                )
                if response.status_code == 200:
                    print("  ✅ FMP API: connected")
                else:
                    print(colored(f"  ⚠️  FMP API: status {response.status_code}", "yellow"))
            except Exception as e:
                print(colored(f"  ❌ FMP API: connection failed - {e}", "red"))
        
        # Test Fear & Greed API
        fear_greed_key = os.getenv("FEAR_GREED_API_KEY")
        if fear_greed_key:
            try:
                response = requests.get(
                    "https://cnn-fear-and-greed-index.p.rapidapi.com/cnn/v1/fear_and_greed/index",
                    headers={
                        "x-rapidapi-key": fear_greed_key,
                        "x-rapidapi-host": "cnn-fear-and-greed-index.p.rapidapi.com"
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    print("  ✅ Fear & Greed API: connected")
                else:
                    print(colored(f"  ⚠️  Fear & Greed API: status {response.status_code}", "yellow"))
            except Exception as e:
                print(colored(f"  ❌ Fear & Greed API: connection failed - {e}", "red"))
        
        print(colored("✅ API connectivity tests completed!", "green"))
        return True
        
    except ImportError:
        print(colored("  ❌ requests package not available for API testing", "red"))
        return False

def main():
    """Run all health checks."""
    print("🏥 MacroIntel Startup Health Check")
    print("=" * 50)
    
    checks = [
        ("Environment Variables", check_environment_variables),
        ("Directories", check_directories),
        ("Python Packages", check_python_packages),
        ("API Connectivity", check_api_connectivity)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print(colored(f"❌ {check_name} check failed with error: {e}", "red"))
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print(colored("🎉 All systems ready! MacroIntel is ready to run.", "green"))
        print(colored("💡 Run with: python run_macrointel.py", "cyan"))
        return True
    else:
        print(colored("❌ Some checks failed. Please fix the issues above before running MacroIntel.", "red"))
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 