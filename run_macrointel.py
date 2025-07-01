#!/usr/bin/env python3
"""
MacroIntel Startup Script
Easy entry point for the MacroIntel agent swarm system.
"""

import sys
import os
import argparse

def main():
    """Main entry point for MacroIntel."""
    parser = argparse.ArgumentParser(
        description='MacroIntel - Advanced Market Intelligence System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_macrointel.py                    # Run agent swarm immediately
  python run_macrointel.py --schedule         # Run in scheduled mode (7:15 AM daily)
  python run_macrointel.py --test             # Test individual agents
  python run_macrointel.py --legacy           # Use legacy system
  python run_macrointel.py --fear-greed       # Run Fear & Greed dashboard
        """
    )
    
    parser.add_argument('--schedule', action='store_true',
                       help='Run agent swarm in scheduled mode (daily at 7:15 AM)')
    parser.add_argument('--test', action='store_true',
                       help='Test individual agents')
    parser.add_argument('--legacy', action='store_true',
                       help='Use legacy system (main.py)')
    parser.add_argument('--fear-greed', action='store_true',
                       help='Run Fear & Greed dashboard')
    parser.add_argument('--chart', action='store_true',
                       help='Generate Fear & Greed chart')
    parser.add_argument('--report', action='store_true',
                       help='Generate Fear & Greed report')
    
    args = parser.parse_args()
    
    # Add agents directory to path
    sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))
    
    if args.fear_greed:
        print("📊 Running Fear & Greed Dashboard...")
        try:
            import fear_greed_dashboard
            if args.chart:
                os.system("python fear_greed_dashboard.py --chart")
            elif args.report:
                os.system("python fear_greed_dashboard.py --report")
            else:
                os.system("python fear_greed_dashboard.py --chart --report")
        except ImportError:
            print("❌ Fear & Greed dashboard not available")
        return
    
    if args.test:
        print("🧪 Testing MacroIntel Agent Swarm...")
        try:
            os.system("python agents/test_swarm.py")
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
        return
    
    if args.legacy:
        print("🔄 Running Legacy MacroIntel System...")
        try:
            os.system("python main.py --swarm")
        except Exception as e:
            print(f"❌ Legacy system failed: {str(e)}")
        return
    
    # Default: Run agent swarm
    print("🤖 Starting MacroIntel Agent Swarm...")
    try:
        if args.schedule:
            print("📅 Running in scheduled mode (daily at 7:15 AM)")
            os.system("python agents/swarm_orchestrator.py --schedule")
        else:
            print("⚡ Executing immediately...")
            os.system("python agents/swarm_orchestrator.py --now")
    except Exception as e:
        print(f"❌ Agent swarm failed: {str(e)}")
        print("💡 Try running: python agents/test_swarm.py")

if __name__ == "__main__":
    main() 