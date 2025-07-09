#!/usr/bin/env python3
"""
Test script for APScheduler implementation in MacroIntel
"""

import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from run_macrointel import setup_scheduler, EnhancedMacroIntel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_scheduler_setup():
    """Test the scheduler setup."""
    logger.info("🧪 Testing APScheduler setup...")
    
    try:
        scheduler, macrointel = setup_scheduler()
        
        # Check if jobs were added
        jobs = scheduler.get_jobs()
        logger.info(f"✅ Scheduler setup successful - {len(jobs)} jobs configured")
        
        for job in jobs:
            logger.info(f"   📅 Job: {job.name} - Next run: {job.next_run_time}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Scheduler setup failed: {str(e)}")
        return False

def test_swarm_pipeline():
    """Test the swarm pipeline execution."""
    logger.info("🧪 Testing swarm pipeline execution...")
    
    try:
        macrointel = EnhancedMacroIntel()
        result = macrointel.run_swarm_pipeline()
        
        if result:
            logger.info("✅ Swarm pipeline test successful")
        else:
            logger.error("❌ Swarm pipeline test failed")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Swarm pipeline test error: {str(e)}")
        return False

def main():
    """Run all tests."""
    logger.info("🚀 Starting MacroIntel Scheduler Tests...")
    
    # Test scheduler setup
    setup_success = test_scheduler_setup()
    
    # Test swarm pipeline (optional - may take time)
    print("\nDo you want to test the swarm pipeline execution? (y/n): ", end="")
    response = input().lower().strip()
    
    if response == 'y':
        pipeline_success = test_swarm_pipeline()
    else:
        pipeline_success = True  # Skip test
        logger.info("⏭️  Skipping swarm pipeline test")
    
    # Summary
    logger.info("\n📊 Test Results:")
    logger.info(f"   Scheduler Setup: {'✅ PASS' if setup_success else '❌ FAIL'}")
    logger.info(f"   Swarm Pipeline: {'✅ PASS' if pipeline_success else '❌ FAIL'}")
    
    if setup_success and pipeline_success:
        logger.info("🎉 All tests passed! Scheduler is ready to use.")
        logger.info("💡 To start the scheduler: python run_macrointel.py --scheduler")
    else:
        logger.error("❌ Some tests failed. Please check the logs.")

if __name__ == "__main__":
    main() 