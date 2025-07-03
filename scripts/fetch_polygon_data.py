#!/usr/bin/env python3
"""
Polygon Data Fetcher Script

This script fetches market data from Polygon API and processes it for MacroIntel.
Designed to be called by the API dispatcher in an isolated environment.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(dotenv_path=project_root / "config" / ".env")

def fetch_polygon_indices():
    """Fetch key market indices and stock data from Polygon API."""
 try:
 import requests
 
 print(" Fetching Polygon market data...")
 
 api_key = os.getenv("POLYGON_API_KEY")
 if not api_key:
 raise ValueError("POLYGON_API_KEY not found in environment variables")
 
 # Define symbols to fetch
 symbols = [
 "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", # Tech stocks
 "SPY", "QQQ", "IWM", "DIA", # ETFs
 "BTC-USD", "ETH-USD", # Crypto
 "XAUUSD", "XAGUSD" # Precious metals
 ]
 
 base_url = "https://api.polygon.io"
 market_data = {}
 
 for symbol in symbols:
 try:
 print(f"🔍 Fetching data for {symbol}...")
 
 # Get snapshot data
 snapshot_url = f"{base_url}/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"
 params = {"apiKey": api_key}
 
 response = requests.get(snapshot_url, params=params, timeout=30)
 
 if response.status_code == 200:
 data = response.json()
 market_data[symbol] = {
 "snapshot": data,
 "timestamp": datetime.now().isoformat()
 }
 print(f" {symbol}: Success")
 else:
            print(f" {symbol}: API Error {response.status_code}")
 market_data[symbol] = {
 "error": f"API Error {response.status_code}",
 "timestamp": datetime.now().isoformat()
 }
 
 except Exception as e:
        print(f" {symbol}: {e}")
 market_data[symbol] = {
 "error": str(e),
 "timestamp": datetime.now().isoformat()
 }
 
 # Save to output directory
 output_dir = project_root / "output"
 output_dir.mkdir(exist_ok=True)
 
 timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
 output_file = output_dir / f"polygon_indices_{timestamp}.json"
 
 with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(market_data, f, indent=2, default=str)
 
 print(f" Market data saved to: {output_file}")
 
 # Count successful fetches
 successful_fetches = sum(1 for data in market_data.values() if "snapshot" in data)
 
 return {
            "success": True,
 "symbols_fetched": len(symbols),
 "successful_fetches": successful_fetches,
 "output_file": str(output_file),
 "timestamp": datetime.now().isoformat(),
 "source": "polygon"
 }
 
 except ImportError as e:
        print(f" Import error: {e}")
 return {
            "success": False,
 "error": f"Import error: {e}",
 "timestamp": datetime.now().isoformat(),
 "source": "polygon"
 }
 except Exception as e:
        print(f" Error fetching Polygon data: {e}")
 return {
            "success": False,
 "error": str(e),
 "timestamp": datetime.now().isoformat(),
 "source": "polygon"
 }

def fetch_polygon_news():
    """Fetch news from Polygon API."""
 try:
 import requests
 
 print(" Fetching Polygon news...")
 
 api_key = os.getenv("POLYGON_API_KEY")
 if not api_key:
 raise ValueError("POLYGON_API_KEY not found in environment variables")
 
 url = "https://api.polygon.io/v2/reference/news"
 params = {
 "apiKey": api_key,
 "limit": 50,
 "order": "desc"
 }
 
 response = requests.get(url, params=params, timeout=30)
 
 if response.status_code == 200:
 news_data = response.json()
 
 # Save to output directory
 output_dir = project_root / "output"
 output_dir.mkdir(exist_ok=True)
 
 timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
 output_file = output_dir / f"polygon_news_{timestamp}.json"
 
 with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(news_data, f, indent=2, default=str)
 
 print(f" News data saved to: {output_file}")
 
 return {
            "success": True,
 "articles_count": len(news_data.get("results", [])),
 "output_file": str(output_file),
 "timestamp": datetime.now().isoformat(),
 "source": "polygon"
 }
 else:
 raise Exception(f"API Error {response.status_code}: {response.text}")
 
 except Exception as e:
        print(f" Error fetching Polygon news: {e}")
 return {
            "success": False,
 "error": str(e),
 "timestamp": datetime.now().isoformat(),
 "source": "polygon"
 }

def main():
    """Main function to execute the data fetching."""
 parser = argparse.ArgumentParser(description="Fetch data from Polygon API")
 parser.add_argument("--type", choices=["indices", "news"], default="indices",
 help="Type of data to fetch (default: indices)")
 
 args = parser.parse_args()
 
 print(" Starting Polygon Data Fetcher")
 print(f" Project root: {project_root}")
 print(f" Python executable: {sys.executable}")
 print(f" Fetching type: {args.type}")
 
 # Check API key
 api_key = os.getenv("POLYGON_API_KEY")
 if not api_key:
 print(" POLYGON_API_KEY not found in environment variables")
 sys.exit(1)
 
 # Fetch data based on type
 if args.type == "news":
 result = fetch_polygon_news()
 else:
 result = fetch_polygon_indices()
 
 # Print result
 print(" Execution Result:")
 print(json.dumps(result, indent=2))
 
 # Exit with appropriate code
 if result["success"]:
 print(" Polygon data fetching completed successfully")
 sys.exit(0)
 else:
            print(" Polygon data fetching failed")
 sys.exit(1)

if __name__ == "__main__":
    main() 