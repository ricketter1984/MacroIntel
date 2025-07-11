#!/usr/bin/env python3
"""
MacroIntel Dashboard Launcher
Starts the Streamlit dashboard with proper configuration and checks
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed."""
    
    required_modules = [
        'streamlit',
        'plotly', 
        'pandas',
        'yfinance',
        'requests'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ Missing required modules: {', '.join(missing_modules)}")
        print("📦 Install with: python -m pip install streamlit plotly pandas yfinance requests plyer python-dotenv")
        return False
    
    print("✅ All required dependencies found")
    return True

def check_environment():
    """Check environment configuration."""
    
    print("🔧 Checking environment configuration...")
    
    # Check for .env file
    env_file = Path("config/.env")
    if env_file.exists():
        print("✅ Found config/.env file")
        
        # Check for API keys
        with open(env_file, 'r') as f:
            env_content = f.read()
            
        if "FMP_API_KEY" in env_content:
            print("✅ FMP API key configured")
        else:
            print("⚠️ FMP_API_KEY not found in .env - economic calendar may not work")
            
    else:
        print("⚠️ No config/.env file found - some features may not work")
    
    # Check for data files
    output_dir = Path("output")
    if output_dir.exists():
        print(f"✅ Output directory exists ({len(list(output_dir.glob('*')))} files)")
    else:
        print("⚠️ Output directory not found - creating...")
        output_dir.mkdir(exist_ok=True)
    
    logs_dir = Path("logs")
    if logs_dir.exists():
        print(f"✅ Logs directory exists ({len(list(logs_dir.glob('*')))} files)")
    else:
        print("⚠️ Logs directory not found - creating...")
        logs_dir.mkdir(exist_ok=True)

def launch_dashboard(port=8501, open_browser=True):
    """Launch the Streamlit dashboard."""
    
    print(f"🚀 Starting MacroIntel Dashboard on port {port}...")
    
    # Check if dashboard_app.py exists
    dashboard_file = Path("dashboard_app.py")
    if not dashboard_file.exists():
        print("❌ dashboard_app.py not found!")
        return False
    
    try:
        # Start Streamlit
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            str(dashboard_file),
            "--server.port", str(port),
            "--server.headless", "false"
        ]
        
        print(f"📡 Command: {' '.join(cmd)}")
        print(f"🌐 Dashboard will be available at: http://localhost:{port}")
        
        if open_browser:
            # Wait a moment then open browser
            def open_browser_delayed():
                time.sleep(3)
                try:
                    webbrowser.open(f"http://localhost:{port}")
                    print("🌐 Opened dashboard in browser")
                except Exception as e:
                    print(f"⚠️ Could not open browser: {e}")
            
            import threading
            browser_thread = threading.Thread(target=open_browser_delayed)
            browser_thread.daemon = True
            browser_thread.start()
        
        # Run Streamlit
        process = subprocess.run(cmd)
        return process.returncode == 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Dashboard stopped by user")
        return True
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        return False

def show_help():
    """Show help information."""
    
    print("""
🎛️ MacroIntel Dashboard Launcher

Usage:
  python launch_dashboard.py [options]

Options:
  --port PORT       Set dashboard port (default: 8501)
  --no-browser      Don't open browser automatically
  --help            Show this help message

Features:
  📊 Live watchlist tracking with performance metrics
  📅 Economic calendar from FMP API
  📈 Interactive charts (performance, volatility, correlation, volume)
  🎯 Regime analysis and strategy recommendations  
  📰 Recent news with sentiment analysis
  🔄 Auto-refresh every 10 minutes
  🔔 Desktop notifications (optional)

Configuration:
  • Add FMP_API_KEY to config/.env for economic calendar
  • Customize watchlist in dashboard sidebar
  • Enable notifications in dashboard settings

Troubleshooting:
  • Ensure all dependencies installed: pip install -r requirements_dashboard.txt
  • Check that config/.env exists with API keys
  • Verify MacroIntel modules are available
  • Try different port if 8501 is in use
""")

def main():
    """Main launcher function."""
    
    print("🎛️ MacroIntel Dashboard Launcher")
    print("=" * 50)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Launch MacroIntel Dashboard")
    parser.add_argument("--port", type=int, default=8501, help="Dashboard port")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser")
    parser.add_argument("--help-full", action="store_true", help="Show detailed help")
    
    try:
        args = parser.parse_args()
    except:
        # Fallback for simple usage
        args = type('Args', (), {
            'port': 8501,
            'no_browser': False,
            'help_full': '--help' in sys.argv or '-h' in sys.argv
        })()
    
    if args.help_full or '--help' in sys.argv:
        show_help()
        return
    
    # Check dependencies
    if not check_dependencies():
        print("\n💡 Tip: Install missing dependencies and try again")
        return
    
    # Check environment
    check_environment()
    
    print("\n" + "=" * 50)
    
    # Launch dashboard
    success = launch_dashboard(
        port=args.port,
        open_browser=not args.no_browser
    )
    
    if success:
        print("\n✅ Dashboard session completed")
    else:
        print("\n❌ Dashboard failed to start")

if __name__ == "__main__":
    main() 