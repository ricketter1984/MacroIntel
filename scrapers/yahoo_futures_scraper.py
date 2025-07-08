#!/usr/bin/env python3
"""
Yahoo Futures Scraper

This module scrapes futures data from Yahoo Finance's futures page.
Extracts symbol, name, price, change %, and last updated time for various futures contracts.
"""

import os
import sys
import json
import logging
import requests
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import time
import random

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YahooFuturesScraper:
    """Scraper for Yahoo Finance futures data."""
    
    def __init__(self):
        """Initialize the scraper."""
        # Try multiple possible Yahoo Finance futures URLs
        self.base_urls = [
            "https://finance.yahoo.com/quote/ES=F",
            "https://finance.yahoo.com/quote/CL=F", 
            "https://finance.yahoo.com/quote/GC=F",
            "https://finance.yahoo.com/quote/ZB=F",
            "https://finance.yahoo.com/quote/6E=F",
            "https://finance.yahoo.com/quote/6J=F",
            "https://finance.yahoo.com/quote/6B=F",
            "https://finance.yahoo.com/quote/6A=F",
            "https://finance.yahoo.com/quote/6C=F",
            "https://finance.yahoo.com/quote/6S=F"
        ]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Create output directory if it doesn't exist
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info("🚀 Yahoo Futures Scraper initialized")
    
    def _make_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """
        Make HTTP request with retry logic and error handling.
        
        Args:
            url: URL to request
            max_retries: Maximum number of retry attempts
            
        Returns:
            Response object or None if failed
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"📡 Making request to: {url} (attempt {attempt + 1}/{max_retries})")
                
                # Add random delay to avoid rate limiting
                if attempt > 0:
                    delay = random.uniform(1, 3)
                    logger.info(f"⏳ Waiting {delay:.1f}s before retry...")
                    time.sleep(delay)
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                logger.info(f"✅ Request successful: {response.status_code}")
                return response
                
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Request failed (attempt {attempt + 1}): {str(e)}")
                if attempt == max_retries - 1:
                    logger.error(f"💥 All retry attempts failed for: {url}")
                    return None
                continue
        
        return None
    
    def _parse_futures_table(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Parse the futures data table from the HTML.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of futures data dictionaries
        """
        futures_data = []
        
        try:
            # Look for the main futures table
            # Yahoo Finance uses different table structures, so we'll try multiple selectors
            table_selectors = [
                'table[data-test="futures-table"]',
                'table[class*="futures"]',
                'table[class*="quote"]',
                'table[data-test="quote-table"]',
                'div[data-test="futures-table"] table',
                'div[class*="futures"] table'
            ]
            
            table = None
            for selector in table_selectors:
                table = soup.select_one(selector)
                if table:
                    logger.info(f"✅ Found futures table with selector: {selector}")
                    break
            
            if not table:
                # Fallback: look for any table with futures-like data
                tables = soup.find_all('table')
                for t in tables:
                    if any(keyword in t.get_text().lower() for keyword in ['futures', 'contract', 'symbol', 'price']):
                        table = t
                        logger.info("✅ Found futures table using fallback method")
                        break
            
            if not table:
                logger.warning("⚠️ No futures table found on page")
                # Try to extract data from script tags (Yahoo sometimes loads data via JavaScript)
                return self._extract_from_scripts(soup)
            
            # Extract table rows
            rows = table.find_all('tr')
            logger.info(f"📊 Found {len(rows)} table rows")
            
            for row in rows:
                try:
                    # Skip header rows
                    if row.find('th') or 'header' in row.get('class', []):
                        continue
                    
                    # Extract cells
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 4:  # Need at least symbol, name, price, change
                        continue
                    
                    # Parse cell data
                    futures_item = self._parse_row_cells(cells)
                    if futures_item:
                        futures_data.append(futures_item)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing row: {str(e)}")
                    continue
            
            logger.info(f"✅ Successfully parsed {len(futures_data)} futures contracts")
            
        except Exception as e:
            logger.error(f"❌ Error parsing futures table: {str(e)}")
        
        return futures_data
    
    def _extract_from_scripts(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract futures data from JavaScript data embedded in script tags.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of futures data dictionaries
        """
        futures_data = []
        
        try:
            # Look for script tags containing JSON data
            scripts = soup.find_all('script')
            
            for script in scripts:
                if not script.string:
                    continue
                
                script_text = script.string
                
                # Look for common patterns in Yahoo Finance data
                if any(keyword in script_text for keyword in ['futures', 'quotes', 'symbols']):
                    try:
                        # Try to extract JSON data
                        import re
                        
                        # Look for JSON-like structures
                        json_patterns = [
                            r'\{[^{}]*"symbol"[^{}]*\}',
                            r'\[[^\[\]]*\{[^{}]*"symbol"[^{}]*\}[^\[\]]*\]',
                            r'"quotes":\s*(\[.*?\])',
                            r'"futures":\s*(\[.*?\])'
                        ]
                        
                        for pattern in json_patterns:
                            matches = re.findall(pattern, script_text, re.DOTALL)
                            for match in matches:
                                try:
                                    data = json.loads(match)
                                    if isinstance(data, list):
                                        for item in data:
                                            if isinstance(item, dict) and 'symbol' in item:
                                                futures_item = self._parse_json_item(item)
                                                if futures_item:
                                                    futures_data.append(futures_item)
                                    elif isinstance(data, dict) and 'symbol' in data:
                                        futures_item = self._parse_json_item(data)
                                        if futures_item:
                                            futures_data.append(futures_item)
                                except json.JSONDecodeError:
                                    continue
                        
                    except Exception as e:
                        logger.debug(f"⚠️ Error parsing script data: {str(e)}")
                        continue
            
            logger.info(f"✅ Extracted {len(futures_data)} futures contracts from scripts")
            
        except Exception as e:
            logger.error(f"❌ Error extracting from scripts: {str(e)}")
        
        return futures_data
    
    def _parse_row_cells(self, cells: List) -> Optional[Dict[str, Any]]:
        """
        Parse individual row cells to extract futures data.
        
        Args:
            cells: List of table cells
            
        Returns:
            Dictionary with futures data or None if parsing failed
        """
        try:
            if len(cells) < 4:
                return None
            
            # Extract text from cells
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            # Try to identify which cell contains what data
            symbol = None
            name = None
            price = None
            change_pct = None
            last_updated = None
            
            for i, text in enumerate(cell_texts):
                if not text:
                    continue
                
                # Symbol pattern (usually uppercase letters/numbers)
                if not symbol and re.match(r'^[A-Z0-9]+$', text):
                    symbol = text
                
                # Price pattern (decimal number)
                elif not price and re.match(r'^\d+\.?\d*$', text):
                    try:
                        price = float(text.replace(',', ''))
                    except ValueError:
                        continue
                
                # Change percentage pattern
                elif not change_pct and ('%' in text or '+' in text or '-' in text):
                    change_text = text.replace('%', '').replace('+', '').replace(',', '')
                    try:
                        change_pct = float(change_text)
                        if '+' in text:
                            change_pct = abs(change_pct)
                        elif '-' in text:
                            change_pct = -abs(change_pct)
                    except ValueError:
                        continue
                
                # Time pattern
                elif not last_updated and re.match(r'\d{1,2}:\d{2}', text):
                    last_updated = text
                
                # Name (usually longer text without special patterns)
                elif not name and len(text) > 3 and not re.match(r'^[A-Z0-9]+$', text):
                    name = text
            
            # Create futures item if we have at least symbol and price
            if symbol and price is not None:
                return {
                    "symbol": symbol,
                    "name": name or f"{symbol} Futures",
                    "price": price,
                    "change_percent": change_pct,
                    "last_updated": last_updated or datetime.now().strftime("%H:%M"),
                    "scraped_at": datetime.now().isoformat()
                }
            
        except Exception as e:
            logger.debug(f"⚠️ Error parsing row cells: {str(e)}")
        
        return None
    
    def _parse_json_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a JSON item to extract futures data.
        
        Args:
            item: JSON object with futures data
            
        Returns:
            Dictionary with futures data or None if parsing failed
        """
        try:
            # Common field mappings
            symbol = item.get('symbol') or item.get('ticker') or item.get('code')
            name = item.get('name') or item.get('longName') or item.get('shortName')
            price = item.get('price') or item.get('regularMarketPrice') or item.get('lastPrice')
            change_pct = item.get('changePercent') or item.get('regularMarketChangePercent')
            last_updated = item.get('lastUpdated') or item.get('regularMarketTime')
            
            if symbol and price is not None:
                # Convert price to float
                try:
                    price = float(price)
                except (ValueError, TypeError):
                    return None
                
                # Convert change percent to float
                if change_pct is not None:
                    try:
                        change_pct = float(change_pct)
                    except (ValueError, TypeError):
                        change_pct = None
                
                return {
                    "symbol": str(symbol),
                    "name": str(name) if name else f"{symbol} Futures",
                    "price": price,
                    "change_percent": change_pct,
                    "last_updated": str(last_updated) if last_updated else datetime.now().strftime("%H:%M"),
                    "scraped_at": datetime.now().isoformat()
                }
            
        except Exception as e:
            logger.debug(f"⚠️ Error parsing JSON item: {str(e)}")
        
        return None
    
    def scrape_futures(self) -> List[Dict[str, Any]]:
        """
        Scrape futures data from Yahoo Finance.
        
        Returns:
            List of futures data dictionaries
        """
        logger.info("🚀 Starting Yahoo Futures scraping...")
        
        all_futures_data = []
        
        try:
            # Try multiple futures URLs to get comprehensive data
            for url in self.base_urls:
                logger.info(f"📡 Scraping futures data from: {url}")
                
                # Make request to Yahoo Finance futures page
                response = self._make_request(url)
                if not response:
                    logger.warning(f"⚠️ Failed to fetch: {url}")
                    continue
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                logger.info(f"✅ HTML parsed successfully for: {url}")
                
                # Extract futures data from this page
                futures_data = self._parse_futures_table(soup)
                
                if not futures_data:
                    logger.warning(f"⚠️ No futures data extracted from: {url}")
                    # Try alternative approach - look for any structured data
                    futures_data = self._extract_alternative_data(soup)
                
                # Add to collection
                all_futures_data.extend(futures_data)
                
                # Add small delay between requests
                time.sleep(random.uniform(1, 2))
            
            # Remove duplicates based on symbol
            unique_futures = {}
            for item in all_futures_data:
                symbol = item.get('symbol')
                if symbol and symbol not in unique_futures:
                    unique_futures[symbol] = item
            
            final_futures_data = list(unique_futures.values())
            
            logger.info(f"✅ Scraping completed: {len(final_futures_data)} unique futures contracts found")
            return final_futures_data
            
        except Exception as e:
            logger.error(f"❌ Error during scraping: {str(e)}")
            return []
    
    def _extract_alternative_data(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Alternative method to extract futures data when main parsing fails.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of futures data dictionaries
        """
        futures_data = []
        
        try:
            # Look for any elements that might contain futures data
            # This is a fallback method when the main parsing fails
            
            # Look for elements with futures-related classes or IDs
            futures_elements = soup.find_all(['div', 'span', 'td'], 
                                           class_=lambda x: x and any(keyword in x.lower() 
                                                                     for keyword in ['futures', 'quote', 'price', 'symbol']))
            
            for element in futures_elements:
                text = element.get_text(strip=True)
                if not text or len(text) < 2:
                    continue
                
                # Try to extract structured data from text
                futures_item = self._extract_from_text(text)
                if futures_item:
                    futures_data.append(futures_item)
            
            logger.info(f"✅ Alternative extraction found {len(futures_data)} items")
            
        except Exception as e:
            logger.error(f"❌ Error in alternative extraction: {str(e)}")
        
        return futures_data
    
    def _extract_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract futures data from plain text.
        
        Args:
            text: Text to parse
            
        Returns:
            Dictionary with futures data or None if parsing failed
        """
        try:
            import re
            
            # Look for patterns in text
            # Symbol pattern
            symbol_match = re.search(r'\b([A-Z]{1,5})\b', text)
            if not symbol_match:
                return None
            
            symbol = symbol_match.group(1)
            
            # Price pattern
            price_match = re.search(r'\$?(\d+\.?\d*)', text)
            if not price_match:
                return None
            
            price = float(price_match.group(1))
            
            # Change pattern
            change_match = re.search(r'([+-]?\d+\.?\d*)%', text)
            change_pct = None
            if change_match:
                change_pct = float(change_match.group(1))
            
            return {
                "symbol": symbol,
                "name": f"{symbol} Futures",
                "price": price,
                "change_percent": change_pct,
                "last_updated": datetime.now().strftime("%H:%M"),
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.debug(f"⚠️ Error extracting from text: {str(e)}")
        
        return None
    
    def save_results(self, futures_data: List[Dict[str, Any]]) -> str:
        """
        Save futures data to JSON file.
        
        Args:
            futures_data: List of futures data dictionaries
            
        Returns:
            Path to saved file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"yahoo_futures_{timestamp}.json"
            filepath = self.output_dir / filename
            
            result_data = {
                "timestamp": datetime.now().isoformat(),
                "source": "Yahoo Finance Futures",
                "urls": self.base_urls,
                "total_contracts": len(futures_data),
                "futures_data": futures_data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Results saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Error saving results: {str(e)}")
            return ""
    
    def run(self) -> Dict[str, Any]:
        """
        Run the complete scraping process.
        
        Returns:
            Dictionary with scraping results
        """
        logger.info("🚀 Starting Yahoo Futures Scraper...")
        
        start_time = datetime.now()
        
        try:
            # Scrape futures data
            futures_data = self.scrape_futures()
            
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
            
            logger.info(f"✅ Yahoo Futures Scraper completed successfully")
            logger.info(f"📊 Total contracts: {len(futures_data)}")
            logger.info(f"⏱️ Execution time: {execution_time}")
            
            return {
                "success": True,
                "total_contracts": len(futures_data),
                "output_file": output_file,
                "execution_time": str(execution_time),
                "timestamp": datetime.now().isoformat(),
                "source": "yahoo_futures"
            }
            
        except Exception as e:
            logger.error(f"❌ Yahoo Futures Scraper failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": str(datetime.now() - start_time),
                "timestamp": datetime.now().isoformat(),
                "source": "yahoo_futures"
            }


def main():
    """Main function for running the scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Yahoo Futures Scraper")
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run scraper
    scraper = YahooFuturesScraper()
    results = scraper.run()
    
    # Print results
    if results.get("success"):
        print(f"\n✅ Yahoo Futures Scraper completed successfully!")
        print(f"📊 Total contracts: {results.get('total_contracts', 0)}")
        print(f"📁 Output file: {results.get('output_file', 'N/A')}")
        print(f"⏱️ Execution time: {results.get('execution_time', 'N/A')}")
    else:
        print(f"\n❌ Yahoo Futures Scraper failed!")
        print(f"Error: {results.get('error', 'Unknown error')}")
        print(f"⏱️ Execution time: {results.get('execution_time', 'N/A')}")
    
    return results


if __name__ == "__main__":
    main() 