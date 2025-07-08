#!/usr/bin/env python3
"""
API Explorer Agent
CLI runner for the modular API Explorer system.
"""

import os
import argparse
import logging
from typing import Optional
from openai import OpenAI

# Import the modular components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.api_explorer.api_explorer_engine import APIExplorerEngine
from agents.api_explorer.api_explorer_interface import APIExplorerInterface
from agents.api_explorer.api_explorer_prompt import APIExplorerPrompt

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIExplorerAgent:
    """Main API Explorer Agent that coordinates all components"""
    
    def __init__(self, schemas_dir: str = "data/api_schemas", openai_api_key: Optional[str] = None):
        # Initialize OpenAI client if API key provided
        self.client: Optional[OpenAI] = None
        if openai_api_key:
            self.client = OpenAI(api_key=openai_api_key)
        else:
            # Try to get from environment
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.client = OpenAI(api_key=api_key)
            else:
                logger.warning("No OpenAI API key provided. Some features may be limited.")
        
        # Initialize components
        self.engine = APIExplorerEngine(schemas_dir)
        self.prompt = APIExplorerPrompt(self.client)
        self.interface = APIExplorerInterface(self.engine)
        
        logger.info(f"Initialized API Explorer Agent")
        logger.info(f"Schemas directory: {self.engine.schemas_dir.absolute()}")
    
    def load_schemas(self) -> dict:
        """Load all API schemas"""
        return self.engine.load_schemas()
    
    def search_endpoints(self, query: str, max_results: int = 5) -> list:
        """Search endpoints using natural language query"""
        # Use AI enhancement if available
        if self.client:
            try:
                # Get sample endpoints for context
                sample_endpoints = []
                for endpoint in self.engine.endpoint_index[:10]:
                    sample_endpoints.append({
                        'method': endpoint['method'],
                        'path': endpoint['endpoint'],
                        'description': endpoint['description'][:100]
                    })
                
                enhanced_query = self.prompt.interpret_query_with_openai(query, sample_endpoints)
                logger.info(f"OpenAI interpreted query: {enhanced_query}")
                query = enhanced_query
            except Exception as e:
                logger.warning(f"OpenAI interpretation failed: {str(e)}")
        
        return self.engine.search_endpoints(query, max_results)
    
    def ask_question(self, question: str) -> dict:
        """Main method to ask a question and get structured response"""
        return self.engine.ask_question(question)
    
    def get_endpoint_details(self, api_name: str, endpoint_path: str):
        """Get detailed information about a specific endpoint"""
        return self.engine.get_endpoint_details(api_name, endpoint_path)
    
    def list_apis(self) -> list:
        """List all loaded APIs"""
        return self.engine.list_apis()
    
    def get_api_summary(self, api_name: str) -> dict:
        """Get summary information about a specific API"""
        return self.engine.get_api_summary(api_name)

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='API Explorer Agent - Search API endpoints using natural language')
    parser.add_argument('--ask', type=str, help='Ask a question about API endpoints')
    parser.add_argument('--list-apis', action='store_true', help='List all loaded APIs')
    parser.add_argument('--api-summary', type=str, help='Get summary for specific API')
    parser.add_argument('--schemas-dir', type=str, default='data/api_schemas', 
                       help='Directory containing API schema JSON files')
    parser.add_argument('--openai-key', type=str, help='OpenAI API key (or set OPENAI_API_KEY env var)')
    parser.add_argument('--max-results', type=int, default=5, help='Maximum number of results to return')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize agent
    agent = APIExplorerAgent(
        schemas_dir=args.schemas_dir,
        openai_api_key=args.openai_key
    )
    
    try:
        if args.list_apis:
            # List all APIs
            agent.load_schemas()
            agent.interface.list_apis_command()
        
        elif args.api_summary:
            # Get API summary
            agent.load_schemas()
            agent.interface.api_summary_command(args.api_summary)
        
        elif args.ask:
            # Ask a question
            response = agent.ask_question(args.ask)
            agent.interface.process_query(args.ask, show_json=True)
        
        else:
            # Interactive mode
            agent.load_schemas()
            agent.interface.interactive_mode()
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 