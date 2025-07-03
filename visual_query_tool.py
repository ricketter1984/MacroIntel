import os
import argparse
import logging
import json
import glob
from datetime import datetime, timedelta
from pathlib import Path
import requests
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from core.visual_query_engine import generate_comparison_chart, fetch_asset_history
from playbook_loader import get_playbook_loader, PlaybookConfigError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv(dotenv_path="config/.env")

FMP_API_KEY = os.getenv('FMP_API_KEY')
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
FEAR_GREED_API_KEY = os.getenv('FEAR_GREED_API_KEY')

OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Regime Score Functions ---
def load_regime_score_data():
    """
    Load the most recent regime score data from output directory.
    
    Returns:
        Dict containing regime score data or None if not found
    """
    try:
        # Look for regime score files in output directory
        output_dir = Path(OUTPUT_DIR)
        if not output_dir.exists():
            return None
        
        # Find all regime score files
        regime_files = list(output_dir.glob("regime_score_*.json"))
        if not regime_files:
            return None
        
        # Get the most recent file
        latest_file = max(regime_files, key=lambda x: x.stat().st_mtime)
        
        # Load and parse the JSON data
        with open(latest_file, 'r', encoding='utf-8') as f:
            regime_data = json.load(f)
        
        logging.info(f"✅ Loaded regime score data from: {latest_file}")
        return regime_data
        
    except Exception as e:
        logging.warning(f"⚠️ Error loading regime score data: {e}")
        return None

def parse_regime_condition(condition_str, regime_data):
    """
    Parse regime-aware conditions like:
    - "regime > 65"
    - "strategy == 'Tier 1'"
    - "asset in ['MYM', 'MES']"
    
    Args:
        condition_str: String containing the condition
        regime_data: Dict containing regime score data
        
    Returns:
        Boolean indicating if condition is met
    """
    if not regime_data:
        logging.warning("No regime data available for condition parsing")
        return False
    
    try:
        condition = condition_str.strip().lower()
        
        # Parse regime score conditions
        if 'regime' in condition:
            if '>' in condition:
                threshold = float(condition.split('>')[1].strip())
                regime_score = regime_data.get('total_score', 0)
                return regime_score > threshold
            elif '<' in condition:
                threshold = float(condition.split('<')[1].strip())
                regime_score = regime_data.get('total_score', 0)
                return regime_score < threshold
            elif '==' in condition:
                threshold = float(condition.split('==')[1].strip())
                regime_score = regime_data.get('total_score', 0)
                return regime_score == threshold
        
        # Parse strategy conditions with playbook loader enhancement
        elif 'strategy' in condition:
            if '==' in condition:
                strategy = condition.split('==')[1].strip().strip("'\"")
                current_strategy = regime_data.get('strategy_recommendation', '')
                
                # Try to use playbook loader for enhanced strategy matching
                try:
                    playbook_loader = get_playbook_loader()
                    if playbook_loader.is_strategy_available(strategy):
                        # Check if current strategy matches the requested strategy
                        return strategy.lower() in current_strategy.lower()
                except PlaybookConfigError:
                    pass
                
                # Fallback to simple string matching
                return strategy.lower() in current_strategy.lower()
                
            elif 'in' in condition:
                # Extract strategy list from condition like "strategy in ['Tier 1', 'Tier 2']"
                start = condition.find('[')
                end = condition.find(']')
                if start != -1 and end != -1:
                    strategy_list_str = condition[start+1:end]
                    strategies = [s.strip().strip("'\"") for s in strategy_list_str.split(',')]
                    current_strategy = regime_data.get('strategy_recommendation', '')
                    
                    # Try to use playbook loader for enhanced strategy matching
                    try:
                        playbook_loader = get_playbook_loader()
                        available_strategies = playbook_loader.get_available_strategies()
                        # Filter strategies to only those available in playbook
                        valid_strategies = [s for s in strategies if s in available_strategies]
                        if valid_strategies:
                            return any(s.lower() in current_strategy.lower() for s in valid_strategies)
                    except PlaybookConfigError:
                        pass
                    
                    # Fallback to simple string matching
                    return any(s.lower() in current_strategy.lower() for s in strategies)
        
        # Parse asset conditions with playbook loader enhancement
        elif 'asset' in condition:
            if 'in' in condition:
                # Extract asset list from condition like "asset in ['MYM', 'MES']"
                start = condition.find('[')
                end = condition.find(']')
                if start != -1 and end != -1:
                    asset_list_str = condition[start+1:end]
                    assets = [a.strip().strip("'\"") for a in asset_list_str.split(',')]
                    current_asset = regime_data.get('instrument', '')
                    
                    # Try to use playbook loader to validate assets against strategy instruments
                    try:
                        playbook_loader = get_playbook_loader()
                        current_strategy = regime_data.get('strategy_recommendation', '')
                        for strategy_name in playbook_loader.get_available_strategies():
                            if strategy_name.lower() in current_strategy.lower():
                                strategy_instruments = playbook_loader.get_strategy_instruments(strategy_name)
                                # Check if current asset is in strategy instruments
                                if current_asset.upper() in [i.upper() for i in strategy_instruments]:
                                    return current_asset.upper() in [a.upper() for a in assets]
                    except PlaybookConfigError:
                        pass
                    
                    # Fallback to simple asset matching
                    return current_asset.upper() in [a.upper() for a in assets]
                    
            elif '==' in condition:
                asset = condition.split('==')[1].strip().strip("'\"")
                current_asset = regime_data.get('instrument', '')
                return asset.upper() == current_asset.upper()
        
        # Parse classification conditions
        elif 'classification' in condition:
            if '==' in condition:
                classification = condition.split('==')[1].strip().strip("'\"")
                current_classification = regime_data.get('regime_classification', '')
                return classification.lower() == current_classification.lower()
        
        # Parse risk allocation conditions
        elif 'risk' in condition:
            if '>' in condition:
                threshold = float(condition.split('>')[1].strip().rstrip('%'))
                risk_allocation = regime_data.get('risk_allocation', '0%')
                current_risk = float(risk_allocation.rstrip('%'))
                return current_risk > threshold
            elif '<' in condition:
                threshold = float(condition.split('<')[1].strip().rstrip('%'))
                risk_allocation = regime_data.get('risk_allocation', '0%')
                current_risk = float(risk_allocation.rstrip('%'))
                return current_risk < threshold
        
        logging.warning(f"Unknown condition format: {condition_str}")
        return False
        
    except Exception as e:
        logging.error(f"Error parsing regime condition '{condition_str}': {e}")
        return False

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
def parse_condition(condition_str, context, regime_data=None):
    """
    Parse conditions including regime-aware conditions.
    Supports both legacy conditions and new regime conditions.
    """
    if not condition_str:
        return True
    
    try:
        # Check if this is a regime-aware condition
        regime_keywords = ['regime', 'strategy', 'asset', 'classification', 'risk']
        if any(keyword in condition_str.lower() for keyword in regime_keywords):
            if regime_data:
                return parse_regime_condition(condition_str, regime_data)
            else:
                logging.warning("Regime condition specified but no regime data available")
                return False
        
        # Legacy condition parsing (fear, vix, etc.)
        tokens = condition_str.lower().replace(' ', '').replace('fear&greed', 'fear').split(',')
        for token in tokens:
            if 'fear<' in token:
                val = int(token.split('<')[1])
                if context.get('fear', 50) >= val:
                    return False
            elif 'fear>' in token:
                val = int(token.split('>')[1])
                if context.get('fear', 50) <= val:
                    return False
            elif 'vix<' in token:
                val = float(token.split('<')[1])
                if context.get('vix', 20) >= val:
                    return False
            elif 'vix>' in token:
                val = float(token.split('>')[1])
                if context.get('vix', 20) <= val:
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

# --- Email Functions ---
def send_email_with_attachment(file_path, subject="MacroIntel Visual Query Results"):
    """
    Send email with chart attachment using the existing email infrastructure.
    """
    try:
        from core.email_report import send_daily_report
        
        # Create simple HTML content
        html_content = f"""
        <html>
        <body>
            <h2>📊 MacroIntel Visual Query Results</h2>
            <p>Your requested chart has been generated and is attached to this email.</p>
            <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <p><strong>File:</strong> {os.path.basename(file_path)}</p>
        </body>
        </html>
        """
        
        # Send email with attachment
        success = send_daily_report(html_content, attachments=[file_path])
        
        if success:
            logging.info(f"✅ Email sent successfully with attachment: {file_path}")
            return True
        else:
            logging.error("❌ Failed to send email")
            return False
            
    except Exception as e:
        logging.error(f"❌ Error sending email: {e}")
        return False

# --- Main CLI ---
def main():
    parser = argparse.ArgumentParser(description="Visual Query Tool for MacroIntel")
    parser.add_argument('--assets', type=str, required=True, help='Comma-separated asset symbols (e.g. BTCUSD,XAUUSD,QQQ)')
    parser.add_argument('--condition', type=str, default='', help='Condition string, e.g. "fear < 30", "vix > 20", "regime > 65", "strategy == \'Tier 1\'", "asset in [\'MYM\', \'MES\']"')
    parser.add_argument('--export', type=str, choices=['csv', 'json'], help='Export data as CSV or JSON')
    parser.add_argument('--days', type=int, default=365, help='Number of days of history to fetch')
    parser.add_argument('--email', action='store_true', help='Send results by email')
    parser.add_argument('--save', action='store_true', help='Save chart to output directory with timestamp')
    args = parser.parse_args()

    asset_symbols = [a.strip().upper() for a in args.assets.split(',')]
    days = args.days
    
    # Load regime score data if condition might be regime-aware
    regime_data = None
    if args.condition and any(keyword in args.condition.lower() for keyword in ['regime', 'strategy', 'asset', 'classification', 'risk']):
        regime_data = load_regime_score_data()
        if regime_data:
            logging.info(f"📊 Current regime: {regime_data.get('total_score', 'N/A')}/100 - {regime_data.get('strategy_recommendation', 'N/A')}")
        else:
            logging.warning("⚠️ Regime condition specified but no regime data available")
    
    # Check condition before proceeding
    if args.condition:
        vix_data = fetch_vix_history()
        context = {
            'fear': fetch_fear_greed() or 50,
            'vix': vix_data['VIX'].iloc[-1] if vix_data is not None and len(vix_data) > 0 else 20
        }
        
        condition_met = parse_condition(args.condition, context, regime_data)
        if not condition_met:
            logging.info(f"❌ Condition not met: {args.condition}")
            logging.info("Skipping chart generation")
            return
        else:
            logging.info(f"✅ Condition met: {args.condition}")
    
    # Determine output path
    if args.save:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(OUTPUT_DIR, f'visual_query_{timestamp}.png')
    else:
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
    
    # Send email if requested
    if args.email:
        if os.path.exists(output_path):
            send_email_with_attachment(output_path)
        else:
            logging.error("Cannot send email: chart file not found")

if __name__ == "__main__":
    main() 