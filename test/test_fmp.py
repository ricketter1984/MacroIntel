#!/usr/bin/env python3
"""
FMP API Test Script
Test various FMP API endpoints with CLI arguments.
"""

import os
import sys
import json
import argparse
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fetch_fmp_data(ticker, endpoint):
    """
    Fetch data from FMP API based on ticker and endpoint.
    
    Args:
        ticker (str): Stock ticker symbol
        endpoint (str): FMP API endpoint (e.g., 'quote', 'profile', 'income-statement')
    
    Returns:
        dict: API response or error information
    """
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        return {"error": "FMP_API_KEY not found in environment variables"}
    
    # Base URL for FMP API
    base_url = "https://financialmodelingprep.com/api/v3"
    
    # Common endpoints mapping
    endpoints = {
        "quote": f"{base_url}/quote/{ticker}",
        "profile": f"{base_url}/profile/{ticker}",
        "income": f"{base_url}/income-statement/{ticker}",
        "balance": f"{base_url}/balance-sheet-statement/{ticker}",
        "cashflow": f"{base_url}/cash-flow-statement/{ticker}",
        "ratios": f"{base_url}/ratios/{ticker}",
        "metrics": f"{base_url}/key-metrics/{ticker}",
        "growth": f"{base_url}/financial-growth/{ticker}",
        "news": f"{base_url}/stock_news?tickers={ticker}",
        "earnings": f"{base_url}/earnings/{ticker}",
        "price": f"{base_url}/historical-price-full/{ticker}",
        "market-cap": f"{base_url}/market-capitalization/{ticker}"
    }
    
    if endpoint not in endpoints:
        return {"error": f"Unknown endpoint: {endpoint}. Available: {list(endpoints.keys())}"}
    
    url = endpoints[endpoint]
    params = {"apikey": api_key}
    
    try:
        print(f"🔍 Fetching {endpoint} data for {ticker}...")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "endpoint": endpoint,
                "ticker": ticker,
                "data": data,
                "count": len(data) if isinstance(data, list) else 1
            }
        else:
            return {
                "error": f"API Error {response.status_code}",
                "response": response.text,
                "endpoint": endpoint,
                "ticker": ticker
            }
            
    except requests.exceptions.Timeout:
        return {"error": "Request timeout"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def main():
    parser = argparse.ArgumentParser(description="Test FMP API endpoints")
    parser.add_argument("--ticker", "-t", required=True, help="Stock ticker symbol (e.g., AAPL)")
    parser.add_argument("--endpoint", "-e", required=True, 
                       choices=["quote", "profile", "income", "balance", "cashflow", 
                               "ratios", "metrics", "growth", "news", "earnings", 
                               "price", "market-cap"],
                       help="FMP API endpoint to test")
    
    args = parser.parse_args()
    
    print(f"🚀 Testing FMP API: {args.ticker} -> {args.endpoint}")
    print("=" * 50)
    
    result = fetch_fmp_data(args.ticker, args.endpoint)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        if "response" in result:
            print(f"Response: {result['response']}")
        sys.exit(1)
    else:
        print(f"✅ Success! Retrieved {result['count']} items")
        print("\n📊 Data Preview:")
        print(json.dumps(result['data'], indent=2)[:1000] + "..." if len(json.dumps(result['data'])) > 1000 else json.dumps(result['data'], indent=2))

if __name__ == "__main__":
    main() 