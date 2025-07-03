#!/usr/bin/env python3
"""
Script to recreate all API scripts with proper indentation.
"""

import os
from pathlib import Path

def create_polygon_indices_script():
    """Create the Polygon indices script."""
    content = '''#!/usr/bin/env python3
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
            
            print(f"\\nMarket Summary:")
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
    print(f"\\nIndices fetch completed successfully!")
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    if result["success"]:
        sys.exit(0)
    else:
        print(f"Indices fetch failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    with open("scripts/fetch_polygon_indices.py", 'w', encoding='utf-8') as f:
        f.write(content)
    print("Created fetch_polygon_indices.py")

def create_fmp_calendar_script():
    """Create the FMP calendar script."""
    content = '''#!/usr/bin/env python3
"""
FMP Economic Calendar Fetcher Script

This script fetches economic calendar data from Financial Modeling Prep API.
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

def fetch_fmp_calendar():
    """Fetch economic calendar data from FMP API."""
    try:
        from utils.api_clients import fetch_fmp_calendar
        
        print("Fetching FMP economic calendar data...")
        
        # Fetch calendar data for next 7 days
        end_date = datetime.now() + timedelta(days=7)
        calendar_data = fetch_fmp_calendar(
            from_date=datetime.now().strftime("%Y-%m-%d"),
            to_date=end_date.strftime("%Y-%m-%d")
        )
        
        if calendar_data and len(calendar_data) > 0:
            # Process and categorize events
            processed_events = []
            high_impact_events = []
            medium_impact_events = []
            
            for event in calendar_data:
                processed_event = {
                    "event": event.get("event", "Unknown"),
                    "date": event.get("date", ""),
                    "time": event.get("time", ""),
                    "country": event.get("country", ""),
                    "currency": event.get("currency", ""),
                    "impact": event.get("impact", "Low"),
                    "actual": event.get("actual", ""),
                    "forecast": event.get("forecast", ""),
                    "previous": event.get("previous", "")
                }
                processed_events.append(processed_event)
                
                if processed_event["impact"] == "High":
                    high_impact_events.append(processed_event)
                elif processed_event["impact"] == "Medium":
                    medium_impact_events.append(processed_event)
            
            print(f"Successfully fetched {len(processed_events)} economic events")
            print(f"  High impact: {len(high_impact_events)}")
            print(f"  Medium impact: {len(medium_impact_events)}")
            print(f"  Low impact: {len(processed_events) - len(high_impact_events) - len(medium_impact_events)}")
            
            # Save to output directory
            output_dir = project_root / "output"
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"fmp_calendar_{timestamp}.json"
            
            result_data = {
                "success": True,
                "total_events": len(processed_events),
                "high_impact_events": high_impact_events,
                "medium_impact_events": medium_impact_events,
                "all_events": processed_events,
                "timestamp": datetime.now().isoformat(),
                "source": "fmp_calendar"
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, default=str)
            
            print(f"Calendar data saved to: {output_file}")
            
            return result_data
            
        else:
            error_msg = "No calendar data retrieved"
            print(f"{error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "source": "fmp_calendar"
            }
            
    except ImportError as e:
        error_msg = f"Import error: {e}"
        print(f"{error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
            "source": "fmp_calendar"
        }
    except Exception as e:
        error_msg = f"Error fetching FMP calendar: {e}"
        print(f"{error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
            "source": "fmp_calendar"
        }

def main():
    """Main function to execute the calendar fetching."""
    print("Fetching FMP Economic Calendar Data...")
    print(f"Project root: {project_root}")
    print(f"Python executable: {sys.executable}")
    
    # Check API key
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        print("FMP_API_KEY not found in environment variables")
        sys.exit(1)
    
    # Fetch calendar
    result = fetch_fmp_calendar()
    
    # Print result
    print(f"\\nCalendar fetch completed successfully!")
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    if result["success"]:
        sys.exit(0)
    else:
        print(f"Calendar fetch failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    with open("scripts/fetch_fmp_calendar.py", 'w', encoding='utf-8') as f:
        f.write(content)
    print("Created fetch_fmp_calendar.py")

def create_messari_script():
    """Create the Messari script."""
    content = '''#!/usr/bin/env python3
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
            
            print(f"\\nCrypto Market Summary:")
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
    print(f"\\nCrypto intelligence fetch completed successfully!")
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    if result["success"]:
        sys.exit(0)
    else:
        print(f"Crypto intelligence fetch failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    with open("scripts/fetch_messari_intel.py", 'w', encoding='utf-8') as f:
        f.write(content)
    print("Created fetch_messari_intel.py")

def create_twelve_data_script():
    """Create the Twelve Data script."""
    content = '''#!/usr/bin/env python3
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
            
            print(f"\\nMarket Summary:")
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
    print(f"\\nChart data fetch completed successfully!")
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    if result["success"]:
        sys.exit(0)
    else:
        print(f"Chart data fetch failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    with open("scripts/fetch_twelve_data.py", 'w', encoding='utf-8') as f:
        f.write(content)
    print("Created fetch_twelve_data.py")

def main():
    """Recreate all scripts."""
    print("Recreating all API scripts with proper indentation...")
    
    # Ensure scripts directory exists
    scripts_dir = Path("scripts")
    scripts_dir.mkdir(exist_ok=True)
    
    # Recreate all scripts
    create_polygon_indices_script()
    create_fmp_calendar_script()
    create_messari_script()
    create_twelve_data_script()
    
    print("All scripts recreated successfully!")

if __name__ == "__main__":
    main() 