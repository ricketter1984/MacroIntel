#!/usr/bin/env python3
"""
Messari Crypto Intelligence Fetcher Script

This script fetches crypto intelligence data from Messari API.
Designed to be called by the API dispatcher in an isolated environment.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(dotenv_path=project_root / "config" / ".env")

def fetch_messari_intel():
    """Fetch crypto intelligence data from Messari API."""
    try:
        from utils.api_clients import fetch_messari_metrics, fetch_messari_news
        
        print("Fetching Messari crypto intelligence data...")
        
        # Define crypto assets to fetch
        crypto_assets = ["bitcoin", "ethereum", "cardano", "solana", "polkadot"]
        
        # Fetch metrics for each asset
        crypto_data = {}
        for symbol in crypto_assets:
            try:
                metrics = fetch_messari_metrics(symbol)
                if metrics:
                    crypto_data[symbol] = {
                        "price_usd": metrics.get("price_usd", 0),
                        "percent_change_usd_last_24_hours": metrics.get("percent_change_usd_last_24_hours", 0),
                        "market_cap": metrics.get("market_cap", 0),
                        "volume_last_24_hours": metrics.get("volume_last_24_hours", 0),
                        "roi_data": metrics.get("roi_data", {})
                    }
                    print(f"{symbol}: ${crypto_data[symbol]['price_usd']:.2f} ({crypto_data[symbol]['percent_change_usd_last_24_hours']:+.2f}%)")
            except Exception as e:
                print(f"Error fetching {symbol}: {str(e)}")
        
        # Fetch crypto news
        crypto_news = []
        try:
            news_data = fetch_messari_news(limit=10)
            if news_data:
                crypto_news = news_data[:10]  # Limit to 10 articles
                print(f"Fetched {len(crypto_news)} recent crypto news articles")
        except Exception as e:
            print(f"Error fetching crypto news: {str(e)}")
        
        if crypto_data or crypto_news:
            # Calculate crypto market summary
            total_market_cap = sum(asset.get("market_cap", 0) for asset in crypto_data.values())
            avg_change_24h = sum(asset.get("percent_change_usd_last_24_hours", 0) for asset in crypto_data.values()) / len(crypto_data) if crypto_data else 0
            
            market_summary = {
                "total_market_cap": total_market_cap,
                "avg_24h_change": avg_change_24h,
                "assets_tracked": len(crypto_data),
                "news_articles": len(crypto_news),
                "market_sentiment": "Bullish" if avg_change_24h > 0 else "Bearish" if avg_change_24h < 0 else "Neutral"
            }
            
            print(f"\nCrypto Market Summary:")
            print(f"  Total Market Cap: ${total_market_cap:,.0f}")
            print(f"  Avg 24h Change: {avg_change_24h:+.2f}%")
            print(f"  Assets Tracked: {len(crypto_data)}")
            print(f"  News Articles: {len(crypto_news)}")
            print(f"  Sentiment: {market_summary['market_sentiment']}")
            
            # Save to output directory
            output_dir = project_root / "output"
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"messari_intel_{timestamp}.json"
            
            result_data = {
                "success": True,
                "crypto_data": crypto_data,
                "crypto_news": crypto_news,
                "market_summary": market_summary,
                "timestamp": datetime.now().isoformat(),
                "source": "messari"
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, default=str)
            
            print(f"Crypto data saved to: {output_file}")
            
            return result_data
            
        else:
            error_msg = "No crypto data retrieved"
            print(f"{error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "source": "messari"
            }
            
    except ImportError as e:
        error_msg = f"Import error: {e}"
        print(f"{error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
            "source": "messari"
        }
    except Exception as e:
        error_msg = f"Error fetching Messari data: {e}"
        print(f"{error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
            "source": "messari"
        }

def main():
    """Main function to execute the crypto intelligence fetching."""
    print("Fetching Messari Crypto Intelligence Data...")
    print(f"Project root: {project_root}")
    print(f"Python executable: {sys.executable}")
    
    # Check API key
    api_key = os.getenv("MESSARI_API_KEY")
    if not api_key:
        print("MESSARI_API_KEY not found in environment variables")
        sys.exit(1)
    
    # Fetch crypto intelligence
    result = fetch_messari_intel()
    
    # Print result
    print(f"\nCrypto intelligence fetch completed successfully!")
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    if result["success"]:
        sys.exit(0)
    else:
        print(f"Crypto intelligence fetch failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
