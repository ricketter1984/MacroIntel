#!/usr/bin/env python3
"""
MacroIntel Orchestrator
Integrates various MacroIntel components including the API Explorer Agent
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from agents.api_explorer_agent import APIExplorerAgent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/orchestrator.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class MacroIntelOrchestrator:
    """Main orchestrator for MacroIntel operations"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.api_explorer = None
        
        logger.info("Initialized MacroIntel Orchestrator")
    
    def setup_api_explorer(self, openai_api_key: Optional[str] = None):
        """Initialize the API Explorer agent"""
        try:
            self.api_explorer = APIExplorerAgent(
                schemas_dir="data/api_schemas",
                openai_api_key=None  # OpenAI support disabled
            )
            self.api_explorer.load_schemas()
            logger.info("API Explorer agent initialized successfully")
            logger.info("✅ OpenAI support disabled (API key removed from environment)")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize API Explorer agent: {str(e)}")
            return False
    
    def query_api(self, query: str, openai_api_key: Optional[str] = None) -> Dict[str, Any]:
        """Query the API Explorer agent with natural language"""
        logger.info(f"Processing API query: {query}")
        
        # Initialize API explorer if not already done
        if not self.api_explorer:
            if not self.setup_api_explorer(None):  # OpenAI support disabled
                return {
                    "error": "Failed to initialize API Explorer agent",
                    "query": query,
                    "timestamp": datetime.now().isoformat()
                }
        
        try:
            # Get results from API explorer
            results = self.api_explorer.ask_question(query)
            
            # Save results to output file
            output_file = self.output_dir / "api_query_result.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"API query results saved to: {output_file}")
            
            return results
            
        except Exception as e:
            error_result = {
                "error": str(e),
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"API query failed: {str(e)}")
            return error_result
    
    def run_daily_intel(self, **kwargs):
        """Run the daily intelligence gathering workflow"""
        logger.info("Starting daily intelligence workflow")
        
        try:
            # Import and run the daily intel engine
            from daily_intel_engine import run_daily_intel_workflow
            result = run_daily_intel_workflow(**kwargs)
            
            logger.info("Daily intelligence workflow completed")
            return result
            
        except Exception as e:
            logger.error(f"Daily intelligence workflow failed: {str(e)}")
            return {"error": str(e)}
    
    def run_report_generation(self, **kwargs):
        """Run the report generation workflow"""
        logger.info("Starting report generation workflow")
        
        try:
            # Import and run the report generation
            from core.email_report import generate_email_content
            result = generate_email_content(**kwargs)
            
            logger.info("Report generation workflow completed")
            return result
            
        except Exception as e:
            logger.error(f"Report generation workflow failed: {str(e)}")
            return {"error": str(e)}
    
    def run_agent_pipeline(self, **kwargs):
        """Run the multi-agent pipeline"""
        logger.info("Starting multi-agent pipeline")
        
        try:
            # Import and run the agent pipeline
            from macrointel_agents import run_agents_pipeline
            result = run_agents_pipeline(**kwargs)
            
            logger.info("Multi-agent pipeline completed")
            return result
            
        except Exception as e:
            logger.error(f"Multi-agent pipeline failed: {str(e)}")
            return {"error": str(e)}
    
    def run_full_workflow(self, **kwargs):
        """Run the complete MacroIntel workflow"""
        logger.info("Starting full MacroIntel workflow")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "workflows": {}
        }
        
        # Run daily intel
        try:
            results["workflows"]["daily_intel"] = self.run_daily_intel(**kwargs)
        except Exception as e:
            results["workflows"]["daily_intel"] = {"error": str(e)}
        
        # Run agent pipeline
        try:
            results["workflows"]["agent_pipeline"] = self.run_agent_pipeline(**kwargs)
        except Exception as e:
            results["workflows"]["agent_pipeline"] = {"error": str(e)}
        
        # Run report generation
        try:
            results["workflows"]["report_generation"] = self.run_report_generation(**kwargs)
        except Exception as e:
            results["workflows"]["report_generation"] = {"error": str(e)}
        
        # Save workflow results
        output_file = self.output_dir / "full_workflow_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Full workflow results saved to: {output_file}")
        return results

def main():
    """Main CLI interface for the orchestrator"""
    parser = argparse.ArgumentParser(description='MacroIntel Orchestrator - Manage MacroIntel workflows')
    
    # Workflow options
    parser.add_argument('--daily-intel', action='store_true', 
                       help='Run daily intelligence gathering workflow')
    parser.add_argument('--report', action='store_true',
                       help='Run report generation workflow')
    parser.add_argument('--agents', action='store_true',
                       help='Run multi-agent pipeline')
    parser.add_argument('--full-workflow', action='store_true',
                       help='Run complete MacroIntel workflow')
    
    # API Explorer options
    parser.add_argument('--query-api', type=str,
                       help='Query API schemas using natural language')
    
    # General options
    parser.add_argument('--output-dir', type=str, default='output',
                       help='Output directory for results')
    parser.add_argument('--openai-key', type=str,
                       help='OpenAI API key for enhanced features')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize orchestrator
    orchestrator = MacroIntelOrchestrator(output_dir=args.output_dir)
    
    try:
        if args.query_api:
            # Handle API query
            print(f"\n🔍 Querying API: {args.query_api}")
            results = orchestrator.query_api(args.query_api, args.openai_key)
            
            if "error" in results:
                print(f"❌ Error: {results['error']}")
                return 1
            
            print(f"\n📊 Found {results.get('total_results', 0)} matching endpoints:")
            
            for i, result in enumerate(results.get('results', []), 1):
                print(f"\n{i}. {result.get('method', '')} {result.get('endpoint', '')}")
                print(f"   API: {result.get('api_name', '')}")
                print(f"   Description: {result.get('description', '')[:100]}...")
                if result.get('required_params'):
                    print(f"   Required params: {', '.join(result['required_params'])}")
                print(f"   Score: {result.get('score', 0):.1f}")
            
            print(f"\n📄 Results saved to: output/api_query_result.json")
            
        elif args.daily_intel:
            # Run daily intel workflow
            print("\n📊 Running Daily Intelligence Workflow...")
            results = orchestrator.run_daily_intel()
            
            if "error" in results:
                print(f"❌ Error: {results['error']}")
                return 1
            
            print("✅ Daily Intelligence Workflow completed successfully")
            
        elif args.report:
            # Run report generation
            print("\n📋 Running Report Generation...")
            results = orchestrator.run_report_generation()
            
            if "error" in results:
                print(f"❌ Error: {results['error']}")
                return 1
            
            print("✅ Report Generation completed successfully")
            
        elif args.agents:
            # Run agent pipeline
            print("\n🤖 Running Multi-Agent Pipeline...")
            results = orchestrator.run_agent_pipeline()
            
            if "error" in results:
                print(f"❌ Error: {results['error']}")
                return 1
            
            print("✅ Multi-Agent Pipeline completed successfully")
            
        elif args.full_workflow:
            # Run full workflow
            print("\n🚀 Running Full MacroIntel Workflow...")
            results = orchestrator.run_full_workflow()
            
            print("✅ Full MacroIntel Workflow completed")
            print(f"📄 Results saved to: {args.output_dir}/full_workflow_result.json")
            
        else:
            # Show help if no action specified
            print("\n🤖 MacroIntel Orchestrator")
            print("Available workflows:")
            print("  --daily-intel     Run daily intelligence gathering")
            print("  --report          Run report generation")
            print("  --agents          Run multi-agent pipeline")
            print("  --full-workflow   Run complete workflow")
            print("  --query-api       Query API schemas with natural language")
            print("\nExample:")
            print("  python macrointel_automation/orchestrator.py --query-api 'Which endpoint gets crypto prices?'")
            print("  python macrointel_automation/orchestrator.py --full-workflow")
    
    except KeyboardInterrupt:
        print("\n👋 Workflow interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Orchestrator error: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 