import os
import requests
import datetime as dt
import re
from dotenv import load_dotenv
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET

# Load environment variables
load_dotenv(dotenv_path="config/.env")

def strip_emojis(text: str) -> str:
    import re
    if not text:
        return ""
    # Only remove actual emoji characters, preserve dashes, apostrophes, etc.
    return re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF]', '', text)

def init_env():
    # Environment already loaded above
    pass

# -- FMP Client (updated to use v4)
def fetch_fmp_events():
    api_key = os.getenv("FMP_API_KEY")
    url = "https://financialmodelingprep.com/api/v4/economic_calendar"
    params = {
        "from": dt.datetime.utcnow().strftime("%Y-%m-%d"),
        "to": dt.datetime.utcnow().strftime("%Y-%m-%d"),
        "apikey": api_key
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[FMP ERROR] {response.status_code}: {response.text}")
        return []

def fetch_fmp_news():
    """
    Fetch news from Financial Modeling Prep API v3/stock_news endpoint
    Returns headlines about macro/market events
    """
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        print("[FMP ERROR] FMP_API_KEY not found in environment variables")
        return []
    
    url = "https://financialmodelingprep.com/api/v3/stock_news"
    params = {
        "apikey": api_key,
        "limit": 50  # Get recent news items
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            news_data = response.json()
            formatted_news = []
            
            for item in news_data:
                formatted_news.append({
                    "title": item.get("title", ""),
                    "body": item.get("text", ""),
                    "url": item.get("url", ""),
                    "timestamp": item.get("publishedDate", "")
                })
            
            return formatted_news
        else:
            print(f"[FMP NEWS ERROR] {response.status_code}: {response.text}")
            return []
    except Exception as e:
        print(f"[FMP NEWS ERROR] Exception: {e}")
        return []

def fetch_polygon_news():
    """
    Fetch financial news from Polygon API /v2/reference/news endpoint
    Returns financial news items
    """
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        print("[POLYGON ERROR] POLYGON_API_KEY not found in environment variables")
        return []
    
    url = "https://api.polygon.io/v2/reference/news"
    params = {
        "apiKey": api_key,
        "limit": 50,
        "order": "desc"
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            news_data = response.json()
            formatted_news = []
            
            for item in news_data.get("results", []):
                formatted_news.append({
                    "title": item.get("title", ""),
                    "body": item.get("description", ""),
                    "url": item.get("article_url", ""),
                    "timestamp": item.get("published_utc", "")
                })
            
            return formatted_news
        else:
            print(f"[POLYGON NEWS ERROR] {response.status_code}: {response.text}")
            return []
    except Exception as e:
        print(f"[POLYGON NEWS ERROR] Exception: {e}")
        return []

def fetch_messari_news(**kwargs):
    """
    Fetch recent articles from Messari API
    Returns parsed news items
    """
    api_key = os.getenv("MESSARI_API_KEY")
    if not api_key:
        print("[MESSARI ERROR] MESSARI_API_KEY not found in environment variables")
        return []
    
    url = "https://data.messari.io/api/v1/news"
    headers = {
        "x-messari-api-key": api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            news_data = response.json()
            formatted_news = []
            
            for item in news_data.get("data", []):
                formatted_news.append({
                    "title": item.get("title", ""),
                    "body": item.get("content", ""),
                    "url": item.get("url", ""),
                    "timestamp": item.get("published_at", "")
                })
            
            return formatted_news
        else:
            print(f"[MESSARI NEWS ERROR] {response.status_code}: {response.text}")
            return []
    except Exception as e:
        print(f"[MESSARI NEWS ERROR] Exception: {e}")
        return []



def fetch_all_news():
    """
    Fetch news from all available sources and merge results
    Returns a combined list of news items from all sources
    """
    all_news = []
    
    # Fetch from all sources
    print("Fetching news from all sources...")
    
    # Perplexity macro news
    try:
        from agents.perplexity_macro_agent import PerplexityMacroAgent
        perplexity_agent = PerplexityMacroAgent()
        perplexity_result = perplexity_agent.run()
        perplexity_articles = perplexity_result.get('articles', [])
        print(f"Perplexity: {len(perplexity_articles)} articles")
        
        # Convert Perplexity format to standard format
        for item in perplexity_articles:
            # Ensure all text fields are properly encoded
            title = strip_emojis(item.get("title", ""))
            summary = strip_emojis(item.get("summary", ""))
            url = item.get("url", "")
            timestamp = item.get("timestamp", "")
            
            all_news.append({
                "title": title,
                "body": summary,  # Use summary as body
                "url": url,
                "timestamp": timestamp,
                "source": "perplexity"
            })
    except Exception as e:
        print(f"Perplexity fetch failed: {e}")
    
    # FMP news
    try:
        fmp_news = fetch_fmp_news()
        print(f"FMP: {len(fmp_news)} articles")
        for item in fmp_news:
            # Ensure all text fields are properly encoded
            title = strip_emojis(item.get("title", ""))
            body = strip_emojis(item.get("body", ""))
            url = item.get("url", "")
            timestamp = item.get("timestamp", "")
            
            all_news.append({
                "title": title,
                "body": body,
                "url": url,
                "timestamp": timestamp,
                "source": "fmp"
            })
    except Exception as e:
        print(f"FMP fetch failed: {e}")
    
    # Polygon news
    try:
        polygon_news = fetch_polygon_news()
        print(f"Polygon: {len(polygon_news)} articles")
        for item in polygon_news:
            # Ensure all text fields are properly encoded
            title = strip_emojis(item.get("title", ""))
            body = strip_emojis(item.get("body", ""))
            url = item.get("url", "")
            timestamp = item.get("timestamp", "")
            
            all_news.append({
                "title": title,
                "body": body,
                "url": url,
                "timestamp": timestamp,
                "source": "polygon"
            })
    except Exception as e:
        print(f"Polygon fetch failed: {e}")
    
    # Messari news
    try:
        messari_news = fetch_messari_news()
        print(f"Messari: {len(messari_news)} articles")
        for item in messari_news:
            # Ensure all text fields are properly encoded
            title = strip_emojis(item.get("title", ""))
            body = strip_emojis(item.get("body", ""))
            url = item.get("url", "")
            timestamp = item.get("timestamp", "")
            
            all_news.append({
                "title": title,
                "body": body,
                "url": url,
                "timestamp": timestamp,
                "source": "messari"
            })
    except Exception as e:
        print(f"Messari fetch failed: {e}")
    
    return all_news

# -- Polygon Indices Client
def fetch_polygon_indices(config=None):
    """Fetch index data from Polygon API v3 reference endpoint for major indices."""
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        print("[ERROR] POLYGON_API_KEY not set.")
        return None

    # Use v3 reference endpoint for indices
    url = f"https://api.polygon.io/v3/reference/tickers?ticker.type=index&active=true&apiKey={api_key}"
    
    print(f"[INFO] Fetching Polygon indices from: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Log response metadata
        print(f"[INFO] Polygon API Response Status: {response.status_code}")
        print(f"[INFO] Response contains {data.get('count', 0)} total results")
        print(f"[INFO] Next URL: {data.get('next_url', 'None')}")
        
        # Log any warnings or additional info
        if 'status' in data:
            print(f"[INFO] API Status: {data['status']}")
        if 'request_id' in data:
            print(f"[INFO] Request ID: {data['request_id']}")

        if "results" in data:
            # Filter for major indices we're interested in
            target_indices = ["SPX", "NDX", "RUT", "VIX", "DJI"]
            index_data = {}
            
            for ticker_info in data["results"]:
                ticker = ticker_info.get("ticker", "")
                # Check if it's one of our target indices
                if any(target in ticker for target in target_indices):
                    index_data[ticker] = {
                        "ticker": ticker,
                        "name": ticker_info.get("name", ""),
                        "market": ticker_info.get("market", ""),
                        "locale": ticker_info.get("locale", ""),
                        "primary_exchange": ticker_info.get("primary_exchange", ""),
                        "type": ticker_info.get("type", ""),
                        "active": ticker_info.get("active", False),
                        "currency_name": ticker_info.get("currency_name", ""),
                        "cik": ticker_info.get("cik", ""),
                        "composite_figi": ticker_info.get("composite_figi", ""),
                        "share_class_figi": ticker_info.get("share_class_figi", ""),
                        "last_updated_utc": ticker_info.get("last_updated_utc", "")
                    }
            
            print(f"[SUCCESS] Retrieved {len(index_data)} index references: {list(index_data.keys())}")
            return index_data
        else:
            print(f"[FAIL] No 'results' field in response. Response keys: {list(data.keys())}")
            print(f"[DEBUG] Full response: {data}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"[REQUEST ERROR] {e}")
        return None
    except Exception as e:
        print(f"[UNEXPECTED ERROR] {e}")
        return None

# -- FMP Calendar Client
def fetch_fmp_calendar(from_date=None, to_date=None):
    """
    Fetch economic calendar data from FMP API /v3/economic_calendar endpoint
    Returns today's economic events and impact levels
    """
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        print("[FMP ERROR] FMP_API_KEY not found in environment variables")
        return []
    
    # Default to today if no dates provided
    if not from_date:
        from_date = dt.datetime.now().strftime("%Y-%m-%d")
    if not to_date:
        to_date = dt.datetime.now().strftime("%Y-%m-%d")
    
    url = "https://financialmodelingprep.com/api/v3/economic_calendar"
    params = {
        "from": from_date,
        "to": to_date,
        "apikey": api_key
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            calendar_data = response.json()
            formatted_events = []
            
            for event in calendar_data:
                formatted_events.append({
                    "event": event.get("event", ""),
                    "date": event.get("date", ""),
                    "time": event.get("time", ""),
                    "country": event.get("country", ""),
                    "currency": event.get("currency", ""),
                    "impact": event.get("impact", "Low"),
                    "actual": event.get("actual", ""),
                    "forecast": event.get("forecast", ""),
                    "previous": event.get("previous", "")
                })
            
            return formatted_events
        else:
            print(f"[FMP CALENDAR ERROR] {response.status_code}: {response.text}")
            return []
    except Exception as e:
        print(f"[FMP CALENDAR ERROR] Exception: {e}")
        return []

# -- Messari Metrics Client
def fetch_messari_metrics(symbol="bitcoin"):
    """
    Fetch crypto metrics from Messari API
    Returns structured metrics data for crypto assets
    """
    api_key = os.getenv("MESSARI_API_KEY")
    if not api_key:
        print("[MESSARI ERROR] MESSARI_API_KEY not found in environment variables")
        return None
    
    # Try different endpoints for Messari
    endpoints = [
        f"https://data.messari.io/api/v1/assets/{symbol}/metrics",
        f"https://data.messari.io/api/v1/assets/{symbol}",
        f"https://data.messari.io/api/v1/assets/{symbol}/profile"
    ]
    
    for url in endpoints:
        headers = {
            "x-messari-api-key": api_key
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and data.get("data"):
                    metrics = data["data"]
                    # Handle different response formats
                    if "market_data" in metrics:
                        return {
                            "symbol": symbol,
                            "price_usd": metrics.get("market_data", {}).get("price_usd", 0),
                            "percent_change_usd_last_24_hours": metrics.get("market_data", {}).get("percent_change_usd_last_24_hours", 0),
                            "market_cap": metrics.get("market_data", {}).get("market_cap", 0),
                            "volume_last_24_hours": metrics.get("market_data", {}).get("volume_last_24_hours", 0),
                            "roi_data": metrics.get("roi_data", {}),
                            "timestamp": dt.datetime.now().isoformat()
                        }
                    elif "profile" in metrics:
                        # Profile endpoint response
                        return {
                            "symbol": symbol,
                            "name": metrics.get("profile", {}).get("name", symbol),
                            "category": metrics.get("profile", {}).get("category", ""),
                            "description": metrics.get("profile", {}).get("description", ""),
                            "timestamp": dt.datetime.now().isoformat()
                        }
        except Exception as e:
            continue
    
    print(f"[MESSARI METRICS ERROR] No data returned for {symbol} from any endpoint")
    return None

# -- Twelve Data Chart Client
def fetch_twelve_data_chart(symbol, interval="1day", outputsize=30):
    """
    Fetch chart data from Twelve Data API /time_series endpoint
    Returns OHLC chart data for symbols like BTC/USD or AAPL
    """
    api_key = os.getenv("TWELVE_DATA_API_KEY")
    if not api_key:
        print("[TWELVE DATA ERROR] TWELVE_DATA_API_KEY not found in environment variables")
        return None
    
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": api_key
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok" and data.get("values"):
                # Convert to pandas DataFrame format
                import pandas as pd
                df = pd.DataFrame(data["values"])
                
                # Handle missing columns gracefully
                required_columns = ["datetime", "open", "high", "low", "close"]
                for col in required_columns:
                    if col not in df.columns:
                        print(f"[TWELVE DATA ERROR] Missing required column: {col}")
                        return None
                
                df["datetime"] = pd.to_datetime(df["datetime"])
                df["open"] = pd.to_numeric(df["open"], errors='coerce')
                df["high"] = pd.to_numeric(df["high"], errors='coerce')
                df["low"] = pd.to_numeric(df["low"], errors='coerce')
                df["close"] = pd.to_numeric(df["close"], errors='coerce')
                
                # Handle volume column if it exists
                if "volume" in df.columns:
                    df["volume"] = pd.to_numeric(df["volume"], errors='coerce')
                
                df.set_index("datetime", inplace=True)
                return df
            else:
                print(f"[TWELVE DATA ERROR] No data returned for {symbol}")
                return None
        else:
            print(f"[TWELVE DATA ERROR] {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"[TWELVE DATA ERROR] Exception: {e}")
        return None

# -- VIX Data Client (FMP API)
def fetch_vix_data(days=365):
    """
    Fetch VIX data from FMP API using the correct symbol format ^VIX.
    
    Args:
        days (int): Number of days of historical data to fetch (default: 365)
        
    Returns:
        pandas.DataFrame: DataFrame with datetime index and VIX close prices
        None: If fetch fails
    """
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        print("[FMP VIX ERROR] FMP_API_KEY not found in environment variables")
        return None
    
    import pandas as pd
    
    url = "https://financialmodelingprep.com/api/v3/historical-chart/1day/VIXY"
    params = {
        "serietype": "line",
        "apikey": api_key,
        "from": (dt.datetime.now() - dt.timedelta(days=days)).strftime("%Y-%m-%d"),
        "to": dt.datetime.now().strftime("%Y-%m-%d")
    }
    
    try:
        print(f"[FMP VIX] Fetching VIX data for last {days} days...")
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if we have historical data
            if "historical" in data and data["historical"]:
                # Convert to DataFrame
                df = pd.DataFrame(data["historical"])
                
                # Parse date and convert to datetime index
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date').sort_index()
                
                # Extract only the close price and rename to VIX
                result_df = df[['close']].rename(columns={'close': 'VIX'})
                
                print(f"[FMP VIX SUCCESS] Retrieved {len(result_df)} VIX data points")
                print(f"[FMP VIX] Date range: {result_df.index.min()} to {result_df.index.max()}")
                print(f"[FMP VIX] VIX range: {result_df['VIX'].min():.2f} - {result_df['VIX'].max():.2f}")
                
                return result_df
            else:
                print("[FMP VIX ERROR] No historical data found in response")
                return None
        else:
            print(f"[FMP VIX ERROR] HTTP {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("[FMP VIX ERROR] Request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[FMP VIX ERROR] Request failed: {e}")
        return None
    except Exception as e:
        print(f"[FMP VIX ERROR] Unexpected error: {e}")
        return None
