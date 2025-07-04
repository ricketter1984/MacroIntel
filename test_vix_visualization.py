#!/usr/bin/env python3
"""
Test script for the new VIX Strategic Chart visualization.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv(dotenv_path="config/.env")

from core.enhanced_visualizations import EnhancedVisualizations

def test_vix_strategic_chart():
    """Test the new VIX strategic chart functionality."""
    print("🚀 Testing VIX Strategic Chart...")
    
    # Initialize the visualization engine
    viz_engine = EnhancedVisualizations()
    
    # Test the new VIX strategic chart
    try:
        print("📊 Creating VIX Strategic Chart...")
        chart_path = viz_engine.create_vix_strategic_chart()
        
        if chart_path:
            print(f"✅ VIX Strategic Chart created successfully!")
            print(f"📁 Chart saved to: {chart_path}")
            
            # Check if file exists
            if os.path.exists(chart_path):
                file_size = os.path.getsize(chart_path)
                print(f"📏 File size: {file_size:,} bytes")
            else:
                print("⚠️ Chart file not found on disk")
        else:
            print("❌ Failed to create VIX Strategic Chart")
            
    except Exception as e:
        print(f"❌ Error testing VIX Strategic Chart: {str(e)}")
        import traceback
        traceback.print_exc()

def test_with_simulated_data():
    """Test with simulated data to ensure functionality works."""
    print("\n🧪 Testing with simulated data...")
    
    # Initialize the visualization engine
    viz_engine = EnhancedVisualizations()
    
    # Create simulated VIX data
    dates = pd.date_range(start=datetime.now() - timedelta(days=365), end=datetime.now(), freq='D')
    vix_values = np.random.normal(20, 8, len(dates))
    vix_values = np.clip(vix_values, 10, 50)  # Keep VIX in reasonable range
    
    vix_data = pd.DataFrame({
        'VIX': vix_values
    }, index=pd.DatetimeIndex(dates))
    
    # Create simulated Fear & Greed data
    fg_values = np.random.normal(50, 15, len(dates))
    fg_values = np.clip(fg_values, 0, 100)
    
    fear_greed_data = pd.DataFrame({
        'Fear_Greed': fg_values
    }, index=pd.DatetimeIndex(dates))
    
    # Create simulated Regime Score data
    regime_values = np.random.normal(50, 20, len(dates))
    regime_values = np.clip(regime_values, 0, 100)
    
    regime_data = pd.DataFrame({
        'Regime_Score': regime_values
    }, index=pd.DatetimeIndex(dates))
    
    try:
        print("📊 Creating VIX Strategic Chart with simulated data...")
        chart_path = viz_engine.create_vix_strategic_chart(
            vix_data=vix_data,
            fear_greed_data=fear_greed_data,
            regime_data=regime_data,
            output_filename="vix_strategic_test.png"
        )
        
        if chart_path:
            print(f"✅ VIX Strategic Chart with simulated data created successfully!")
            print(f"📁 Chart saved to: {chart_path}")
        else:
            print("❌ Failed to create VIX Strategic Chart with simulated data")
            
    except Exception as e:
        print(f"❌ Error testing with simulated data: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function."""
    print("🎨 VIX Strategic Chart Test Suite")
    print("=" * 50)
    
    # Test 1: Using real data (if available)
    test_vix_strategic_chart()
    
    # Test 2: Using simulated data
    test_with_simulated_data()
    
    print("\n✅ Test suite completed!")

if __name__ == "__main__":
    main() 