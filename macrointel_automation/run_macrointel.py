import sys
import os
import logging
import time
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

# Add parent directory to path to access project modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import project modules
from macrointel_agents import run_agents_pipeline
from core.enhanced_visualizations import EnhancedVisualizations
from core.email_report import send_daily_report, generate_email_content
from utils.api_clients import fetch_all_news
from utils.cme_scraper import fetch_cme_data
from agents.ticker_news_agent import TickerNewsAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_cme_only():
    """
    Run CME data scraping only with summary output.
    
    Returns:
        bool: True if successful, False if failed
    """
    try:
        logging.info("🏦 Running CME-only mode...")
        
        # Fetch CME data
        df = fetch_cme_data()
        
        if df.empty:
            logging.error("❌ No CME data available")
            print("❌ Failed to fetch CME data - check logs for details")
            return False
        
        # Print summary of top 3 highest volume contracts
        print("📊 CME Data Summary")
        print("=" * 50)
        
        # Sort by volume (descending) and get top 3
        if 'volume' in df.columns:
            top_volume = df.nlargest(3, 'volume')
            print("🔥 Top 3 Highest Volume Contracts:")
            print()
            
            for i, (_, row) in enumerate(top_volume.iterrows(), 1):
                symbol = row.get('symbol', 'N/A')
                volume = row.get('volume', 0)
                last_price = row.get('last_price', 0)
                change = row.get('change', 0)
                open_interest = row.get('open_interest', 0)
                
                # Handle None values in change comparison
                change_val = change if change is not None else 0
                change_symbol = "📈" if change_val > 0 else "📉" if change_val < 0 else "➡️"
                
                print(f"#{i} {symbol}")
                print(f"   💰 Last Price: ${last_price:,.2f}")
                print(f"   {change_symbol} Change: {change:+.2f}")
                print(f"   📊 Volume: {volume:,}")
                print(f"   🏗️ Open Interest: {open_interest:,}")
                print()
        else:
            print("⚠️ Volume data not available for ranking")
            print("📋 All Contracts:")
            for _, row in df.iterrows():
                symbol = row.get('symbol', 'N/A')
                last_price = row.get('last_price', 0)
                change = row.get('change', 0)
                # Handle None values in change comparison
                change_val = change if change is not None else 0
                change_symbol = "📈" if change_val > 0 else "📉" if change_val < 0 else "➡️"
                print(f"   {symbol}: ${last_price:,.2f} ({change_symbol}{change_val:+.2f})")
        
        print("=" * 50)
        print(f"✅ CME data saved to output/cme_data_today.csv")
        logging.info("✅ CME-only mode completed successfully")
        return True
        
    except Exception as e:
        logging.error(f"❌ Failed to run CME-only mode: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False

def fetch_cme_data_and_save():
    """
    Fetch CME forex futures data and save to CSV file.
    
    Returns:
        bool: True if successful, False if failed
    """
    try:
        logging.info("🏦 Step: Fetching CME forex futures data...")
        
        # Fetch CME data
        cme_data = fetch_cme_data()
        
        if cme_data.empty:
            logging.error("❌ No CME data available to save")
            return False
        
        # Create output directory if it doesn't exist
        output_dir = project_root / "output"
        output_dir.mkdir(exist_ok=True)
        
        # Save to CSV
        output_file = output_dir / "cme_data_today.csv"
        cme_data.to_csv(output_file, index=False)
        
        # Log success with summary
        logging.info(f"✅ CME data saved to {output_file}")
        logging.info(f"📊 Saved {len(cme_data)} forex contracts:")
        
        # Log brief summary of each contract
        for _, row in cme_data.iterrows():
            pct_change = float(row['pct_change_5d'])
            status = "📈" if pct_change > 0 else "📉" if pct_change < 0 else "➡️"
            logging.info(f"   {status} {row['name']}: {pct_change:+.2f}% (Vol Rank #{row['volatility_rank']})")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Failed to fetch and save CME data: {str(e)}")
        return False

def main(send_email=False):
    logging.info("🚀 MacroIntel automation started")

    # Step 1: Aggregate news and macro data
    logging.info("📰 Step 1: Fetching news and macro data...")
    articles = fetch_all_news()
    logging.info(f"📰 Retrieved {len(articles)} articles")
    
    # Create visualization engine and fetch regime data
    logging.info("📊 Step 1.5: Fetching regime data...")
    viz_engine = EnhancedVisualizations()
    regime_data = viz_engine._fetch_regime_data()
    if regime_data is None:
        regime_data = {}
    elif hasattr(regime_data, 'to_dict'):
        regime_data = regime_data.to_dict()
    if isinstance(regime_data, dict):
        logging.info(f"📊 Regime data keys: {list(regime_data.keys())}")
    else:
        logging.info("📊 Regime data keys: None")

    # Step 2: Run AI agent pipeline
    logging.info("🤖 Step 2: Running AI agent pipeline...")
    # Extract headlines from articles for agent pipeline
    headlines = [article.get('title', '') for article in articles if article.get('title')]
    logging.info(f"🤖 Processing {len(headlines)} headlines")
    
    # Get regime data with proper defaults and type conversion
    total_score = regime_data.get('total_score', 50)
    regime_score = (total_score / 100.0) if total_score is not None else 0.5
    
    vix_raw = regime_data.get('vix_level', 20.0)
    vix_level = 20.0 if vix_raw is None else float(vix_raw)
    
    fg_raw = regime_data.get('fear_greed_score', 50)
    fear_greed_score = 50 if fg_raw is None else int(fg_raw)
    
    logging.info(f"🤖 Agent inputs - Regime: {regime_score:.2f}, VIX: {vix_level:.1f}, F&G: {fear_greed_score}")
    
    agent_results = run_agents_pipeline(
        news_headlines=headlines,
        regime_score=regime_score,
        vix_level=vix_level,
        fear_greed_score=fear_greed_score
    )
    logging.info("🤖 Agent pipeline completed")

    # Step 3: Fetch and save CME data
    logging.info("🏦 Step 3: Fetching CME forex futures data...")
    cme_success = fetch_cme_data_and_save()
    if cme_success:
        logging.info("🏦 CME data fetch completed")
    else:
        logging.warning("⚠️ CME data fetch failed, continuing with pipeline")

    # Step 4: Generate all visualizations
    logging.info("📈 Step 4: Generating visualizations...")
    viz_engine.generate_all_visualizations(regime_data)
    logging.info("📈 Visualizations completed")

    # Step 5: Send daily report if requested
    if send_email:
        logging.info("📧 Step 5: Sending email report...")
        # Generate email content
        html_content = generate_email_content(articles)
        send_daily_report(html_content)
        logging.info("📧 Email report sent")
    else:
        logging.info("📧 Step 5: Email report skipped (use --email flag to send)")

    logging.info("✅ MacroIntel automation completed")

def run_watchlist_news(tickers, send_email=False, include_quiver=False):
    """
    Run the TickerNewsAgent for specific tickers.
    
    Args:
        tickers: List of ticker symbols to process
        send_email: Whether to send email report
        include_quiver: Whether to include congressional trading data
    """
    logging.info(f"📰 Running TickerNewsAgent for tickers: {', '.join(tickers)}")
    if include_quiver:
        logging.info("🏛️ Including congressional trading data")
    
    try:
        # Initialize and run the TickerNewsAgent
        agent = TickerNewsAgent(include_quiver=include_quiver)
        results = agent.run(tickers)
        
        if results["status"] == "success":
            logging.info(f"✅ Successfully processed {results['tickers_processed']} tickers")
            logging.info(f"📰 Found {results['total_articles']} total articles")
            logging.info(f"📄 Report saved to: {results['markdown_file']}")
            
            # Print summary
            for ticker, data in results["results"].items():
                article_count = len(data.get("headlines", []))
                logging.info(f"   {ticker}: {article_count} articles")
            
            # Send email if requested
            if send_email:
                logging.info("📧 Sending ticker news email report...")
                try:
                    # Convert ticker results to article format for email generation
                    articles = []
                    for ticker, data in results["results"].items():
                        for headline in data.get("headlines", []):
                            article = {
                                "title": headline.get("title", ""),
                                "summary": headline.get("summary", ""),
                                "url": headline.get("url", ""),
                                "source": "TickerNewsAgent",
                                "symbols": [ticker],
                                "sector": headline.get("sector", "Unknown"),
                                "impact": headline.get("impact", "Neutral")
                            }
                            articles.append(article)
                    
                    # Generate email content
                    email_content = generate_email_content(articles, limit=50)
                    
                    # Send the email
                    email_sent = send_daily_report(email_content)
                    
                    if email_sent:
                        logging.info("✅ Ticker news email report sent successfully")
                        print("📧 Email report sent successfully")
                    else:
                        logging.error("❌ Failed to send ticker news email report")
                        print("❌ Failed to send email report")
                        
                except Exception as e:
                    logging.error(f"❌ Error sending ticker news email: {str(e)}")
                    print(f"❌ Email error: {str(e)}")
            
            print(f"✅ TickerNewsAgent completed successfully")
            print(f"📰 Processed {results['tickers_processed']} tickers, found {results['total_articles']} articles")
            print(f"📄 Report saved to: {results['markdown_file']}")
            
        else:
            logging.error(f"❌ TickerNewsAgent failed: {results.get('error', 'Unknown error')}")
            print(f"❌ Error: {results.get('error', 'Unknown error')}")
            
    except Exception as e:
        logging.error(f"❌ Error running TickerNewsAgent: {str(e)}")
        print(f"❌ Error: {str(e)}")

def run_scheduled_pipeline():
    """Run the MacroIntel pipeline with email enabled for scheduled jobs."""
    logger.info("🕐 Running scheduled MacroIntel pipeline...")
    try:
        main(send_email=True)
        logger.info("✅ Scheduled pipeline completed successfully")
    except Exception as e:
        logger.error(f"❌ Scheduled pipeline failed: {str(e)}")

def setup_scheduler():
    """Setup APScheduler with daily MacroIntel pipeline jobs."""
    scheduler = BackgroundScheduler()
    
    # Add morning job at 7:30 AM Eastern Time
    scheduler.add_job(
        func=run_scheduled_pipeline,
        trigger=CronTrigger(hour=7, minute=30, timezone='America/New_York'),
        id='morning_macrointel',
        name='Morning MacroIntel Pipeline (7:30 AM ET)',
        replace_existing=True
    )
    
    # Add afternoon job at 3:45 PM Eastern Time
    scheduler.add_job(
        func=run_scheduled_pipeline,
        trigger=CronTrigger(hour=15, minute=45, timezone='America/New_York'),
        id='afternoon_macrointel',
        name='Afternoon MacroIntel Pipeline (3:45 PM ET)',
        replace_existing=True
    )
    
    return scheduler

def run_scheduler():
    """Start the scheduler and keep it running."""
    scheduler = setup_scheduler()
    
    logger.info("🚀 Starting MacroIntel Scheduler...")
    logger.info("📅 Scheduled jobs:")
    logger.info("   - Morning: 7:30 AM Eastern Time")
    logger.info("   - Afternoon: 3:45 PM Eastern Time")
    
    scheduler.start()
    
    try:
        # Keep the scheduler running
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Shutting down scheduler...")
        scheduler.shutdown()
        logger.info("✅ Scheduler stopped")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MacroIntel Automation Pipeline")
    parser.add_argument("--send", action="store_true", help="Send the email report")
    parser.add_argument("--schedule", action="store_true", help="Run in scheduled mode (twice daily)")
    parser.add_argument("--cme", action="store_true", help="Fetch CME settlement data and show top 3 highest volume contracts")
    parser.add_argument("--watchlist-news", type=str, help="Fetch news for specific tickers (comma-separated, e.g., MGC,SPY,XLE)")
    parser.add_argument("--include-quiver", action="store_true", help="Include congressional trading data when using --watchlist-news")
    args = parser.parse_args()
    
    # Validate argument combinations
    if args.watchlist_news and args.include_quiver and not args.watchlist_news:
        parser.error("--include-quiver requires --watchlist-news")
    
    if args.schedule:
        run_scheduler()
    elif args.cme:
        run_cme_only()
    elif args.watchlist_news:
        # Parse comma-separated tickers
        tickers = [ticker.strip() for ticker in args.watchlist_news.split(',') if ticker.strip()]
        if not tickers:
            parser.error("--watchlist-news requires at least one ticker symbol")
        run_watchlist_news(tickers, send_email=args.send, include_quiver=args.include_quiver)
    else:
        main(send_email=args.send) 