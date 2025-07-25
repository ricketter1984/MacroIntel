#!/usr/bin/env python3
"""
Yahoo Futures Fetcher using yfinance

This module fetches futures data using yfinance library.
Extracts symbol, name, price, change %, and volume for various futures contracts.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import yfinance as yf

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YahooFuturesFetcher:
    """Fetcher for Yahoo Finance futures data using yfinance."""
    
    def __init__(self):
        """Initialize the fetcher."""
        # Define the futures tickers to fetch
        self.tickers = ["ES=F", "YM=F", "NQ=F", "RTY=F", "GC=F", "CL=F", "NG=F"]
        
        # Create output directory if it doesn't exist
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info("🚀 Yahoo Futures Fetcher initialized")
    
    def fetch_futures_data(self) -> List[Dict[str, Any]]:
        """
        Fetch futures data for all specified tickers.
        
        Returns:
            List of futures data dictionaries
        """
        futures_data = []
        
        logger.info(f"📡 Fetching data for {len(self.tickers)} futures contracts...")
        
        for ticker_symbol in self.tickers:
            try:
                logger.info(f"📊 Fetching data for {ticker_symbol}...")
                
                # Create yfinance Ticker object
                ticker = yf.Ticker(ticker_symbol)
                
                # Get ticker info
                info = ticker.info
                
                # Extract required fields
                name = info.get('shortName', ticker_symbol)
                last_price = info.get('regularMarketPrice', 0)
                change_percent = info.get('regularMarketChangePercent', 0)
                volume = info.get('volume', 0)
                
                # Format the data
                futures_item = {
                    "symbol": ticker_symbol,
                    "name": name,
                    "last_price": str(last_price) if last_price else "",
                    "change": "",  # Not directly available from yfinance
                    "percent_change": f"({change_percent:+.2f}%)" if change_percent else "",
                    "volume": str(volume) if volume else ""
                }
                
                futures_data.append(futures_item)
                logger.info(f"✅ Successfully fetched {ticker_symbol}: {name} @ {last_price}")
                
            except Exception as e:
                logger.error(f"❌ Error fetching {ticker_symbol}: {str(e)}")
                # Skip failed ticker instead of adding placeholder data
                logger.warning(f"⚠️ Skipping {ticker_symbol} - data unavailable")
        
        logger.info(f"✅ Successfully fetched data for {len(futures_data)} futures contracts")
        return futures_data
    
    def save_results(self, futures_data: List[Dict[str, Any]]) -> str:
        """
        Save the futures data to JSON file.
        
        Args:
            futures_data: List of futures data dictionaries
            
        Returns:
            Path to the saved file
        """
        try:
            # Generate filename with current date
            date_str = datetime.now().strftime('%Y%m%d')
            filename = f"yahoo_futures_{date_str}.json"
            filepath = self.output_dir / filename
            
            # Save as JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(futures_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Saved futures data to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Error saving results: {str(e)}")
            return ""
    
    def run(self) -> Dict[str, Any]:
        """
        Run the complete fetching process.
        
        Returns:
            Dictionary with fetching results
        """
        logger.info("🚀 Starting Yahoo Futures Fetcher...")
        
        start_time = datetime.now()
        
        try:
            # Fetch futures data
            futures_data = self.fetch_futures_data()
            
            if not futures_data:
                logger.warning("⚠️ No futures data found")
                return {
                    "success": False,
                    "error": "No futures data found",
                    "total_contracts": 0,
                    "execution_time": str(datetime.now() - start_time)
                }
            
            # Save results
            output_file = self.save_results(futures_data)
            
            execution_time = datetime.now() - start_time
            
            logger.info(f"✅ Yahoo Futures Fetcher completed successfully")
            logger.info(f"📊 Total contracts: {len(futures_data)}")
            logger.info(f"⏱️ Execution time: {execution_time}")
            
            return {
                "success": True,
                "total_contracts": len(futures_data),
                "output_file": output_file,
                "execution_time": str(execution_time),
                "timestamp": datetime.now().isoformat(),
                "source": "yahoo_futures_yfinance"
            }
            
        except Exception as e:
            logger.error(f"❌ Yahoo Futures Fetcher failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": str(datetime.now() - start_time),
                "timestamp": datetime.now().isoformat(),
                "source": "yahoo_futures_yfinance"
            }

def main():
    """Main function to run the fetcher."""
    try:
        fetcher = YahooFuturesFetcher()
        result = fetcher.run()
        
        if result["success"]:
            print(f"✅ Successfully fetched {result['total_contracts']} futures contracts")
            print(f"📁 Output saved to: {result['output_file']}")
        else:
            print(f"❌ Fetcher failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"❌ Main execution failed: {str(e)}")
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main() 