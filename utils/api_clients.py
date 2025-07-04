import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import xml.etree.ElementTree as ET

# Load environment variables
load_dotenv(dotenv_path="config/.env")

def init_env():
    # Environment already loaded above
    pass

# -- FMP Client (updated to use v4)
def fetch_fmp_events():
    api_key = os.getenv("FMP_API_KEY")
    url = "https://financialmodelingprep.com/api/v4/economic_calendar"
    params = {
        "from": datetime.utcnow().strftime("%Y-%m-%d"),
        "to": datetime.utcnow().strftime("%Y-%m-%d"),
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

def fetch_messari_news():
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

def fetch_benzinga_news():
    api_key = os.getenv("BENZINGA_API_KEY")
    print(f"🔑 Benzinga API KEY: {api_key}")

    url = "https://api.benzinga.com/api/v2/news"
    params = {
        "token": api_key,
        "pagesize": 50,
        "displayOutput": "full",
        "format": "xml"  # explicitly request XML
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"[Benzinga Error] {response.status_code}: {response.text}")
        return []

    # Parse XML manually
    headlines = []
    try:
        root = ET.fromstring(response.content)
        for item in root.findall("item"):
            headlines.append({
                "id": item.findtext("id"),
                "title": item.findtext("title"),
                "body": item.findtext("body") or "",
                "author": item.findtext("author"),
                "created": item.findtext("created"),
                "url": item.findtext("url"),
            })
        return headlines
    except Exception as e:
        print(f"[Parse Error] {e}")
        return []

def fetch_all_news():
    """
    Fetch news from all available sources and merge results
    Returns a combined list of news items from all sources
    """
    all_news = []
    
    # Fetch from all sources
    print("\U0001F4F0 Fetching news from all sources...")
    
    # Benzinga news
    try:
        benzinga_news = fetch_benzinga_news()
        print(f"\u2705 Benzinga: {len(benzinga_news)} articles")
        # Convert Benzinga format to standard format
        for item in benzinga_news:
            all_news.append({
                "title": item.get("title", ""),
                "body": item.get("body", ""),
                "url": item.get("url", ""),
                "timestamp": item.get("created", ""),
                "source": "benzinga"
            })
    except Exception as e:
        print(f"\u274c Benzinga fetch failed: {e}")
    
    # FMP news
    try:
        fmp_news = fetch_fmp_news()
        print(f"\u2705 FMP: {len(fmp_news)} articles")
        for item in fmp_news:
            all_news.append({
                "title": item.get("title", ""),
                "body": item.get("body", ""),
                "url": item.get("url", ""),
                "timestamp": item.get("timestamp", ""),
                "source": "fmp"
            })
    except Exception as e:
        print(f"\u274c FMP fetch failed: {e}")
    
    # Polygon news
    try:
        polygon_news = fetch_polygon_news()
        print(f"\u2705 Polygon: {len(polygon_news)} articles")
        for item in polygon_news:
            all_news.append({
                "title": item.get("title", ""),
                "body": item.get("body", ""),
                "url": item.get("url", ""),
                "timestamp": item.get("timestamp", ""),
                "source": "polygon"
            })
    except Exception as e:
        print(f"\u274c Polygon fetch failed: {e}")
    
    # Messari news
    try:
        messari_news = fetch_messari_news()
        print(f"\u2705 Messari: {len(messari_news)} articles")
        for item in messari_news:
            all_news.append({
                "title": item.get("title", ""),
                "body": item.get("body", ""),
                "url": item.get("url", ""),
                "timestamp": item.get("timestamp", ""),
                "source": "messari"
            })
    except Exception as e:
        print(f"\u274c Messari fetch failed: {e}")
    
    return all_news

# -- Polygon Indices Client
def fetch_polygon_indices():
    """Fetch index snapshot data from Polygon API for major indices (SPX, NDX, RUT)."""
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        print("[ERROR] POLYGON_API_KEY not set.")
        return None

    base_url = "https://api.polygon.io/v2/snapshot/indices/STOCKS"
    params = {"apiKey": api_key}

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "tickers" in data:
            index_data = {d["ticker"]: d for d in data["tickers"] if d["ticker"] in ["I:SPX", "I:NDX", "I:RUT"]}
            print(f"[SUCCESS] Retrieved {len(index_data)} index snapshots.")
            return index_data
        else:
            print("[FAIL] No 'tickers' field in response.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"[REQUEST ERROR] {e}")
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
        from_date = datetime.now().strftime("%Y-%m-%d")
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m-%d")
    
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
                            "timestamp": datetime.now().isoformat()
                        }
                    elif "profile" in metrics:
                        # Profile endpoint response
                        return {
                            "symbol": symbol,
                            "name": metrics.get("profile", {}).get("name", symbol),
                            "category": metrics.get("profile", {}).get("category", ""),
                            "description": metrics.get("profile", {}).get("description", ""),
                            "timestamp": datetime.now().isoformat()
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
    
    from datetime import datetime, timedelta
    import pandas as pd
    
    url = "https://financialmodelingprep.com/api/v3/historical-price-full/^VIX"
    params = {
        "serietype": "line",
        "apikey": api_key,
        "from": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
        "to": datetime.now().strftime("%Y-%m-%d")
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
