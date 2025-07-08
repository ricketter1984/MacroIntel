#!/usr/bin/env python3
"""
Perplexity Macro Agent for MacroIntel Swarm
Fetches and summarizes macroeconomic news using the Perplexity API or HTTP search scraping fallback.
Target news types: CPI, inflation, rate hikes, crude oil, Middle East conflict, gold, metals, macro drivers, VIX, etc.
"""

import os
import sys
import json
import logging
import requests
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from config/.env
load_dotenv(dotenv_path="config/.env")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_clients import strip_emojis

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerplexityMacroAgent:
    """Agent responsible for fetching and summarizing macroeconomic news from Perplexity."""
    
    def __init__(self):
        """Initialize the Perplexity macro agent."""
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        # Clean the model name - remove any comments or extra text
        raw_model = os.getenv("PERPLEXITY_MODEL", "sonar")
        self.model = raw_model.split('#')[0].strip() if '#' in raw_model else raw_model.strip()
        self.base_url = "https://api.perplexity.ai"
        self.chat_endpoint = "https://api.perplexity.ai/chat/completions"
        
        # Default macro keywords if no topic provided
        self.default_keywords = [
            "CPI inflation data", "Federal Reserve rate decision", "crude oil prices",
            "Middle East conflict", "gold prices", "metals market", "VIX volatility",
            "macroeconomic indicators", "economic calendar", "FOMC meeting",
            "jobs report", "GDP growth", "retail sales", "housing market",
            "trade war", "geopolitical risk", "OPEC production", "energy crisis"
        ]
        
        logger.info("🧠 Perplexity Macro Agent initialized")
        if self.api_key:
            logger.info("✅ Perplexity API key found")
            logger.info(f"🤖 Using model: {self.model}")
        else:
            logger.warning("⚠️ Perplexity API key not found")
    
    def _make_perplexity_api_request(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Make a request to the Perplexity API.
        
        Args:
            query: Search query string
            
        Returns:
            API response or None if failed
        """
        if not self.api_key:
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a macroeconomic news assistant. Provide concise, headline-style summaries."
                    },
                    {
                        "role": "user",
                        "content": f"Find recent macroeconomic news about {query}"
                    }
                ]
            }
            
            response = requests.post(
                self.chat_endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Perplexity API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error making Perplexity API request: {str(e)}")
            return None
    
    def _parse_api_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse the Perplexity API response to extract articles.
        
        Args:
            response: API response dictionary
            
        Returns:
            List of parsed articles
        """
        articles = []
        
        try:
            # Extract content from choices[0].message.content
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if content:
                # Create a single article from the content
                article = {
                    "title": f"Perplexity Macro News: {content[:50]}...",
                    "summary": content,
                    "url": "",
                    "timestamp": datetime.now().isoformat(),
                    "source": "Perplexity",
                    "tags": self._extract_tags(content)
                }
                articles.append(article)
            
        except Exception as e:
            logger.error(f"❌ Error parsing API response: {str(e)}")
            articles = []
        
        return articles
    

    
    def fetch_macro_news(self, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch macroeconomic news from Perplexity.
        
        Args:
            topic: Specific topic to search for, or None for default keywords
            
        Returns:
            List of news articles with metadata
        """
        try:
            if topic:
                queries = [topic]
            else:
                # Use default macro keywords
                queries = self.default_keywords[:3]  # Limit to 3 queries to avoid rate limits
            
            all_articles = []
            
            for query in queries:
                logger.info(f"🔍 Searching Perplexity for: {query}")
                
                # Make API request
                articles = []
                if self.api_key:
                    api_response = self._make_perplexity_api_request(query)
                    if api_response:
                        articles = self._parse_api_response(api_response)
                        logger.info(f"✅ API returned {len(articles)} articles for '{query}'")
                    else:
                        logger.warning(f"⚠️ API failed for '{query}'")
                else:
                    logger.error("❌ No API key available - cannot make requests")
                
                all_articles.extend(articles)
            
            # Clean and format articles
            cleaned_articles = []
            for article in all_articles:
                cleaned_article = {
                    "timestamp": article.get("timestamp", datetime.now().isoformat()),
                    "source": "Perplexity",
                    "summary": strip_emojis(article.get("summary", "")),
                    "title": strip_emojis(article.get("title", "")),
                    "url": article.get("url", ""),
                    "tags": self._extract_tags(article.get("title", "") + " " + article.get("summary", ""))
                }
                cleaned_articles.append(cleaned_article)
            
            # Remove duplicates based on title
            seen_titles = set()
            unique_articles = []
            for article in cleaned_articles:
                title = article["title"].lower()
                if title not in seen_titles and len(title) > 10:
                    seen_titles.add(title)
                    unique_articles.append(article)
            
            logger.info(f"📰 Fetched {len(unique_articles)} unique articles from Perplexity")
            return unique_articles[:10]  # Limit to top 10 articles
            
        except Exception as e:
            logger.error(f"❌ Error fetching macro news: {str(e)}")
            return []
    
    def _extract_tags(self, text: str) -> List[str]:
        """
        Extract relevant tags from article text.
        
        Args:
            text: Article title and summary text
            
        Returns:
            List of relevant tags
        """
        text_lower = text.lower()
        tags = []
        
        # Define tag keywords
        tag_keywords = {
            "inflation": ["cpi", "inflation", "prices", "consumer price"],
            "rates": ["federal reserve", "fomc", "interest rates", "rate hike", "rate cut"],
            "oil": ["crude oil", "oil prices", "opec", "energy"],
            "gold": ["gold", "precious metals", "bullion"],
            "geopolitics": ["middle east", "iran", "israel", "geopolitical", "conflict"],
            "vix": ["vix", "volatility", "fear", "greed"],
            "earnings": ["earnings", "quarterly", "revenue", "profit"],
            "jobs": ["jobs report", "employment", "unemployment", "non-farm payrolls"],
            "gdp": ["gdp", "economic growth", "recession"],
            "housing": ["housing market", "real estate", "mortgage rates"]
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(tag)
        
        return tags
    
    def save_results(self, articles: List[Dict[str, Any]]) -> str:
        """
        Save results to output file.
        
        Args:
            articles: List of articles to save
            
        Returns:
            Path to saved file
        """
        try:
            os.makedirs("output", exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"perplexity_news_{timestamp}.json"
            filepath = os.path.join("output", filename)
            
            result_data = {
                "timestamp": datetime.now().isoformat(),
                "source": "Perplexity Macro Agent",
                "articles": articles,
                "total_count": len(articles),
                "tags_summary": self._get_tags_summary(articles)
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Results saved to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Error saving results: {str(e)}")
            return ""
    
    def _get_tags_summary(self, articles: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Get summary of tags across all articles.
        
        Args:
            articles: List of articles
            
        Returns:
            Dictionary of tag counts
        """
        tag_counts = {}
        for article in articles:
            for tag in article.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return tag_counts
    
    def run(self, topic: Optional[str] = None) -> Dict[str, Any]:
        """
        Main execution method for the Perplexity macro agent.
        
        Args:
            topic: Specific topic to search for, or None for default keywords
            
        Returns:
            Dictionary with fetched news data
        """
        logger.info("🚀 Starting Perplexity Macro Agent execution...")
        
        # Fetch macro news
        articles = self.fetch_macro_news(topic)
        
        # Save results
        output_file = self.save_results(articles)
        
        # Prepare result
        result = {
            "status": "success" if articles else "no_articles",
            "articles": articles,
            "total_count": len(articles),
            "output_file": output_file,
            "timestamp": datetime.now().isoformat(),
            "topic_searched": topic or "default_macro_keywords"
        }
        
        if articles:
            tags_summary = self._get_tags_summary(articles)
            result["tags_summary"] = tags_summary
            logger.info(f"✅ Perplexity Macro Agent completed: {len(articles)} articles found")
        else:
            logger.warning("⚠️ Perplexity Macro Agent completed: No articles found")
        
        return result

def main():
    """Main function for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Perplexity Macro Agent")
    parser.add_argument('--topic', type=str, help='Specific topic to search for')
    args = parser.parse_args()
    
    agent = PerplexityMacroAgent()
    result = agent.run(args.topic)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 