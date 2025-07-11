#!/usr/bin/env python3
"""
Summarizer Agent for MacroIntel Swarm
Fetches and summarizes news from Benzinga, Messari, Polygon, and FMP APIs.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from config/.env
load_dotenv(dotenv_path="config/.env")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_clients import fetch_all_news, init_env
from news_scanner.news_insight_feed import scan_relevant_news

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import data store for database operations
try:
    from data_store import insert_news_headline
    DATA_STORE_AVAILABLE = True
    logger.info("✅ Data store module imported successfully")
except ImportError as e:
    DATA_STORE_AVAILABLE = False
    logger.warning(f"⚠️ Data store module not available: {e}")

class SummarizerAgent:
    """Agent responsible for fetching and summarizing news from multiple sources."""
    
    def __init__(self):
        """Initialize the summarizer agent."""
        init_env()
        self.sources = ["benzinga", "messari", "polygon", "fmp"]
        
        # Geopolitical and trade-related keywords for detection
        self.geopolitical_keywords = {
            'tariffs': ['tariff', 'tariffs', 'trade duty', 'trade duties', 'customs duty'],
            'china': ['china', 'chinese', 'beijing', 'xi jinping', 'prc', 'mainland china'],
            'sanctions': ['sanction', 'sanctions', 'embargo', 'trade ban', 'economic restrictions'],
            'trade': ['import', 'imports', 'export', 'exports', 'import/export', 'trade deficit', 'trade surplus'],
            'supply_chains': ['supply chain', 'supply chains', 'global supply', 'supply disruption', 'logistics', 'shipping']
        }
        
        logger.info("🧠 Summarizer Agent initialized with geopolitical keyword detection")
    
    def fetch_news(self) -> List[Dict[str, Any]]:
        """
        Fetch news from all configured sources.
        
        Returns:
            List of news articles with metadata
        """
        try:
            logger.info("📰 Fetching news from all sources...")
            all_news = fetch_all_news()
            
            # Process through news scanner for relevance and sentiment
            processed_news = scan_relevant_news(all_news)
            
            logger.info(f"✅ Fetched {len(processed_news)} relevant articles")
            return processed_news
            
        except Exception as e:
            logger.error(f"❌ Error fetching news: {str(e)}")
            return []
    
    def detect_geopolitical_keywords(self, text: str) -> Dict[str, Any]:
        """
        Detect geopolitical and trade-related keywords in text.
        
        Args:
            text: Text to analyze (title + summary)
            
        Returns:
            Dictionary with detected keywords and metadata
        """
        if not text:
            return {"is_geopolitical": False, "categories": [], "keywords_found": []}
        
        text_lower = text.lower()
        detected_categories = []
        keywords_found = []
        
        for category, keywords in self.geopolitical_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    if category not in detected_categories:
                        detected_categories.append(category)
                    if keyword not in keywords_found:
                        keywords_found.append(keyword)
        
        is_geopolitical = len(detected_categories) > 0
        
        # Determine impact level based on number of categories detected
        impact_level = "low"
        if len(detected_categories) >= 3:
            impact_level = "high"
        elif len(detected_categories) >= 2:
            impact_level = "medium"
        elif len(detected_categories) == 1:
            impact_level = "low"
        
        return {
            "is_geopolitical": is_geopolitical,
            "categories": detected_categories,
            "keywords_found": keywords_found,
            "impact_level": impact_level,
            "category_count": len(detected_categories)
        }
    
    def summarize_articles(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Summarize articles and extract key insights.
        
        Args:
            articles: List of news articles
            
        Returns:
            Dictionary with summarized articles and metadata
        """
        try:
            summarized_articles = []
            geopolitical_articles = []
            sources_processed = set()
            db_insertions = 0
            
            for article in articles:
                # Extract key information
                title = article.get("title", "")
                article_summary = article.get("summary", article.get("body", "")[:200] + "...")
                
                # Detect geopolitical content
                text_to_analyze = f"{title} {article_summary}"
                geopolitical_data = self.detect_geopolitical_keywords(text_to_analyze)
                
                summary = {
                    "title": title,
                    "summary": article_summary,
                    "sentiment": article.get("tone", "Neutral"),
                    "source": article.get("source", "unknown"),
                    "url": article.get("url", ""),
                    "timestamp": article.get("timestamp", datetime.now().isoformat()),
                    "affected_tickers": article.get("affected_tickers", ""),
                    "geopolitical": geopolitical_data
                }
                
                summarized_articles.append(summary)
                
                # Track geopolitical articles separately for email section
                if geopolitical_data["is_geopolitical"]:
                    geopolitical_articles.append(summary)
                    logger.info(f"🌍 Detected geopolitical content: {title} - Categories: {geopolitical_data['categories']}")
                
                sources_processed.add(summary["source"])
                
                # Store summarized headline in database
                if DATA_STORE_AVAILABLE:
                    try:
                        # Build headline dictionary for database insertion
                        affected_tickers = summary.get('affected_tickers', '')
                        symbol = None
                        if affected_tickers and isinstance(affected_tickers, str):
                            symbol = affected_tickers.split(',')[0].strip()
                        elif affected_tickers and isinstance(affected_tickers, list):
                            symbol = str(affected_tickers[0]) if affected_tickers else None
                        
                        headline_dict = {
                            'timestamp': summary['timestamp'],
                            'source': summary['source'],
                            'symbol': symbol,
                            'headline': summary['title'],
                            'summary': summary['summary'],
                            'sentiment': summary['sentiment']
                        }
                        
                        # Insert into database
                        headline_id = insert_news_headline(headline_dict)
                        db_insertions += 1
                        logger.debug(f"✅ Inserted headline into database with ID: {headline_id}")
                        
                    except Exception as db_exc:
                        logger.error(f"❌ Error inserting headline into database: {db_exc}")
            
            result = {
                "articles": summarized_articles,
                "geopolitical_articles": geopolitical_articles,
                "total_count": len(summarized_articles),
                "geopolitical_count": len(geopolitical_articles),
                "sources_processed": list(sources_processed),
                "timestamp": datetime.now().isoformat(),
                "database_insertions": db_insertions
            }
            
            logger.info(f"📝 Summarized {len(summarized_articles)} articles from {len(sources_processed)} sources")
            logger.info(f"🌍 Detected {len(geopolitical_articles)} geopolitical/trade-related articles")
            if DATA_STORE_AVAILABLE:
                logger.info(f"💾 Stored {db_insertions} headlines in database")
            else:
                logger.warning("⚠️ Data store not available, skipping database insertion")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error summarizing articles: {str(e)}")
            return {
                "articles": [],
                "total_count": 0,
                "sources_processed": [],
                "error": str(e)
            }
    
    def run(self) -> Dict[str, Any]:
        """
        Main execution method for the summarizer agent.
        
        Returns:
            Dictionary with summarized news data
        """
        logger.info("🚀 Starting Summarizer Agent execution...")
        
        # Fetch news from all sources
        articles = self.fetch_news()
        
        # Summarize articles
        summary_result = self.summarize_articles(articles)
        
        logger.info("✅ Summarizer Agent execution completed")
        return summary_result

def main():
    """Main function for standalone execution."""
    agent = SummarizerAgent()
    result = agent.run()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 