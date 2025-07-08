#!/usr/bin/env python3
"""
Test script for the MacroIntel scheduler
"""

import sys
import os
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_job():
    """Test job function"""
    print(f"🧪 Test job executed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def test_scheduler():
    """Test the scheduler functionality"""
    print("🧪 Testing MacroIntel Scheduler...")
    
    # Create scheduler
    scheduler = BlockingScheduler()
    
    # Add a test job that runs in 10 seconds
    from datetime import datetime, timedelta
    test_time = datetime.now() + timedelta(seconds=10)
    
    scheduler.add_job(
        func=test_job,
        trigger='date',
        run_date=test_time,
        id='test_job',
        name='Test Job',
        replace_existing=True
    )
    
    print(f"⏰ Test job scheduled for: {test_time}")
    print("🔄 Starting scheduler (will run for ~15 seconds)...")
    
    try:
        # Start the scheduler
        scheduler.start()
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
        scheduler.shutdown()
    
    print("✅ Scheduler test completed")

if __name__ == "__main__":
    test_scheduler() 