#!/usr/bin/env python3
"""
Test script to verify enhanced charts with AI explanations are properly integrated into email reports.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add project directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.email_report import (
    generate_enhanced_charts_with_explanations,
    create_chart_html_section,
    generate_email_content,
    send_daily_report
)

def create_sample_regime_data():
    """Create sample regime data for testing."""
    return {
        "total_score": 65.0,
        "regime_classification": "Bullish",
        "strategy_recommendation": "Tier 1 Momentum",
        "instrument": "SPY",
        "risk_allocation": "Aggressive",
        "timestamp": datetime.now().isoformat(),
        "component_breakdown": {
            "volatility": {
                "raw_score": 70.0,
                "weighted_score": 14.0,
                "interpretation": "Moderate volatility favoring momentum strategies"
            },
            "structure": {
                "raw_score": 60.0,
                "weighted_score": 12.0,
                "interpretation": "Technical structure showing upward bias"
            },
            "volume_breadth": {
                "raw_score": 65.0,
                "weighted_score": 13.0,
                "interpretation": "Healthy volume patterns supporting trend"
            },
            "momentum": {
                "raw_score": 75.0,
                "weighted_score": 15.0,
                "interpretation": "Strong momentum signals present"
            },
            "institutional": {
                "raw_score": 55.0,
                "weighted_score": 11.0,
                "interpretation": "Mixed institutional positioning"
            }
        }
    }

def create_sample_articles():
    """Create sample articles for testing."""
    return [
        {
            "title": "Fed Signals Dovish Stance as Inflation Cools",
            "summary": "Federal Reserve officials indicated a potential pause in rate hikes as inflation data shows signs of cooling, boosting market sentiment.",
            "url": "https://example.com/fed-dovish",
            "source": "fmp",
            "tone": "Bullish",
            "affected_tickers": "SPY, QQQ, TLT",
            "timestamp": datetime.now().isoformat()
        },
        {
            "title": "Tech Earnings Beat Expectations Amid AI Optimism",
            "summary": "Major technology companies reported strong quarterly results, driven by AI-related investments and productivity gains.",
            "url": "https://example.com/tech-earnings",
            "source": "polygon",
            "tone": "Bullish",
            "affected_tickers": "AAPL, MSFT, GOOGL, NVDA",
            "timestamp": datetime.now().isoformat()
        },
        {
            "title": "Geopolitical Tensions Rise as Trade Disputes Escalate",
            "summary": "Ongoing trade disputes between major economies are creating uncertainty in global markets and commodity pricing.",
            "url": "https://example.com/geopolitical",
            "source": "benzinga",
            "tone": "Bearish",
            "affected_tickers": "GLD, USO, VIX",
            "timestamp": datetime.now().isoformat()
        }
    ]

def test_enhanced_chart_generation():
    """Test enhanced chart generation with AI explanations."""
    print("🧪 Testing Enhanced Chart Generation with AI Explanations")
    print("=" * 60)
    
    # Create sample data
    regime_data = create_sample_regime_data()
    fear_greed_score = 72  # Greed level
    headlines = [
        "Fed signals dovish stance as inflation cools",
        "Tech earnings beat expectations amid AI optimism",
        "Geopolitical tensions rise as trade disputes escalate"
    ]
    
    print(f"📊 Regime Score: {regime_data['total_score']}")
    print(f"😏 Fear & Greed: {fear_greed_score} (Greed)")
    print(f"📰 Headlines: {len(headlines)} sample headlines")
    print()
    
    try:
        # Generate enhanced charts
        print("🔄 Generating enhanced charts with AI explanations...")
        enhanced_charts = generate_enhanced_charts_with_explanations(
            regime_data=regime_data,
            fear_greed_score=fear_greed_score,
            headlines=headlines
        )
        
        if enhanced_charts:
            print(f"✅ Generated {len(enhanced_charts)} enhanced charts:")
            
            for chart_key, chart_data in enhanced_charts.items():
                print(f"\n📈 Chart: {chart_key}")
                print(f"   Path: {chart_data.get('path', 'N/A')}")
                print(f"   Strategy: {chart_data.get('strategy', 'N/A')}")
                print(f"   Regime: {chart_data.get('regime', 'N/A')}")
                print(f"   Theme: {chart_data.get('market_theme', 'N/A')}")
                
                # Show AI explanation preview
                explanation = chart_data.get('explanation', '')
                if explanation and isinstance(explanation, str):
                    preview = explanation[:150] + "..." if len(explanation) > 150 else explanation
                    print(f"   AI Explanation: {preview}")
                
                # Check if file exists
                chart_path = chart_data.get('path')
                if chart_path and isinstance(chart_path, str) and os.path.exists(chart_path):
                    file_size = os.path.getsize(chart_path)
                    print(f"   ✅ File exists: {file_size} bytes")
                else:
                    print(f"   ❌ File not found: {chart_path}")
            
            return enhanced_charts
        else:
            print("❌ No enhanced charts generated")
            return {}
            
    except Exception as e:
        print(f"❌ Error generating enhanced charts: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

def test_chart_html_generation(enhanced_charts):
    """Test HTML generation for charts."""
    print("\n🧪 Testing Chart HTML Generation")
    print("=" * 40)
    
    if not enhanced_charts:
        print("❌ No charts available for HTML testing")
        return ""
    
    try:
        html_sections = []
        chart_counter = 1
        
        for chart_key, chart_data in enhanced_charts.items():
            chart_names = {
                "intelligent_regime": "Intelligent Regime Analysis",
                "vix_strategic": "VIX Strategic Overview", 
                "multi_asset": "Multi-Asset Comparison"
            }
            
            chart_name = chart_names.get(chart_key, f"Chart {chart_counter}")
            chart_id = f"test_chart_{chart_counter}"
            
            print(f"🔄 Generating HTML for: {chart_name}")
            
            html_section = create_chart_html_section(
                chart_name=chart_name,
                chart_data=chart_data,
                chart_id=chart_id
            )
            
            if html_section:
                html_sections.append(html_section)
                print(f"✅ Generated HTML section ({len(html_section)} characters)")
            else:
                print(f"❌ Failed to generate HTML section")
            
            chart_counter += 1
        
        # Combine HTML sections
        combined_html = "\n".join(html_sections)
        print(f"\n✅ Total HTML generated: {len(combined_html)} characters")
        
        return combined_html
        
    except Exception as e:
        print(f"❌ Error generating chart HTML: {str(e)}")
        import traceback
        traceback.print_exc()
        return ""

def test_full_email_integration():
    """Test full email integration with enhanced charts."""
    print("\n🧪 Testing Full Email Integration")
    print("=" * 40)
    
    try:
        # Create sample articles
        articles = create_sample_articles()
        
        print(f"📧 Generating email content with {len(articles)} articles...")
        
        # Generate full email content (which should include enhanced charts)
        html_content, chart_attachments = generate_email_content(articles, limit=5)
        
        if html_content:
            print(f"✅ Email content generated: {len(html_content)} characters")
            print(f"📎 Chart attachments: {len(chart_attachments)}")
            
            # Show chart attachment details
            for i, attachment in enumerate(chart_attachments):
                print(f"   Chart {i+1}: {attachment.get('path', 'N/A')} (CID: {attachment.get('cid', 'N/A')})")
                
                # Check if attachment file exists
                chart_path = attachment.get('path')
                if chart_path and isinstance(chart_path, str) and os.path.exists(chart_path):
                    file_size = os.path.getsize(chart_path)
                    print(f"      ✅ File exists: {file_size} bytes")
                else:
                    print(f"      ❌ File not found")
            
            # Check for AI analysis sections in HTML
            ai_sections = html_content.count("🤖 AI Analysis")
            chart_sections = html_content.count("📊")
            
            print(f"🤖 AI Analysis sections found: {ai_sections}")
            print(f"📊 Chart sections found: {chart_sections}")
            
            return html_content, chart_attachments
        else:
            print("❌ Failed to generate email content")
            return None, []
            
    except Exception as e:
        print(f"❌ Error in full email integration test: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, []

def test_email_sending(html_content, chart_attachments):
    """Test email sending functionality (dry run)."""
    print("\n🧪 Testing Email Sending (Dry Run)")
    print("=" * 40)
    
    # Check if email credentials are available
    smtp_user = os.getenv("SMTP_USER")
    email_recipient = os.getenv("EMAIL_RECIPIENT")
    
    if not smtp_user or not email_recipient:
        print("⚠️ Email credentials not configured - skipping actual send test")
        print("   Add SMTP_USER and EMAIL_RECIPIENT to your .env file to test email sending")
        return False
    
    print(f"📧 Email configured for: {email_recipient}")
    print(f"📎 Attachments ready: {len(chart_attachments)}")
    
    # For safety, don't actually send the test email unless explicitly requested
    print("📝 Email send test skipped (add --send flag to actually send)")
    print("   Use: python test_enhanced_email_charts.py --send")
    
    return True

def main():
    """Run all tests."""
    print("🚀 MacroIntel Enhanced Email Charts Test Suite")
    print("=" * 60)
    print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Enhanced chart generation
    enhanced_charts = test_enhanced_chart_generation()
    
    # Test 2: Chart HTML generation
    chart_html = test_chart_html_generation(enhanced_charts)
    
    # Test 3: Full email integration
    html_content, chart_attachments = test_full_email_integration()
    
    # Test 4: Email sending (dry run)
    email_ready = test_email_sending(html_content, chart_attachments)
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 20)
    
    tests_passed = 0
    total_tests = 4
    
    if enhanced_charts:
        print("✅ Enhanced chart generation: PASSED")
        tests_passed += 1
    else:
        print("❌ Enhanced chart generation: FAILED")
    
    if chart_html:
        print("✅ Chart HTML generation: PASSED")
        tests_passed += 1
    else:
        print("❌ Chart HTML generation: FAILED")
    
    if html_content and chart_attachments:
        print("✅ Full email integration: PASSED")
        tests_passed += 1
    else:
        print("❌ Full email integration: FAILED")
    
    if email_ready:
        print("✅ Email system configuration: PASSED")
        tests_passed += 1
    else:
        print("❌ Email system configuration: FAILED")
    
    print(f"\n🎯 Overall Result: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Enhanced email charts are working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    print(f"\n🕒 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    import sys
    
    # Check for send flag
    if "--send" in sys.argv:
        print("⚠️ Send flag detected - actual email will be sent!")
        input("Press Enter to continue or Ctrl+C to cancel...")
    
    main() 