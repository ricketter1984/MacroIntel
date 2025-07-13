#!/usr/bin/env python3
"""
SQLite Agent for MacroIntel

This agent provides:
- SQLite database management for MacroIntel data
- Natural language to SQL query conversion using Vanna
- Market data storage and retrieval
- Regime score historical tracking
- Query optimization and caching
"""

import os
import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass
import hashlib

try:
    import vanna as vn
    from vanna.local import LocalContext_OpenAI
    VANNA_AVAILABLE = True
except ImportError:
    VANNA_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QueryResult:
    """Data class for query results."""
    success: bool
    data: Optional[pd.DataFrame] = None
    sql_query: Optional[str] = None
    explanation: Optional[str] = None
    error: Optional[str] = None
    cached: bool = False
    execution_time: float = 0.0

class MacroIntelSQLiteAgent:
    """
    SQLite Agent for MacroIntel with Vanna AI integration.
    
    Features:
    - Natural language to SQL conversion
    - Market data storage and retrieval
    - Regime score tracking
    - Query caching and optimization
    - Data analytics and insights
    """
    
    def __init__(self, db_path: str = "data/macrointel.db", 
                 enable_vanna: bool = True, openai_api_key: str = None):
        """
        Initialize the SQLite Agent.
        
        Args:
            db_path: Path to SQLite database file
            enable_vanna: Whether to enable Vanna AI features
            openai_api_key: OpenAI API key for Vanna (optional)
        """
        self.db_path = db_path
        self.enable_vanna = enable_vanna and VANNA_AVAILABLE
        self.cache_dir = Path("data/query_cache")
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Initialize Vanna if available
        if self.enable_vanna:
            self._init_vanna(openai_api_key)
        else:
            logger.warning("⚠️ Vanna not available - natural language queries disabled")
            self.vn = None
        
        logger.info(f"🗄️ SQLite Agent initialized (DB: {db_path})")
    
    def _init_database(self):
        """Initialize database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Market data table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS market_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        date DATE NOT NULL,
                        open_price REAL,
                        high_price REAL,
                        low_price REAL,
                        close_price REAL,
                        volume INTEGER,
                        adjusted_close REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(symbol, date)
                    )
                """)
                
                # Regime scores table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS regime_scores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        total_score REAL NOT NULL,
                        volatility_score REAL,
                        structure_score REAL,
                        volume_breadth_score REAL,
                        momentum_score REAL,
                        institutional_score REAL,
                        regime_classification TEXT,
                        strategy_recommendation TEXT,
                        instrument TEXT,
                        risk_allocation REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(date)
                    )
                """)
                
                # Economic events table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS economic_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        event_name TEXT NOT NULL,
                        country TEXT,
                        impact TEXT,
                        actual_value TEXT,
                        forecast_value TEXT,
                        previous_value TEXT,
                        currency TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # News data table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS news_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        headline TEXT NOT NULL,
                        summary TEXT,
                        source TEXT,
                        sentiment_score REAL,
                        symbols TEXT,  -- JSON array of related symbols
                        url TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Query cache table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS query_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query_hash TEXT NOT NULL UNIQUE,
                        natural_query TEXT,
                        sql_query TEXT NOT NULL,
                        result_data TEXT,  -- JSON
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        access_count INTEGER DEFAULT 1
                    )
                """)
                
                # Create indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_data_symbol_date ON market_data(symbol, date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_regime_scores_date ON regime_scores(date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_economic_events_date ON economic_events(date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_data_date ON news_data(date)")
                
                conn.commit()
                logger.info("✅ Database schema initialized")
                
        except Exception as e:
            logger.error(f"❌ Error initializing database: {str(e)}")
            raise
    
    def _init_vanna(self, openai_api_key: str = None):
        """Initialize Vanna AI for natural language queries."""
        try:
            if not openai_api_key:
                openai_api_key = os.getenv("OPENAI_API_KEY")
            
            if not openai_api_key:
                logger.warning("⚠️ No OpenAI API key found - Vanna features limited")
                self.vn = None
                return
            
            # Initialize Vanna with local context
            self.vn = LocalContext_OpenAI(api_key=openai_api_key)
            
            # Train Vanna with our schema
            self._train_vanna()
            
            logger.info("✅ Vanna AI initialized for natural language queries")
            
        except Exception as e:
            logger.error(f"❌ Error initializing Vanna: {str(e)}")
            self.vn = None
    
    def _train_vanna(self):
        """Train Vanna with MacroIntel-specific schema and examples."""
        if not self.vn:
            return
        
        try:
            # Define our schema for Vanna
            schema_info = """
            MacroIntel Database Schema:
            
            1. market_data: Historical market data
               - symbol: Trading symbol (e.g., 'SPY', 'QQQ', 'MES=F')
               - date: Trading date
               - open_price, high_price, low_price, close_price: OHLC prices
               - volume: Trading volume
               - adjusted_close: Adjusted closing price
            
            2. regime_scores: Market regime analysis scores
               - date: Analysis date
               - total_score: Overall regime score (0-100)
               - volatility_score, structure_score, volume_breadth_score, momentum_score, institutional_score: Component scores
               - regime_classification: 'Bullish', 'Bearish', 'Neutral'
               - strategy_recommendation: Trading strategy recommendation
               - instrument: Recommended trading instrument
               - risk_allocation: Recommended risk percentage
            
            3. economic_events: Economic calendar events
               - date: Event date
               - event_name: Name of economic event
               - country: Country code
               - impact: 'High', 'Medium', 'Low'
               - actual_value, forecast_value, previous_value: Event values
            
            4. news_data: Financial news and sentiment
               - date: News date
               - headline: News headline
               - summary: News summary
               - source: News source
               - sentiment_score: Sentiment analysis score (-1 to 1)
               - symbols: JSON array of related symbols
            """
            
            # Training examples
            training_examples = [
                {
                    "question": "What is the latest SPY closing price?",
                    "sql": "SELECT close_price, date FROM market_data WHERE symbol = 'SPY' ORDER BY date DESC LIMIT 1"
                },
                {
                    "question": "Show me the regime scores for the last 30 days",
                    "sql": "SELECT date, total_score, regime_classification FROM regime_scores WHERE date >= date('now', '-30 days') ORDER BY date DESC"
                },
                {
                    "question": "What were the high impact economic events this week?",
                    "sql": "SELECT event_name, date, country, actual_value FROM economic_events WHERE impact = 'High' AND date >= date('now', '-7 days') ORDER BY date DESC"
                },
                {
                    "question": "Show me the best performing stocks last month",
                    "sql": "SELECT symbol, ((close_price - LAG(close_price, 30) OVER (PARTITION BY symbol ORDER BY date)) / LAG(close_price, 30) OVER (PARTITION BY symbol ORDER BY date)) * 100 as return_pct FROM market_data WHERE date >= date('now', '-30 days') ORDER BY return_pct DESC LIMIT 10"
                },
                {
                    "question": "What is the current market regime classification?",
                    "sql": "SELECT regime_classification, total_score, strategy_recommendation FROM regime_scores ORDER BY date DESC LIMIT 1"
                }
            ]
            
            # Train with schema
            self.vn.train(documentation=schema_info)
            
            # Train with examples
            for example in training_examples:
                self.vn.train(question=example["question"], sql=example["sql"])
            
            logger.info("✅ Vanna training completed with MacroIntel schema")
            
        except Exception as e:
            logger.error(f"❌ Error training Vanna: {str(e)}")
    
    def execute_natural_query(self, natural_query: str, use_cache: bool = True) -> QueryResult:
        """
        Execute a natural language query using Vanna AI.
        
        Args:
            natural_query: Natural language query
            use_cache: Whether to use cached results
            
        Returns:
            QueryResult with data and metadata
        """
        start_time = datetime.now()
        
        try:
            # Check cache first
            if use_cache:
                cached_result = self._get_cached_query(natural_query)
                if cached_result:
                    return cached_result
            
            if not self.vn:
                return QueryResult(
                    success=False,
                    error="Vanna AI not available - OpenAI API key required for natural language queries"
                )
            
            # Generate SQL from natural language
            sql_query = self.vn.generate_sql(natural_query)
            
            if not sql_query:
                return QueryResult(
                    success=False,
                    error="Could not generate SQL from natural language query"
                )
            
            # Execute the generated SQL
            result = self.execute_sql_query(sql_query)
            
            # Add explanation
            if result.success and result.data is not None:
                explanation = f"Generated SQL: {sql_query}\nReturned {len(result.data)} rows"
            else:
                explanation = f"Generated SQL: {sql_query}"
            
            # Update result with natural language info
            result.sql_query = sql_query
            result.explanation = explanation
            result.execution_time = (datetime.now() - start_time).total_seconds()
            
            # Cache successful results
            if result.success and use_cache:
                self._cache_query(natural_query, sql_query, result)
            
            return result
            
        except Exception as e:
            return QueryResult(
                success=False,
                error=f"Error executing natural query: {str(e)}",
                execution_time=(datetime.now() - start_time).total_seconds()
            )
    
    def execute_sql_query(self, sql_query: str, params: tuple = None) -> QueryResult:
        """
        Execute a raw SQL query.
        
        Args:
            sql_query: SQL query string
            params: Query parameters (optional)
            
        Returns:
            QueryResult with data and metadata
        """
        start_time = datetime.now()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Use row factory for easier data access
                conn.row_factory = sqlite3.Row
                
                if params:
                    cursor = conn.execute(sql_query, params)
                else:
                    cursor = conn.execute(sql_query)
                
                # Fetch results
                rows = cursor.fetchall()
                
                # Convert to DataFrame if there are results
                if rows:
                    # Convert sqlite3.Row objects to dictionaries
                    data = [dict(row) for row in rows]
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame()
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return QueryResult(
                    success=True,
                    data=df,
                    sql_query=sql_query,
                    execution_time=execution_time
                )
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return QueryResult(
                success=False,
                error=f"SQL execution error: {str(e)}",
                sql_query=sql_query,
                execution_time=execution_time
            )
    
    def store_market_data(self, symbol: str, data: pd.DataFrame) -> bool:
        """
        Store market data in the database.
        
        Args:
            symbol: Trading symbol
            data: DataFrame with OHLCV data
            
        Returns:
            Success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Prepare data for insertion
                insert_data = []
                for _, row in data.iterrows():
                    insert_data.append((
                        symbol,
                        row.name.strftime('%Y-%m-%d') if hasattr(row.name, 'strftime') else str(row.name),
                        float(row.get('Open', 0)) if pd.notna(row.get('Open')) else None,
                        float(row.get('High', 0)) if pd.notna(row.get('High')) else None,
                        float(row.get('Low', 0)) if pd.notna(row.get('Low')) else None,
                        float(row.get('Close', 0)) if pd.notna(row.get('Close')) else None,
                        int(row.get('Volume', 0)) if pd.notna(row.get('Volume')) else None,
                        float(row.get('Adj Close', row.get('Close', 0))) if pd.notna(row.get('Adj Close', row.get('Close'))) else None
                    ))
                
                # Insert data (using INSERT OR REPLACE to handle duplicates)
                cursor = conn.cursor()
                cursor.executemany("""
                    INSERT OR REPLACE INTO market_data 
                    (symbol, date, open_price, high_price, low_price, close_price, volume, adjusted_close)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, insert_data)
                
                conn.commit()
                logger.info(f"✅ Stored {len(insert_data)} records for {symbol}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error storing market data for {symbol}: {str(e)}")
            return False
    
    def store_regime_score(self, regime_data: Dict[str, Any]) -> bool:
        """
        Store regime score data in the database.
        
        Args:
            regime_data: Dictionary with regime analysis data
            
        Returns:
            Success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Extract component scores
                breakdown = regime_data.get('component_breakdown', {})
                
                cursor.execute("""
                    INSERT OR REPLACE INTO regime_scores 
                    (date, total_score, volatility_score, structure_score, volume_breadth_score, 
                     momentum_score, institutional_score, regime_classification, 
                     strategy_recommendation, instrument, risk_allocation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().strftime('%Y-%m-%d'),
                    float(regime_data.get('total_score', 0)),
                    float(breakdown.get('volatility', {}).get('weighted_score', 0)),
                    float(breakdown.get('structure', {}).get('weighted_score', 0)),
                    float(breakdown.get('volume_breadth', {}).get('weighted_score', 0)),
                    float(breakdown.get('momentum', {}).get('weighted_score', 0)),
                    float(breakdown.get('institutional', {}).get('weighted_score', 0)),
                    regime_data.get('regime_classification', 'Neutral'),
                    regime_data.get('strategy_recommendation', 'Unknown'),
                    regime_data.get('instrument', 'Unknown'),
                    float(regime_data.get('risk_allocation', 0))
                ))
                
                conn.commit()
                logger.info("✅ Stored regime score data")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error storing regime score: {str(e)}")
            return False
    
    def store_economic_events(self, events: List[Dict[str, Any]]) -> bool:
        """
        Store economic events in the database.
        
        Args:
            events: List of economic event dictionaries
            
        Returns:
            Success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                insert_data = []
                for event in events:
                    insert_data.append((
                        event.get('date', datetime.now().strftime('%Y-%m-%d')),
                        event.get('event', 'Unknown Event'),
                        event.get('country', 'Unknown'),
                        event.get('impact', 'Medium'),
                        str(event.get('actual', '')),
                        str(event.get('estimate', '')),
                        str(event.get('previous', '')),
                        event.get('currency', 'USD')
                    ))
                
                cursor.executemany("""
                    INSERT OR IGNORE INTO economic_events 
                    (date, event_name, country, impact, actual_value, forecast_value, previous_value, currency)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, insert_data)
                
                conn.commit()
                logger.info(f"✅ Stored {len(insert_data)} economic events")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error storing economic events: {str(e)}")
            return False
    
    def get_market_summary(self, symbols: List[str] = None, days: int = 30) -> Dict[str, Any]:
        """
        Get market summary for specified symbols and time period.
        
        Args:
            symbols: List of symbols (None for all)
            days: Number of days to include
            
        Returns:
            Market summary dictionary
        """
        try:
            # Build query
            base_query = """
                SELECT 
                    symbol,
                    COUNT(*) as trading_days,
                    MIN(date) as start_date,
                    MAX(date) as end_date,
                    ROUND(AVG(close_price), 2) as avg_price,
                    ROUND(MIN(close_price), 2) as min_price,
                    ROUND(MAX(close_price), 2) as max_price,
                    ROUND(
                        (MAX(close_price) - MIN(close_price)) / MIN(close_price) * 100, 2
                    ) as price_range_pct,
                    SUM(volume) as total_volume
                FROM market_data 
                WHERE date >= date('now', '-{} days')
            """.format(days)
            
            if symbols:
                symbol_list = "', '".join(symbols)
                base_query += f" AND symbol IN ('{symbol_list}')"
            
            base_query += " GROUP BY symbol ORDER BY symbol"
            
            result = self.execute_sql_query(base_query)
            
            if result.success and not result.data.empty:
                summary = {
                    "period_days": days,
                    "symbols_count": len(result.data),
                    "summary_data": result.data.to_dict('records'),
                    "generated_at": datetime.now().isoformat()
                }
                
                # Add regime context if available
                regime_query = """
                    SELECT regime_classification, total_score, strategy_recommendation
                    FROM regime_scores 
                    ORDER BY date DESC 
                    LIMIT 1
                """
                regime_result = self.execute_sql_query(regime_query)
                
                if regime_result.success and not regime_result.data.empty:
                    summary["current_regime"] = regime_result.data.iloc[0].to_dict()
                
                return summary
            else:
                return {"error": "No market data found for the specified criteria"}
                
        except Exception as e:
            logger.error(f"❌ Error generating market summary: {str(e)}")
            return {"error": str(e)}
    
    def _get_cached_query(self, natural_query: str) -> Optional[QueryResult]:
        """Get cached query result if available."""
        try:
            query_hash = hashlib.md5(natural_query.lower().encode()).hexdigest()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT sql_query, result_data, created_at
                    FROM query_cache 
                    WHERE query_hash = ? AND created_at > datetime('now', '-1 hour')
                """, (query_hash,))
                
                row = cursor.fetchone()
                if row:
                    sql_query, result_json, created_at = row
                    
                    # Update access count
                    cursor.execute("""
                        UPDATE query_cache 
                        SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1
                        WHERE query_hash = ?
                    """, (query_hash,))
                    conn.commit()
                    
                    # Reconstruct result
                    result_data = json.loads(result_json) if result_json else None
                    df = pd.DataFrame(result_data) if result_data else pd.DataFrame()
                    
                    return QueryResult(
                        success=True,
                        data=df,
                        sql_query=sql_query,
                        explanation=f"Cached result from {created_at}",
                        cached=True
                    )
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Error accessing query cache: {str(e)}")
            return None
    
    def _cache_query(self, natural_query: str, sql_query: str, result: QueryResult):
        """Cache query result for future use."""
        try:
            query_hash = hashlib.md5(natural_query.lower().encode()).hexdigest()
            result_json = result.data.to_json(orient='records') if result.data is not None else None
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO query_cache 
                    (query_hash, natural_query, sql_query, result_data)
                    VALUES (?, ?, ?, ?)
                """, (query_hash, natural_query, sql_query, result_json))
                conn.commit()
                
        except Exception as e:
            logger.warning(f"⚠️ Error caching query: {str(e)}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics and health information."""
        try:
            stats = {}
            
            # Table row counts
            tables = ['market_data', 'regime_scores', 'economic_events', 'news_data', 'query_cache']
            
            for table in tables:
                result = self.execute_sql_query(f"SELECT COUNT(*) as count FROM {table}")
                if result.success and not result.data.empty:
                    stats[f"{table}_count"] = int(result.data.iloc[0]['count'])
                else:
                    stats[f"{table}_count"] = 0
            
            # Database file size
            if os.path.exists(self.db_path):
                stats["database_size_mb"] = round(os.path.getsize(self.db_path) / (1024 * 1024), 2)
            else:
                stats["database_size_mb"] = 0
            
            # Date ranges
            for table, date_col in [('market_data', 'date'), ('regime_scores', 'date'), ('economic_events', 'date')]:
                result = self.execute_sql_query(f"SELECT MIN({date_col}) as min_date, MAX({date_col}) as max_date FROM {table}")
                if result.success and not result.data.empty and result.data.iloc[0]['min_date']:
                    stats[f"{table}_date_range"] = {
                        "from": result.data.iloc[0]['min_date'],
                        "to": result.data.iloc[0]['max_date']
                    }
            
            # Vanna status
            stats["vanna_enabled"] = self.enable_vanna and self.vn is not None
            
            # Cache stats
            cache_result = self.execute_sql_query("""
                SELECT COUNT(*) as total, SUM(access_count) as total_accesses
                FROM query_cache 
                WHERE created_at > datetime('now', '-24 hours')
            """)
            if cache_result.success and not cache_result.data.empty:
                stats["cache_24h"] = {
                    "queries": int(cache_result.data.iloc[0]['total']),
                    "accesses": int(cache_result.data.iloc[0]['total_accesses'] or 0)
                }
            
            stats["generated_at"] = datetime.now().isoformat()
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting database stats: {str(e)}")
            return {"error": str(e)}

def main():
    """Test function for the SQLite Agent."""
    print("🗄️ Testing MacroIntel SQLite Agent...")
    
    # Initialize agent
    agent = MacroIntelSQLiteAgent()
    
    # Test database stats
    stats = agent.get_database_stats()
    print(f"📊 Database Stats: {json.dumps(stats, indent=2)}")
    
    # Test SQL query
    result = agent.execute_sql_query("SELECT name FROM sqlite_master WHERE type='table'")
    if result.success:
        print(f"📋 Database Tables: {result.data['name'].tolist()}")
    
    # Test natural language query (if Vanna is available)
    if agent.vn:
        nl_result = agent.execute_natural_query("How many records are in the market_data table?")
        if nl_result.success:
            print(f"🧠 Natural Language Query Result: {nl_result.data}")
        else:
            print(f"❌ Natural Language Query Failed: {nl_result.error}")
    
    print("✅ SQLite Agent test completed!")

if __name__ == "__main__":
    main() 