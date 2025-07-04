#!/usr/bin/env python3
"""
Visual Query Engine for MacroIntel
Monitors Fear & Greed Index and generates asset comparison charts during extreme fear periods.
"""

import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from dotenv import load_dotenv
import warnings
import logging
from query_parser import parse_condition
from utils.api_clients import fetch_twelve_data_chart

# Load environment variables
load_dotenv(dotenv_path="config/.env")

FMP_API_KEY = os.getenv("FMP_API_KEY")
FEAR_GREED_API_KEY = os.getenv("FEAR_GREED_API_KEY")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

class VisualQueryEngine:
    def __init__(self):
        """Initialize the Visual Query Engine with API keys and configuration."""
        self.fmp_api_key = os.getenv("FMP_API_KEY")
        self.twelve_data_api_key = os.getenv("TWELVE_DATA_API_KEY")
        self.fear_greed_api_key = os.getenv("FEAR_GREED_API_KEY")
        
        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)
        
        # Asset symbols for data fetching
        self.assets = {
            "BTC": "BTCUSD",
            "Gold": "XAUUSD", 
            "QQQ": "QQQ"
        }
        
        print("🔍 Visual Query Engine initialized")
        print(f"📊 Monitoring assets: {', '.join(self.assets.keys())}")
    
    def get_fear_greed_index(self):
        """Fetch current Fear & Greed Index from CNN API."""
        try:
            url = "https://cnn-fear-and-greed-index.p.rapidapi.com/cnn/v1/fear_and_greed/index"
            headers = {
                "x-rapidapi-key": self.fear_greed_api_key,
                "x-rapidapi-host": "cnn-fear-and-greed-index.p.rapidapi.com"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                score = data.get("fear_and_greed", {}).get("score", 50)
                rating = data.get("fear_and_greed", {}).get("rating", "Neutral")
                
                print(f"😨 Fear & Greed Index: {score} ({rating})")
                return score, rating
            else:
                print(f"⚠️ Fear & Greed API error: {response.status_code}")
                return None, None
                
        except Exception as e:
            print(f"❌ Error fetching Fear & Greed Index: {str(e)}")
            return None, None
    
    def get_historical_data_fmp(self, symbol, days=365):
        """Fetch historical price data using Financial Modeling Prep API."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
            params = {
                "apikey": self.fmp_api_key,
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d")
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if "historical" in data:
                    df = pd.DataFrame(data["historical"])
                    df["date"] = pd.to_datetime(df["date"])
                    df = df.sort_values("date")
                    df = df.set_index("date")
                    
                    # Calculate percentage change from start
                    if len(df) > 0:
                        start_price = float(df["close"].iloc[0])
                        df["pct_change"] = ((df["close"].astype(float) - start_price) / start_price) * 100
                    
                    print(f"✅ FMP: {symbol} - {len(df)} data points")
                    return df
                else:
                    print(f"⚠️ No historical data found for {symbol}")
                    return None
            else:
                print(f"⚠️ FMP API error for {symbol}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching {symbol} data from FMP: {str(e)}")
            return None
    
    def get_historical_data_twelve_data(self, symbol, days=365):
        """Fetch historical price data using Twelve Data API."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            url = "https://api.twelvedata.com/time_series"
            params = {
                "symbol": symbol,
                "interval": "1day",
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "apikey": self.twelve_data_api_key
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if "values" in data:
                    df = pd.DataFrame(data["values"])
                    df["datetime"] = pd.to_datetime(df["datetime"])
                    df = df.sort_values("datetime")
                    df = df.set_index("datetime")
                    
                    # Convert string values to numeric
                    df["close"] = pd.to_numeric(df["close"], errors='coerce')
                    
                    # Calculate percentage change from start
                    if len(df) > 0:
                        start_price = float(df["close"].iloc[0])
                        df["pct_change"] = ((df["close"] - start_price) / start_price) * 100
                    
                    print(f"✅ TwelveData: {symbol} - {len(df)} data points")
                    return df
                else:
                    print(f"⚠️ No historical data found for {symbol}")
                    return None
            else:
                print(f"⚠️ TwelveData API error for {symbol}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching {symbol} data from TwelveData: {str(e)}")
            return None
    
    def fetch_asset_data(self):
        """Fetch historical data for all assets using available APIs."""
        asset_data = {}
        
        for asset_name, symbol in self.assets.items():
            print(f"\n📈 Fetching data for {asset_name} ({symbol})...")
            
            # Try FMP first, then TwelveData as fallback
            df = self.get_historical_data_fmp(symbol)
            if df is None:
                df = self.get_historical_data_twelve_data(symbol)
            
            if df is not None:
                asset_data[asset_name] = df
            else:
                print(f"❌ Failed to fetch data for {asset_name}")
        
        return asset_data
    
    def create_comparison_chart(self, asset_data):
        """Create a comparison chart of asset performance."""
        try:
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(14, 8))
            
            colors = {
                "BTC": "#F7931A",  # Bitcoin orange
                "Gold": "#FFD700",  # Gold
                "QQQ": "#00A1F1"   # Nasdaq blue
            }
            
            for asset_name, df in asset_data.items():
                if df is not None and not df.empty:
                    ax.plot(df.index, df["pct_change"], 
                           label=asset_name, 
                           color=colors.get(asset_name, "#FFFFFF"),
                           linewidth=2.5)
            
            # Customize chart
            ax.set_title("Asset Performance During Market Fear\n1-Year Historical Comparison", 
                        fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel("Date", fontsize=12)
            ax.set_ylabel("Percentage Change (%)", fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=12, loc='upper left')
            
            # Format x-axis dates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.xticks(rotation=45)
            
            # Add zero line
            ax.axhline(y=0, color='white', linestyle='--', alpha=0.5)
            
            # Add current date annotation
            current_date = datetime.now().strftime("%B %d, %Y")
            ax.text(0.02, 0.98, f"Generated: {current_date}", 
                   transform=ax.transAxes, fontsize=10, 
                   verticalalignment='top', alpha=0.7)
            
            plt.tight_layout()
            
            # Save chart
            output_path = "output/fear_vs_assets.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                       facecolor='black', edgecolor='none')
            plt.close()
            
            print(f"📊 Chart saved: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Error creating chart: {str(e)}")
            return None
    
    def run_analysis(self):
        """Main analysis function - check Fear & Greed index and generate chart if needed."""
        print("🚀 Starting Visual Query Engine Analysis...")
        print("=" * 50)
        
        # Check Fear & Greed Index
        fear_score, fear_rating = self.get_fear_greed_index()
        
        if fear_score is None:
            print("❌ Cannot proceed without Fear & Greed Index data")
            return False
        
        # Check if we're in extreme fear (below 30)
        if fear_score < 30:
            print(f"\n😱 EXTREME FEAR DETECTED! Score: {fear_score}")
            print("📊 Generating asset comparison chart...")
            
            # Fetch asset data
            asset_data = self.fetch_asset_data()
            
            if asset_data:
                # Create and save chart
                chart_path = self.create_comparison_chart(asset_data)
                if chart_path:
                    print(f"\n✅ Analysis complete! Chart saved: {chart_path}")
                    return True
                else:
                    print("❌ Failed to create chart")
                    return False
            else:
                print("❌ No asset data available for chart generation")
                return False
        else:
            print(f"\n😌 Market sentiment is {fear_rating.lower()} (Score: {fear_score})")
            print("📊 No extreme fear detected - chart generation skipped")
            return True

def generate_extreme_fear_chart():
    """
    Generate extreme fear chart if Fear & Greed Index is below 30.
    
    Returns:
        str or None: Path to the generated chart file, or None if no chart was generated
    """
    try:
        # Initialize engine
        engine = VisualQueryEngine()
        
        # Check Fear & Greed Index
        fear_score, fear_rating = engine.get_fear_greed_index()
        
        if fear_score is None:
            print("⚠️ Cannot check Fear & Greed Index - skipping chart generation")
            return None
        
        # Check if we're in extreme fear (below 30)
        if fear_score < 30:
            print(f"😱 EXTREME FEAR DETECTED! Score: {fear_score} - Generating chart...")
            
            # Fetch asset data
            asset_data = engine.fetch_asset_data()
            
            if asset_data:
                # Create and save chart
                chart_path = engine.create_comparison_chart(asset_data)
                if chart_path:
                    print(f"✅ Extreme fear chart generated: {chart_path}")
                    return chart_path
                else:
                    print("❌ Failed to create extreme fear chart")
                    return None
            else:
                print("❌ No asset data available for chart generation")
                return None
        else:
            print(f"😌 Market sentiment is {fear_rating.lower()} (Score: {fear_score}) - No extreme fear chart needed")
            return None
            
    except Exception as e:
        print(f"❌ Error in generate_extreme_fear_chart: {str(e)}")
        return None

def main():
    """Main function to run the Visual Query Engine."""
    try:
        # Initialize engine
        engine = VisualQueryEngine()
        
        # Run analysis
        success = engine.run_analysis()
        
        if success:
            print("\n🎉 Visual Query Engine completed successfully!")
        else:
            print("\n❌ Visual Query Engine encountered errors")
            
    except Exception as e:
        print(f"❌ Fatal error in Visual Query Engine: {str(e)}")

def fetch_fear_greed_history(days=365):
    # This API only gives current value, so we simulate a flat series for demo
    url = "https://cnn-fear-and-greed-index.p.rapidapi.com/cnn/v1/fear_and_greed/index"
    headers = {
        "x-rapidapi-key": FEAR_GREED_API_KEY,
        "x-rapidapi-host": "cnn-fear-and-greed-index.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            score = int(data.get("fear_and_greed", {}).get("score", 50))
            today = datetime.now()
            dates = pd.date_range(today - timedelta(days=days), today)
            return pd.Series([score]*len(dates), index=dates, name='fear')
        else:
            logging.warning(f"Fear & Greed API error: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error fetching Fear & Greed Index: {str(e)}")
        return None

def fetch_vix_history(days=365):
    """Fetch VIX data using the dedicated FMP API function."""
    try:
        from utils.api_clients import fetch_vix_data
        return fetch_vix_data(days=days)
    except Exception as e:
        logging.error(f"Error fetching VIX history: {e}")
        return None

def fetch_asset_history(symbol, days=365):
    """Fetch asset history data, with special handling for VIX using multiple fallback sources."""
    
    # Special handling for VIX using multiple fallback sources
    if symbol.upper() == "VIX":
        return fetch_vix_with_fallbacks(days)
    
    # Default FMP handling for other assets
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
    return None

def fetch_vix_with_fallbacks(days=365):
    """
    Fetch VIX data using the dedicated FMP API function.
    """
    logging.info("📊 Fetching VIX data from FMP API...")
    
    try:
        from utils.api_clients import fetch_vix_data
        return fetch_vix_data(days=days)
    except Exception as e:
        logging.error(f"Error fetching VIX data: {e}")
        return None

def generate_comparison_chart(assets, condition=None, output_path="output/custom_query.png", days=365):
    """
    Generate a normalized performance comparison chart for given assets, filtered by condition.
    assets: list of asset symbols (e.g. ["GLD", "USO", "SPY"])
    condition: string like "fear < 30" or "vix > 20"
    output_path: where to save the chart
    days: number of days of history
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Fetch asset data with graceful error handling
    asset_dfs = {}
    missing_assets = []
    
    for symbol in assets:
        try:
            df = fetch_asset_history(symbol, days=days)
            if df is not None and not df.empty:
                asset_dfs[symbol] = df
                logging.info(f"✅ Successfully fetched data for {symbol}: {len(df)} records")
            else:
                missing_assets.append(symbol)
                logging.warning(f"⚠️ No data available for {symbol} - skipping this asset")
        except Exception as e:
            missing_assets.append(symbol)
            logging.warning(f"⚠️ Error fetching data for {symbol}: {e} - skipping this asset")
    
    # Check if we have any data to plot
    if not asset_dfs:
        logging.error(f"❌ No data available for any of the requested assets: {', '.join(assets)}")
        logging.error("Chart generation failed - all assets are missing data")
        return None
    
    # Log summary of what we have
    available_assets = list(asset_dfs.keys())
    logging.info(f"📊 Chart will include {len(available_assets)} assets: {', '.join(available_assets)}")
    
    if missing_assets:
        logging.info(f"⚠️ Skipped {len(missing_assets)} assets with missing data: {', '.join(missing_assets)}")
    # Merge on date
    merged = pd.concat(asset_dfs.values(), axis=1, join='inner')
    # Fetch and merge condition data
    filter_mask = pd.Series(True, index=merged.index)
    if condition:
        try:
            cond = parse_condition(condition)
            if cond['type'] == 'fear':
                fear_series = fetch_fear_greed_history(days=days)
                if fear_series is not None:
                    # Align to merged index
                    fear_series = fear_series.reindex(merged.index, method='nearest')
                    op = cond['operator']
                    val = cond['value']
                    if op == '<':
                        filter_mask = fear_series < val
                    elif op == '>':
                        filter_mask = fear_series > val
                    elif op == '<=':
                        filter_mask = fear_series <= val
                    elif op == '>=':
                        filter_mask = fear_series >= val
                    elif op == '==':
                        filter_mask = fear_series == val
                    elif op == '!=':
                        filter_mask = fear_series != val
            elif cond['type'] == 'vix':
                vix_df = fetch_vix_history(days=days)
                if vix_df is not None:
                    vix_series = vix_df['vix'].reindex(merged.index, method='nearest')
                    op = cond['operator']
                    val = cond['value']
                    if op == '<':
                        filter_mask = vix_series < val
                    elif op == '>':
                        filter_mask = vix_series > val
                    elif op == '<=':
                        filter_mask = vix_series <= val
                    elif op == '>=':
                        filter_mask = vix_series >= val
                    elif op == '==':
                        filter_mask = vix_series == val
                    elif op == '!=':
                        filter_mask = vix_series != val
        except Exception as e:
            logging.warning(f"⚠️ Overlay condition failed to apply: {e}")
    filtered = merged[filter_mask]
    if filtered.empty:
        logging.warning("No data after filtering by condition.")
        return
    # Normalize and plot
    plt.figure(figsize=(12, 6))
    for symbol in available_assets:  # Use available_assets instead of original assets list
        if symbol in filtered.columns:  # Double-check the symbol exists in filtered data
            normed = filtered[symbol] / filtered[symbol].iloc[0] * 100
            plt.plot(filtered.index, normed, label=symbol)
    plt.title('Asset Performance Comparison')
    plt.xlabel('Date')
    plt.ylabel('Normalized Price (100 = start)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logging.info(f"Chart saved to {output_path}")
    return output_path

if __name__ == "__main__":
    main() 