#!/usr/bin/env python3
"""
Benzinga News Fetcher Script

This script fetches news from Benzinga API and processes it for MacroIntel.
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

def fetch_benzinga_news():
    """Fetch news from Benzinga API."""
    try:
        from utils.api_clients import fetch_benzinga_news
        from news_scanner.news_insight_feed import scan_benzinga_news
        
        print("Fetching Benzinga news...")
        
        # Fetch news with keyword filtering
        keywords = ["Trump", "Musk", "oil", "Nvidia", "attack", "Middle East", "Fed", "inflation", "earnings"]
        news_data = scan_benzinga_news(keyword_filter=keywords)
        
        if news_data:
            print(f"Retrieved {len(news_data)} relevant news articles")
            
            # Save to output directory
            output_dir = project_root / "output"
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"benzinga_news_{timestamp}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(news_data, f, indent=2, default=str)
            
            print(f"News data saved to: {output_file}")
            
            # Return summary for logging
            return {
                "success": True,
                "articles_count": len(news_data),
                "output_file": str(output_file),
                "timestamp": datetime.now().isoformat(),
                "source": "benzinga"
            }
        else:
            print("No news articles retrieved")
            return {
                "success": True,
                "articles_count": 0,
                "message": "No relevant news found",
                "timestamp": datetime.now().isoformat(),
                "source": "benzinga"
            }
            
    except ImportError as e:
        print(f"Import error: {e}")
        return {
            "success": False,
            "error": f"Import error: {e}",
            "timestamp": datetime.now().isoformat(),
            "source": "benzinga"
        }
    except Exception as e:
        print(f"Error fetching Benzinga news: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "source": "benzinga"
        }

def main():
    """Main function to execute the news fetching."""
    print("Starting Benzinga News Fetcher")
    print(f"Project root: {project_root}")
    print(f"Python executable: {sys.executable}")
    
    # Check API key
    api_key = os.getenv("BENZINGA_API_KEY")
    if not api_key:
        print("BENZINGA_API_KEY not found in environment variables")
        sys.exit(1)
    
    # Fetch news
    result = fetch_benzinga_news()
    
    # Print result
    print("Execution Result:")
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    if result["success"]:
        print("Benzinga news fetching completed successfully")
        sys.exit(0)
    else:
        print("Benzinga news fetching failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 