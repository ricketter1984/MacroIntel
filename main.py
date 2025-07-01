import argparse
import sys
import os

# Add agents directory to path for new swarm orchestrator
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

from event_tracker.econ_event_tracker import get_today_events
from news_scanner.news_insight_feed import scan_relevant_news
from email_report import send_daily_report, generate_text_report
from utils.api_clients import init_env

# Import visual query engine
try:
    from visual_query_engine import generate_extreme_fear_chart
    VISUAL_ENGINE_AVAILABLE = True
except ImportError:
    print("⚠️ Visual query engine not available - charts will be skipped")
    VISUAL_ENGINE_AVAILABLE = False

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='MacroIntel News Scanner and Email Reporter')
    parser.add_argument('--swarm', action='store_true', 
                       help='Use new agent swarm (recommended)')
    parser.add_argument('--engine', choices=['gpt', 'claude', 'gemini'], 
                       default='gpt', help='AI engine for summarization (default: gpt)')
    parser.add_argument('--limit', type=int, default=15, 
                       help='Maximum articles to process (default: 15, max: 20)')
    parser.add_argument('--email', action='store_true', 
                       help='Send daily email report')
    parser.add_argument('--text-only', action='store_true', 
                       help='Generate text report instead of HTML email')
    parser.add_argument('--chart', action='store_true', 
                       help='Generate extreme fear chart if conditions are met')
    
    args = parser.parse_args()
    
    # Check if user wants to use the new agent swarm
    if args.swarm:
        print("🤖 Using new MacroIntel Agent Swarm...")
        try:
            from agents.swarm_orchestrator import MacroIntelSwarm
            swarm = MacroIntelSwarm()
            results = swarm.execute_swarm()
            
            if results.get("status") == "success":
                summary = results.get("summary", {})
                print("\n" + "="*60)
                print("🤖 MACROINTEL SWARM EXECUTION SUMMARY")
                print("="*60)
                print(f"📊 Articles Processed: {summary.get('articles_processed', 0)}")
                print(f"📈 Charts Generated: {summary.get('charts_generated', 0)}")
                print(f"📘 Market Regime: {summary.get('market_regime', 'Unknown')}")
                print(f"🎯 Strategies Selected: {summary.get('strategies_selected', 0)}")
                print(f"📧 Email Sent: {'✅ Yes' if summary.get('email_sent', False) else '❌ No'}")
                print(f"👥 Recipients: {summary.get('recipients_count', 0)}")
                print(f"⏱️ Execution Time: {results.get('execution_time', 'Unknown')}")
                print("="*60)
                print("🎉 Agent swarm execution completed successfully!")
            else:
                print(f"❌ Swarm execution failed: {results.get('error', 'Unknown error')}")
            
            return
        except ImportError:
            print("❌ Agent swarm not available. Please ensure agents/ directory exists.")
            return
        except Exception as e:
            print(f"❌ Error running agent swarm: {str(e)}")
            print("Falling back to legacy mode...")
    
    # Validate limit
    limit = args.limit
    if limit > 20:
        print(f"⚠️  Limit {limit} exceeds maximum of 20. Setting to 20.")
        limit = 20
    
    # Initialize environment
    init_env()
    
    print("🚀 MacroIntel News Scanner Starting (Legacy Mode)...\n")
    print("💡 Tip: Use --swarm for the new agent swarm system")
    
    # Check for extreme fear chart if requested
    if args.chart and VISUAL_ENGINE_AVAILABLE:
        print("📊 Checking for extreme fear conditions...")
        chart_path = generate_extreme_fear_chart()
        if chart_path:
            print(f"✅ Extreme fear chart generated: {chart_path}")
        else:
            print("😌 No extreme fear detected - chart not generated")
        print()
    
    # Check economic events
    print("📆 Checking today's economic events...\n")
    events = get_today_events()
    
    if not events:
        print("✅ No major economic events scheduled today.")
    else:
        print("🟡 Events found:")
        for event in events:
            print(f"- {event['title']} at {event['datetime']} (Impact: {event['impact']})")
    
    print("\n" + "="*60 + "\n")
    
    # Scan for relevant news
    print(f"🔍 Scanning news with {args.engine.upper()} engine (limit: {limit})...\n")
    relevant_articles = scan_relevant_news(limit=limit, engine=args.engine)
    
    if not relevant_articles:
        print("⚠️ No relevant articles found for your watchlist.")
        return
    
    print(f"\n✅ Found {len(relevant_articles)} relevant articles")
    
    # Generate and send report
    if args.email:
        print("\n📧 Generating email report...")
        
        if args.text_only:
            # Generate text report
            text_report = generate_text_report(relevant_articles, limit)
            print("\n" + "="*60)
            print("📰 TEXT REPORT")
            print("="*60)
            print(text_report)
        else:
            # Send HTML email (will automatically include extreme fear chart if available)
            success = send_daily_report(relevant_articles)
            if success:
                print("✅ Email report sent successfully!")
            else:
                print("❌ Failed to send email report")
    else:
        # Display summary in console
        print("\n" + "="*60)
        print("📰 NEWS SUMMARY")
        print("="*60)
        
        for i, article in enumerate(relevant_articles, 1):
            print(f"\n{i}. {article.get('title', 'No title')}")
            print(f"   URL: {article.get('url', 'No URL')}")
            print(f"   Summary: {article.get('summary', 'No summary')}")
            print(f"   Tickers: {article.get('affected_tickers', 'None')}")
            print(f"   Tone: {article.get('tone', 'Neutral')}")
            print(f"   Source: {article.get('source', 'Unknown')}")
            print("-" * 40)
    
    print(f"\n🎉 MacroIntel scan completed! Processed {len(relevant_articles)} articles.")

if __name__ == "__main__":
    main()
