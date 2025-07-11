#!/usr/bin/env python3
"""
Test script to verify the updated Fear & Greed 14-day trend chart functionality.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add project directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.enhanced_visualizations import EnhancedVisualizations
from core.email_report import generate_fear_greed_trend_chart, generate_email_content

def test_enhanced_visualizations_fear_greed():
    """Test the new Fear & Greed chart generation in enhanced_visualizations.py"""
    print("🧪 Testing Enhanced Visualizations Fear & Greed Chart")
    print("=" * 60)
    
    try:
        # Initialize the enhanced visualizations engine
        viz_engine = EnhancedVisualizations()
        print("✅ Enhanced Visualizations engine initialized")
        
        # Generate the Fear & Greed trend chart
        print("📊 Generating 14-day Fear & Greed trend chart...")
        chart_path = viz_engine.generate_fear_greed_trend_chart()
        
        if chart_path:
            print(f"✅ Chart generated successfully: {chart_path}")
            
            # Check if file exists and get stats
            if os.path.exists(chart_path):
                file_size = os.path.getsize(chart_path)
                print(f"   📁 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                
                # Check filename
                expected_filename = "fear_greed_trend.png"
                actual_filename = os.path.basename(chart_path)
                if actual_filename == expected_filename:
                    print(f"✅ Correct filename: {actual_filename}")
                else:
                    print(f"❌ Unexpected filename: {actual_filename} (expected: {expected_filename})")
                
                # Check if it's in output directory
                if "output" in chart_path:
                    print("✅ Chart saved in output directory")
                else:
                    print(f"⚠️ Chart not in output directory: {chart_path}")
                
                return True
            else:
                print(f"❌ Chart file not found: {chart_path}")
                return False
        else:
            print("❌ Chart generation returned None")
            return False
            
    except Exception as e:
        print(f"❌ Error testing enhanced visualizations: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_email_report_integration():
    """Test the Fear & Greed chart integration in email reports"""
    print("\n🧪 Testing Email Report Integration")
    print("=" * 40)
    
    try:
        # Test the email report function
        print("📧 Testing email report Fear & Greed chart generation...")
        chart_path = generate_fear_greed_trend_chart()
        
        if chart_path:
            print(f"✅ Email report chart generated: {chart_path}")
            
            # Check if file exists
            if os.path.exists(chart_path):
                file_size = os.path.getsize(chart_path)
                print(f"   📁 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                return True
            else:
                print(f"❌ Chart file not found: {chart_path}")
                return False
        else:
            print("❌ Email report chart generation returned None")
            return False
            
    except Exception as e:
        print(f"❌ Error testing email report integration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_full_email_generation():
    """Test full email generation with Fear & Greed chart inclusion"""
    print("\n🧪 Testing Full Email Generation")
    print("=" * 40)
    
    try:
        # Sample articles for email generation
        sample_articles = [
            {
                "title": "Market Shows Mixed Signals as Fed Decision Looms",
                "summary": "Investors await Federal Reserve decision amid mixed economic indicators",
                "url": "https://example.com/fed-decision",
                "source": "fmp",
                "tone": "Neutral",
                "affected_tickers": "SPY, QQQ",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        print(f"📧 Generating email content with {len(sample_articles)} articles...")
        
        # Generate email content
        html_content, chart_attachments = generate_email_content(sample_articles, limit=5)
        
        if html_content:
            print(f"✅ Email content generated: {len(html_content):,} characters")
            print(f"📎 Chart attachments: {len(chart_attachments)}")
            
            # Check for Fear & Greed chart in attachments
            fear_greed_chart_found = False
            for attachment in chart_attachments:
                chart_path = attachment.get('path', '')
                chart_cid = attachment.get('cid', '')
                print(f"   📈 Chart: {os.path.basename(chart_path)} (CID: {chart_cid})")
                
                if 'fear_greed_trend' in chart_path or chart_cid == 'fear_greed_trend_chart':
                    fear_greed_chart_found = True
                    if os.path.exists(chart_path):
                        file_size = os.path.getsize(chart_path)
                        print(f"      ✅ Fear & Greed chart found and verified ({file_size:,} bytes)")
                    else:
                        print(f"      ❌ Fear & Greed chart file not found: {chart_path}")
                        return False
            
            if fear_greed_chart_found:
                print("✅ Fear & Greed chart successfully included in email attachments")
            else:
                print("❌ Fear & Greed chart NOT found in email attachments")
                return False
            
            # Check HTML content for Fear & Greed references
            fear_greed_html_count = html_content.count("Fear & Greed")
            if fear_greed_html_count > 0:
                print(f"✅ Fear & Greed mentioned {fear_greed_html_count} times in HTML content")
            else:
                print("⚠️ Fear & Greed not mentioned in HTML content")
            
            # Check for chart image references
            fear_greed_img_count = html_content.count("fear_greed_trend_chart")
            if fear_greed_img_count > 0:
                print(f"✅ Fear & Greed chart image referenced {fear_greed_img_count} times in HTML")
            else:
                print("❌ Fear & Greed chart image NOT referenced in HTML")
                return False
            
            return True
            
        else:
            print("❌ Failed to generate email content")
            return False
            
    except Exception as e:
        print(f"❌ Error testing full email generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_configuration():
    """Test if Fear & Greed API is configured"""
    print("\n🧪 Testing API Configuration")
    print("=" * 30)
    
    api_key = os.getenv("FEAR_GREED_API_KEY")
    if api_key:
        print("✅ FEAR_GREED_API_KEY found in environment")
        print(f"   Key length: {len(api_key)} characters")
        print(f"   Key preview: {api_key[:8]}...{api_key[-4:]}")
        return True
    else:
        print("❌ FEAR_GREED_API_KEY not found in environment")
        print("   Add FEAR_GREED_API_KEY to your .env file for real data")
        return False

def cleanup_test_files():
    """Clean up any test files generated"""
    try:
        output_dir = Path("output")
        test_files = list(output_dir.glob("fear_greed_trend.png"))
        
        if test_files:
            print(f"\n🧹 Test completed - Fear & Greed chart available at: {test_files[0]}")
        else:
            print("\n🧹 Test completed - no test files to clean up")
            
    except Exception as e:
        print(f"⚠️ Error during cleanup: {str(e)}")

def main():
    """Run all Fear & Greed chart tests"""
    print("🚀 Fear & Greed 14-Day Trend Chart Test Suite")
    print("=" * 60)
    print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests_results = []
    
    # Test 1: Enhanced Visualizations Engine
    test1_result = test_enhanced_visualizations_fear_greed()
    tests_results.append(("Enhanced Visualizations", test1_result))
    
    # Test 2: Email Report Integration
    test2_result = test_email_report_integration()
    tests_results.append(("Email Report Integration", test2_result))
    
    # Test 3: Full Email Generation
    test3_result = test_full_email_generation()
    tests_results.append(("Full Email Generation", test3_result))
    
    # Test 4: API Configuration
    test4_result = test_api_configuration()
    tests_results.append(("API Configuration", test4_result))
    
    # Summary
    print("\n📋 Test Results Summary")
    print("=" * 30)
    
    passed_tests = 0
    total_tests = len(tests_results)
    
    for test_name, result in tests_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed_tests += 1
    
    print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Fear & Greed 14-day chart is working correctly.")
        print("📧 The chart will be included in every daily email report.")
    elif passed_tests >= 3:
        print("🎊 Most tests passed! System is functional with minor issues.")
    else:
        print("⚠️ Some critical tests failed. Check the output above for details.")
    
    # Cleanup
    cleanup_test_files()
    
    print(f"\n🕒 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 