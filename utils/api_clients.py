import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import xml.etree.ElementTree as ET

def init_env():
    load_dotenv()

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
    print("📰 Fetching news from all sources...")
    
    # Benzinga news
    try:
        benzinga_news = fetch_benzinga_news()
        print(f"✅ Benzinga: {len(benzinga_news)} articles")
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
        print(f"❌ Benzinga fetch failed: {e}")
    
    # FMP news
    try:
        fmp_news = fetch_fmp_news()
        print(f"✅ FMP: {len(fmp_news)} articles")
        for item in fmp_news:
            item["source"] = "fmp"
            all_news.append(item)
    except Exception as e:
        print(f"❌ FMP fetch failed: {e}")
    
    # Polygon news
    try:
        polygon_news = fetch_polygon_news()
        print(f"✅ Polygon: {len(polygon_news)} articles")
        for item in polygon_news:
            item["source"] = "polygon"
            all_news.append(item)
    except Exception as e:
        print(f"❌ Polygon fetch failed: {e}")
    
    # Messari news
    try:
        messari_news = fetch_messari_news()
        print(f"✅ Messari: {len(messari_news)} articles")
        for item in messari_news:
            item["source"] = "messari"
            all_news.append(item)
    except Exception as e:
        print(f"❌ Messari fetch failed: {e}")
    
    print(f"📊 Total articles fetched: {len(all_news)}")
    return all_news
