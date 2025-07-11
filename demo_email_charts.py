#!/usr/bin/env python3
"""
Demonstration of Enhanced Email Charts with AI Explanations

This script shows how the MacroIntel system now generates sophisticated
visual charts with AI-powered explanations that are embedded in email reports.
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
    generate_email_content
)

def demonstrate_ai_chart_explanations():
    """Demonstrate the AI explanation capabilities."""
    print("🧠 MacroIntel Enhanced Email Charts with AI Explanations")
    print("=" * 60)
    print(f"🕒 Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Sample regime data
    regime_data = {
        "total_score": 72.5,
        "regime_classification": "Bullish",
        "strategy_recommendation": "Tier 1 Momentum",
        "instrument": "SPY",
        "risk_allocation": "Aggressive",
        "timestamp": datetime.now().isoformat(),
        "component_breakdown": {
            "volatility": {
                "raw_score": 75.0,
                "weighted_score": 15.0,
                "interpretation": "Elevated volatility supporting momentum strategies"
            },
            "structure": {
                "raw_score": 70.0,
                "weighted_score": 14.0,
                "interpretation": "Strong technical structure with upward bias"
            },
            "momentum": {
                "raw_score": 80.0,
                "weighted_score": 16.0,
                "interpretation": "Powerful momentum signals across multiple timeframes"
            },
            "institutional": {
                "raw_score": 68.0,
                "weighted_score": 13.6,
                "interpretation": "Institutional positioning favoring risk assets"
            }
        }
    }
    
    fear_greed_score = 78  # Greed level
    headlines = [
        "Fed Chair Powell hints at policy pivot as inflation shows signs of cooling",
        "Tech giants report stellar Q4 earnings driven by AI revolution",
        "U.S. dollar weakens as global growth outlook improves"
    ]
    
    print("📊 Current Market Context:")
    print(f"   Regime Score: {regime_data['total_score']:.1f}/100 ({regime_data['regime_classification']})")
    print(f"   Fear & Greed: {fear_greed_score} (Greed)")
    print(f"   Strategy: {regime_data['strategy_recommendation']}")
    print(f"   Headlines: {len(headlines)} market-moving stories")
    print()
    
    # Generate enhanced charts
    print("🔄 Generating enhanced charts with AI explanations...")
    enhanced_charts = generate_enhanced_charts_with_explanations(
        regime_data=regime_data,
        fear_greed_score=fear_greed_score,
        headlines=headlines
    )
    
    if enhanced_charts:
        print(f"✅ Generated {len(enhanced_charts)} enhanced charts with AI explanations")
        print()
        
        # Show each chart's AI explanation
        for chart_key, chart_data in enhanced_charts.items():
            chart_names = {
                "intelligent_regime": "🧠 Intelligent Regime Analysis",
                "vix_strategic": "📈 VIX Strategic Overview", 
                "multi_asset": "📊 Multi-Asset Comparison"
            }
            
            chart_name = chart_names.get(chart_key, f"Chart: {chart_key}")
            print(f"{chart_name}")
            print("-" * 50)
            
            # Chart details
            strategy = chart_data.get('strategy', 'N/A')
            regime = chart_data.get('regime', 'N/A')
            theme = chart_data.get('market_theme', 'N/A')
            
            print(f"📁 File: {chart_data.get('path', 'N/A')}")
            print(f"🎯 Strategy: {strategy}")
            print(f"📈 Regime: {regime}")
            print(f"🎨 Theme: {theme}")
            print()
            
            # AI Explanation
            explanation = chart_data.get('explanation', '')
            if explanation:
                print("🤖 AI Explanation:")
                print(f"   {explanation}")
            else:
                print("⚠️ No AI explanation available")
            
            # Sentiment Data
            sentiment_data = chart_data.get('sentiment_data', {})
            if sentiment_data:
                print()
                print("📊 Sentiment Data:")
                for key, value in sentiment_data.items():
                    if isinstance(value, (int, float)):
                        print(f"   {key.replace('_', ' ').title()}: {value:.1f}")
                    else:
                        print(f"   {key.replace('_', ' ').title()}: {value}")
            
            print()
            print("=" * 60)
            print()
    else:
        print("❌ No enhanced charts generated")
    
    return enhanced_charts

def demonstrate_html_integration(enhanced_charts):
    """Demonstrate HTML integration for email."""
    print("📧 Email HTML Integration Demo")
    print("=" * 40)
    
    if not enhanced_charts:
        print("❌ No charts available for HTML demo")
        return
    
    # Sample articles for context
    sample_articles = [
        {
            "title": "Fed Chair Powell Signals Policy Flexibility",
            "summary": "Federal Reserve Chair Jerome Powell indicated potential flexibility in monetary policy as economic data shows mixed signals.",
            "url": "https://example.com/fed-policy",
            "source": "fmp",
            "tone": "Neutral",
            "affected_tickers": "SPY, QQQ, TLT",
            "timestamp": datetime.now().isoformat()
        },
        {
            "title": "AI Stocks Surge on Regulatory Clarity",
            "summary": "Artificial intelligence stocks rallied following new regulatory guidance that provides clearer framework for AI development.",
            "url": "https://example.com/ai-stocks",
            "source": "polygon",
            "tone": "Bullish",
            "affected_tickers": "NVDA, MSFT, GOOGL",
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    print(f"🔄 Generating full email content with {len(sample_articles)} articles...")
    
    # Generate complete email content
    html_content, chart_attachments = generate_email_content(sample_articles, limit=10)
    
    if html_content:
        print(f"✅ Email content generated: {len(html_content):,} characters")
        print(f"📎 Chart attachments: {len(chart_attachments)}")
        
        # Show attachment details
        for i, attachment in enumerate(chart_attachments, 1):
            chart_path = attachment.get('path', 'N/A')
            chart_cid = attachment.get('cid', 'N/A')
            print(f"   📈 Chart {i}: {os.path.basename(chart_path)} (CID: {chart_cid})")
            
            # Check file size
            if chart_path and isinstance(chart_path, str) and os.path.exists(chart_path):
                file_size = os.path.getsize(chart_path) / 1024  # KB
                print(f"      Size: {file_size:.1f} KB")
            else:
                print(f"      ⚠️ File not found")
        
        # Analyze email content
        ai_sections = html_content.count("🤖 AI Analysis")
        chart_sections = html_content.count("📊")
        regime_sections = html_content.count("regime")
        explanation_sections = html_content.count("explanation")
        
        print()
        print("📊 Email Content Analysis:")
        print(f"   🤖 AI Analysis sections: {ai_sections}")
        print(f"   📊 Chart references: {chart_sections}")
        print(f"   📈 Regime mentions: {regime_sections}")
        print(f"   💡 Explanation sections: {explanation_sections}")
        
        # Show a snippet of the AI explanation in HTML
        if "🤖 AI Analysis" in html_content:
            start_idx = html_content.find("🤖 AI Analysis")
            snippet_start = max(0, start_idx - 100)
            snippet_end = min(len(html_content), start_idx + 500)
            snippet = html_content[snippet_start:snippet_end]
            
            print()
            print("📝 Sample AI Analysis HTML:")
            print("-" * 30)
            print(snippet[:300] + "..." if len(snippet) > 300 else snippet)
            print("-" * 30)
        
        return True
    else:
        print("❌ Failed to generate email content")
        return False

def show_system_capabilities():
    """Show the enhanced capabilities of the system."""
    print("\n🎯 Enhanced Email Charts System Capabilities")
    print("=" * 50)
    
    capabilities = [
        "🧠 AI-Powered Chart Explanations",
        "📊 Regime-Aware Chart Selection", 
        "🎯 Strategy Tier Determination",
        "📰 News Context Integration",
        "😨 Sentiment Analysis Integration",
        "📈 Multi-Asset Correlation Analysis",
        "🔍 Perplexity Topic Classification",
        "📧 Seamless Email Embedding",
        "🖼️ Inline Chart Attachments",
        "📱 HTML Responsive Design"
    ]
    
    for capability in capabilities:
        print(f"   ✅ {capability}")
    
    print()
    print("🔧 Technical Features:")
    technical_features = [
        "Real-time regime score analysis",
        "Fear & Greed Index integration", 
        "VIX volatility correlation",
        "Multi-timeframe momentum analysis",
        "Institutional positioning insights",
        "Cross-asset correlation matrices",
        "Risk-adjusted positioning logic",
        "Dynamic strategy selection"
    ]
    
    for feature in technical_features:
        print(f"   🛠️ {feature}")

def main():
    """Run the complete demonstration."""
    print("🚀 MacroIntel Enhanced Email Charts Demonstration")
    print("=" * 60)
    
    # Step 1: Demonstrate AI chart generation
    enhanced_charts = demonstrate_ai_chart_explanations()
    
    # Step 2: Demonstrate HTML integration
    if enhanced_charts:
        html_success = demonstrate_html_integration(enhanced_charts)
    else:
        html_success = False
    
    # Step 3: Show system capabilities
    show_system_capabilities()
    
    # Summary
    print("\n📋 Demonstration Summary")
    print("=" * 30)
    
    if enhanced_charts:
        print("✅ AI Chart Generation: Working")
    else:
        print("❌ AI Chart Generation: Failed")
    
    if html_success:
        print("✅ Email Integration: Working")
    else:
        print("❌ Email Integration: Failed")
    
    chart_count = len(enhanced_charts) if enhanced_charts else 0
    print(f"📊 Charts Generated: {chart_count}")
    
    if chart_count > 0:
        print("🎉 Enhanced email charts with AI explanations are fully operational!")
        print("📧 Ready to embed sophisticated visual analysis in daily reports.")
    else:
        print("⚠️ System needs attention - check configuration and dependencies.")
    
    print(f"\n🕒 Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 