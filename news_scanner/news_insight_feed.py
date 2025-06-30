import time
import json
import os
from utils.api_clients import fetch_all_news
from news_scanner.macro_insight_builder import summarize_article

def load_watchlist_keywords():
    """Load watchlist keywords from config file"""
    try:
        config_path = os.path.join("config", "watchlist_keywords.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Combine all keywords for filtering
        all_keywords = []
        all_keywords.extend(config.get("tickers", []))
        all_keywords.extend(config.get("macro_keywords", []))
        all_keywords.extend(config.get("sectors", []))
        
        return all_keywords, config
    except Exception as e:
        print(f"⚠️ Error loading watchlist: {e}")
        return [], {}

def is_relevant_article(article, keywords):
    """Check if article is relevant to watchlist keywords"""
    if not keywords:
        return True
    
    title = article.get("title", "").lower()
    body = article.get("body", "").lower()
    
    for keyword in keywords:
        if keyword.lower() in title or keyword.lower() in body:
            return True
    
    return False

def scan_relevant_news(limit=15, engine="gpt-3.5-turbo"):
    """
    Scan for news relevant to user's watchlist and summarize with GPT-3.5
    
    Args:
        limit: Maximum number of articles to process (default: 15)
        engine: AI engine to use for summarization (default: gpt-3.5-turbo)
    
    Returns:
        List of relevant articles with summaries
    """
    print("🔍 Scanning for relevant news based on watchlist...\n")
    
    # Load watchlist keywords
    keywords, config = load_watchlist_keywords()
    print(f"📋 Loaded {len(keywords)} watchlist keywords")
    print(f"   Tickers: {len(config.get('tickers', []))}")
    print(f"   Macro keywords: {len(config.get('macro_keywords', []))}")
    print(f"   Sectors: {len(config.get('sectors', []))}\n")
    
    # Fetch all news from available sources
    all_articles = fetch_all_news()
    print(f"📰 Retrieved {len(all_articles)} total articles\n")
    
    # Filter for relevant articles
    relevant_articles = []
    skipped_count = 0
    
    for article in all_articles:
        if is_relevant_article(article, keywords):
            relevant_articles.append(article)
        else:
            skipped_count += 1
            print(f"⏭️  Skipped: {article.get('title', 'No title')[:60]}... (not in watchlist)")
    
    print(f"\n✅ Found {len(relevant_articles)} relevant articles")
    print(f"⏭️  Skipped {skipped_count} articles (not in watchlist)")
    
    # Limit articles for processing (default 15, max 20)
    max_limit = min(limit, 20)
    articles_to_process = relevant_articles[:max_limit]
    if len(relevant_articles) > max_limit:
        print(f"⚠️  Limiting to first {max_limit} articles for processing")
    
    # Summarize relevant articles
    print(f"\n🧠 Summarizing {len(articles_to_process)} articles using {engine.upper()}...\n")
    
    summarized_articles = []
    for i, article in enumerate(articles_to_process, 1):
        print(f"  {i}. {article.get('title', 'No title')[:80]}...")
        
        try:
            # Use specified engine for summarization
            summary_result = summarize_article(article, model=engine.split('-')[0])  # Extract model name
            
            # Combine article with summary
            final_article = {
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "body": article.get("body", ""),
                "source": article.get("source", "unknown"),
                "timestamp": article.get("timestamp", ""),
                "summary": summary_result.get("summary", ""),
                "affected_tickers": summary_result.get("affected_tickers", ""),
                "tone": summary_result.get("tone", "Neutral")
            }
            
            summarized_articles.append(final_article)
            
        except Exception as e:
            print(f"    ❌ Error summarizing: {str(e)}")
            # Add article without summary
            final_article = {
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "body": article.get("body", ""),
                "source": article.get("source", "unknown"),
                "timestamp": article.get("timestamp", ""),
                "summary": f"[Error summarizing: {str(e)}]",
                "affected_tickers": "",
                "tone": "Neutral"
            }
            summarized_articles.append(final_article)
    
    print(f"\n✅ Completed processing {len(summarized_articles)} articles")
    return summarized_articles

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
