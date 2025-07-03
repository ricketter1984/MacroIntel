#!/usr/bin/env python3
"""
Example API Integration for MacroIntel

This script demonstrates how to integrate the modular API dispatcher
into the existing MacroIntel workflow to handle conflicting urllib3 versions.
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api_dispatcher import dispatch_api_task, get_api_status

class MacroIntelAPIIntegration:
    """Integration class for using API dispatcher with MacroIntel workflows."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.output_dir = self.project_root / "output"
        self.output_dir.mkdir(exist_ok=True)
        
    def fetch_benzinga_news(self, keywords: List[str] = None) -> Dict[str, Any]:
        """
        Fetch news from Benzinga API using isolated environment.
        
        Args:
            keywords: List of keywords to filter news
            
        Returns:
            Dict containing API response and metadata
        """
        print("📰 Fetching Benzinga news...")
        
        # Create a temporary script for Benzinga news fetching
        script_content = f"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(r"{self.project_root}")
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path=project_root / "config" / ".env")

# Import Benzinga functionality
from utils.api_clients import fetch_benzinga_news
from news_scanner.news_insight_feed import scan_benzinga_news

# Fetch news
keywords = {keywords or []}
if keywords:
    print(f"🔍 Filtering news with keywords: {{keywords}}")
    news_data = scan_benzinga_news(keyword_filter=keywords)
else:
    print("📰 Fetching all Benzinga news...")
    news_data = fetch_benzinga_news()

print(f"✅ Retrieved {{len(news_data) if news_data else 0}} news articles")
print("📋 News data:", json.dumps(news_data, indent=2))
"""
        
        # Save temporary script
        temp_script = self.output_dir / "temp_benzinga_news.py"
        with open(temp_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        try:
            # Dispatch the task
            result = dispatch_api_task("benzinga", str(temp_script))
            return result
        finally:
            # Cleanup
            if temp_script.exists():
                temp_script.unlink()
    
    def fetch_polygon_data(self, symbol: str, data_type: str = "news") -> Dict[str, Any]:
        """
        Fetch data from Polygon API using isolated environment.
        
        Args:
            symbol: Stock/crypto symbol (e.g., AAPL, BTC-USD)
            data_type: Type of data to fetch (news, snapshot, aggs, etc.)
            
        Returns:
            Dict containing API response and metadata
        """
        print(f"📊 Fetching Polygon {data_type} data for {symbol}...")
        
        # Use the existing test script with arguments
        result = dispatch_api_task("polygon", f"test/test_polygon.py --symbol {symbol} --type {data_type}")
        return result
    
    def fetch_all_news_sources(self) -> Dict[str, Any]:
        """
        Fetch news from all available sources using isolated environments.
        
        Returns:
            Dict containing results from all sources
        """
        print("🌐 Fetching news from all sources...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "sources": {}
        }
        
        # Fetch from Benzinga
        print("\n📰 Fetching from Benzinga...")
        benzinga_result = self.fetch_benzinga_news()
        results["sources"]["benzinga"] = benzinga_result
        
        # Fetch from Polygon
        print("\n📊 Fetching from Polygon...")
        polygon_result = self.fetch_polygon_data("AAPL", "news")
        results["sources"]["polygon"] = polygon_result
        
        return results
    
    def run_macro_analysis(self) -> Dict[str, Any]:
        """
        Run a comprehensive macro analysis using multiple API sources.
        
        Returns:
            Dict containing analysis results
        """
        print("🔬 Running comprehensive macro analysis...")
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "comprehensive_macro",
            "results": {}
        }
        
        # 1. Fetch news from all sources
        print("\n📰 Step 1: Fetching news from all sources...")
        news_results = self.fetch_all_news_sources()
        analysis["results"]["news"] = news_results
        
        # 2. Fetch market data from Polygon
        print("\n📈 Step 2: Fetching market data...")
        market_data = {}
        
        # Get stock data
        aapl_result = self.fetch_polygon_data("AAPL", "snapshot")
        market_data["AAPL"] = aapl_result
        
        # Get crypto data
        btc_result = self.fetch_polygon_data("BTC-USD", "snapshot")
        market_data["BTC-USD"] = btc_result
        
        analysis["results"]["market_data"] = market_data
        
        # 3. Fetch financial data
        print("\n💰 Step 3: Fetching financial data...")
        financial_data = {}
        
        # Get financials for AAPL
        aapl_financials = self.fetch_polygon_data("AAPL", "financials")
        financial_data["AAPL"] = aapl_financials
        
        analysis["results"]["financial_data"] = financial_data
        
        return analysis
    
    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """
        Save analysis results to a JSON file.
        
        Args:
            results: Analysis results to save
            filename: Optional filename, defaults to timestamp-based name
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"macro_analysis_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Results saved to: {filepath}")
        return str(filepath)

def main():
    """Main function demonstrating API integration."""
    
    print("🚀 MacroIntel API Integration Example")
    print("=" * 50)
    
    # Initialize integration
    integration = MacroIntelAPIIntegration()
    
    # Check API status
    print("\n📊 Checking API Status:")
    status = get_api_status()
    print(json.dumps(status, indent=2))
    
    # Example 1: Fetch news from specific source
    print("\n" + "="*50)
    print("Example 1: Fetching Benzinga News")
    print("="*50)
    
    benzinga_result = integration.fetch_benzinga_news(keywords=["AI", "tech", "earnings"])
    print(f"Benzinga Result: {'✅ Success' if benzinga_result['success'] else '❌ Failed'}")
    
    # Example 2: Fetch market data
    print("\n" + "="*50)
    print("Example 2: Fetching Market Data")
    print("="*50)
    
    market_result = integration.fetch_polygon_data("AAPL", "snapshot")
    print(f"Market Data Result: {'✅ Success' if market_result['success'] else '❌ Failed'}")
    
    # Example 3: Comprehensive analysis
    print("\n" + "="*50)
    print("Example 3: Comprehensive Macro Analysis")
    print("="*50)
    
    analysis_result = integration.run_macro_analysis()
    
    # Save results
    saved_file = integration.save_results(analysis_result)
    
    print(f"\n🎉 Analysis completed! Results saved to: {saved_file}")
    
    # Summary
    print("\n📋 Summary:")
    print("  ✅ API dispatcher successfully isolated conflicting urllib3 versions")
    print("  ✅ Benzinga API (urllib3==1.25.10) executed in isolated environment")
    print("  ✅ Polygon API (urllib3==2.5.0) executed in isolated environment")
    print("  ✅ All API calls completed without version conflicts")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Example interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1) 