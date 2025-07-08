#!/usr/bin/env python3
"""
API Explorer Interface
Handles CLI and interactive input for the API Explorer.
"""

import json
import logging
from typing import Dict, Any, Optional
from .api_explorer_engine import APIExplorerEngine

logger = logging.getLogger(__name__)

class APIExplorerInterface:
    """Interface for CLI and interactive API exploration"""
    
    def __init__(self, engine: APIExplorerEngine):
        self.engine = engine
    
    def display_apis(self) -> None:
        """Display all loaded APIs"""
        apis = self.engine.list_apis()
        print("\n📋 Loaded APIs:")
        for api in apis:
            summary = self.engine.get_api_summary(api)
            print(f"  • {api} (v{summary.get('version', 'unknown')}) - {summary.get('total_endpoints', 0)} endpoints")
    
    def display_api_summary(self, api_name: str) -> None:
        """Display summary for a specific API"""
        summary = self.engine.get_api_summary(api_name)
        if summary:
            print(f"\n📊 API Summary: {api_name}")
            print(json.dumps(summary, indent=2))
        else:
            print(f"❌ API '{api_name}' not found")
    
    def display_search_results(self, results: Dict[str, Any]) -> None:
        """Display search results in a formatted way"""
        print(f"\n🔍 Question: {results['question']}")
        print(f"📊 Found {results['total_results']} matching endpoints\n")
        
        if results['results']:
            for i, result in enumerate(results['results'], 1):
                print(f"{i}. {result['method']} {result['endpoint']}")
                print(f"   API: {result['api_name']}")
                print(f"   Description: {result['description']}")
                if result['required_params']:
                    print(f"   Required params: {', '.join(result['required_params'])}")
                print(f"   Score: {result['score']:.1f}")
                print()
        else:
            print("❌ No matching endpoints found")
    
    def display_json_response(self, results: Dict[str, Any]) -> None:
        """Display results as JSON"""
        print("📄 JSON Response:")
        print(json.dumps(results, indent=2))
    
    def interactive_mode(self) -> None:
        """Run interactive mode for API exploration"""
        print("🤖 API Explorer Agent - Interactive Mode")
        print("Type 'quit' to exit, 'help' for commands\n")
        
        while True:
            try:
                question = input("❓ Ask about API endpoints: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    break
                elif question.lower() == 'help':
                    self._show_help()
                    continue
                elif question.lower() == 'list apis':
                    self.display_apis()
                    print()
                    continue
                elif not question:
                    continue
                
                results = self.engine.ask_question(question)
                self.display_search_results(results)
                print("-" * 50)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    def _show_help(self) -> None:
        """Show help information"""
        print("\n📖 Available commands:")
        print("  • Ask questions like: 'Which endpoint gets crypto prices?'")
        print("  • 'list apis' - Show all loaded APIs")
        print("  • 'quit' - Exit the program")
        print()
    
    def process_query(self, query: str, show_json: bool = False) -> Dict[str, Any]:
        """Process a single query and display results"""
        results = self.engine.ask_question(query)
        
        # Display results
        self.display_search_results(results)
        
        # Show JSON if requested
        if show_json:
            self.display_json_response(results)
        
        return results
    
    def list_apis_command(self) -> None:
        """Handle the list-apis command"""
        self.display_apis()
    
    def api_summary_command(self, api_name: str) -> None:
        """Handle the api-summary command"""
        self.display_api_summary(api_name) 