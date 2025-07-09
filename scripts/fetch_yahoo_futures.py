#!/usr/bin/env python3
"""
Fetches most active futures from Yahoo Finance and saves as CSV/JSON.
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_yahoo_futures():
    """Fetch futures data from Yahoo Finance."""
    url = "https://finance.yahoo.com/markets/commodities/"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error fetching Yahoo Commodities page: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Look for the commodities table
    table = soup.find("table")
    if not table:
        logger.warning("⚠️ Could not find commodities table on Yahoo page")
        return None

    rows = table.find_all("tr")
    data = []

    for row in rows[1:]:  # skip header
        cols = row.find_all("td")
        if len(cols) < 3:  # Minimum required columns
            continue
        
        # Extract data - the structure appears to be: Symbol, Name, Price/Change/Volume
        symbol = cols[0].text.strip()
        name = cols[1].text.strip()
        
        # The third column contains price, change, and percentage in one string
        # Format: "6,266.00 -6.00 (-0.10%)"
        price_change_text = cols[2].text.strip() if len(cols) > 2 else ""
        
        # Parse the combined price/change text
        last_price = ""
        change = ""
        percent_change = ""
        
        if price_change_text:
            # Look for patterns like "6,266.00 -6.00 (-0.10%)"
            import re
            # Match pattern: number, space, +/-number, space, (percentage)
            match = re.match(r'([\d,]+\.?\d*)\s+([+-]\d+\.?\d*)\s+\(([+-]\d+\.?\d*%)\)', price_change_text)
            if match:
                last_price = match.group(1)
                change = match.group(2)
                percent_change = match.group(3)
            else:
                # Fallback: just use the text as is
                last_price = price_change_text
        
        # Volume might be in a separate column
        volume = cols[3].text.strip() if len(cols) > 3 else ""

        data.append({
            "symbol": symbol,
            "name": name,
            "last_price": last_price,
            "change": change,
            "percent_change": percent_change,
            "volume": volume
        })

    df = pd.DataFrame(data)

    # Save to CSV
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save as CSV
    csv_filename = f"yahoo_futures_{timestamp}.csv"
    csv_filepath = os.path.join(output_dir, csv_filename)
    df.to_csv(csv_filepath, index=False)
    
    # Save as JSON
    json_filename = f"yahoo_futures_{timestamp}.json"
    json_filepath = os.path.join(output_dir, json_filename)
    with open(json_filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    # Also save with date-only filename for daily tracking
    date_str = datetime.now().strftime('%Y-%m-%d')
    daily_csv_filename = f"yahoo_futures_{date_str}.csv"
    daily_csv_filepath = os.path.join(output_dir, daily_csv_filename)
    df.to_csv(daily_csv_filepath, index=False)
    
    daily_json_filename = f"yahoo_futures_{date_str}.json"
    daily_json_filepath = os.path.join(output_dir, daily_json_filename)
    with open(daily_json_filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    logger.info(f"✅ Saved Yahoo futures data to:")
    logger.info(f"   📄 CSV: {csv_filepath}")
    logger.info(f"   📄 JSON: {json_filepath}")
    logger.info(f"   📄 Daily CSV: {daily_csv_filepath}")
    logger.info(f"   📄 Daily JSON: {daily_json_filepath}")
    logger.info(f"   📊 Total records: {len(data)}")
    
    return df

if __name__ == "__main__":
    fetch_yahoo_futures() 