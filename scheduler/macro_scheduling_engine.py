#!/usr/bin/env python3
"""
Macro Scheduling Engine for MacroIntel Swarm
Handles time-aware and condition-aware scheduling with market event detection.
"""

import os
import sys
import json
import logging
import argparse
import subprocess
import schedule
import time
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fear_greed_dashboard import FearGreedDashboard
from event_tracker.econ_event_tracker import EconEventTracker
from utils.api_clients import init_env

# Load .env if present
load_dotenv(dotenv_path="config/.env")
init_env()

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MacroSchedulingEngine:
    """Engine for time-aware and condition-aware scheduling with market event detection."""
    
    def __init__(self):
        self.fear_dashboard = FearGreedDashboard()
        self.event_tracker = EconEventTracker()
        self.scheduled_jobs = []
        self.is_running = False
        logger.info("⏰ Macro Scheduling Engine initialized")
    
    def parse_condition(self, condition_str: str) -> Dict[str, Any]:
        try:
            pattern = r'(\w+)\s*([<>=!]+)\s*(\d+(?:\.\d+)?)'
            match = re.match(pattern, condition_str.strip())
            if match:
                metric, operator, value = match.groups()
                return {
                    "metric": metric.lower(),
                    "operator": operator,
                    "value": float(value),
                    "original": condition_str
                }
            else:
                logger.warning(f"⚠️ Could not parse condition: {condition_str}")
                return None
        except Exception as e:
            logger.error(f"❌ Error parsing condition '{condition_str}': {str(e)}")
            return None
    
    def evaluate_condition(self, condition: Dict[str, Any], fear_score: float) -> bool:
        try:
            if not condition:
                return True
            metric = condition.get("metric")
            operator = condition.get("operator")
            value = condition.get("value")
            if metric == "fear":
                current_value = fear_score
            else:
                logger.warning(f"⚠️ Unknown metric: {metric}")
                return True
            if value is None:
                logger.warning("⚠️ Invalid condition value")
                return True
            if operator == "<":
                result = current_value < value
            elif operator == "<=":
                result = current_value <= value
            elif operator == ">":
                result = current_value > value
            elif operator == ">=":
                result = current_value >= value
            elif operator == "==" or operator == "=":
                result = current_value == value
            elif operator == "!=":
                result = current_value != value
            else:
                logger.warning(f"⚠️ Unknown operator: {operator}")
                return True
            logger.info(f"🔍 Condition evaluation: {current_value} {operator} {value} = {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Error evaluating condition: {str(e)}")
            return True
    
    def check_red_folder_events(self) -> List[Dict[str, Any]]:
        try:
            logger.info("🔴 Checking for red folder events...")
            events = self.event_tracker.get_upcoming_events(days=7)
            red_folder_events = []
            for event in events:
                if event.get("impact") == "High" or event.get("importance") == "High":
                    red_folder_events.append(event)
            logger.info(f"🔴 Found {len(red_folder_events)} red folder events")
            return red_folder_events
        except Exception as e:
            logger.error(f"❌ Error checking red folder events: {str(e)}")
            return []
    
    def should_skip_execution(self, skip_on_red_folders: bool = False) -> bool:
        if not skip_on_red_folders:
            return False
        red_folder_events = self.check_red_folder_events()
        if red_folder_events:
            logger.warning(f"⚠️ Skipping execution due to {len(red_folder_events)} red folder events")
            for event in red_folder_events[:3]:
                logger.warning(f"  🔴 {event.get('name', 'Unknown')} - {event.get('date', 'Unknown')}")
            return True
        return False
    
    def get_current_fear_score(self) -> float:
        try:
            fear_score, fear_rating = self.fear_dashboard.get_fear_greed_index()
            logger.info(f"😨 Current Fear & Greed Index: {fear_score} ({fear_rating})")
            return fear_score
        except Exception as e:
            logger.error(f"❌ Error getting fear score: {str(e)}")
            return 50.0
    
    def trigger_swarm_execution(self) -> bool:
        try:
            logger.info("🚀 Triggering full agent swarm execution...")
            result = subprocess.run(
                [sys.executable, "swarm_console.py", "full"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                logger.info("✅ Swarm execution completed successfully")
                return True
            else:
                logger.error(f"❌ Swarm execution failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error("❌ Swarm execution timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Error triggering swarm execution: {str(e)}")
            return False
    
    def scheduled_job(self, condition: Optional[Dict[str, Any]] = None, skip_on_red_folders: bool = False) -> None:
        try:
            logger.info("⏰ Scheduled job triggered")
            if self.should_skip_execution(skip_on_red_folders):
                logger.info("⏭️ Skipping execution due to red folder events")
                return
            fear_score = self.get_current_fear_score()
            if condition:
                condition_met = self.evaluate_condition(condition, fear_score)
                if not condition_met:
                    logger.info(f"⏭️ Skipping execution - condition not met: {condition['original']}")
                    return
            success = self.trigger_swarm_execution()
            if success:
                logger.info("✅ Scheduled job completed successfully")
            else:
                logger.error("❌ Scheduled job failed")
        except Exception as e:
            logger.error(f"❌ Error in scheduled job: {str(e)}")
    
    def schedule_job(self, time_str: Optional[str] = None, condition: Optional[str] = None, skip_on_red_folders: bool = False) -> bool:
        try:
            parsed_condition = None
            if condition:
                parsed_condition = self.parse_condition(condition)
                if not parsed_condition:
                    logger.error(f"❌ Failed to parse condition: {condition}")
                    return False
            def job_func():
                self.scheduled_job(parsed_condition, skip_on_red_folders)
            if time_str:
                logger.info(f"⏰ Scheduling job for {time_str}")
                schedule.every().day.at(time_str).do(job_func)
                if condition:
                    logger.info(f"  📋 With condition: {condition}")
                if skip_on_red_folders:
                    logger.info(f"  🔴 Skip on red folders: enabled")
            else:
                logger.info(f"🔍 Scheduling condition-based job: {condition}")
                schedule.every(15).minutes.do(job_func)
            self.scheduled_jobs.append({
                "time": time_str,
                "condition": condition,
                "skip_on_red_folders": skip_on_red_folders,
                "created_at": datetime.now().isoformat()
            })
            logger.info("✅ Job scheduled successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Error scheduling job: {str(e)}")
            return False
    
    def run_scheduler(self, test_mode: bool = False) -> None:
        try:
            logger.info("🚀 Starting Macro Scheduling Engine...")
            self.is_running = True
            if test_mode:
                logger.info("🧪 Running in test mode - executing once")
                self.scheduled_job()
                return
            logger.info("⏰ Scheduler running - press Ctrl+C to stop")
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("⏹️ Scheduler stopped by user")
        except Exception as e:
            logger.error(f"❌ Error in scheduler loop: {str(e)}")
        finally:
            self.is_running = False
    
    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        return self.scheduled_jobs.copy()
    
    def clear_scheduled_jobs(self) -> None:
        schedule.clear()
        self.scheduled_jobs.clear()
        logger.info("🗑️ All scheduled jobs cleared")

def main():
    parser = argparse.ArgumentParser(
        description="Macro Scheduling Engine - Time-aware and condition-aware scheduling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python macro_scheduling_engine.py --at 07:15 --when "fear < 30"
  python macro_scheduling_engine.py --when "fear > 70" --skip-on red_folders
  python macro_scheduling_engine.py --at 09:00 --test
        """
    )
    parser.add_argument("--at", type=str, help="Specific time to run (e.g., '07:15', '09:00')")
    parser.add_argument("--when", type=str, help="Condition to trigger execution (e.g., 'fear < 30', 'fear > 70')")
    parser.add_argument("--skip-on", type=str, choices=["red_folders"], help="Skip execution on certain conditions")
    parser.add_argument("--test", action="store_true", help="Run in test mode (execute once and exit)")
    parser.add_argument("--list", action="store_true", help="List currently scheduled jobs")
    parser.add_argument("--clear", action="store_true", help="Clear all scheduled jobs")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    scheduler = MacroSchedulingEngine()
    if args.list:
        jobs = scheduler.get_scheduled_jobs()
        if jobs:
            print("\n📋 Scheduled Jobs:")
            for i, job in enumerate(jobs, 1):
                print(f"  {i}. Time: {job['time'] or 'Condition-based'}")
                print(f"     Condition: {job['condition'] or 'None'}")
                print(f"     Skip on red folders: {job['skip_on_red_folders']}")
                print(f"     Created: {job['created_at']}")
        else:
            print("📋 No scheduled jobs")
        return
    if args.clear:
        scheduler.clear_scheduled_jobs()
        print("🗑️ All scheduled jobs cleared")
        return
    if not args.at and not args.when:
        print("❌ Error: Must specify either --at (time) or --when (condition)")
        return
    skip_on_red_folders = args.skip_on == "red_folders"
    success = scheduler.schedule_job(
        time_str=args.at,
        condition=args.when,
        skip_on_red_folders=skip_on_red_folders
    )
    if not success:
        print("❌ Failed to schedule job")
        return
    scheduler.run_scheduler(test_mode=args.test)

if __name__ == "__main__":
    main()
