#!/usr/bin/env python3
"""
QuiverQuant Agent for MacroIntel

This agent connects to QuiverQuant API to fetch:
- Congressional trading data (Senate and House)
- Government contracts data
- Corporate lobbying data
- WallStreetBets discussion data

Data is stored in SQLite database for analysis and querying.
"""

import os
import sys
import json
import sqlite3
import requests
import pandas as pd
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuiverAgent:
    """
    QuiverQuant API Agent for fetching alternative financial data.
    
    Features:
    - Congressional trading data (Senate and House)
    - Government contracts data
    - Corporate lobbying data
    - WallStreetBets discussion data
    - SQLite database storage
    - Rate limiting and error handling
    """
    
    def __init__(self, api_key: str | None = None, db_path: str = "data/macrointel_data.sqlite"):
        """
        Initialize QuiverAgent with API key and database path.
        
        Args:
            api_key: QuiverQuant API key
            db_path: Path to SQLite database
        """
        self.api_key = api_key or os.getenv("QUIVER_API_KEY")
        if not self.api_key:
            logger.error("❌ QuiverQuant API key not found. Please set QUIVER_API_KEY environment variable.")
            print("Example .env content:")
            print("QUIVER_API_KEY=your_api_key_here")
            sys.exit(1)
        
        self.base_url = "https://api.quiverquant.com"
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        
        # Initialize database
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._init_database()
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("✅ Database schema initialized for QuiverQuant data")
        self.logger.info("🦅 QuiverAgent initialized successfully")
    
    def _init_database(self):
        """Initialize SQLite database tables for QuiverQuant data."""
        
        # Congressional trading table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS congress_trading (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                politician TEXT NOT NULL,
                chamber TEXT NOT NULL,  -- 'Senate' or 'House'
                ticker TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                amount_range TEXT,
                amount_min INTEGER,
                amount_max INTEGER,
                transaction_date TEXT,
                disclosure_date TEXT,
                asset_description TEXT,
                party TEXT,
                state TEXT,
                district TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(politician, ticker, transaction_date, transaction_type)
            )
        ''')
        
        # Government contracts table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS government_contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                company_name TEXT,
                contract_amount REAL,
                contract_description TEXT,
                agency TEXT,
                date_awarded TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, contract_description, date_awarded)
            )
        ''')
        
        # Corporate lobbying table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS corporate_lobbying (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                company_name TEXT,
                lobbying_amount REAL,
                issue_description TEXT,
                client TEXT,
                year INTEGER,
                quarter INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, issue_description, year, quarter)
            )
        ''')
        
        # WallStreetBets discussion table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS wallstreetbets_discussion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                mentions INTEGER,
                sentiment_score REAL,
                date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, date)
            )
        ''')
        
        # Create indexes for better query performance
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_congress_ticker ON congress_trading(ticker)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_congress_date ON congress_trading(transaction_date)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_contracts_ticker ON government_contracts(ticker)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_lobbying_ticker ON corporate_lobbying(ticker)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_wsb_ticker ON wallstreetbets_discussion(ticker)')
        
        self.conn.commit()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] | None = None) -> Optional[Dict[str, Any]]:
        """
        Make authenticated request to QuiverQuant API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            API response data or None if failed
        """
        try:
            url = f"{self.base_url}{endpoint}"
            self.logger.info(f"📡 Making request to: {endpoint}")
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"❌ API request failed for {endpoint}: {e}")
            self.logger.error(f"❌ Response status: {response.status_code}")
            self.logger.error(f"❌ Response text: {response.text}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Request failed for {endpoint}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ JSON decode error for {endpoint}: {e}")
            return None
    
    def fetch_congress_trading(self, days: int = 30, tickers: List[str] | None = None) -> bool:
        """
        Fetch congressional trading data from both Senate and House.
        
        Args:
            days: Number of days of historical data
            tickers: Specific tickers to fetch (optional)
            
        Returns:
            Success status
        """
        self.logger.info(f"🏛️ Fetching congressional trading data for last {days} days")
        
        senate_success = self._fetch_senate_trading(days, tickers)
        house_success = self._fetch_house_trading(days, tickers)
        
        return senate_success or house_success
    
    def _fetch_senate_trading(self, days: int, tickers: List[str] | None = None) -> bool:
        """Fetch Senate trading data"""
        try:
            params = {}
            if tickers:
                params["tickers"] = ",".join(tickers)
            
            data = self._make_request("/beta/live/senatetrading", params)
            
            if not data:
                return False
            
            # Process and store data
            records = []
            for item in data:
                if isinstance(item, dict):
                    records.append({
                        "politician": str(item.get("Senator", "")),
                        "chamber": "Senate",
                        "ticker": str(item.get("Ticker", "")),
                        "transaction_type": str(item.get("Transaction", "")),
                        "amount_range": str(item.get("Range", "")),
                        "amount_min": self._parse_amount_range(str(item.get("Range", "")), "min"),
                        "amount_max": self._parse_amount_range(str(item.get("Range", "")), "max"),
                        "transaction_date": str(item.get("TransactionDate", "")),
                        "disclosure_date": str(item.get("DisclosureDate", "")),
                        "asset_description": str(item.get("AssetDescription", "")),
                        "party": str(item.get("Party", "")),
                        "state": str(item.get("State", "")),
                        "district": ""
                    })
            
            return self._store_congress_data(records)
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching Senate trading data: {str(e)}")
            return False
    
    def _fetch_house_trading(self, days: int, tickers: List[str] | None = None) -> bool:
        """Fetch House trading data"""
        try:
            params = {}
            if tickers:
                params["tickers"] = ",".join(tickers)
            
            data = self._make_request("/beta/live/housetrading", params)
            
            if not data:
                return False
            
            # Process and store data
            records = []
            for item in data:
                if isinstance(item, dict):
                    records.append({
                        "politician": str(item.get("Representative", "")),
                        "chamber": "House",
                        "ticker": str(item.get("Ticker", "")),
                        "transaction_type": str(item.get("Transaction", "")),
                        "amount_range": str(item.get("Range", "")),
                        "amount_min": self._parse_amount_range(str(item.get("Range", "")), "min"),
                        "amount_max": self._parse_amount_range(str(item.get("Range", "")), "max"),
                        "transaction_date": str(item.get("TransactionDate", "")),
                        "disclosure_date": str(item.get("DisclosureDate", "")),
                        "asset_description": str(item.get("AssetDescription", "")),
                        "party": str(item.get("Party", "")),
                        "state": str(item.get("State", "")),
                        "district": str(item.get("District", ""))
                    })
            
            return self._store_congress_data(records)
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching House trading data: {str(e)}")
            return False
    
    def fetch_government_contracts(self, tickers: List[str] | None = None) -> bool:
        """
        Fetch government contracts data.
        
        Args:
            tickers: Specific tickers to fetch (optional)
            
        Returns:
            Success status
        """
        self.logger.info("🏛️ Fetching government contracts data")
        
        params = {}
        if tickers:
            params["tickers"] = ",".join(tickers)
        
        data = self._make_request("/beta/live/govcontracts", params)
        
        if not data:
            return False
        
        # Process and store data
        try:
            records = []
            for item in data:
                if isinstance(item, dict):
                    records.append({
                        "ticker": item.get("Ticker", ""),
                        "company_name": item.get("Company", ""),
                        "contract_amount": item.get("Amount", 0),
                        "contract_description": item.get("Description", ""),
                        "agency": item.get("Agency", ""),
                        "date_awarded": item.get("Date", "")
                    })
            
            return self._store_contracts_data(records)
            
        except Exception as e:
            self.logger.error(f"❌ Error processing government contracts data: {str(e)}")
            return False
    
    def fetch_corporate_lobbying(self, tickers: List[str] | None = None) -> bool:
        """
        Fetch corporate lobbying data.
        
        Args:
            tickers: Specific tickers to fetch (optional)
            
        Returns:
            Success status
        """
        self.logger.info("🏛️ Fetching corporate lobbying data")
        
        params = {}
        if tickers:
            params["tickers"] = ",".join(tickers)
        
        data = self._make_request("/beta/live/lobbying", params)
        
        if not data:
            return False
        
        # Process and store data
        try:
            records = []
            for item in data:
                if isinstance(item, dict):
                    records.append({
                        "ticker": str(item.get("Ticker", "")),
                        "company_name": str(item.get("Company", "")),
                        "lobbying_amount": float(item.get("Amount", 0)),
                        "issue_description": str(item.get("Issue", "")),
                        "client": str(item.get("Client", "")),
                        "year": str(item.get("Year", "")),
                        "quarter": str(item.get("Quarter", ""))
                    })
            
            return self._store_lobbying_data(records)
            
        except Exception as e:
            self.logger.error(f"❌ Error processing corporate lobbying data: {str(e)}")
            return False
    
    def fetch_wallstreetbets_discussion(self, tickers: List[str] | None = None) -> bool:
        """
        Fetch WallStreetBets discussion data.
        
        Args:
            tickers: Specific tickers to fetch (optional)
            
        Returns:
            Success status
        """
        self.logger.info("📈 Fetching WallStreetBets discussion data")
        
        params = {}
        if tickers:
            params["tickers"] = ",".join(tickers)
        
        data = self._make_request("/beta/live/wallstreetbets", params)
        
        if not data:
            return False
        
        # Process and store data
        try:
            records = []
            for item in data:
                if isinstance(item, dict):
                    records.append({
                        "ticker": str(item.get("Ticker", "")),
                        "mentions": int(item.get("Mentions", 0)),
                        "sentiment_score": float(item.get("Sentiment", 0.0)),
                        "date": str(item.get("Date", ""))
                    })
            
            return self._store_wsb_data(records)
            
        except Exception as e:
            self.logger.error(f"❌ Error processing WallStreetBets discussion data: {str(e)}")
            return False
    
    def _parse_amount_range(self, range_str: str, part: str) -> Optional[int]:
        """
        Parse amount range string to extract min/max values.
        
        Args:
            range_str: Range string like "$1,001 - $15,000"
            part: "min" or "max"
        
        Returns:
            Parsed amount or None
        """
        if not range_str:
            return None
        
        try:
            # Remove $ and commas, split on -
            clean_range = range_str.replace("$", "").replace(",", "")
            if " - " in clean_range:
                parts = clean_range.split(" - ")
                if len(parts) == 2:
                    return int(parts[0]) if part == "min" else int(parts[1])
            
            # Single value
            return int(clean_range)
            
        except (ValueError, IndexError):
            return None
    
    def _store_congress_data(self, records: List[Dict[str, Any]]) -> bool:
        """Store congressional trading data in database"""
        try:
            count = 0
            for record in records:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO congress_trading 
                    (politician, chamber, ticker, transaction_type, amount_range, 
                     amount_min, amount_max, transaction_date, disclosure_date, 
                     asset_description, party, state, district)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record["politician"],
                    record["chamber"],
                    record["ticker"],
                    record["transaction_type"],
                    record["amount_range"],
                    record["amount_min"],
                    record["amount_max"],
                    record["transaction_date"],
                    record["disclosure_date"],
                    record["asset_description"],
                    record["party"],
                    record["state"],
                    record["district"]
                ))
                count += 1
            
            self.conn.commit()
            self.logger.info(f"✅ Stored {count} congressional trading records")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error storing congressional data: {str(e)}")
            return False
    
    def _store_contracts_data(self, records: List[Dict[str, Any]]) -> bool:
        """Store government contracts data in database"""
        try:
            count = 0
            for record in records:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO government_contracts 
                    (ticker, company_name, contract_amount, contract_description, agency, date_awarded)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    record["ticker"],
                    record["company_name"],
                    record["contract_amount"],
                    record["contract_description"],
                    record["agency"],
                    record["date_awarded"]
                ))
                count += 1
            
            self.conn.commit()
            self.logger.info(f"✅ Stored {count} government contract records")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error storing contracts data: {str(e)}")
            return False
    
    def _store_lobbying_data(self, records: List[Dict[str, Any]]) -> bool:
        """Store corporate lobbying data in database"""
        try:
            count = 0
            for record in records:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO corporate_lobbying 
                    (ticker, company_name, lobbying_amount, issue_description, client, year, quarter)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record["ticker"],
                    record["company_name"],
                    record["lobbying_amount"],
                    record["issue_description"],
                    record["client"],
                    record["year"],
                    record["quarter"]
                ))
                count += 1
            
            self.conn.commit()
            self.logger.info(f"✅ Stored {count} corporate lobbying records")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error storing lobbying data: {str(e)}")
            return False
    
    def _store_wsb_data(self, records: List[Dict[str, Any]]) -> bool:
        """Store WallStreetBets discussion data in database"""
        try:
            count = 0
            for record in records:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO wallstreetbets_discussion 
                    (ticker, mentions, sentiment_score, date)
                    VALUES (?, ?, ?, ?)
                ''', (
                    record["ticker"],
                    record["mentions"],
                    record["sentiment_score"],
                    record["date"]
                ))
                count += 1
            
            self.conn.commit()
            self.logger.info(f"✅ Stored {count} WallStreetBets discussion records")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error storing WallStreetBets data: {str(e)}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with counts of various data types
        """
        stats = {}
        
        # Congressional trading count
        self.cursor.execute("SELECT COUNT(*) FROM congress_trading")
        stats["congress_trading_count"] = self.cursor.fetchone()[0]
        
        # Government contracts count
        self.cursor.execute("SELECT COUNT(*) FROM government_contracts")
        stats["government_contracts_count"] = self.cursor.fetchone()[0]
        
        # Corporate lobbying count
        self.cursor.execute("SELECT COUNT(*) FROM corporate_lobbying")
        stats["corporate_lobbying_count"] = self.cursor.fetchone()[0]
        
        # WallStreetBets discussion count
        self.cursor.execute("SELECT COUNT(*) FROM wallstreetbets_discussion")
        stats["wallstreetbets_discussion_count"] = self.cursor.fetchone()[0]
        
        return stats
    
    def get_recent_congress_trades(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent congressional trades.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of recent trades
        """
        self.cursor.execute('''
            SELECT politician, chamber, ticker, transaction_type, amount_range, 
                   transaction_date, disclosure_date, party, state
            FROM congress_trading
            ORDER BY disclosure_date DESC
            LIMIT ?
        ''', (limit,))
        
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
    
    def get_ticker_activity(self, ticker: str) -> Dict[str, Any]:
        """
        Get all QuiverQuant activity for a specific ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with all activity data
        """
        activity = {}
        
        # Congressional trading
        self.cursor.execute('''
            SELECT politician, chamber, transaction_type, amount_range, 
                   transaction_date, disclosure_date, party, state
            FROM congress_trading
            WHERE ticker = ?
            ORDER BY disclosure_date DESC
            LIMIT 50
        ''', (ticker,))
        
        columns = [desc[0] for desc in self.cursor.description]
        activity["congress_trading"] = [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        
        # Government contracts
        self.cursor.execute('''
            SELECT company_name, contract_amount, contract_description, agency, date_awarded
            FROM government_contracts
            WHERE ticker = ?
            ORDER BY date_awarded DESC
            LIMIT 50
        ''', (ticker,))
        
        columns = [desc[0] for desc in self.cursor.description]
        activity["government_contracts"] = [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        
        # Corporate lobbying
        self.cursor.execute('''
            SELECT company_name, lobbying_amount, issue_description, client, year, quarter
            FROM corporate_lobbying
            WHERE ticker = ?
            ORDER BY year DESC, quarter DESC
            LIMIT 50
        ''', (ticker,))
        
        columns = [desc[0] for desc in self.cursor.description]
        activity["corporate_lobbying"] = [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        
        # WallStreetBets discussion
        self.cursor.execute('''
            SELECT mentions, sentiment_score, date
            FROM wallstreetbets_discussion
            WHERE ticker = ?
            ORDER BY date DESC
            LIMIT 50
        ''', (ticker,))
        
        columns = [desc[0] for desc in self.cursor.description]
        activity["wallstreetbets_discussion"] = [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        
        return activity
    
    def run_quiver_pipeline(self, days: int = 30, fetch_all: bool = True) -> Dict[str, Any]:
        """
        Run complete Quiver data pipeline.
        
        Args:
            days: Number of days of historical data to fetch
            fetch_all: Whether to fetch all data types or just congressional trades
            
        Returns:
            Dictionary with pipeline results and statistics
        """
        results = {
            'success': True,
            'errors': [],
            'data_fetched': {},
            'stats': {}
        }
        
        logger.info("🚀 Starting Quiver data pipeline...")
        
        try:
            # Always fetch congressional trading data
            congress_success = self.fetch_congress_trading(days)
            results['data_fetched']['congress_trading'] = congress_success
            if not congress_success:
                results['errors'].append("Failed to fetch congressional trading data")
            
            if fetch_all:
                # Fetch government contracts
                contracts_success = self.fetch_government_contracts()
                results['data_fetched']['government_contracts'] = contracts_success
                if not contracts_success:
                    results['errors'].append("Failed to fetch government contracts data")
                
                # Fetch corporate lobbying
                lobbying_success = self.fetch_corporate_lobbying()
                results['data_fetched']['corporate_lobbying'] = lobbying_success
                if not lobbying_success:
                    results['errors'].append("Failed to fetch corporate lobbying data")
                
                # Fetch WallStreetBets discussion
                wsb_success = self.fetch_wallstreetbets_discussion()
                results['data_fetched']['wallstreetbets'] = wsb_success
                if not wsb_success:
                    results['errors'].append("Failed to fetch WallStreetBets data")
            
            # Get final database statistics
            results['stats'] = self.get_database_stats()
            
            if results['errors']:
                results['success'] = False
                logger.warning(f"⚠️ Pipeline completed with {len(results['errors'])} errors")
            else:
                logger.info("✅ Quiver data pipeline completed successfully")
                
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Pipeline error: {str(e)}")
            logger.error(f"❌ Pipeline failed: {str(e)}")
        
        return results

def run_quiver_pipeline(days: int = 30, fetch_all: bool = True) -> Dict[str, Any]:
    """
    Convenience function to run Quiver data pipeline.
    
    Args:
        days: Number of days of historical data to fetch
        fetch_all: Whether to fetch all data types or just congressional trades
        
    Returns:
        Dictionary with pipeline results and statistics
    """
    try:
        agent = QuiverAgent()
        return agent.run_quiver_pipeline(days, fetch_all)
    except Exception as e:
        logger.error(f"❌ Failed to run Quiver pipeline: {str(e)}")
        return {
            'success': False,
            'errors': [f"Pipeline initialization error: {str(e)}"],
            'data_fetched': {},
            'stats': {}
        }

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="QuiverQuant Data Fetcher")
    parser.add_argument("--congress", action="store_true", help="Fetch congressional trading data")
    parser.add_argument("--contracts", action="store_true", help="Fetch government contracts data")
    parser.add_argument("--lobbying", action="store_true", help="Fetch corporate lobbying data")
    parser.add_argument("--wsb", action="store_true", help="Fetch WallStreetBets discussion data")
    parser.add_argument("--all", action="store_true", help="Fetch all available data")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--tickers", nargs="+", help="Specific tickers to fetch")
    parser.add_argument("--days", type=int, default=30, help="Days of historical data")
    
    args = parser.parse_args()
    
    try:
        agent = QuiverAgent()
        
        if args.stats:
            stats = agent.get_database_stats()
            print("📊 Database Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value:,}")
            return
        
        if args.all:
            print("🔄 Fetching all QuiverQuant data...")
            agent.fetch_congress_trading(args.days, args.tickers)
            agent.fetch_government_contracts(args.tickers)
            agent.fetch_corporate_lobbying(args.tickers)
            agent.fetch_wallstreetbets_discussion(args.tickers)
        else:
            if args.congress:
                agent.fetch_congress_trading(args.days, args.tickers)
            if args.contracts:
                agent.fetch_government_contracts(args.tickers)
            if args.lobbying:
                agent.fetch_corporate_lobbying(args.tickers)
            if args.wsb:
                agent.fetch_wallstreetbets_discussion(args.tickers)
        
        # Show final stats
        stats = agent.get_database_stats()
        print("\n📊 Final Database Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value:,}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()