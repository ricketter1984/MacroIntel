#!/usr/bin/env python3
"""
Fetch Barchart Most Active Futures and save to output/barchart_futures_<DATE>.json
"""
import requests
import json
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BARCHART_URL = "https://www.barchart.com/proxies/core-api/v1/quotes/get"
PARAMS = {
    "lists": "mostActive",
    "fields": "symbol,name,lastPrice,percentChange,volume"
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.barchart.com/"
}

def fetch_barchart_futures():
    try:
        logger.info(f"Fetching Barchart Most Active Futures...")
        response = requests.get(BARCHART_URL, params=PARAMS, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        # Extract the 'data' field if present
        futures = data.get("data", [])
        logger.info(f"Fetched {len(futures)} futures from Barchart.")
        return futures
    except Exception as e:
        logger.error(f"Error fetching Barchart futures: {e}")
        return []

def save_futures(futures):
    try:
        Path("output").mkdir(exist_ok=True)
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"barchart_futures_{date_str}.json"
        filepath = Path("output") / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(futures, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved Barchart futures to {filepath}")
        return str(filepath)
    except Exception as e:
        logger.error(f"Error saving Barchart futures: {e}")
        return ""

def main():
    futures = fetch_barchart_futures()
    if futures:
        save_futures(futures)
    else:
        logger.warning("No futures data to save.")

if __name__ == "__main__":
    main() 