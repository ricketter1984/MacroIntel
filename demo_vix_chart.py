#!/usr/bin/env python3
"""
Demonstration script for the VIX Strategic Chart functionality.

This script shows how to use the new create_vix_strategic_chart() method
to generate high-quality two-panel VIX analysis charts.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv(dotenv_path="config/.env")

from core.enhanced_visualizations import EnhancedVisualizations

def demo_vix_strategic_chart():
    """Demonstrate the VIX Strategic Chart functionality."""
    print("🎨 VIX Strategic Chart Demonstration")
    print("=" * 50)
    
    # Initialize the visualization engine
    viz_engine = EnhancedVisualizations()
    
    print("📊 Creating VIX Strategic Chart with live data...")
    print("   - Panel 1: VIX Over Time with volatility zones")
    print("   - Panel 2: VIX vs Fear & Greed vs Regime Score")
    print("   - Strategy markers for Tier 1 setups")
    print()
    
    # Method 1: Let the function fetch all data automatically
    print("🔧 Method 1: Automatic data fetching")
    chart_path = viz_engine.create_vix_strategic_chart()
    
    if chart_path:
        print(f"✅ Chart created: {chart_path}")
        
        # Check file details
        if os.path.exists(chart_path):
            file_size = os.path.getsize(chart_path)
            print(f"📏 File size: {file_size:,} bytes")
            print(f"📅 Created: {datetime.fromtimestamp(os.path.getctime(chart_path))}")
        print()
    else:
        print("❌ Failed to create chart")
        print()
    
    # Method 2: Custom filename
    print("🔧 Method 2: Custom filename")
    custom_filename = f"vix_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    chart_path2 = viz_engine.create_vix_strategic_chart(output_filename=custom_filename)
    
    if chart_path2:
        print(f"✅ Chart created: {chart_path2}")
        print()
    else:
        print("❌ Failed to create chart")
        print()
    
    print("🎯 Chart Features:")
    print("   • Panel 1: VIX Over Time")
    print("     - Blue VIX line with 1 year of data")
    print("     - Shaded volatility zones:")
    print("       * < 15: Light gray (Low Vol)")
    print("       * 15-20: Light green (Watch Zone)")
    print("       * 20-30: Orange (Reversal-Friendly)")
    print("       * > 30: Red (Chaos)")
    print()
    print("   • Panel 2: Multi-Indicator Comparison")
    print("     - VIX (blue line)")
    print("     - Fear & Greed Index (green line, scaled)")
    print("     - Regime Score (red dashed line, scaled)")
    print("     - Strategy markers for Tier 1 setups")
    print()
    print("   • Data Sources:")
    print("     - VIX: FMP API (^VIX symbol)")
    print("     - Fear & Greed: CNN API")
    print("     - Regime Score: Local JSON files")
    print("     - Fallback: Simulated data if APIs fail")
    print()
    print("✅ Demonstration completed!")

if __name__ == "__main__":
    demo_vix_strategic_chart() 