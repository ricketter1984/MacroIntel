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
from perplexity_macro_agent import PerplexityMacroAgent

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
    
    def __init__(self, debug_mode: bool = False):
        """Initialize the swarm with all agents."""
        self.debug_mode = debug_mode
        self.agents = {
            "summarizer": SummarizerAgent(),
            "chart_generator": ChartGeneratorAgent(),
            "playbook_strategist": PlaybookStrategistAgent(),
            "email_dispatcher": EmailDispatcherAgent(),
            "perplexity_macro": PerplexityMacroAgent()
        }
        os.makedirs("logs", exist_ok=True)
        os.makedirs("output", exist_ok=True)
        logger.info("🤖 MacroIntel Swarm initialized - New Default Execution Engine")
        if self.debug_mode:
            print("🔍 DEBUG MODE ENABLED - Enhanced diagnostic output active")
    
    def extract_dominant_keywords(self, summarizer_result: Dict[str, Any]) -> list:
        """Extract dominant keywords from Perplexity summaries and tags."""
        try:
            dominant_keywords = []
            articles = summarizer_result.get('articles', [])
            
            # Method 1: Extract tags from Perplexity articles
            perplexity_articles = [a for a in articles if a.get('source') == 'perplexity']
            for article in perplexity_articles:
                tags = article.get('tags', [])
                if tags:
                    dominant_keywords.extend(tags)
            
            # Method 2: Extract from tags_summary if available
            if not dominant_keywords:
                tags_summary = summarizer_result.get('tags_summary', [])
                if tags_summary:
                    dominant_keywords.extend(tags_summary)
                    if self.debug_mode:
                        print(f"🔍 DEBUG: Using tags_summary: {tags_summary}")
            
            # Method 3: Fallback to top keywords from all summaries
            if not dominant_keywords:
                all_summaries = []
                for article in articles:
                    summary = article.get('summary', '')
                    if summary:
                        all_summaries.append(summary)
                
                if all_summaries:
                    # Extract potential keywords from summaries
                    import re
                    keywords = []
                    for summary in all_summaries:
                        # Look for common macro keywords
                        macro_keywords = ['oil', 'inflation', 'ai', 'stocks', 'rates', 'fed', 'middle east', 'china', 'europe', 'gdp', 'employment', 'earnings']
                        for keyword in macro_keywords:
                            if keyword.lower() in summary.lower():
                                keywords.append(keyword)
                    
                    # Take top 3 most frequent keywords
                    from collections import Counter
                    keyword_counts = Counter(keywords)
                    top_keywords = [kw for kw, count in keyword_counts.most_common(3)]
                    dominant_keywords.extend(top_keywords)
                    
                    if self.debug_mode:
                        print(f"🔍 DEBUG: Extracted keywords from summaries: {top_keywords}")
            
            # Normalize to lowercase and filter duplicates
            normalized_keywords = []
            seen_keywords = set()
            
            for keyword in dominant_keywords:
                normalized = keyword.lower().strip()
                if normalized and normalized not in seen_keywords:
                    normalized_keywords.append(normalized)
                    seen_keywords.add(normalized)
            
            # Ensure we have at least some keywords
            if not normalized_keywords:
                normalized_keywords = ['general']  # Default fallback
            
            logger.info(f"🔍 Extracted {len(normalized_keywords)} dominant keywords: {normalized_keywords}")
            
            if self.debug_mode:
                print(f"🔍 DEBUG: Loaded dominant keywords: {normalized_keywords}")
                print(f"🔍 DEBUG: Total articles processed: {len(articles)}")
                print(f"🔍 DEBUG: Perplexity articles found: {len(perplexity_articles)}")
                print(f"🔍 DEBUG: Tags summary available: {'Yes' if summarizer_result.get('tags_summary') else 'No'}")
            
            return normalized_keywords
            
        except Exception as e:
            logger.error(f"❌ Error extracting dominant keywords: {str(e)}")
            if self.debug_mode:
                print(f"🔍 DEBUG: Keyword extraction failed, using default: ['general']")
            return ['general']  # Safe fallback

    def execute_swarm(self) -> Dict[str, Any]:
        """Execute the complete swarm workflow - replaces run_daily_analysis()."""
        logger.info("🚀 Starting MacroIntel Swarm execution...")
        
        execution_start = datetime.now()
        
        try:
            # Step 1: Summarizer Agent - News Collection & Summarization (includes Perplexity)
            logger.info("📰 Executing Summarizer Agent...")
            summarizer_input = {"debug_mode": self.debug_mode} if self.debug_mode else None
            summarizer_result = self.agents["summarizer"].run()
            logger.info(f"✅ Summarizer completed: {summarizer_result.get('total_count', 0)} articles from {summarizer_result.get('sources_processed', [])}")
            
            if self.debug_mode:
                print(f"🔍 DEBUG: Summarizer completed with {summarizer_result.get('total_count', 0)} articles")
                sources = summarizer_result.get('sources_processed', [])
                print(f"🔍 DEBUG: Sources processed: {sources}")
                articles = summarizer_result.get('articles', [])
                for source in set(a.get('source', 'unknown') for a in articles):
                    count = len([a for a in articles if a.get('source') == source])
                    print(f"🔍 DEBUG: {source}: {count} articles")
            
            # 🔍 Extract dominant keywords from Perplexity summaries
            logger.info("🔍 Extracting dominant keywords from Perplexity summaries...")
            dominant_keywords = self.extract_dominant_keywords(summarizer_result)
            
            # Step 2: Playbook Strategist Agent - Market Analysis & Strategy Selection
            logger.info("📘 Executing Playbook Strategist Agent...")
            strategy_input_data = {
                "dominant_keywords": dominant_keywords,
                "vix_score": 20,  # Default value
                "fear_greed_score": 50,  # Default value
                "debug_mode": self.debug_mode
            }
            strategy_result = self.agents["playbook_strategist"].run(strategy_input_data)
            
            # Replace Tier logic - only use Tier 1 and Tier 2
            strategy_tier = strategy_result.get('strategy_tier', 'Tier 2')
            if strategy_tier not in ["Tier 1", "Tier 2"]:
                strategy_tier = "Tier 2"
                strategy_result['strategy_tier'] = strategy_tier
                logger.info(f"🔄 Strategy tier adjusted to: {strategy_tier}")
            
            if self.debug_mode:
                print(f"🔍 DEBUG: Strategy tier selected: {strategy_tier}")
                print(f"🔍 DEBUG: Market regime: {strategy_result.get('market_regime', 'Unknown')}")
                print(f"🔍 DEBUG: Regime score: {strategy_result.get('regime_score', 'Unknown')}")
                print(f"🔍 DEBUG: VIX score: {strategy_result.get('vix_score', 'Unknown')}")
                print(f"🔍 DEBUG: Fear & Greed score: {strategy_result.get('fear_greed_score', 'Unknown')}")
            
            market_regime = strategy_result.get('market_regime', 'Unknown')
            strategy_count = len(strategy_result.get('selected_strategies', []))
            logger.info(f"✅ Playbook Strategist completed: {market_regime} regime with {strategy_count} strategies")
            
            # Step 3: Chart Generator Agent - Market Visualizations with dominant_keywords
            logger.info("📈 Executing Chart Generator Agent...")
            chart_input_data = {
                "strategy_tier": strategy_tier,
                "regime_score": strategy_result.get("regime_score", 50),
                "vix_score": strategy_result.get("vix_score", 20),
                "fear_greed_score": strategy_result.get("fear_greed_score", 50),
                "dominant_keywords": dominant_keywords,
                "tags": dominant_keywords,
                "debug_mode": self.debug_mode
            }
            chart_result = self.agents["chart_generator"].run(chart_input_data)
            successful_charts = [c for c in chart_result.get('charts_generated', []) if c.get('success', False)]
            logger.info(f"✅ Chart Generator completed: {len(successful_charts)} charts generated")
            
            if self.debug_mode:
                print(f"🔍 DEBUG: Charts generated: {len(successful_charts)}")
                print(f"🔍 DEBUG: Charts failed: {len(chart_result.get('charts_failed', []))}")
                for chart in successful_charts:
                    print(f"🔍 DEBUG: Chart type: {chart.get('chart_type', 'Unknown')}")
                    print(f"🔍 DEBUG: Chart file: {chart.get('file_path', 'Unknown')}")
                    if chart.get('ai_explanation'):
                        print(f"🔍 DEBUG: Chart explanation: {chart.get('ai_explanation')}")
                    if chart.get('primary_instrument'):
                        print(f"🔍 DEBUG: Primary asset chosen: {chart.get('primary_instrument')}")
                    if chart.get('secondary_instrument'):
                        print(f"🔍 DEBUG: Secondary asset chosen: {chart.get('secondary_instrument')}")
            
            # Step 4: Email Dispatcher Agent - Report Generation & Distribution
            logger.info("📧 Executing Email Dispatcher Agent...")
            email_input = {
                "news_summary": summarizer_result,
                "charts": chart_result,
                "strategy_analysis": strategy_result,
                "market_data": {
                    "fear_greed": chart_result.get("market_conditions", {}),
                    "strategies": strategy_result,
                    "dominant_keywords": dominant_keywords,
                    "execution_time": execution_start.isoformat()
                },
                "debug_mode": self.debug_mode
            }
            email_result = self.agents["email_dispatcher"].run(email_input)
            
            if email_result.get("email_sent", False):
                recipients = email_result.get("recipients", [])
                logger.info(f"✅ Email Dispatcher completed: Email sent successfully to {len(recipients)} recipients")
                
                if self.debug_mode:
                    print(f"🔍 DEBUG: Email sent successfully")
                    print(f"🔍 DEBUG: Email recipients: {recipients}")
                    print(f"🔍 DEBUG: Email subject: {email_result.get('subject', 'Unknown')}")
            else:
                logger.warning("⚠️ Email Dispatcher completed: Email sending failed")
                if self.debug_mode:
                    print(f"🔍 DEBUG: Email sending failed: {email_result.get('error', 'Unknown error')}")
            
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
                    "recipients_count": len(email_result.get('recipients', [])),
                    "dominant_keywords": dominant_keywords
                }
            }
            
            logger.info("🎉 MacroIntel Swarm execution completed successfully!")
            logger.info(f"⏱️ Total execution time: {execution_duration}")
            
            if self.debug_mode:
                print(f"🔍 DEBUG: Total execution time: {execution_duration}")
                print(f"🔍 DEBUG: Final summary:")
                print(f"   - Articles processed: {results['summary']['articles_processed']}")
                print(f"   - Charts generated: {results['summary']['charts_generated']}")
                print(f"   - Market regime: {results['summary']['market_regime']}")
                print(f"   - Strategies selected: {results['summary']['strategies_selected']}")
                print(f"   - Email sent: {results['summary']['email_sent']}")
                print(f"   - Recipients: {results['summary']['recipients_count']}")
                print(f"   - Dominant keywords: {results['summary']['dominant_keywords']}")
            
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
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with enhanced diagnostic output')
    args = parser.parse_args()
    
    if args.schedule:
        logger.info("🕐 Starting MacroIntel Swarm in scheduled mode...")
        schedule_daily_run()
    elif args.now:
        logger.info("⚡ Executing MacroIntel Swarm immediately...")
        swarm = MacroIntelSwarm(debug_mode=args.debug)
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
            if args.debug:
                print(f"🔍 Dominant Keywords: {summary.get('dominant_keywords', [])}")
            print("="*60)
        else:
            print(f"❌ Swarm execution failed: {results.get('error', 'Unknown error')}")
        
        return results
    else:
        # Default: execute immediately
        logger.info("⚡ Executing MacroIntel Swarm immediately...")
        swarm = MacroIntelSwarm(debug_mode=args.debug)
        results = swarm.execute_swarm()
        return results

if __name__ == "__main__":
    main() 