#!/usr/bin/env python3
"""
Polygon API Test Script
Test various Polygon API endpoints with CLI arguments.
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fetch_polygon_data(symbol, data_type):
    """
    Fetch data from Polygon API based on symbol and data type.
    
    Args:
        symbol (str): Stock/crypto symbol (e.g., AAPL, BTC-USD)
        data_type (str): Type of data to fetch (news, snapshot, aggs, etc.)
    
    Returns:
        dict: API response or error information
    """
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        return {"error": "POLYGON_API_KEY not found in environment variables"}
    
    # Base URL for Polygon API
    base_url = "https://api.polygon.io"
    
    # Endpoint mapping
    endpoints = {
        "news": f"{base_url}/v2/reference/news",
        "snapshot": f"{base_url}/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}",
        "aggs": f"{base_url}/v2/aggs/ticker/{symbol}/range/1/day/{datetime.now().strftime('%Y-%m-%d')}/{datetime.now().strftime('%Y-%m-%d')}",
        "ticker": f"{base_url}/v3/reference/tickers/{symbol}",
        "financials": f"{base_url}/v2/reference/financials/{symbol}",
        "dividends": f"{base_url}/v2/reference/dividends/{symbol}",
        "splits": f"{base_url}/v2/reference/splits/{symbol}",
        "trades": f"{base_url}/v2/ticks/stocks/trades/{symbol}/{datetime.now().strftime('%Y-%m-%d')}",
        "quotes": f"{base_url}/v2/ticks/stocks/quotes/{symbol}/{datetime.now().strftime('%Y-%m-%d')}"
    }
    
    if data_type not in endpoints:
        return {"error": f"Unknown data type: {data_type}. Available: {list(endpoints.keys())}"}
    
    url = endpoints[data_type]
    params = {"apiKey": api_key}
    
    # Add specific parameters for certain endpoints
    if data_type == "news":
        params.update({
            "limit": 10,
            "order": "desc"
        })
    elif data_type == "aggs":
        params.update({
            "limit": 100,
            "adjusted": "true"
        })
    
    try:
        print(f"🔍 Fetching {data_type} data for {symbol}...")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "data_type": data_type,
                "symbol": symbol,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "error": f"API Error {response.status_code}",
                "response": response.text,
                "data_type": data_type,
                "symbol": symbol
            }
            
    except requests.exceptions.Timeout:
        return {"error": "Request timeout"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def save_to_file(data, filename="output/polygon_test.json"):
    """Save data to JSON file."""
    try:
        os.makedirs("output", exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"💾 Data saved to {filename}")
        return True
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test Polygon API endpoints")
    parser.add_argument("--symbol", "-s", required=True, help="Stock/crypto symbol (e.g., AAPL, BTC-USD)")
    parser.add_argument("--type", "-t", required=True,
                       choices=["news", "snapshot", "aggs", "ticker", "financials", 
                               "dividends", "splits", "trades", "quotes"],
                       help="Type of data to fetch")
    parser.add_argument("--save", action="store_true", help="Save response to output/polygon_test.json")
    
    args = parser.parse_args()
    
    print(f"🚀 Testing Polygon API: {args.symbol} -> {args.type}")
    print("=" * 50)
    
    result = fetch_polygon_data(args.symbol, args.type)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        if "response" in result:
            print(f"Response: {result['response']}")
        sys.exit(1)
    else:
        print(f"✅ Success! Retrieved {args.type} data for {args.symbol}")
        
        # Save to file if requested
        if args.save:
            save_to_file(result)
        
        # Print summary
        print(f"\n📊 Data Summary:")
        print(f"  Type: {result['data_type']}")
        print(f"  Symbol: {result['symbol']}")
        print(f"  Timestamp: {result['timestamp']}")
        
        # Print data preview
        data = result['data']
        if isinstance(data, dict):
            if 'results' in data:
                print(f"  Results count: {len(data['results'])}")
                if data['results']:
                    print(f"  First result: {list(data['results'][0].keys())}")
            else:
                print(f"  Keys: {list(data.keys())}")
        elif isinstance(data, list):
            print(f"  Items count: {len(data)}")
            if data:
                print(f"  First item keys: {list(data[0].keys())}")
        
        # Show full data if it's small
        data_str = json.dumps(data, indent=2, default=str)
        if len(data_str) < 2000:
            print(f"\n📋 Full Response:")
            print(data_str)
        else:
            print(f"\n📋 Data Preview (first 1000 chars):")
            print(data_str[:1000] + "...")

if __name__ == "__main__":
    main() 