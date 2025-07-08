#!/usr/bin/env python3
"""
Polygon Market Indices Fetcher Script

This script fetches market indices data from Polygon API and processes it for MacroIntel.
Designed to be called by the API dispatcher in an isolated environment.
"""

import os
import sys
import json
import requests
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(dotenv_path=project_root / "config" / ".env")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_polygon_indices(config=None):
    """Fetch market indices data from Polygon API using v2/aggs/ticker endpoint."""
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        raise ValueError("Missing POLYGON_API_KEY in environment variables")

    indices = {
        "SPX": "I:SPX",
        "NDX": "I:NDX",
        "RUT": "I:RUT"
    }

    base_url = "https://api.polygon.io/v2/aggs/ticker"
    headers = {"accept": "application/json"}
    results = {}

    for label, ticker in indices.items():
        url = f"{base_url}/{ticker}/prev?adjusted=true&apiKey={api_key}"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            if "results" in data and data["results"]:
                results[label] = {
                    "close": data["results"][0]["c"],
                    "volume": data["results"][0]["v"],
                    "timestamp": data["results"][0]["t"]
                }
            else:
                logging.warning(f"No results for {label} ({ticker})")
        except Exception as e:
            logging.error(f"[Polygon] Error fetching {label}: {e}")
            results[label] = None

    return results

def main():
    """Main function to execute the indices fetching."""
    print("Fetching Polygon Market Indices Data...")
    print(f"Project root: {project_root}")
    print(f"Python executable: {sys.executable}")
    
    try:
        # Fetch indices
        results = fetch_polygon_indices()
        
        if results:
            # Save to output directory
            output_dir = project_root / "output"
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"polygon_indices_{timestamp}.json"
            
            result_data = {
                "market_data": results,
                "timestamp": datetime.now().isoformat(),
                "source": "polygon"
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, default=str)
            
            print(f"Indices data saved to: {output_file}")
            
            # Print summary
            for label, data in results.items():
                if data:
                    print(f"{label}: Close: {data['close']}, Volume: {data['volume']}")
                else:
                    print(f"{label}: No data available")
            
            return {
                "success": True,
                "indices_count": len([r for r in results.values() if r is not None]),
                "output_file": str(output_file),
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
            
    except Exception as e:
        error_msg = f"Error fetching Polygon indices: {e}"
        print(f"{error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
            "source": "polygon"
        }

if __name__ == "__main__":
    result = main()
    
    # Print result
    if result is None:
        print("Indices fetch failed: No result returned")
        sys.exit(1)
    
    print(f"\nIndices fetch completed!")
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    if result["success"]:
        sys.exit(0)
    else:
        print(f"Indices fetch failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)
