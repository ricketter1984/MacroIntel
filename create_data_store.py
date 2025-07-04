#!/usr/bin/env python3
"""
Script to create the data_store.py module
"""

content = '''"""
MacroIntel Data Store Module

Provides persistent storage for MacroIntel using SQLite database.
Manages economic events, news headlines, and regime scores.
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
import os
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_PATH = "macrointel.db"
DB_VERSION = "1.0"

class MacroIntelDataStore:
    """Main data store class for MacroIntel persistent storage."""
    
    def __init__(self, db_path: str = DB_PATH):
        """Initialize the data store with the specified database path."""
        self.db_path = db_path
        self.setup_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections with automatic cleanup."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def setup_database(self):
        """Create database tables if they don't exist."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create economic_events table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS economic_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        time TEXT NOT NULL,
                        event_name TEXT NOT NULL,
                        impact_level TEXT,
                        forecast TEXT,
                        actual TEXT,
                        category TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create news_headlines table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS news_headlines (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        source TEXT NOT NULL,
                        symbol TEXT,
                        headline TEXT NOT NULL,
                        summary TEXT,
                        sentiment TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create regime_scores table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS regime_scores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        total_score REAL NOT NULL,
                        volatility REAL NOT NULL,
                        structure REAL NOT NULL,
                        momentum REAL NOT NULL,
                        breadth REAL NOT NULL,
                        institutional REAL NOT NULL,
                        strategy TEXT,
                        instrument TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_economic_events_date ON economic_events(date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_headlines_symbol ON news_headlines(symbol)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_headlines_timestamp ON news_headlines(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_regime_scores_timestamp ON regime_scores(timestamp)")
                
                conn.commit()
                logger.info("Database setup completed successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Database setup error: {e}")
            raise
    
    def insert_economic_event(self, event_data: Dict[str, Any]) -> int:
        """Insert a new economic event record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO economic_events 
                    (date, time, event_name, impact_level, forecast, actual, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_data.get('date'),
                    event_data.get('time'),
                    event_data.get('event_name'),
                    event_data.get('impact_level'),
                    event_data.get('forecast'),
                    event_data.get('actual'),
                    event_data.get('category')
                ))
                conn.commit()
                event_id = cursor.lastrowid
                logger.info(f"Inserted economic event with ID: {event_id}")
                return event_id
                
        except sqlite3.Error as e:
            logger.error(f"Error inserting economic event: {e}")
            raise
    
    def insert_news_headline(self, headline_data: Dict[str, Any]) -> int:
        """Insert a new news headline record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO news_headlines 
                    (timestamp, source, symbol, headline, summary, sentiment)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    headline_data.get('timestamp'),
                    headline_data.get('source'),
                    headline_data.get('symbol'),
                    headline_data.get('headline'),
                    headline_data.get('summary'),
                    headline_data.get('sentiment')
                ))
                conn.commit()
                headline_id = cursor.lastrowid
                logger.info(f"Inserted news headline with ID: {headline_id}")
                return headline_id
                
        except sqlite3.Error as e:
            logger.error(f"Error inserting news headline: {e}")
            raise
    
    def insert_regime_score(self, score_data: Dict[str, Any]) -> int:
        """Insert a new regime score record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO regime_scores 
                    (timestamp, total_score, volatility, structure, momentum, breadth, institutional, strategy, instrument)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    score_data.get('timestamp'),
                    score_data.get('total_score'),
                    score_data.get('volatility'),
                    score_data.get('structure'),
                    score_data.get('momentum'),
                    score_data.get('breadth'),
                    score_data.get('institutional'),
                    score_data.get('strategy'),
                    score_data.get('instrument')
                ))
                conn.commit()
                score_id = cursor.lastrowid
                logger.info(f"Inserted regime score with ID: {score_id}")
                return score_id
                
        except sqlite3.Error as e:
            logger.error(f"Error inserting regime score: {e}")
            raise
    
    def get_economic_events_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Fetch all economic events for a given date."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM economic_events 
                    WHERE date = ? 
                    ORDER BY time ASC
                """, (date,))
                
                events = []
                for row in cursor.fetchall():
                    events.append(dict(row))
                
                logger.info(f"Retrieved {len(events)} economic events for date: {date}")
                return events
                
        except sqlite3.Error as e:
            logger.error(f"Error fetching economic events: {e}")
            raise
    
    def get_latest_regime_score(self) -> Optional[Dict[str, Any]]:
        """Fetch the most recent regime score."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM regime_scores 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                if row:
                    score = dict(row)
                    logger.info(f"Retrieved latest regime score: {score['total_score']}")
                    return score
                else:
                    logger.info("No regime scores found")
                    return None
                
        except sqlite3.Error as e:
            logger.error(f"Error fetching latest regime score: {e}")
            raise
    
    def get_recent_news_by_symbol(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent news headlines for a specific symbol."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM news_headlines 
                    WHERE symbol = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (symbol, limit))
                
                headlines = []
                for row in cursor.fetchall():
                    headlines.append(dict(row))
                
                logger.info(f"Retrieved {len(headlines)} news headlines for symbol: {symbol}")
                return headlines
                
        except sqlite3.Error as e:
            logger.error(f"Error fetching news headlines: {e}")
            raise
    
    def get_regime_scores_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Fetch regime scores within a date range."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM regime_scores 
                    WHERE timestamp BETWEEN ? AND ? 
                    ORDER BY timestamp DESC
                """, (start_date, end_date))
                
                scores = []
                for row in cursor.fetchall():
                    scores.append(dict(row))
                
                logger.info(f"Retrieved {len(scores)} regime scores between {start_date} and {end_date}")
                return scores
                
        except sqlite3.Error as e:
            logger.error(f"Error fetching regime scores by date range: {e}")
            raise
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Count economic events
                cursor.execute("SELECT COUNT(*) FROM economic_events")
                stats['economic_events'] = cursor.fetchone()[0]
                
                # Count news headlines
                cursor.execute("SELECT COUNT(*) FROM news_headlines")
                stats['news_headlines'] = cursor.fetchone()[0]
                
                # Count regime scores
                cursor.execute("SELECT COUNT(*) FROM regime_scores")
                stats['regime_scores'] = cursor.fetchone()[0]
                
                logger.info(f"Database stats: {stats}")
                return stats
                
        except sqlite3.Error as e:
            logger.error(f"Error getting database stats: {e}")
            raise
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data older than specified days."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Calculate cutoff date
                cutoff_date = datetime.now().strftime('%Y-%m-%d')
                
                # Delete old economic events
                cursor.execute("""
                    DELETE FROM economic_events 
                    WHERE date < ?
                """, (cutoff_date,))
                events_deleted = cursor.rowcount
                
                # Delete old news headlines
                cursor.execute("""
                    DELETE FROM news_headlines 
                    WHERE timestamp < ?
                """, (cutoff_date,))
                headlines_deleted = cursor.rowcount
                
                # Delete old regime scores
                cursor.execute("""
                    DELETE FROM regime_scores 
                    WHERE timestamp < ?
                """, (cutoff_date,))
                scores_deleted = cursor.rowcount
                
                conn.commit()
                
                logger.info(f"Cleanup completed: {events_deleted} events, {headlines_deleted} headlines, {scores_deleted} scores deleted")
                
        except sqlite3.Error as e:
            logger.error(f"Error during cleanup: {e}")
            raise

# Global instance for easy access
data_store = MacroIntelDataStore()

# Convenience functions for backward compatibility
def setup_database():
    """Setup database tables."""
    return data_store.setup_database()

def insert_economic_event(event_data: Dict[str, Any]) -> int:
    """Insert economic event."""
    return data_store.insert_economic_event(event_data)

def insert_news_headline(headline_data: Dict[str, Any]) -> int:
    """Insert news headline."""
    return data_store.insert_news_headline(headline_data)

def insert_regime_score(score_data: Dict[str, Any]) -> int:
    """Insert regime score."""
    return data_store.insert_regime_score(score_data)

def get_economic_events_by_date(date: str) -> List[Dict[str, Any]]:
    """Get economic events by date."""
    return data_store.get_economic_events_by_date(date)

def get_latest_regime_score() -> Optional[Dict[str, Any]]:
    """Get latest regime score."""
    return data_store.get_latest_regime_score()

def get_recent_news_by_symbol(symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent news by symbol."""
    return data_store.get_recent_news_by_symbol(symbol, limit)

if __name__ == "__main__":
    # Test the data store
    print("Testing MacroIntel Data Store...")
    
    # Setup database
    setup_database()
    
    # Test insert economic event
    event_data = {
        'date': '2024-01-15',
        'time': '14:30',
        'event_name': 'CPI Data Release',
        'impact_level': 'High',
        'forecast': '3.2%',
        'actual': '3.1%',
        'category': 'Inflation'
    }
    event_id = insert_economic_event(event_data)
    print(f"Inserted economic event with ID: {event_id}")
    
    # Test insert news headline
    headline_data = {
        'timestamp': '2024-01-15 10:30:00',
        'source': 'Reuters',
        'symbol': 'AAPL',
        'headline': 'Apple Reports Strong Q4 Earnings',
        'summary': 'Apple exceeded analyst expectations with record revenue',
        'sentiment': 'positive'
    }
    headline_id = insert_news_headline(headline_data)
    print(f"Inserted news headline with ID: {headline_id}")
    
    # Test insert regime score
    score_data = {
        'timestamp': '2024-01-15 16:00:00',
        'total_score': 75.5,
        'volatility': 20.0,
        'structure': 18.5,
        'momentum': 15.0,
        'breadth': 12.0,
        'institutional': 10.0,
        'strategy': 'Tier 1',
        'instrument': 'ES'
    }
    score_id = insert_regime_score(score_data)
    print(f"Inserted regime score with ID: {score_id}")
    
    # Test retrievals
    events = get_economic_events_by_date('2024-01-15')
    print(f"Retrieved {len(events)} economic events")
    
    latest_score = get_latest_regime_score()
    if latest_score:
        print(f"Latest regime score: {latest_score['total_score']}")
    
    news = get_recent_news_by_symbol('AAPL')
    print(f"Retrieved {len(news)} news headlines for AAPL")
    
    # Get database stats
    stats = data_store.get_database_stats()
    print(f"Database stats: {stats}")
    
    print("Data store test completed successfully!")
'''

# Write the content to data_store.py
with open('data_store.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("data_store.py created successfully!") 