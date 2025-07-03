#!/usr/bin/env python3
"""
Twelve Data API Test Script
Test Twelve Data API for time series data with CLI arguments.
"""

import os
import sys
import csv
import argparse
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="config/.env")

def fetch_twelvedata(symbol, interval="1day"):
    """
    Fetch time series data from Twelve Data API.
    
    Args:
        symbol (str): Symbol to fetch (e.g., ETH/USD, AAPL)
        interval (str): Time interval (1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month)
    
    Returns:
        dict: API response or error information
    """
    api_key = os.getenv("TWELVEDATA_API_KEY")
    if not api_key:
        return {"error": "TWELVEDATA_API_KEY not found in environment variables"}
    
    # Twelve Data API endpoint
    url = "https://api.twelvedata.com/time_series"
    
    # Calculate date range (last 30 days for daily data, last 7 days for intraday)
    end_date = datetime.now()
    if interval in ["1min", "5min", "15min", "30min", "45min", "1h", "2h", "4h"]:
        start_date = end_date - timedelta(days=7)
    else:
        start_date = end_date - timedelta(days=30)
    
    params = {
        "symbol": symbol,
        "interval": interval,
        "apikey": api_key,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "format": "JSON"
    }
    
    try:
        print(f"🔍 Fetching {interval} data for {symbol}...")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for API errors in response
            if "status" in data and data["status"] == "error":
                return {"error": f"API Error: {data.get('message', 'Unknown error')}"}
            
            return {
                "success": True,
                "symbol": symbol,
                "interval": interval,
                "data": data,
                "values": data.get("values", []),
                "meta": data.get("meta", {}),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "error": f"HTTP Error {response.status_code}",
                "response": response.text,
                "symbol": symbol,
                "interval": interval
            }
            
    except requests.exceptions.Timeout:
        return {"error": "Request timeout"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def save_to_csv(data, filename="output/eth_twelvedata.csv"):
    """Save time series data to CSV file."""
    try:
        os.makedirs("output", exist_ok=True)
        
        if not data.get("values"):
            print("⚠️  No data values to save")
            return False
        
        # Convert to DataFrame for easier handling
        df = pd.DataFrame(data["values"])
        
        # Rename columns to be more descriptive
        column_mapping = {
            "datetime": "datetime",
            "open": "open",
            "high": "high", 
            "low": "low",
            "close": "close",
            "volume": "volume"
        }
        
        # Only keep columns that exist
        existing_columns = [col for col in column_mapping.keys() if col in df.columns]
        df = df[existing_columns]
        
        # Save to CSV
        df.to_csv(filename, index=False)
        print(f"💾 Data saved to {filename}")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {list(df.columns)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving CSV: {e}")
        return False

def print_last_rows(data, num_rows=5):
    """Print the last N rows of the data."""
    try:
        if not data.get("values"):
            print("⚠️  No data values to display")
            return
        
        df = pd.DataFrame(data["values"])
        
        if len(df) == 0:
            print("⚠️  Empty dataset")
            return
        
        print(f"\n📊 Last {min(num_rows, len(df))} rows:")
        print("=" * 80)
        
        # Display last N rows
        last_rows = df.tail(num_rows)
        print(last_rows.to_string(index=False))
        
        # Print summary stats
        print(f"\n📈 Summary:")
        print(f"  Total rows: {len(df)}")
        print(f"  Date range: {df['datetime'].iloc[0]} to {df['datetime'].iloc[-1]}")
        
        # Convert numeric columns for stats
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        numeric_cols = [col for col in numeric_cols if col in df.columns]
        
        if numeric_cols:
            df_numeric = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
            print(f"  Latest close: {df_numeric['close'].iloc[-1]:.4f}")
            print(f"  Price range: {df_numeric['low'].min():.4f} - {df_numeric['high'].max():.4f}")
        
    except Exception as e:
        print(f"❌ Error displaying data: {e}")

def main():
    parser = argparse.ArgumentParser(description="Test Twelve Data API for time series")
    parser.add_argument("--symbol", "-s", default="ETH/USD", help="Symbol to fetch (default: ETH/USD)")
    parser.add_argument("--interval", "-i", default="1day", 
                       choices=["1min", "5min", "15min", "30min", "45min", "1h", "2h", "4h", "1day", "1week", "1month"],
                       help="Time interval (default: 1day)")
    parser.add_argument("--rows", "-r", type=int, default=5, help="Number of last rows to display (default: 5)")
    
    args = parser.parse_args()
    
    print(f"🚀 Testing Twelve Data API: {args.symbol} -> {args.interval}")
    print("=" * 60)
    
    result = fetch_twelvedata(args.symbol, args.interval)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        if "response" in result:
            print(f"Response: {result['response']}")
        sys.exit(1)
    else:
        print(f"✅ Success! Retrieved {len(result['values'])} data points")
        
        # Print metadata
        meta = result.get("meta", {})
        print(f"\n📋 Metadata:")
        print(f"  Symbol: {meta.get('symbol', 'N/A')}")
        print(f"  Interval: {meta.get('interval', 'N/A')}")
        print(f"  Currency Base: {meta.get('currency_base', 'N/A')}")
        print(f"  Currency Quote: {meta.get('currency_quote', 'N/A')}")
        
        # Save to CSV
        filename = f"output/{args.symbol.replace('/', '_').lower()}_twelvedata.csv"
        save_to_csv(result, filename)
        
        # Print last rows
        print_last_rows(result, args.rows)

if __name__ == "__main__":
    main() 