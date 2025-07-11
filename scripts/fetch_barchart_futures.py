#!/usr/bin/env python3
"""
Yahoo Finance Top Movers Fetcher (formerly Barchart)
Fetch top moving stocks/ETFs by 24-hour percent change using yfinance
"""
import yfinance as yf
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YahooTopMovers:
    """Yahoo Finance Top Movers fetcher focusing on 24h percent change."""
    
    def __init__(self):
        # Popular tickers for top movers analysis
        self.tickers = [
            # Major indices
            'SPY', 'QQQ', 'IWM', 'DIA',
            # Sector ETFs
            'XLF', 'XLK', 'XLE', 'XLI', 'XLV', 'XLY', 'XLP', 'XLU', 'XLB', 'XLRE',
            # Popular individual stocks
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
            'AMD', 'INTC', 'JPM', 'BAC', 'WMT', 'JNJ', 'PG', 'KO',
            # Crypto-related
            'COIN', 'MSTR', 'SQ',
            # Commodities
            'GLD', 'SLV', 'USO', 'UNG',
            # Volatility
            'VIX', 'UVXY', 'VXX'
        ]
        
    def fetch_yahoo_gainers_losers(self) -> List[Dict[str, Any]]:
        """Fetch top gainers and losers from Yahoo Finance screener page."""
        movers_data = []
        
        try:
            # Fetch top gainers
            gainers_url = "https://finance.yahoo.com/screener/predefined/day_gainers"
            logger.info("📈 Fetching top gainers from Yahoo Finance...")
            gainers = self._scrape_yahoo_screener(gainers_url, "gainers")
            movers_data.extend(gainers[:10])  # Top 10 gainers
            
            # Fetch top losers  
            losers_url = "https://finance.yahoo.com/screener/predefined/day_losers"
            logger.info("📉 Fetching top losers from Yahoo Finance...")
            losers = self._scrape_yahoo_screener(losers_url, "losers")
            movers_data.extend(losers[:10])  # Top 10 losers
            
        except Exception as e:
            logger.warning(f"⚠️ Error fetching Yahoo screener data: {e}")
            
        return movers_data
    
    def _scrape_yahoo_screener(self, url: str, mover_type: str) -> List[Dict[str, Any]]:
        """Scrape Yahoo Finance screener page for movers."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the data table
            table = soup.find('table')
            if not table:
                logger.warning(f"⚠️ No table found on {mover_type} page")
                return []
            
            tbody = table.find('tbody')
            rows = []
            if tbody and hasattr(tbody, 'find_all'):
                rows = tbody.find_all('tr')
            screener_data = []
            
            for row in rows[:15]:  # Limit to top 15
                if hasattr(row, 'find_all'):
                    cols = row.find_all('td')
                else:
                    continue
                if len(cols) >= 5:
                    symbol = cols[0].text.strip()
                    name = cols[1].text.strip()
                    price = cols[2].text.strip()
                    change = cols[3].text.strip()
                    percent_change = cols[4].text.strip()
                    
                    screener_data.append({
                        "symbol": symbol,
                        "name": name,
                        "lastPrice": price,
                        "change": change,
                        "percentChange": percent_change,
                        "volume": "",  # Volume might be in a different column
                        "mover_type": mover_type
                    })
            
            logger.info(f"✅ Scraped {len(screener_data)} {mover_type} from Yahoo")
            return screener_data
            
        except Exception as e:
            logger.error(f"❌ Error scraping {mover_type}: {e}")
            return []
    
    def fetch_yfinance_movers(self) -> List[Dict[str, Any]]:
        """Fetch top movers using yfinance for our predefined ticker list."""
        movers_data = []
        
        logger.info(f"📊 Analyzing {len(self.tickers)} tickers for 24h moves...")
        
        # Fetch data for all tickers
        ticker_changes = []
        
        for symbol in self.tickers:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")  # Get last 2 days
                
                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    previous_price = hist['Close'].iloc[-2]
                    change = current_price - previous_price
                    percent_change = (change / previous_price) * 100
                    
                    # Get basic info
                    info = ticker.info
                    name = info.get('shortName', symbol)
                    volume = hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0
                    
                    ticker_changes.append({
                        "symbol": symbol,
                        "name": name,
                        "lastPrice": f"{current_price:.2f}",
                        "change": f"{change:+.2f}",
                        "percentChange": f"{percent_change:+.2f}%",
                        "volume": f"{int(volume):,}" if volume > 0 else "",
                        "percent_change_numeric": percent_change
                    })
                    
            except Exception as e:
                logger.warning(f"⚠️ Error fetching {symbol}: {e}")
                continue
        
        # Sort by absolute percent change (biggest movers first)
        ticker_changes.sort(key=lambda x: abs(x['percent_change_numeric']), reverse=True)
        
        # Take top 20 movers
        top_movers = ticker_changes[:20]
        
        # Add mover type based on direction
        for mover in top_movers:
            mover['mover_type'] = 'gainer' if mover['percent_change_numeric'] > 0 else 'loser'
            # Remove the numeric field used for sorting
            del mover['percent_change_numeric']
        
        logger.info(f"✅ Found {len(top_movers)} top movers from yfinance")
        return top_movers

def fetch_barchart_futures():
    """Main function - now fetches Yahoo top movers instead of Barchart futures."""
    logger.info("🚀 Fetching Yahoo Finance Top Movers (24h % change)...")
    
    fetcher = YahooTopMovers()
    
    # Try both methods and combine results
    all_movers = []
    
    # Method 1: Scrape Yahoo screener pages
    screener_movers = fetcher.fetch_yahoo_gainers_losers()
    all_movers.extend(screener_movers)
    
    # Method 2: Use yfinance for our curated list
    yfinance_movers = fetcher.fetch_yfinance_movers()
    all_movers.extend(yfinance_movers)
    
    # Remove duplicates based on symbol
    seen_symbols = set()
    unique_movers = []
    for mover in all_movers:
        if mover['symbol'] not in seen_symbols:
            unique_movers.append(mover)
            seen_symbols.add(mover['symbol'])
    
    # Sort by absolute percent change if available
    try:
        def get_abs_percent_change(mover):
            pct_str = mover.get('percentChange', '0%').replace('%', '').replace('+', '').replace('(', '').replace(')', '')
            try:
                return abs(float(pct_str))
            except:
                return 0
        
        unique_movers.sort(key=get_abs_percent_change, reverse=True)
    except:
        pass
    
    # Limit to top 25 overall
    final_movers = unique_movers[:25]
    
    logger.info(f"✅ Total unique movers found: {len(final_movers)}")
    return final_movers

def save_futures(futures):
    """Save movers data - keeping original function name for compatibility."""
    try:
        Path("output").mkdir(exist_ok=True)
        date_str = datetime.now().strftime('%Y%m%d')
        
        # Save with original filename for backward compatibility
        filename = f"barchart_futures_{date_str}.json"
        filepath = Path("output") / filename
        
        # Also save with new descriptive filename
        new_filename = f"yahoo_top_movers_{date_str}.json"
        new_filepath = Path("output") / new_filename
        
        # Save both files
        for file_path in [filepath, new_filepath]:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(futures, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Saved Yahoo top movers to:")
        logger.info(f"   📄 {filepath} (backward compatibility)")
        logger.info(f"   📄 {new_filepath} (new format)")
        
        return str(filepath)
    except Exception as e:
        logger.error(f"❌ Error saving Yahoo top movers: {e}")
        return ""

def main():
    movers = fetch_barchart_futures()
    if movers:
        save_futures(movers)
        
        # Print summary
        gainers = [m for m in movers if m.get('mover_type') == 'gainer' or '+' in m.get('percentChange', '')]
        losers = [m for m in movers if m.get('mover_type') == 'loser' or '-' in m.get('percentChange', '')]
        
        logger.info(f"📊 Summary: {len(gainers)} gainers, {len(losers)} losers")
        
        if gainers:
            top_gainer = max(gainers, key=lambda x: float(x.get('percentChange', '0%').replace('%', '').replace('+', '').replace('(', '').replace(')', '')) if x.get('percentChange') else 0)
            logger.info(f"🚀 Top gainer: {top_gainer['symbol']} ({top_gainer.get('percentChange', 'N/A')})")
        
        if losers:
            top_loser = min(losers, key=lambda x: float(x.get('percentChange', '0%').replace('%', '').replace('+', '').replace('(', '').replace(')', '').replace('-', '-')) if x.get('percentChange') else 0)
            logger.info(f"📉 Top loser: {top_loser['symbol']} ({top_loser.get('percentChange', 'N/A')})")
            
    else:
        logger.warning("⚠️ No movers data to save.")

if __name__ == "__main__":
    main() 