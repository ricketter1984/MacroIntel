#!/usr/bin/env python3
"""
Messari API Test Script
Test Messari API for crypto asset data with CLI arguments.
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fetch_messari_data(asset, data_type="profile"):
    """
    Fetch data from Messari API for a crypto asset.
    
    Args:
        asset (str): Asset symbol (e.g., BTC, ETH, SOL)
        data_type (str): Type of data to fetch (profile, metrics, news)
    
    Returns:
        dict: API response or error information
    """
    api_key = os.getenv("MESSARI_API_KEY")
    if not api_key:
        return {"error": "MESSARI_API_KEY not found in environment variables"}
    
    # Messari API endpoints
    base_url = "https://data.messari.io/api/v1"
    
    endpoints = {
        "profile": f"{base_url}/assets/{asset}/profile",
        "metrics": f"{base_url}/assets/{asset}/metrics",
        "news": f"{base_url}/news",
        "market-data": f"{base_url}/assets/{asset}/metrics/market-data",
        "all": f"{base_url}/assets/{asset}"
    }
    
    if data_type not in endpoints:
        return {"error": f"Unknown data type: {data_type}. Available: {list(endpoints.keys())}"}
    
    url = endpoints[data_type]
    headers = {
        "x-messari-api-key": api_key
    }
    
    try:
        print(f"🔍 Fetching {data_type} data for {asset}...")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "asset": asset,
                "data_type": data_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "error": f"API Error {response.status_code}",
                "response": response.text,
                "asset": asset,
                "data_type": data_type
            }
            
    except requests.exceptions.Timeout:
        return {"error": "Request timeout"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def print_summary(data, asset, data_type):
    """Print a summary of the Messari data."""
    try:
        if data_type == "profile":
            profile = data.get("data", {})
            print(f"\n📋 {asset} Profile Summary:")
            print(f"  Name: {profile.get('name', 'N/A')}")
            print(f"  Symbol: {profile.get('symbol', 'N/A')}")
            print(f"  Category: {profile.get('category', 'N/A')}")
            print(f"  Sector: {profile.get('sector', 'N/A')}")
            
            # Links
            links = profile.get('links', {})
            if links:
                print(f"  Website: {links.get('website', ['N/A'])[0] if links.get('website') else 'N/A'}")
                print(f"  Whitepaper: {links.get('whitepaper', ['N/A'])[0] if links.get('whitepaper') else 'N/A'}")
            
            # Description
            description = profile.get('description', '')
            if description:
                print(f"  Description: {description[:200]}...")
        
        elif data_type == "metrics":
            metrics = data.get("data", {})
            market_data = metrics.get("market_data", {})
            
            print(f"\n📊 {asset} Market Metrics:")
            print(f"  Price USD: ${market_data.get('price_usd', 'N/A')}")
            print(f"  Market Cap: ${market_data.get('market_cap_usd', 'N/A'):,.0f}" if market_data.get('market_cap_usd') else "  Market Cap: N/A")
            print(f"  24h Volume: ${market_data.get('volume_last_24_hours', 'N/A')}")
            print(f"  24h Change: {market_data.get('percent_change_usd_last_24_hours', 'N/A')}%")
            
            # Supply info
            supply_data = metrics.get("supply", {})
            if supply_data:
                print(f"  Circulating Supply: {supply_data.get('circulating', 'N/A'):,.0f}" if supply_data.get('circulating') else "  Circulating Supply: N/A")
                print(f"  Max Supply: {supply_data.get('max', 'N/A'):,.0f}" if supply_data.get('max') else "  Max Supply: N/A")
        
        elif data_type == "market-data":
            market_data = data.get("data", {})
            
            print(f"\n💹 {asset} Market Data:")
            print(f"  Price USD: ${market_data.get('price_usd', 'N/A')}")
            print(f"  Market Cap: ${market_data.get('market_cap_usd', 'N/A'):,.0f}" if market_data.get('market_cap_usd') else "  Market Cap: N/A")
            print(f"  24h Volume: ${market_data.get('volume_last_24_hours', 'N/A')}")
            print(f"  24h Change: {market_data.get('percent_change_usd_last_24_hours', 'N/A')}%")
        
        elif data_type == "news":
            news_items = data.get("data", [])
            print(f"\n📰 Recent News ({len(news_items)} items):")
            for i, item in enumerate(news_items[:5], 1):
                print(f"  {i}. {item.get('title', 'No title')}")
                print(f"     Published: {item.get('published_at', 'N/A')}")
                print(f"     URL: {item.get('url', 'N/A')}")
                print()
        
        elif data_type == "all":
            profile = data.get("data", {})
            print(f"\n🔍 {asset} Complete Profile:")
            print(f"  Name: {profile.get('name', 'N/A')}")
            print(f"  Symbol: {profile.get('symbol', 'N/A')}")
            print(f"  Category: {profile.get('category', 'N/A')}")
            
            # Market data if available
            if "market_data" in profile:
                market_data = profile["market_data"]
                print(f"  Price USD: ${market_data.get('price_usd', 'N/A')}")
                print(f"  Market Cap: ${market_data.get('market_cap_usd', 'N/A'):,.0f}" if market_data.get('market_cap_usd') else "  Market Cap: N/A")
        
        else:
            print(f"\n📄 {asset} {data_type.title()} Data:")
            print(f"  Data type: {data_type}")
            print(f"  Keys available: {list(data.get('data', {}).keys())}")
            
    except Exception as e:
        print(f"❌ Error printing summary: {e}")

def main():
    parser = argparse.ArgumentParser(description="Test Messari API for crypto assets")
    parser.add_argument("--asset", "-a", default="BTC", help="Asset symbol (default: BTC)")
    parser.add_argument("--type", "-t", default="profile",
                       choices=["profile", "metrics", "news", "market-data", "all"],
                       help="Type of data to fetch (default: profile)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print full response")
    
    args = parser.parse_args()
    
    print(f"🚀 Testing Messari API: {args.asset} -> {args.type}")
    print("=" * 50)
    
    result = fetch_messari_data(args.asset, args.type)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        if "response" in result:
            print(f"Response: {result['response']}")
        sys.exit(1)
    else:
        print(f"✅ Success! Retrieved {args.type} data for {args.asset}")
        
        # Print summary
        print_summary(result["data"], args.asset, args.type)
        
        # Print full response if verbose
        if args.verbose:
            print(f"\n📋 Full Response:")
            print(json.dumps(result["data"], indent=2, default=str))
        
        # Print metadata
        print(f"\n⏰ Timestamp: {result['timestamp']}")

if __name__ == "__main__":
    main() 