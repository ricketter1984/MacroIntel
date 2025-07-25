#!/usr/bin/env python3
"""
CME Data Scraper Module

Scrapes settlement data from CME Group quotes pages for specific futures contracts:
- MGC (Micro Gold Futures)
- MCL (Crude Oil Futures)  
- MYM (Micro E-mini Dow Futures)

Extracts: Symbol, Last Price, Change, Volume, Open Interest
"""

import requests
import pandas as pd
import logging
import traceback
import os
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class CMEQuotesScraper:
    """CME Group quotes page scraper."""
    
    def __init__(self):
        """Initialize the CME quotes scraper."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Hardcoded CME URLs for each symbol
        self.cme_urls = {
            'MGC': 'https://www.cmegroup.com/markets/metals/precious/gold.html',
            'MCL': 'https://www.cmegroup.com/markets/energy/crude-oil/light-sweet-crude.html', 
            'MYM': 'https://www.cmegroup.com/markets/equities/dow-jones/e-mini-dow.html'
        }
        
        # Alternative CME URLs if primary fails
        self.alt_urls = {
            'MGC': [
                'https://www.cmegroup.com/trading/metals/precious/gold-futures.html',
                'https://www.cmegroup.com/markets/metals/precious/micro-gold-futures.html'
            ],
            'MCL': [
                'https://www.cmegroup.com/trading/energy/crude-oil/light-sweet-crude-oil.html',
                'https://www.cmegroup.com/markets/energy/crude-oil/wti-crude-oil-futures.html'
            ],
            'MYM': [
                'https://www.cmegroup.com/trading/equity-index/us-index/e-mini-dow-futures.html',
                'https://www.cmegroup.com/markets/equities/dow-jones/micro-e-mini-dow-futures.html'
            ]
        }
        
        logger.info(f"🏦 CME Quotes Scraper initialized for {len(self.cme_urls)} symbols")
    
    def scrape_symbol_data(self, symbol):
        """
        Scrape settlement data for a specific symbol from CME Group.
        
        Args:
            symbol (str): Symbol to scrape (MGC, MCL, MYM)
            
        Returns:
            dict: Settlement data or None if failed
        """
        if symbol not in self.cme_urls:
            logger.error(f"❌ Unknown symbol: {symbol}")
            return None
        
        logger.info(f"📊 Scraping {symbol} from CME Group...")
        
        # Try primary URL first
        urls_to_try = [self.cme_urls[symbol]] + self.alt_urls.get(symbol, [])
        
        for url in urls_to_try:
            try:
                logger.info(f"🌐 Attempting to fetch: {url}")
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    data = self._parse_cme_page(symbol, response.content, url)
                    if data:
                        logger.info(f"✅ Successfully scraped {symbol} data")
                        return data
                else:
                    logger.warning(f"⚠️ HTTP {response.status_code} for {url}")
                    
            except Exception as e:
                logger.error(f"❌ Error fetching {url}: {str(e)}")
                logger.debug(f"Full traceback: {traceback.format_exc()}")
                continue
        
        # If all URLs fail, return None instead of creating mock data
        logger.warning(f"⚠️ All URLs failed for {symbol} - data unavailable")
        return None
    
    def _parse_cme_page(self, symbol, html_content, url):
        """Parse CME Group page for settlement data."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Strategy 1: Look for quotes tables
            data = self._parse_quotes_table(symbol, soup)
            if data:
                return data
            
            # Strategy 2: Look for settlement tables
            data = self._parse_settlement_table(symbol, soup)
            if data:
                return data
            
            # Strategy 3: Look for market data divs/sections
            data = self._parse_market_data_sections(symbol, soup)
            if data:
                return data
            
            # Strategy 4: Try pandas read_html
            data = self._parse_with_pandas(symbol, html_content)
            if data:
                return data
            
            logger.warning(f"⚠️ No parseable data found on {url}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error parsing {symbol} page: {str(e)}")
            logger.debug(f"Full traceback: {traceback.format_exc()}")
            return None
    
    def _parse_quotes_table(self, symbol, soup):
        """Parse quotes table from CME page."""
        try:
            # Look for tables with quote/price data
            tables = soup.find_all('table')
            for table in tables:
                # Check table headers for relevant content
                headers = []
                header_rows = table.find_all('tr')[:3]  # Check first few rows
                for row in header_rows:
                    cells = row.find_all(['th', 'td'])
                    for cell in cells:
                        if cell.get_text():
                            headers.append(cell.get_text().strip().lower())
                
                header_text = ' '.join(headers)
                if any(keyword in header_text for keyword in ['last', 'price', 'volume', 'open interest', 'change']):
                    return self._extract_data_from_table(symbol, table)
            
            return None
            
        except Exception as e:
            logger.debug(f"Error parsing quotes table for {symbol}: {str(e)}")
            return None
    
    def _parse_settlement_table(self, symbol, soup):
        """Parse settlement table from CME page."""
        try:
            # Look for elements with settlement-related classes or IDs
            settlement_elements = soup.find_all(['table', 'div'], class_=lambda x: x and any(
                term in str(x).lower() for term in ['settlement', 'quote', 'price', 'market']
            ))
            
            for element in settlement_elements:
                if element.name == 'table':
                    data = self._extract_data_from_table(symbol, element)
                    if data:
                        return data
                elif element.name == 'div':
                    # Look for nested tables
                    nested_tables = element.find_all('table')
                    for table in nested_tables:
                        data = self._extract_data_from_table(symbol, table)
                        if data:
                            return data
            
            return None
            
        except Exception as e:
            logger.debug(f"Error parsing settlement table for {symbol}: {str(e)}")
            return None
    
    def _parse_market_data_sections(self, symbol, soup):
        """Parse market data from structured sections."""
        try:
            # Look for market data in structured divs/spans
            data_dict = {'symbol': symbol}
            
            # Common patterns for market data
            patterns = {
                'last_price': ['last', 'price', 'current'],
                'change': ['change', 'chg', 'net change'],
                'volume': ['volume', 'vol'],
                'open_interest': ['open interest', 'oi', 'open int']
            }
            
            for field, keywords in patterns.items():
                value = self._find_market_value(soup, keywords)
                if value is not None:
                    data_dict[field] = value
            
            # Check if we found meaningful data
            if len(data_dict) > 2:  # More than just symbol
                return data_dict
            
            return None
            
        except Exception as e:
            logger.debug(f"Error parsing market data sections for {symbol}: {str(e)}")
            return None
    
    def _parse_with_pandas(self, symbol, html_content):
        """Try parsing with pandas read_html."""
        try:
            # Use pandas to read all tables
            dfs = pd.read_html(html_content)
            
            for df in dfs:
                if len(df) > 0 and len(df.columns) >= 3:
                    # Look for columns that might contain our data
                    df_str = df.to_string().lower()
                    if any(keyword in df_str for keyword in ['last', 'price', 'volume', 'change']):
                        # Try to extract data from this table
                        data = self._extract_from_dataframe(symbol, df)
                        if data:
                            return data
            
            return None
            
        except Exception as e:
            logger.debug(f"Error parsing with pandas for {symbol}: {str(e)}")
            return None
    
    def _extract_data_from_table(self, symbol, table):
        """Extract settlement data from a table element."""
        try:
            rows = table.find_all('tr')
            if len(rows) < 2:
                return None
            
            # Get headers
            header_row = rows[0]
            headers = [th.get_text().strip().lower() for th in header_row.find_all(['th', 'td'])]
            
            # Find data row (usually first data row after header)
            data_row = None
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= len(headers) and any(cell.get_text().strip() for cell in cells):
                    data_row = row
                    break
            
            if not data_row:
                return None
            
            # Extract cell values
            values = [cell.get_text().strip() for cell in data_row.find_all(['td', 'th'])]
            
            # Map headers to values
            data_dict = {'symbol': symbol}
            for i, header in enumerate(headers):
                if i < len(values) and values[i]:
                    value = self._clean_numeric_value(values[i])
                    if 'last' in header or 'price' in header:
                        data_dict['last_price'] = value
                    elif 'change' in header or 'chg' in header:
                        data_dict['change'] = value
                    elif 'volume' in header or 'vol' in header:
                        data_dict['volume'] = value
                    elif 'open interest' in header or 'oi' in header:
                        data_dict['open_interest'] = value
            
            # Check if we found meaningful data
            if len(data_dict) > 2:
                return data_dict
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting data from table for {symbol}: {str(e)}")
            return None
    
    def _extract_from_dataframe(self, symbol, df):
        """Extract data from pandas DataFrame."""
        try:
            df_str = df.to_string().lower()
            data_dict = {'symbol': symbol}
            
            # Try to find values by searching the string representation
            lines = df_str.split('\n')
            for line in lines:
                # Look for numeric values that might be our data
                import re
                numbers = re.findall(r'[\d,]+\.?\d*', line)
                if numbers and any(keyword in line for keyword in ['last', 'price', 'change', 'volume']):
                    # This is a heuristic approach - would need refinement for production
                    if 'last' in line or 'price' in line:
                        data_dict['last_price'] = self._clean_numeric_value(numbers[0])
                    elif 'change' in line:
                        data_dict['change'] = self._clean_numeric_value(numbers[0])
                    elif 'volume' in line:
                        data_dict['volume'] = self._clean_numeric_value(numbers[0])
            
            if len(data_dict) > 1:
                return data_dict
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting from DataFrame for {symbol}: {str(e)}")
            return None
    
    def _find_market_value(self, soup, keywords):
        """Find market value by searching for keywords."""
        try:
            for keyword in keywords:
                # Look for spans, divs, or other elements containing the keyword
                elements = soup.find_all(['span', 'div', 'td', 'th'], 
                                       string=lambda text: text and keyword in text.lower())
                
                for element in elements:
                    # Look for numeric values near this element
                    parent = element.parent
                    if parent:
                        # Check siblings and children for numeric values
                        for sibling in parent.find_all(['span', 'div', 'td']):
                            text = sibling.get_text().strip()
                            if text and any(c.isdigit() for c in text):
                                cleaned = self._clean_numeric_value(text)
                                if cleaned is not None:
                                    return cleaned
            
            return None
            
        except Exception as e:
            logger.debug(f"Error finding market value: {str(e)}")
            return None
    
    def _clean_numeric_value(self, text):
        """Clean and convert text to numeric value."""
        try:
            if not text:
                return None
            
            # Remove common formatting
            cleaned = text.replace(',', '').replace('$', '').replace('%', '').strip()
            
            # Handle negative values
            is_negative = '-' in cleaned or '(' in cleaned
            cleaned = cleaned.replace('-', '').replace('(', '').replace(')', '')
            
            # Try to convert to float
            try:
                value = float(cleaned)
                return -value if is_negative else value
            except ValueError:
                return None
                
        except Exception:
            return None

def fetch_cme_data():
    """
    Fetch CME settlement data for MGC, MCL, and MYM contracts.
    Saves results to output/cme_data_today.csv and returns DataFrame.
    
    Returns:
        pandas.DataFrame: Settlement data with Symbol, Last Price, Change, Volume, Open Interest
    """
    try:
        logger.info("🏦 Starting CME Group data scraping for MGC, MCL, MYM...")
        
        scraper = CMEQuotesScraper()
        results = []
        
        # Scrape each symbol
        for symbol in ['MGC', 'MCL', 'MYM']:
            try:
                data = scraper.scrape_symbol_data(symbol)
                if data:
                    results.append(data)
                    logger.info(f"✅ {symbol}: Last=${data.get('last_price', 'N/A')}, "
                              f"Change={data.get('change', 'N/A')}, "
                              f"Volume={data.get('volume', 'N/A')}")
                else:
                    logger.error(f"❌ {symbol}: No data retrieved")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {symbol}: {str(e)}")
                logger.error(f"Full traceback: {traceback.format_exc()}")
        
        if not results:
            logger.error("❌ No data could be retrieved for any symbols")
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(results)
        
        # Ensure we have the required columns
        required_columns = ['symbol', 'last_price', 'change', 'volume', 'open_interest']
        for col in required_columns:
            if col not in df.columns:
                df[col] = None
        
        # Reorder columns
        df = df[required_columns]
        
        # Add timestamp
        df['fetch_time'] = datetime.now().isoformat()
        
        # Save to CSV
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        csv_path = output_dir / 'cme_data_today.csv'
        df.to_csv(csv_path, index=False)
        
        logger.info(f"✅ CME data saved to {csv_path}")
        logger.info(f"📊 Retrieved data for {len(df)} symbols")
        
        return df
        
    except Exception as e:
        logger.error(f"❌ Critical error in fetch_cme_data: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return pd.DataFrame()

if __name__ == "__main__":
    """Test the CME scraper."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
    
    print("🚀 Testing CME Group Settlement Scraper...")
    
    df = fetch_cme_data()
    
    if not df.empty:
        print(f"✅ Test completed successfully!")
        print(f"📊 Scraped data for {len(df)} symbols:")
        print(df.to_string(index=False))
    else:
        print("❌ Test failed - check logs for details") 