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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    # Step 3: Generate all visualizations
    logging.info("📈 Step 3: Generating visualizations...")
    viz_engine.generate_all_visualizations(regime_data)
    logging.info("📈 Visualizations completed")

    # Step 4: Send daily report if requested
    if send_email:
        logging.info("📧 Step 4: Sending email report...")
        # Generate email content
        html_content = generate_email_content(articles)
        send_daily_report(html_content)
        logging.info("📧 Email report sent")
    else:
        logging.info("📧 Step 4: Email report skipped (use --email flag to send)")

    logging.info("✅ MacroIntel automation completed")

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
    parser.add_argument("--email", action="store_true", help="Send the email report")
    parser.add_argument("--schedule", action="store_true", help="Run in scheduled mode (twice daily)")
    args = parser.parse_args()
    
    if args.schedule:
        run_scheduler()
    else:
        main(send_email=args.email) 