import argparse
from event_tracker.econ_event_tracker import get_today_events
from news_scanner.news_insight_feed import scan_relevant_news
from email_report import send_daily_report, generate_text_report
from utils.api_clients import init_env

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='MacroIntel News Scanner and Email Reporter')
    parser.add_argument('--engine', choices=['gpt', 'claude', 'gemini'], 
                       default='gpt', help='AI engine for summarization (default: gpt)')
    parser.add_argument('--limit', type=int, default=15, 
                       help='Maximum articles to process (default: 15, max: 20)')
    parser.add_argument('--email', action='store_true', 
                       help='Send daily email report')
    parser.add_argument('--text-only', action='store_true', 
                       help='Generate text report instead of HTML email')
    
    args = parser.parse_args()
    
    # Validate limit
    limit = args.limit
    if limit > 20:
        print(f"⚠️  Limit {limit} exceeds maximum of 20. Setting to 20.")
        limit = 20
    
    # Initialize environment
    init_env()
    
    print("🚀 MacroIntel News Scanner Starting...\n")
    
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
            # Send HTML email
            success = send_daily_report(relevant_articles, limit)
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
