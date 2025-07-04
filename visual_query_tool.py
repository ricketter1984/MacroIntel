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
from utils.api_clients import fetch_twelve_data_chart

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
    Parse regime-aware conditions with enhanced operator support:
    - "regime > 65", "regime < 30", "regime >= 50", "regime <= 80"
    - "strategy == 'Tier 1'", "strategy in ['Tier 1', 'Tier 2']"
    - "asset in ['MYM', 'MES']", "asset == 'MNQ'"
    - "momentum > 50", "volatility < 30", "structure >= 70"
    - "classification == 'Fear'", "risk > 2.5%"
    - Component sub-scores: "vix_level > 20", "adx < 25", "rsi_divergence > 0"
    
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
        
        # Parse regime score conditions with all operators
        if 'regime' in condition:
            return _parse_numeric_condition(condition, 'regime', regime_data.get('total_score', 0))
        
        # Parse component score conditions (volatility, structure, volume_breadth, momentum, institutional)
        component_mapping = {
            'volatility': 'volatility',
            'structure': 'structure', 
            'volume_breadth': 'volume_breadth',
            'momentum': 'momentum',
            'institutional': 'institutional'
        }
        
        for component_key, component_name in component_mapping.items():
            if component_key in condition:
                component_score = _get_component_score(regime_data, component_name)
                return _parse_numeric_condition(condition, component_key, component_score)
        
        # Parse sub-component conditions (e.g., vix_level, adx, rsi_divergence)
        sub_component_mapping = {
            'vix_level': ('volatility', 'vix_level'),
            'term_structure': ('volatility', 'term_structure'),
            'atr': ('volatility', 'atr'),
            'adx': ('structure', 'adx'),
            'bb_squeeze': ('structure', 'bb_squeeze'),
            'failed_breakouts': ('structure', 'failed_breakouts'),
            'volume_spikes': ('volume_breadth', 'volume_spikes'),
            'ad_divergence': ('volume_breadth', 'ad_divergence'),
            'mcclellan': ('volume_breadth', 'mcclellan'),
            'put_call_ratio': ('volume_breadth', 'put_call_ratio'),
            'rsi_divergence': ('momentum', 'rsi_divergence'),
            'macd_histogram': ('momentum', 'macd_histogram'),
            'oscillator_confluence': ('momentum', 'oscillator_confluence'),
            'smart_money_flow': ('institutional', 'smart_money_flow'),
            'options_flow': ('institutional', 'options_flow'),
            'institutional_sentiment': ('institutional', 'institutional_sentiment')
        }
        
        for sub_component_key, (parent_component, sub_component) in sub_component_mapping.items():
            if sub_component_key in condition:
                sub_component_value = _get_sub_component_value(regime_data, parent_component, sub_component)
                if sub_component_value is not None:
                    return _parse_numeric_condition(condition, sub_component_key, sub_component_value)
        
        # Parse strategy conditions with enhanced substring matching
        if 'strategy' in condition:
            current_strategy = regime_data.get('strategy_recommendation', '')
            
            if '==' in condition:
                strategy = condition.split('==')[1].strip().strip("'\"")
                
                # Enhanced substring matching: case-insensitive and flexible
                # Examples: "Tier 4" matches "Tier 4 Momentum", "tier 4" matches "Tier 4 Momentum"
                strategy_lower = strategy.lower().strip()
                current_strategy_lower = current_strategy.lower().strip()
                
                # Try to use playbook loader for enhanced strategy matching
                try:
                    playbook_loader = get_playbook_loader()
                    if playbook_loader.is_strategy_available(strategy):
                        # Check if current strategy contains the requested strategy (substring match)
                        return strategy_lower in current_strategy_lower
                except PlaybookConfigError:
                    pass
                
                # Fallback to flexible substring matching
                # Handle cases like "Tier 4" matching "Tier 4 Momentum"
                return strategy_lower in current_strategy_lower
                
            elif 'in' in condition:
                # Extract strategy list from condition like "strategy in ['Tier 1', 'Tier 2']"
                start = condition.find('[')
                end = condition.find(']')
                if start != -1 and end != -1:
                    strategy_list_str = condition[start+1:end]
                    strategies = [s.strip().strip("'\"") for s in strategy_list_str.split(',')]
                    
                    # Try to use playbook loader for enhanced strategy matching
                    try:
                        playbook_loader = get_playbook_loader()
                        available_strategies = playbook_loader.get_available_strategies()
                        # Filter strategies to only those available in playbook
                        valid_strategies = [s for s in strategies if s in available_strategies]
                        if valid_strategies:
                            return any(s.lower().strip() in current_strategy.lower().strip() for s in valid_strategies)
                    except PlaybookConfigError:
                        pass
                    
                    # Fallback to flexible substring matching for all strategies
                    return any(s.lower().strip() in current_strategy.lower().strip() for s in strategies)
        
        # Parse asset conditions with playbook loader enhancement
        if 'asset' in condition:
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
                    
                    # Fallback to direct asset matching
                    return current_asset.upper() in [a.upper() for a in assets]
            elif '==' in condition:
                asset = condition.split('==')[1].strip().strip("'\"")
                current_asset = regime_data.get('instrument', '')
                return current_asset.upper() == asset.upper()
        
        # Parse classification conditions
        if 'classification' in condition:
            if '==' in condition:
                classification = condition.split('==')[1].strip().strip("'\"")
                current_classification = regime_data.get('regime_classification', '')
                return classification.lower() == current_classification.lower()
        
        # Parse risk allocation conditions with all operators
        if 'risk' in condition:
            risk_allocation = regime_data.get('risk_allocation', '0%')
            current_risk = float(risk_allocation.rstrip('%'))
            return _parse_numeric_condition(condition, 'risk', current_risk)
        
        logging.warning(f"Unknown condition format: {condition_str}")
        return False
        
    except Exception as e:
        logging.warning(f"⚠️ Overlay condition failed to apply: {e}")
        return False

def _parse_numeric_condition(condition, field_name, current_value):
    """Parse numeric conditions with all comparison operators."""
    try:
        # Handle all comparison operators: >, <, >=, <=, ==, !=
        operators = ['>=', '<=', '!=', '==', '>', '<']
        
        for op in operators:
            if op in condition:
                # Extract the value after the operator
                parts = condition.split(op)
                if len(parts) == 2:
                    threshold_str = parts[1].strip()
                    # Handle percentage values
                    if threshold_str.endswith('%'):
                        threshold = float(threshold_str.rstrip('%'))
                    else:
                        threshold = float(threshold_str)
                    
                    # Apply the comparison
                    if op == '>':
                        return current_value > threshold
                    elif op == '<':
                        return current_value < threshold
                    elif op == '>=':
                        return current_value >= threshold
                    elif op == '<=':
                        return current_value <= threshold
                    elif op == '==':
                        return current_value == threshold
                    elif op == '!=':
                        return current_value != threshold
        
        logging.warning(f"No valid operator found in condition: {condition}")
        return False
        
    except (ValueError, TypeError) as e:
        logging.error(f"Error parsing numeric condition '{condition}': {e}")
        return False

def _get_component_score(regime_data, component_name):
    """Get the raw score for a component."""
    try:
        component_scores = regime_data.get('component_scores', {})
        if component_name in component_scores:
            return component_scores[component_name].get('score', 0)
        
        # Fallback to component_breakdown if component_scores not available
        component_breakdown = regime_data.get('component_breakdown', {})
        if component_name in component_breakdown:
            return component_breakdown[component_name].get('raw_score', 0)
        
        return 0
    except Exception as e:
        logging.error(f"Error getting component score for {component_name}: {e}")
        return 0

def _get_sub_component_value(regime_data, parent_component, sub_component):
    """Get the value for a sub-component."""
    try:
        component_scores = regime_data.get('component_scores', {})
        if parent_component in component_scores:
            components = component_scores[parent_component].get('components', {})
            if sub_component in components:
                return components[sub_component].get('value', 0)
        
        return None
    except Exception as e:
        logging.error(f"Error getting sub-component value for {parent_component}.{sub_component}: {e}")
        return None

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
    """
    Fetch VIX data using the dedicated FMP API function.
    """
    logging.info("📊 Fetching VIX data from FMP API...")
    
    try:
        from utils.api_clients import fetch_vix_data
        return fetch_vix_data(days=days)
    except Exception as e:
        logging.error(f"Error fetching VIX history: {e}")
        return None

def generate_simulated_vix_data(days=365):
    """
    Generate realistic simulated VIX data when all external sources fail.
    Creates data that mimics typical VIX behavior patterns.
    """
    try:
        import numpy as np
        
        # Generate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Generate realistic VIX data with typical patterns
        np.random.seed(42)  # For reproducible results
        
        # Base VIX level (typical range 15-35)
        base_vix = 22.0
        
        # Add market volatility cycles
        volatility_cycles = np.sin(np.linspace(0, 4*np.pi, len(dates))) * 8
        
        # Add random daily movements
        daily_moves = np.random.normal(0, 2, len(dates))
        
        # Add occasional volatility spikes
        spike_probability = 0.05  # 5% chance of spike per day
        spikes = np.random.choice([0, 1], size=len(dates), p=[1-spike_probability, spike_probability])
        spike_values = spikes * np.random.uniform(5, 15, len(dates))
        
        # Combine all components
        vix_values = base_vix + volatility_cycles + daily_moves + spike_values
        
        # Ensure VIX stays in realistic range (10-50)
        vix_values = np.clip(vix_values, 10, 50)
        
        # Create DataFrame
        df = pd.DataFrame({
            'VIX': vix_values
        }, index=dates)
        
        logging.info(f"✅ Generated simulated VIX data: {len(df)} records (range: {df['VIX'].min():.1f}-{df['VIX'].max():.1f})")
        return df
        
    except Exception as e:
        logging.error(f"❌ Error generating simulated VIX data: {e}")
        # Return minimal fallback data
        return pd.DataFrame({
            'VIX': [20.0]  # Default VIX value
        }, index=[datetime.now()])

def fetch_asset_history(symbol, source='fmp', days=365):
    """Fetch asset history data, with special handling for VIX using Twelve Data."""
    
    # Special handling for VIX using Twelve Data
    if symbol.upper() == "VIX":
        return fetch_vix_history(source='twelve_data', days=days)
    
    # Default FMP handling for other assets
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
    
    # Add Twelve Data support for other assets if needed
    elif source == 'twelve_data':
        try:
            df = fetch_twelve_data_chart(symbol, interval="1day", outputsize=min(days, 5000))
            if df is not None and not df.empty:
                result_df = df[['close']].rename(columns={'close': symbol})
                logging.info(f"✅ Successfully fetched {symbol} data from Twelve Data: {len(result_df)} records")
                return result_df
        except Exception as e:
            logging.error(f"Error fetching {symbol} data from Twelve Data: {e}")
    
    logging.warning(f"Asset data for {symbol} not available from specified source.")
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
        logging.warning(f"⚠️ Overlay condition failed to apply: {e}")
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
    parser = argparse.ArgumentParser(
        description="Visual Query Tool for MacroIntel - Generate asset comparison charts with conditional filtering",
        epilog="""
Examples:
  # Basic asset comparison chart
  python visual_query_tool.py --assets BTC,VIX,QQQ --save

  # Chart with fear & greed condition
  python visual_query_tool.py --assets SPY,VIX --condition "fear < 30" --save

  # Regime-aware condition with export
  python visual_query_tool.py --assets BTC,VIX --condition "regime > 70" --export csv --save

  # Strategy-based condition with email
  python visual_query_tool.py --assets MYM,MES --condition "strategy == 'Tier 1'" --save --email

  # VIX threshold condition with custom timeframe
  python visual_query_tool.py --assets VIX,SPY --condition "vix > 25" --days 90 --save

  # Asset-specific condition with data export
  python visual_query_tool.py --assets QQQ,VIX --condition "asset in ['MYM', 'MES']" --export json --save
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--assets', 
        type=str, 
        required=True, 
        help='Comma-separated list of asset symbols to compare (e.g., BTC,VIX,QQQ,SPY). VIX data is fetched from Twelve Data API.'
    )
    
    parser.add_argument(
        '--condition', 
        type=str, 
        default='', 
        help='Conditional filter to apply before generating chart. Supports: fear/greed thresholds (fear < 30), VIX thresholds (vix > 20), regime scores (regime > 65), strategy matching (strategy == "Tier 1"), asset filtering (asset in ["MYM", "MES"]), classification matching, and risk allocation thresholds.'
    )
    
    parser.add_argument(
        '--export', 
        type=str, 
        choices=['csv', 'json'], 
        help='Export normalized asset data to CSV or JSON format. Data is saved to output/query_data.{format}'
    )
    
    parser.add_argument(
        '--days', 
        type=int, 
        default=365, 
        help='Number of days of historical data to fetch for each asset (default: 365, max: 5000)'
    )
    
    parser.add_argument(
        '--email', 
        action='store_true', 
        help='Send the generated chart as an email attachment using the configured email settings'
    )
    
    parser.add_argument(
        '--save', 
        action='store_true', 
        help='Save the chart with a timestamped filename in the output directory (e.g., visual_query_20250703_143022.png)'
    )
    
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
        # Fetch VIX data using Twelve Data (default source)
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