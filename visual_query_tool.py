import os
import argparse
import logging
from datetime import datetime, timedelta
import requests
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from visual_query_engine import generate_comparison_chart, fetch_asset_history

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

FMP_API_KEY = os.getenv('FMP_API_KEY')
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
FEAR_GREED_API_KEY = os.getenv('FEAR_GREED_API_KEY')

OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Data Fetching Functions ---
def fetch_fear_greed():
    url = "https://cnn-fear-and-greed-index.p.rapidapi.com/cnn/v1/fear_and_greed/index"
    headers = {
        "x-rapidapi-key": FEAR_GREED_API_KEY,
        "x-rapidapi-host": "cnn-fear-and-greed-index.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            score = data.get("fear_and_greed", {}).get("score", 50)
            return int(score)
        else:
            logging.warning(f"Fear & Greed API error: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error fetching Fear & Greed Index: {str(e)}")
        return None

def fetch_vix_history(source='fmp', days=365):
    if source == 'fmp':
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/VIX"
        params = {
            "apikey": FMP_API_KEY,
            "from": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
            "to": datetime.now().strftime("%Y-%m-%d")
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if "historical" in data:
                df = pd.DataFrame(data["historical"])
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date').sort_index()
                return df[['close']].rename(columns={'close': 'VIX'})
    # Add Polygon support if needed
    logging.warning("VIX data not available from Polygon in this script.")
    return None

def fetch_asset_history(symbol, source='fmp', days=365):
    if source == 'fmp':
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
        params = {
            "apikey": FMP_API_KEY,
            "from": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
            "to": datetime.now().strftime("%Y-%m-%d")
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if "historical" in data:
                df = pd.DataFrame(data["historical"])
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date').sort_index()
                return df[['close']].rename(columns={'close': symbol})
    # Add Polygon/Twelve Data support if needed
    logging.warning(f"Asset data for {symbol} not available from Polygon/Twelve Data in this script.")
    return None

# --- Condition Parsing ---
def parse_condition(condition_str, context):
    # Only supports simple conditions like 'fear < 30', 'vix > 20', etc.
    try:
        tokens = condition_str.lower().replace(' ', '').replace('fear&greed', 'fear').split(',')
        for token in tokens:
            if 'fear<' in token:
                val = int(token.split('<')[1])
                if context['fear'] >= val:
                    return False
            elif 'fear>' in token:
                val = int(token.split('>')[1])
                if context['fear'] <= val:
                    return False
            elif 'vix<' in token:
                val = float(token.split('<')[1])
                if context['vix'] >= val:
                    return False
            elif 'vix>' in token:
                val = float(token.split('>')[1])
                if context['vix'] <= val:
                    return False
        return True
    except Exception as e:
        logging.error(f"Error parsing condition '{condition_str}': {e}")
        return False

# --- Plotting ---
def plot_assets(asset_dfs, output_path):
    plt.figure(figsize=(12, 6))
    for symbol, df in asset_dfs.items():
        if df is not None:
            normed = df / df.iloc[0] * 100
            plt.plot(normed.index, normed[symbol], label=symbol)
    plt.title('Asset Performance Comparison')
    plt.xlabel('Date')
    plt.ylabel('Normalized Price (100 = start)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logging.info(f"Chart saved to {output_path}")

# --- Main CLI ---
def main():
    parser = argparse.ArgumentParser(description="Visual Query Tool for MacroIntel")
    parser.add_argument('--assets', type=str, required=True, help='Comma-separated asset symbols (e.g. BTCUSD,XAUUSD,QQQ)')
    parser.add_argument('--condition', type=str, default='', help='Condition string, e.g. "fear < 30" or "vix > 20"')
    parser.add_argument('--export', type=str, choices=['csv', 'json'], help='Export data as CSV or JSON')
    parser.add_argument('--days', type=int, default=365, help='Number of days of history to fetch')
    args = parser.parse_args()

    asset_symbols = [a.strip().upper() for a in args.assets.split(',')]
    days = args.days
    output_path = os.path.join(OUTPUT_DIR, 'custom_query.png')

    try:
        # Generate and save chart
        generate_comparison_chart(asset_symbols, condition=args.condition, output_path=output_path, days=days)
        logging.info(f"Chart generated at {output_path}")
    except Exception as e:
        logging.error(f"Failed to generate chart: {e}")
        return

    # If export is requested, save merged percent-change data
    if args.export:
        try:
            # Fetch and merge asset histories
            asset_dfs = {}
            for symbol in asset_symbols:
                df = fetch_asset_history(symbol, days=days)
                if df is not None:
                    # Convert to percent change
                    df = df / df.iloc[0] * 100
                    df.columns = [f"{symbol}_pct"]
                    asset_dfs[symbol] = df
                else:
                    logging.warning(f"No data for {symbol} (export)")
            if not asset_dfs:
                logging.error("No asset data to export.")
                return
            merged = pd.concat(asset_dfs.values(), axis=1, join='inner')
            merged.index.name = 'date'
            export_path = os.path.join(OUTPUT_DIR, f'query_data.{args.export}')
            if args.export == 'csv':
                merged.to_csv(export_path)
            elif args.export == 'json':
                merged.to_json(export_path, orient='records', date_format='iso')
            logging.info(f"Exported data to {export_path}")
        except Exception as e:
            logging.error(f"Failed to export data: {e}")

if __name__ == "__main__":
    main() 