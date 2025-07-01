#!/usr/bin/env python3
"""
News Insight Feed - Enhanced news scanning and relevance filtering
"""

import time
import json
import os
import logging
from typing import List, Dict, Any
from datetime import datetime
from utils.api_clients import fetch_all_news
from news_scanner.macro_insight_builder import summarize_article

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_watchlist_keywords() -> Dict[str, List[str]]:
    """Load watchlist keywords from config file."""
    try:
        with open('config/watchlist_keywords.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Watchlist keywords file not found, using defaults")
        return {
            "tickers": ["BTC", "ETH", "SPY", "QQQ", "GLD", "XAUUSD", "VIX"],
            "macro_keywords": ["inflation", "fed", "interest rates", "recession", "GDP", "employment"],
            "sectors": ["technology", "finance", "energy", "healthcare"]
        }
    except Exception as e:
        logger.error(f"Error loading watchlist keywords: {e}")
        return {"tickers": [], "macro_keywords": [], "sectors": []}

def is_relevant_article(article: Dict[str, Any], watchlist: Dict[str, List[str]]) -> bool:
    """
    Check if an article is relevant based on watchlist keywords.
    
    Args:
        article: Article dictionary with title, body, etc.
        watchlist: Dictionary of watchlist keywords
        
    Returns:
        bool: True if article is relevant
    """
    try:
        # Ensure article has required fields
        title = article.get("title", "").lower()
        body = article.get("body", "").lower()
        
        # Combine title and body for keyword search
        text = f"{title} {body}"
        
        # Check tickers
        for ticker in watchlist.get("tickers", []):
            if ticker.lower() in text:
                return True
        
        # Check macro keywords
        for keyword in watchlist.get("macro_keywords", []):
            if keyword.lower() in text:
                return True
        
        # Check sectors
        for sector in watchlist.get("sectors", []):
            if sector.lower() in text:
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking article relevance: {e}")
        return False

def scan_relevant_news(all_news: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Scan news articles and filter for relevance based on watchlist.
    
    Args:
        all_news: List of news articles from all sources
        
    Returns:
        List of relevant news articles
    """
    try:
        logger.info("🔍 Scanning for relevant news based on watchlist...")
        
        # Load watchlist keywords
        watchlist = load_watchlist_keywords()
        
        # Log watchlist stats
        ticker_count = len(watchlist.get("tickers", []))
        macro_count = len(watchlist.get("macro_keywords", []))
        sector_count = len(watchlist.get("sectors", []))
        
        logger.info(f"📋 Loaded {ticker_count + macro_count + sector_count} watchlist keywords")
        logger.info(f"   Tickers: {ticker_count}")
        logger.info(f"   Macro keywords: {macro_count}")
        logger.info(f"   Sectors: {sector_count}")
        
        # Filter articles for relevance
        relevant_articles = []
        skipped_count = 0
        
        for article in all_news:
            try:
                # Ensure article is a dictionary
                if not isinstance(article, dict):
                    logger.warning(f"Skipping non-dict article: {type(article)}")
                    skipped_count += 1
                    continue
                
                if is_relevant_article(article, watchlist):
                    # Add source information if not present
                    if "source" not in article:
                        article["source"] = "unknown"
                    
                    # Add timestamp if not present
                    if "timestamp" not in article:
                        article["timestamp"] = datetime.now().isoformat()
                    
                    relevant_articles.append(article)
                else:
                    # Log skipped articles (truncated for readability)
                    title = article.get("title", "No title")[:50]
                    if len(title) == 50:
                        title += "..."
                    logger.info(f"⏭️  Skipped: {title} (not in watchlist)")
                    skipped_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing article: {e}")
                skipped_count += 1
                continue
        
        logger.info(f"✅ Found {len(relevant_articles)} relevant articles")
        logger.info(f"⏭️  Skipped {skipped_count} articles (not in watchlist)")
        
        return relevant_articles
        
    except Exception as e:
        logger.error(f"❌ Error in scan_relevant_news: {e}")
        return []

def analyze_sentiment(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze sentiment of news articles.
    
    Args:
        articles: List of news articles
        
    Returns:
        Dictionary with sentiment analysis results
    """
    try:
        # Simple keyword-based sentiment analysis
        positive_words = ["bullish", "surge", "rally", "gain", "positive", "growth", "up"]
        negative_words = ["bearish", "crash", "drop", "decline", "negative", "loss", "down"]
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for article in articles:
            text = f"{article.get('title', '')} {article.get('body', '')}".lower()
            
            pos_score = sum(1 for word in positive_words if word in text)
            neg_score = sum(1 for word in negative_words if word in text)
            
            if pos_score > neg_score:
                positive_count += 1
                article["tone"] = "Positive"
            elif neg_score > pos_score:
                negative_count += 1
                article["tone"] = "Negative"
            else:
                neutral_count += 1
                article["tone"] = "Neutral"
        
        total = len(articles)
        if total > 0:
            sentiment_score = ((positive_count - negative_count) / total) * 100
        else:
            sentiment_score = 0
        
        return {
            "positive": positive_count,
            "negative": negative_count,
            "neutral": neutral_count,
            "sentiment_score": sentiment_score,
            "total_articles": total
        }
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        return {
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "sentiment_score": 0,
            "total_articles": 0
        }

def extract_affected_tickers(articles: List[Dict[str, Any]]) -> List[str]:
    """
    Extract ticker symbols mentioned in articles.
    
    Args:
        articles: List of news articles
        
    Returns:
        List of unique ticker symbols
    """
    try:
        tickers = set()
        watchlist = load_watchlist_keywords()
        
        for article in articles:
            text = f"{article.get('title', '')} {article.get('body', '')}"
            
            for ticker in watchlist.get("tickers", []):
                if ticker.upper() in text.upper():
                    tickers.add(ticker.upper())
        
        return list(tickers)
        
    except Exception as e:
        logger.error(f"Error extracting tickers: {e}")
        return []

def process_news_insights(all_news: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process news articles and generate insights.
    
    Args:
        all_news: List of news articles from all sources
        
    Returns:
        Dictionary with processed news insights
    """
    try:
        # Scan for relevant articles
        relevant_articles = scan_relevant_news(all_news)
        
        # Analyze sentiment
        sentiment_analysis = analyze_sentiment(relevant_articles)
        
        # Extract affected tickers
        affected_tickers = extract_affected_tickers(relevant_articles)
        
        # Add sentiment and ticker info to articles
        for article in relevant_articles:
            article["affected_tickers"] = ", ".join(affected_tickers)
        
        return {
            "articles": relevant_articles,
            "sentiment_analysis": sentiment_analysis,
            "affected_tickers": affected_tickers,
            "total_processed": len(all_news),
            "relevant_count": len(relevant_articles),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing news insights: {e}")
        return {
            "articles": [],
            "sentiment_analysis": {"sentiment_score": 0, "total_articles": 0},
            "affected_tickers": [],
            "total_processed": 0,
            "relevant_count": 0,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def scan_benzinga_news(keyword_filter=None):
    """Legacy function for backward compatibility"""
    print("🔍 Scanning Benzinga headlines...\n")
    headlines = fetch_all_news()  # Use new unified news fetcher
    
    if not headlines:
        print("⚠️ No headlines retrieved.")
        return []

    filtered = []
    for item in headlines:
        title = item.get("title", "")
        summary = item.get("body", "")
        if keyword_filter:
            if any(word.lower() in title.lower() or word.lower() in summary.lower() for word in keyword_filter):
                filtered.append(item)
        else:
            filtered.append(item)

    for story in filtered[:10]:  # preview top 10
        print(f"📰 {story.get('title')}\n   {story.get('body')[:140]}...\n")

    return filtered
