#!/usr/bin/env python3
"""
MacroIntel Swarm Orchestrator - Default Morning Execution Engine
Coordinates the execution of all agents in the MacroIntel swarm.
Replaces daily_intel_engine.py as the primary market intelligence system.
Runs at 7:15 AM daily to provide comprehensive market insights.
"""

import os
import sys
import json
import logging
import schedule
import time
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from config/.env
load_dotenv(dotenv_path="config/.env")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from summarizer_agent import SummarizerAgent
from chart_generator_agent import ChartGeneratorAgent
from playbook_strategist_agent import PlaybookStrategistAgent
from email_dispatcher_agent import EmailDispatcherAgent

# Create logs directory first
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/swarm_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MacroIntelSwarm:
    """Main orchestrator for the MacroIntel agent swarm - replaces daily_intel_engine.py."""
    
    def __init__(self):
        """Initialize the swarm with all agents."""
        self.agents = {
            "summarizer": SummarizerAgent(),
            "chart_generator": ChartGeneratorAgent(),
            "playbook_strategist": PlaybookStrategistAgent(),
            "email_dispatcher": EmailDispatcherAgent()
        }
        os.makedirs("logs", exist_ok=True)
        os.makedirs("output", exist_ok=True)
        logger.info("🤖 MacroIntel Swarm initialized - New Default Execution Engine")
    
    def execute_swarm(self) -> Dict[str, Any]:
        """Execute the complete swarm workflow - replaces run_daily_analysis()."""
        logger.info("🚀 Starting MacroIntel Swarm execution...")
        
        execution_start = datetime.now()
        
        try:
            # Step 1: Summarizer Agent - News Collection & Summarization
            logger.info("📰 Executing Summarizer Agent...")
            summarizer_result = self.agents["summarizer"].run()
            logger.info(f"✅ Summarizer completed: {summarizer_result.get('total_count', 0)} articles from {summarizer_result.get('sources_processed', [])}")
            
            # Step 2: Chart Generator Agent - Market Visualizations
            logger.info("📈 Executing Chart Generator Agent...")
            chart_result = self.agents["chart_generator"].run()
            successful_charts = [c for c in chart_result.get('charts_generated', []) if c.get('success', False)]
            logger.info(f"✅ Chart Generator completed: {len(successful_charts)} charts generated")
            
            # Step 3: Playbook Strategist Agent - Market Analysis & Strategy Selection
            logger.info("📘 Executing Playbook Strategist Agent...")
            strategy_result = self.agents["playbook_strategist"].run()
            market_regime = strategy_result.get('market_regime', 'Unknown')
            strategy_count = len(strategy_result.get('selected_strategies', []))
            logger.info(f"✅ Playbook Strategist completed: {market_regime} regime with {strategy_count} strategies")
            
            # Step 4: Email Dispatcher Agent - Report Generation & Distribution
            logger.info("📧 Executing Email Dispatcher Agent...")
            email_input = {
                "news_summary": summarizer_result,
                "charts": chart_result,
                "strategy_analysis": strategy_result,
                "market_data": {
                    "fear_greed": chart_result.get("market_conditions", {}),
                    "strategies": strategy_result,
                    "execution_time": execution_start.isoformat()
                }
            }
            email_result = self.agents["email_dispatcher"].run(email_input)
            
            if email_result.get("email_sent", False):
                recipients = email_result.get("recipients", [])
                logger.info(f"✅ Email Dispatcher completed: Email sent successfully to {len(recipients)} recipients")
            else:
                logger.warning("⚠️ Email Dispatcher completed: Email sending failed")
            
            # Calculate execution time
            execution_end = datetime.now()
            execution_duration = execution_end - execution_start
            
            # Compile comprehensive results
            results = {
                "status": "success",
                "execution_time": str(execution_duration),
                "start_time": execution_start.isoformat(),
                "end_time": execution_end.isoformat(),
                "agents": {
                    "summarizer": summarizer_result,
                    "chart_generator": chart_result,
                    "playbook_strategist": strategy_result,
                    "email_dispatcher": email_result
                },
                "summary": {
                    "articles_processed": summarizer_result.get('total_count', 0),
                    "charts_generated": len(successful_charts),
                    "market_regime": market_regime,
                    "strategies_selected": strategy_count,
                    "email_sent": email_result.get('email_sent', False),
                    "recipients_count": len(email_result.get('recipients', []))
                }
            }
            
            logger.info("🎉 MacroIntel Swarm execution completed successfully!")
            logger.info(f"⏱️ Total execution time: {execution_duration}")
            
            # Save execution log
            self._save_execution_log(results)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Swarm execution failed: {str(e)}")
            error_result = {
                "status": "failed",
                "error": str(e),
                "execution_time": str(datetime.now() - execution_start),
                "start_time": execution_start.isoformat(),
                "end_time": datetime.now().isoformat()
            }
            self._save_execution_log(error_result)
            return error_result
    
    def _save_execution_log(self, results: Dict[str, Any]) -> None:
        """Save execution results to a JSON log file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"swarm_execution_{timestamp}.json"
            log_path = os.path.join("logs", log_filename)
            
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📝 Execution log saved to: {log_path}")
            
        except Exception as e:
            logger.error(f"❌ Error saving execution log: {str(e)}")

def schedule_daily_run():
    """Schedule the swarm to run daily at 7:15 AM - replaces schedule_daily_run() from daily_intel_engine.py."""
    def daily_job():
        logger.info("⏰ Scheduled daily swarm execution starting...")
        swarm = MacroIntelSwarm()
        results = swarm.execute_swarm()
        
        if results.get("status") == "success":
            logger.info("✅ Scheduled swarm execution completed successfully")
        else:
            logger.error("❌ Scheduled swarm execution failed")
    
    # Schedule daily execution at 7:15 AM
    schedule.every().day.at("07:15").do(daily_job)
    logger.info("📅 Swarm scheduled to run daily at 7:15 AM")
    
    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)

def main():
    """Main function for running the swarm - new default entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MacroIntel Swarm Orchestrator")
    parser.add_argument('--schedule', action='store_true', help='Run in scheduled mode (daily at 7:15 AM)')
    parser.add_argument('--now', action='store_true', help='Execute immediately')
    args = parser.parse_args()
    
    if args.schedule:
        logger.info("🕐 Starting MacroIntel Swarm in scheduled mode...")
        schedule_daily_run()
    elif args.now:
        logger.info("⚡ Executing MacroIntel Swarm immediately...")
        swarm = MacroIntelSwarm()
        results = swarm.execute_swarm()
        
        # Print summary
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
        else:
            print(f"❌ Swarm execution failed: {results.get('error', 'Unknown error')}")
        
        return results
    else:
        # Default: execute immediately
        logger.info("⚡ Executing MacroIntel Swarm immediately...")
        swarm = MacroIntelSwarm()
        results = swarm.execute_swarm()
        return results

if __name__ == "__main__":
    main() 