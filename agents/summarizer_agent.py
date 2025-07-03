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

class SummarizerAgent:
    """Agent responsible for fetching and summarizing news from multiple sources."""
    
    def __init__(self):
        """Initialize the summarizer agent."""
        init_env()
        self.sources = ["benzinga", "messari", "polygon", "fmp"]
        logger.info("🧠 Summarizer Agent initialized")
    
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
            sources_processed = set()
            
            for article in articles:
                # Extract key information
                summary = {
                    "title": article.get("title", ""),
                    "summary": article.get("summary", article.get("body", "")[:200] + "..."),
                    "sentiment": article.get("tone", "Neutral"),
                    "source": article.get("source", "unknown"),
                    "url": article.get("url", ""),
                    "timestamp": article.get("timestamp", datetime.now().isoformat()),
                    "affected_tickers": article.get("affected_tickers", "")
                }
                
                summarized_articles.append(summary)
                sources_processed.add(summary["source"])
            
            result = {
                "articles": summarized_articles,
                "total_count": len(summarized_articles),
                "sources_processed": list(sources_processed),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"📝 Summarized {len(summarized_articles)} articles from {len(sources_processed)} sources")
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