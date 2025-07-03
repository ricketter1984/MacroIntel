#!/usr/bin/env python3
"""
Polygon Market Indices Fetcher Script

This script fetches market indices data from Polygon API and processes it for MacroIntel.
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

def fetch_polygon_indices():
    """Fetch market indices data from Polygon API."""
    try:
        from utils.api_clients import fetch_polygon_indices
        
        print("Fetching Polygon market indices data...")
        
        # Define indices to fetch
        indices = ["SPY", "QQQ", "IWM", "GLD", "TLT", "VIX"]
        
        # Fetch data for each index
        market_data = {}
        for symbol in indices:
            try:
                data = fetch_polygon_indices(symbol)
                if data and len(data) > 0:
                    market_data[symbol] = {
                        "last_price": data["close"].iloc[-1],
                        "daily_change_pct": ((data["close"].iloc[-1] / data["close"].iloc[-2]) - 1) * 100 if len(data) > 1 else 0,
                        "data": data.to_dict("records")
                    }
                    print(f"{symbol}: ${market_data[symbol]['last_price']:.2f} ({market_data[symbol].get('daily_change_pct', 0):+.2f}%)")
            except Exception as e:
                print(f"Error fetching {symbol}: {str(e)}")
        
        if market_data:
            # Calculate market summary
            advancing = len([s for s in market_data.values() if s.get('daily_change_pct', 0) > 0])
            declining = len([s for s in market_data.values() if s.get('daily_change_pct', 0) < 0])
            unchanged = len([s for s in market_data.values() if s.get('daily_change_pct', 0) == 0])
            
            market_summary = {
                "advancing": advancing,
                "declining": declining,
                "unchanged": unchanged,
                "total": len(market_data),
                "market_sentiment": "Bullish" if advancing > declining else "Bearish" if declining > advancing else "Neutral"
            }
            
            print(f"\nMarket Summary:")
            print(f"  Advancing: {advancing}")
            print(f"  Declining: {declining}")
            print(f"  Unchanged: {unchanged}")
            print(f"  Sentiment: {market_summary['market_sentiment']}")
            
            # Save to output directory
            output_dir = project_root / "output"
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"polygon_indices_{timestamp}.json"
            
            result_data = {
                "market_data": market_data,
                "market_summary": market_summary,
                "timestamp": datetime.now().isoformat(),
                "source": "polygon"
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, default=str)
            
            print(f"Indices data saved to: {output_file}")
            
            return {
                "success": True,
                "indices_count": len(market_data),
                "output_file": str(output_file),
                "market_summary": market_summary,
                "timestamp": datetime.now().isoformat(),
                "source": "polygon"
            }
        else:
            error_msg = "No market data retrieved"
            print(f"{error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "source": "polygon"
            }
            
    except ImportError as e:
        error_msg = f"Import error: {e}"
        print(f"{error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
            "source": "polygon"
        }
    except Exception as e:
        error_msg = f"Error fetching Polygon indices: {e}"
        print(f"{error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
            "source": "polygon"
        }

def main():
    """Main function to execute the indices fetching."""
    print("Fetching Polygon Market Indices Data...")
    print(f"Project root: {project_root}")
    print(f"Python executable: {sys.executable}")
    
    # Check API key
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        print("POLYGON_API_KEY not found in environment variables")
        sys.exit(1)
    
    # Fetch indices
    result = fetch_polygon_indices()
    
    # Print result
    print(f"\nIndices fetch completed successfully!")
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    if result["success"]:
        sys.exit(0)
    else:
        print(f"Indices fetch failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
