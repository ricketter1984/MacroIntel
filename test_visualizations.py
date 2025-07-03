#!/usr/bin/env python3
"""
Test script for debugging the enhanced visualization engine.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the visualization engine
from core.enhanced_visualizations import EnhancedVisualizations

def create_test_data():
    """Create test data to verify visualization engine functionality."""
    print("🔧 Creating test data...")
    
    # Create date range
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    
    # Create VIX data
    vix_data = pd.DataFrame({
        'close': np.random.normal(20, 5, len(dates)) + 15
    }, index=dates)
    print(f"✅ VIX data created: {len(vix_data)} rows")
    
    # Create asset data
    asset_data = {
        'SPY': pd.DataFrame({'close': np.random.normal(400, 10, len(dates)) + 380}, index=dates),
        'QQQ': pd.DataFrame({'close': np.random.normal(350, 15, len(dates)) + 330}, index=dates),
        'GLD': pd.DataFrame({'close': np.random.normal(180, 5, len(dates)) + 175}, index=dates),
        'TLT': pd.DataFrame({'close': np.random.normal(90, 3, len(dates)) + 87}, index=dates)
    }
    print(f"✅ Asset data created: {len(asset_data)} assets")
    
    # Create Fear & Greed data
    fear_greed_data = pd.Series(np.random.normal(50, 15, len(dates)), index=dates)
    print(f"✅ Fear & Greed data created: {len(fear_greed_data)} points")
    
    # Create calendar data
    calendar_data = {
        'success': True,
        'high_impact_events': [
            {'event': 'FOMC Meeting', 'date': '2024-01-15', 'impact': 'High'},
            {'event': 'Non-Farm Payrolls', 'date': '2024-01-05', 'impact': 'High'},
            {'event': 'CPI Release', 'date': '2024-01-10', 'impact': 'High'}
        ],
        'medium_impact_events': [
            {'event': 'Retail Sales', 'date': '2024-01-12', 'impact': 'Medium'},
            {'event': 'Housing Starts', 'date': '2024-01-18', 'impact': 'Medium'}
        ],
        'total_events': 5
    }
    print(f"✅ Calendar data created: {calendar_data['total_events']} events")
    
    return {
        'vix_data': vix_data,
        'asset_data': asset_data,
        'fear_greed_data': fear_greed_data,
        'market_data': asset_data,  # Use asset data as market data
        'calendar_data': calendar_data
    }

def test_visualization_engine():
    """Test the visualization engine with sample data."""
    print("🧪 Testing Enhanced Visualization Engine")
    print("=" * 50)
    
    # Create test data
    data_sources = create_test_data()
    
    # Initialize visualization engine
    viz_engine = EnhancedVisualizations()
    
    # Test individual chart generation
    print("\n📊 Testing individual chart generation...")
    
    # Test VIX chart
    print("\n1. Testing VIX chart...")
    vix_chart = viz_engine.create_vix_analysis_chart(data_sources['vix_data'])
    if vix_chart:
        print(f"✅ VIX chart created: {vix_chart}")
    else:
        print("❌ VIX chart failed")
    
    # Test multi-asset chart
    print("\n2. Testing multi-asset chart...")
    asset_chart = viz_engine.create_multi_asset_comparison(data_sources['asset_data'])
    if asset_chart:
        print(f"✅ Multi-asset chart created: {asset_chart}")
    else:
        print("❌ Multi-asset chart failed")
    
    # Test Fear & Greed chart
    print("\n3. Testing Fear & Greed chart...")
    fear_greed_chart = viz_engine.create_fear_greed_analysis(
        data_sources['fear_greed_data'], 
        data_sources['market_data']
    )
    if fear_greed_chart:
        print(f"✅ Fear & Greed chart created: {fear_greed_chart}")
    else:
        print("❌ Fear & Greed chart failed")
    
    # Test economic calendar chart
    print("\n4. Testing economic calendar chart...")
    calendar_chart = viz_engine.create_economic_calendar_impact(
        data_sources['calendar_data'], 
        data_sources['market_data']
    )
    if calendar_chart:
        print(f"✅ Economic calendar chart created: {calendar_chart}")
    else:
        print("❌ Economic calendar chart failed")
    
    # Test comprehensive generation
    print("\n🎨 Testing comprehensive visualization generation...")
    results = viz_engine.generate_all_visualizations(data_sources)
    
    print(f"\n📊 Results Summary:")
    print(f"   Charts generated: {len(results['charts_generated'])}")
    print(f"   Charts skipped: {len(results['charts_skipped'])}")
    print(f"   Errors: {len(results['errors'])}")
    
    if results['charts_generated']:
        print(f"\n✅ Generated charts:")
        for chart in results['charts_generated']:
            print(f"   - {chart['type']}: {chart['path']}")
    
    if results['charts_skipped']:
        print(f"\n⚠️ Skipped charts:")
        for chart in results['charts_skipped']:
            print(f"   - {chart}")
    
    if results['errors']:
        print(f"\n❌ Errors:")
        for error in results['errors']:
            print(f"   - {error}")
    
    return results

def test_with_empty_data():
    """Test visualization engine with empty/incomplete data."""
    print("\n🧪 Testing with empty/incomplete data...")
    print("=" * 50)
    
    viz_engine = EnhancedVisualizations()
    
    # Test with empty data
    empty_data = {}
    results = viz_engine.generate_all_visualizations(empty_data)
    
    print(f"📊 Empty data results:")
    print(f"   Charts generated: {len(results['charts_generated'])}")
    print(f"   Charts skipped: {len(results['charts_skipped'])}")
    print(f"   Errors: {len(results['errors'])}")
    
    # Test with partial data
    partial_data = {
        'vix_data': pd.DataFrame({'close': [20, 21, 22]}, index=pd.date_range('2024-01-01', periods=3)),
        'asset_data': {}  # Empty asset data
    }
    
    results = viz_engine.generate_all_visualizations(partial_data)
    
    print(f"\n📊 Partial data results:")
    print(f"   Charts generated: {len(results['charts_generated'])}")
    print(f"   Charts skipped: {len(results['charts_skipped'])}")
    print(f"   Errors: {len(results['errors'])}")

if __name__ == "__main__":
    # Test with good data
    test_visualization_engine()
    
    # Test with empty/incomplete data
    test_with_empty_data()
    
    print("\n✅ Visualization engine testing completed!") 