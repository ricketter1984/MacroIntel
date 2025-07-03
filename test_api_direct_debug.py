#!/usr/bin/env python3
"""
Standalone debug script for direct API client testing.
Logs full responses, status codes, and error diagnostics for:
  1. fetch_polygon_indices()
  2. fetch_messari_metrics()
  3. fetch_twelve_data_chart("BTC/USD")
"""
import os
import sys
from pathlib import Path
from pprint import pprint
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(dotenv_path=project_root / "config" / ".env")

from utils.api_clients import (
    fetch_polygon_indices,
    fetch_messari_metrics,
    fetch_twelve_data_chart
)

def log_api_key_status(env_var):
    key = os.getenv(env_var)
    if not key:
        print(f"[ERROR] {env_var} is missing from environment. Please add it to config/.env.")
        return False
    if len(key) < 10:
        print(f"[WARNING] {env_var} looks suspiciously short. Double-check your API key.")
    print(f"[INFO] {env_var} is present.")
    return True

def debug_polygon_indices():
    print("\n=== Debug: fetch_polygon_indices() ===")
    if not log_api_key_status("POLYGON_API_KEY"):
        print("[SUGGESTION] Obtain a valid Polygon API key and set POLYGON_API_KEY in config/.env.")
        return
    try:
        result = fetch_polygon_indices("SPX")
        if result:
            print("[SUCCESS] Polygon indices fetch succeeded.")
            pprint(result)
        else:
            print("[FAIL] No data returned from Polygon indices endpoint.")
            print("[SUGGESTION] Check if the symbol is correct (try 'SPX', 'NDX', 'RUT'). Verify your API key and endpoint permissions. If using a free key, some endpoints may be restricted.")
    except Exception as e:
        print(f"[ERROR] Exception during Polygon indices fetch: {e}")
        print("[SUGGESTION] Check your network connection, API key, and endpoint documentation.")

def debug_messari_metrics():
    print("\n=== Debug: fetch_messari_metrics() ===")
    if not log_api_key_status("MESSARI_API_KEY"):
        print("[SUGGESTION] Obtain a valid Messari API key and set MESSARI_API_KEY in config/.env.")
        return
    try:
        result = fetch_messari_metrics("bitcoin")
        if result:
            print("[SUCCESS] Messari metrics fetch succeeded.")
            pprint(result)
        else:
            print("[FAIL] No data returned from Messari metrics endpoint.")
            print("[SUGGESTION] Check if the symbol is correct (try 'bitcoin', 'ethereum'). Verify your API key and endpoint permissions. Some endpoints may require a paid plan.")
    except Exception as e:
        print(f"[ERROR] Exception during Messari metrics fetch: {e}")
        print("[SUGGESTION] Check your network connection, API key, and endpoint documentation.")

def debug_twelve_data_chart():
    print("\n=== Debug: fetch_twelve_data_chart('BTC/USD') ===")
    if not log_api_key_status("TWELVE_DATA_API_KEY"):
        print("[SUGGESTION] Obtain a valid Twelve Data API key and set TWELVE_DATA_API_KEY in config/.env.")
        return
    try:
        df = fetch_twelve_data_chart("BTC/USD", interval="1day", outputsize=5)
        if df is not None:
            print("[SUCCESS] Twelve Data chart fetch succeeded.")
            print(f"Returned DataFrame shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print("Sample data:")
            print(df.head())
        else:
            print("[FAIL] No data returned from Twelve Data chart endpoint.")
            print("[SUGGESTION] Check if the symbol is correct (try 'BTC/USD', 'AAPL'). Verify your API key and endpoint permissions. Free plans may have symbol or frequency restrictions.")
    except Exception as e:
        print(f"[ERROR] Exception during Twelve Data chart fetch: {e}")
        print("[SUGGESTION] Check your network connection, API key, and endpoint documentation.")

def main():
    print("\n================ Direct API Client Debug ================")
    debug_polygon_indices()
    debug_messari_metrics()
    debug_twelve_data_chart()
    print("\n================ End of Debug ================\n")

if __name__ == "__main__":
    main() 