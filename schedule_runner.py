#!/usr/bin/env python3
"""
MacroIntel Daily Scheduler
Runs the macro intelligence system daily at 6:45 AM Eastern Time
"""

import sys
import os
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main orchestration function
from run_macrointel import EnhancedMacroIntel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_daily_macrointel():
    """Execute the daily macro intelligence run"""
    try:
        logger.info("🚀 Starting scheduled MacroIntel run")
        print(f"🕐 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting scheduled MacroIntel run")
        
        # Create MacroIntel instance and run daily report
        macrointel = EnhancedMacroIntel()
        success = macrointel.run_daily_report()
        
        if success:
            logger.info("✅ Scheduled MacroIntel run completed successfully")
            print(f"✅ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scheduled MacroIntel run completed")
        else:
            logger.error("❌ Scheduled MacroIntel run failed")
            print(f"❌ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scheduled MacroIntel run failed")
        
    except Exception as e:
        logger.error(f"❌ Error during scheduled MacroIntel run: {str(e)}")
        print(f"❌ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error during scheduled run: {str(e)}")

def main():
    """Main scheduler function"""
    logger.info("📅 Initializing MacroIntel Daily Scheduler")
    print("📅 MacroIntel Daily Scheduler Starting...")
    print("⏰ Will run daily at 6:45 AM Eastern Time")
    print("🛑 Press Ctrl+C to stop the scheduler")
    
    # Create scheduler
    scheduler = BlockingScheduler()
    
    # Add the daily job at 6:45 AM Eastern Time
    scheduler.add_job(
        func=run_daily_macrointel,
        trigger=CronTrigger(
            hour=6,
            minute=45,
            timezone=pytz.timezone('US/Eastern')
        ),
        id='daily_macrointel',
        name='Daily MacroIntel Run',
        replace_existing=True
    )
    
    # Print next run time
    job = scheduler.get_job('daily_macrointel')
    if job:
        next_run = getattr(job, 'next_run_time', 'Calculating...')
        logger.info(f"Next scheduled run: {next_run}")
        print(f"⏭️  Next scheduled run: {next_run}")
    else:
        logger.warning("Job not found, scheduler may not be properly configured")
        print("⚠️  Job not found, scheduler may not be properly configured")
    
    try:
        # Start the scheduler
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("🛑 Scheduler stopped by user")
        print("\n🛑 Scheduler stopped by user")
        scheduler.shutdown()

if __name__ == "__main__":
    main() 