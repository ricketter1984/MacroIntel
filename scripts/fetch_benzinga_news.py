#!/usr/bin/env python3
"""
Benzinga News Fetcher Script

This script fetches news from Benzinga API and processes it for MacroIntel.
Designed to be called by the API dispatcher in an isolated environment.
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv



# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(dotenv_path=project_root / "config" / ".env")

def strip_emojis(text: str) -> str:
    return re.sub(r'[^ -~]+', '', text)

def fetch_benzinga_news():
    """Fetch news from Benzinga API."""
    try:
        from utils.api_clients import fetch_benzinga_news as api_fetch_benzinga
        
        print(strip_emojis("Fetching Benzinga news..."))
        
        # Fetch news directly from API
        news_data = api_fetch_benzinga()

        # Preview first 3 articles before filtering
        print("\n🔍 Preview of first 3 parsed articles BEFORE filtering:")
        for i, article in enumerate(news_data[:3]):
            print(f"\nArticle #{i+1}")
            print("Title:", article.get("title"))
            print("Summary:", article.get("summary"))
            print("Body:", article.get("body"))
            print("Date:", article.get("date"))
        
        # Apply keyword filtering if needed
        if news_data:
            print(strip_emojis(f"Retrieved {len(news_data)} articles from API"))
            
            keywords = ["Trump", "Musk", "oil", "Nvidia", "attack", "Middle East", "Fed", "inflation", "earnings", 
                       "stock", "market", "trading", "price", "earnings", "revenue", "profit", "loss", "gain", 
                       "drop", "rise", "fall", "surge", "crash", "rally", "bull", "bear", "crypto", "bitcoin", 
                       "ethereum", "gold", "silver", "bonds", "rates", "economy", "GDP", "employment", "jobs"]
            filtered_data = []
            filtered_out = 0
            
            for article in news_data:
                if isinstance(article, dict):
                    title = article.get('title', '').lower()
                    body = article.get('body', '').lower()
                    
                    # Check if article contains any keywords
                    if any(keyword.lower() in title or keyword.lower() in body for keyword in keywords):
                        filtered_data.append(article)
                    else:
                        filtered_out += 1
                        if filtered_out <= 3:  # Show first 3 filtered articles for debugging
                            print(strip_emojis(f"Filtered out: {article.get('title', 'No title')[:50]}..."))
            
            print(strip_emojis(f"Filtered out {filtered_out} articles, kept {len(filtered_data)} articles"))
            news_data = filtered_data
        
        # Apply emoji stripping to all news articles immediately when parsing
        if news_data:
            for article in news_data:
                if isinstance(article, dict):
                    try:
                        # Immediately sanitize headline/title/summary
                        article['title'] = strip_emojis(article.get('title', ''))
                        article['body'] = strip_emojis(article.get('body', ''))
                        article['summary'] = strip_emojis(article.get('summary', '')) if 'summary' in article else ''
                    except Exception as e:
                        print(strip_emojis(f"Warning: Error stripping emojis from article: {e}"))
                        continue
        
        if news_data:
            print(strip_emojis(f"Retrieved {len(news_data)} relevant news articles"))
            
            # Save to output directory
            output_dir = project_root / "output"
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"benzinga_news_{timestamp}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(news_data, f, indent=2, default=str)
            
            print(strip_emojis(f"News data saved to: {output_file}"))
            
            # Return summary for logging
            return {
                "success": True,
                "articles_count": len(news_data),
                "output_file": str(output_file),
                "timestamp": datetime.now().isoformat(),
                "source": "benzinga"
            }
        else:
            print(strip_emojis("No news articles retrieved"))
            return {
                "success": True,
                "articles_count": 0,
                "message": "No relevant news found",
                "timestamp": datetime.now().isoformat(),
                "source": "benzinga"
            }
            
    except ImportError as e:
        print(strip_emojis(f"Import error: {e}"))
        return {
            "success": False,
            "error": f"Import error: {e}",
            "timestamp": datetime.now().isoformat(),
            "source": "benzinga"
        }
    except Exception as e:
        print(strip_emojis(f"Error fetching Benzinga news: {e}"))
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "source": "benzinga"
        }

def test_emoji_stripping():
    """Test the emoji stripping functionality."""
    test_texts = [
        "🚀 Bitcoin surges to new highs! 📈",
        "Fed announces rate hike 💰",
        "Normal text without emojis",
        "Mixed text with 🎯 emoji and normal words",
        "",  # Empty string
        None  # None value
    ]
    
    print(strip_emojis("Testing emoji stripping functionality:"))
    for text in test_texts:
        try:
            if text is None:
                cleaned = strip_emojis("")
                print(strip_emojis(f"Original: None"))
            else:
                cleaned = strip_emojis(text)
                print(strip_emojis(f"Original: {text}"))
            print(strip_emojis(f"Cleaned:  {cleaned}"))
            print()
        except Exception as e:
            print(strip_emojis(f"Error processing '{text}': {e}"))
    print(strip_emojis("Emoji stripping test completed."))

def main():
    """Main function to execute the news fetching."""
    print(strip_emojis("Starting Benzinga News Fetcher"))
    print(strip_emojis(f"Project root: {project_root}"))
    print(strip_emojis(f"Python executable: {sys.executable}"))
    
    # Check API key
    api_key = os.getenv("BENZINGA_API_KEY")
    if not api_key:
        print(strip_emojis("BENZINGA_API_KEY not found in environment variables"))
        sys.exit(1)
    
    # Fetch news
    result = fetch_benzinga_news()
    
    # Print result
    print(strip_emojis("Execution Result:"))
    print(strip_emojis(json.dumps(result, indent=2)))
    
    # Exit with appropriate code
    if result["success"]:
        print(strip_emojis("Benzinga news fetching completed successfully"))
        sys.exit(0)
    else:
        print(strip_emojis("Benzinga news fetching failed"))
        sys.exit(1)

if __name__ == "__main__":
    import sys
    
    # Check if test mode is requested
    if len(sys.argv) > 1 and sys.argv[1] == "--test-emoji":
        test_emoji_stripping()
    else:
        main() 