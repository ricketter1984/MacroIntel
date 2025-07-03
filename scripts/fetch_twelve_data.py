#!/usr/bin/env python3
"""
Twelve Data Chart Fetcher Script

This script fetches forex and equity chart data from Twelve Data API.
Designed to be called by the API dispatcher in an isolated environment.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(dotenv_path=project_root / "config" / ".env")

def fetch_twelve_data():
    """Fetch chart data from Twelve Data API."""
    try:
        from utils.api_clients import fetch_twelve_data_chart
        
        print("Fetching Twelve Data forex/equity chart data...")
        
        # Define symbols to fetch
        symbols = ["BTCUSD", "EURUSD", "GBPUSD", "XAUUSD", "SPY", "QQQ", "AAPL", "MSFT"]
        
        # Fetch data for each symbol
        chart_data = {}
        for symbol in symbols:
            try:
                data = fetch_twelve_data_chart(symbol, interval="1day", outputsize=30)
                if data and len(data) > 0:
                    current_price = float(data["close"].iloc[-1])
                    previous_price = float(data["close"].iloc[-2]) if len(data) > 1 else current_price
                    daily_return = ((current_price / previous_price) - 1) * 100
                    
                    # Determine trend
                    if daily_return > 1:
                        trend = "Strong Bullish"
                    elif daily_return > 0:
                        trend = "Bullish"
                    elif daily_return > -1:
                        trend = "Bearish"
                    else:
                        trend = "Strong Bearish"
                    
                    chart_data[symbol] = {
                        "current_price": current_price,
                        "daily_return": daily_return,
                        "trend": trend,
                        "volume": float(data["volume"].iloc[-1]) if "volume" in data.columns else 0,
                        "data": data.to_dict("records")
                    }
                    print(f"{symbol}: ${chart_data[symbol]['current_price']:.4f} ({chart_data[symbol]['daily_return']:+.2f}%) - {chart_data[symbol]['trend']}")
            except Exception as e:
                print(f"Error fetching {symbol}: {str(e)}")
        
        if chart_data:
            # Calculate market summary
            bullish_count = len([s for s in chart_data.values() if "Bullish" in s["trend"]])
            bearish_count = len([s for s in chart_data.values() if "Bearish" in s["trend"]])
            avg_return = sum(s["daily_return"] for s in chart_data.values()) / len(chart_data)
            
            market_summary = {
                "bullish_symbols": bullish_count,
                "bearish_symbols": bearish_count,
                "total_symbols": len(chart_data),
                "avg_daily_return": avg_return,
                "market_sentiment": "Bullish" if bullish_count > bearish_count else "Bearish" if bearish_count > bullish_count else "Neutral"
            }
            
            print(f"\nMarket Summary:")
            print(f"  Bullish Symbols: {bullish_count}")
            print(f"  Bearish Symbols: {bearish_count}")
            print(f"  Total Symbols: {len(chart_data)}")
            print(f"  Avg Daily Return: {avg_return:+.2f}%")
            print(f"  Sentiment: {market_summary['market_sentiment']}")
            
            # Save to output directory
            output_dir = project_root / "output"
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"twelve_data_{timestamp}.json"
            
            result_data = {
                "success": True,
                "chart_data": chart_data,
                "market_summary": market_summary,
                "timestamp": datetime.now().isoformat(),
                "source": "twelve_data"
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, default=str)
            
            print(f"Chart data saved to: {output_file}")
            
            return result_data
            
        else:
            error_msg = "No chart data retrieved"
            print(f"{error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "source": "twelve_data"
            }
            
    except ImportError as e:
        error_msg = f"Import error: {e}"
        print(f"{error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
            "source": "twelve_data"
        }
    except Exception as e:
        error_msg = f"Error fetching Twelve Data: {e}"
        print(f"{error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
            "source": "twelve_data"
        }

def main():
    """Main function to execute the chart data fetching."""
    print("Fetching Twelve Data Forex/Equity Chart Data...")
    print(f"Project root: {project_root}")
    print(f"Python executable: {sys.executable}")
    
    # Check API key
    api_key = os.getenv("TWELVE_DATA_API_KEY")
    if not api_key:
        print("TWELVE_DATA_API_KEY not found in environment variables")
        sys.exit(1)
    
    # Fetch chart data
    result = fetch_twelve_data()
    
    # Print result
    print(f"\nChart data fetch completed successfully!")
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    if result["success"]:
        sys.exit(0)
    else:
        print(f"Chart data fetch failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
