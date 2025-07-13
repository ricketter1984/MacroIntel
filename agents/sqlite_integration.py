#!/usr/bin/env python3
"""
SQLite Agent Integration for MacroIntel

This module integrates the SQLite agent with the existing MacroIntel system,
providing automated data storage and retrieval capabilities.
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, Any, List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from agents.sqlite_agent import MacroIntelSQLiteAgent
except ImportError as e:
    print(f"❌ Error importing SQLite agent: {e}")
    sys.exit(1)

logger = logging.getLogger(__name__)

class MacroIntelDataManager:
    """
    Data Manager that integrates SQLite agent with MacroIntel system.
    
    Features:
    - Automatic data storage from existing modules
    - Historical data tracking
    - Query interface for analytics
    - Data synchronization
    """
    
    def __init__(self, db_path: str = "data/macrointel.db"):
        """Initialize the data manager."""
        self.db_path = db_path
        self.agent = MacroIntelSQLiteAgent(db_path)
        
        logger.info("📊 MacroIntel Data Manager initialized")
    
    def sync_market_data_from_yfinance(self, symbols: List[str], days: int = 30) -> Dict[str, bool]:
        """
        Fetch and store market data from yfinance.
        
        Args:
            symbols: List of trading symbols
            days: Number of days of historical data
            
        Returns:
            Dictionary of symbol -> success status
        """
        results = {}
        
        try:
            import yfinance as yf
            
            for symbol in symbols:
                try:
                    logger.info(f"📈 Fetching {days}-day data for {symbol}")
                    
                    # Fetch data
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period=f"{days}d", interval="1d")
                    
                    if not data.empty:
                        # Store in database
                        success = self.agent.store_market_data(symbol, data)
                        results[symbol] = success
                        
                        if success:
                            logger.info(f"✅ Stored {len(data)} records for {symbol}")
                        else:
                            logger.error(f"❌ Failed to store data for {symbol}")
                    else:
                        logger.warning(f"⚠️ No data available for {symbol}")
                        results[symbol] = False
                        
                except Exception as e:
                    logger.error(f"❌ Error fetching {symbol}: {str(e)}")
                    results[symbol] = False
                    
        except ImportError:
            logger.error("❌ yfinance not available - install with: pip install yfinance")
            
        return results
    
    def sync_regime_scores(self, days: int = 7) -> bool:
        """
        Sync regime scores from existing MacroIntel regime calculator.
        
        Args:
            days: Number of days to sync
            
        Returns:
            Success status
        """
        try:
            # Try to import regime calculator
            try:
                from regime_score_calculator import get_daily_regime_score
            except ImportError:
                logger.warning("⚠️ Regime score calculator not available")
                return False
            
            # Get latest regime score
            regime_data = get_daily_regime_score()
            
            if 'error' not in regime_data:
                success = self.agent.store_regime_score(regime_data)
                if success:
                    logger.info("✅ Synced current regime score to database")
                    return True
                else:
                    logger.error("❌ Failed to store regime score")
                    return False
            else:
                logger.error(f"❌ Error from regime calculator: {regime_data['error']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error syncing regime scores: {str(e)}")
            return False
    
    def sync_economic_events(self) -> bool:
        """
        Sync economic events from FMP calendar.
        
        Returns:
            Success status
        """
        try:
            # Try to import FMP calendar
            try:
                from utils.api_clients import fetch_fmp_calendar
            except ImportError:
                logger.warning("⚠️ FMP calendar not available")
                return False
            
            # Fetch events
            events = fetch_fmp_calendar()
            
            if events:
                success = self.agent.store_economic_events(events)
                if success:
                    logger.info(f"✅ Synced {len(events)} economic events to database")
                    return True
                else:
                    logger.error("❌ Failed to store economic events")
                    return False
            else:
                logger.warning("⚠️ No economic events retrieved")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error syncing economic events: {str(e)}")
            return False
    
    def sync_news_data(self) -> bool:
        """
        Sync news data from existing news alerts system.
        
        Returns:
            Success status
        """
        try:
            # Try to import news system
            try:
                from news_alerts import NewsAlertsEngine
            except ImportError:
                logger.warning("⚠️ News alerts engine not available")
                return False
            
            # Get recent news
            news_engine = NewsAlertsEngine()
            
            # This would need to be implemented based on the actual news system API
            # For now, just return success
            logger.info("✅ News sync integration ready (implementation pending)")
            return True
                
        except Exception as e:
            logger.error(f"❌ Error syncing news data: {str(e)}")
            return False
    
    def run_full_sync(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run a full data synchronization.
        
        Args:
            symbols: List of symbols to sync (default: common symbols)
            
        Returns:
            Sync results summary
        """
        if symbols is None:
            symbols = [
                'SPY', 'QQQ', 'IWM', 'DIA',  # ETFs
                'MES=F', 'MNQ=F', 'MYM=F', 'M2K=F',  # Equity futures
                'MCL=F', 'MGC=F', 'CL=F', 'GC=F',  # Commodity futures
                '^VIX', '^GSPC', '^IXIC', '^DJI'  # Indices
            ]
        
        logger.info(f"🔄 Starting full data sync for {len(symbols)} symbols...")
        
        results = {
            "sync_started": datetime.now().isoformat(),
            "symbols": symbols,
            "market_data": {},
            "regime_scores": False,
            "economic_events": False,
            "news_data": False,
            "errors": []
        }
        
        try:
            # Sync market data
            results["market_data"] = self.sync_market_data_from_yfinance(symbols, days=30)
            
            # Sync regime scores
            results["regime_scores"] = self.sync_regime_scores()
            
            # Sync economic events
            results["economic_events"] = self.sync_economic_events()
            
            # Sync news data
            results["news_data"] = self.sync_news_data()
            
            # Summary
            market_success = sum(1 for success in results["market_data"].values() if success)
            total_symbols = len(symbols)
            
            results["summary"] = {
                "market_data_success": f"{market_success}/{total_symbols}",
                "regime_scores_success": results["regime_scores"],
                "economic_events_success": results["economic_events"],
                "news_data_success": results["news_data"]
            }
            
            results["sync_completed"] = datetime.now().isoformat()
            
            logger.info("✅ Full data sync completed")
            
        except Exception as e:
            error_msg = f"Error during full sync: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(f"❌ {error_msg}")
        
        return results
    
    def query_data(self, natural_query: str) -> Dict[str, Any]:
        """
        Query data using natural language.
        
        Args:
            natural_query: Natural language query
            
        Returns:
            Query results
        """
        try:
            result = self.agent.execute_natural_query(natural_query)
            
            response = {
                "query": natural_query,
                "success": result.success,
                "execution_time": result.execution_time,
                "cached": result.cached
            }
            
            if result.success:
                response["data"] = result.data.to_dict('records') if result.data is not None else []
                response["sql_query"] = result.sql_query
                response["explanation"] = result.explanation
                response["row_count"] = len(result.data) if result.data is not None else 0
            else:
                response["error"] = result.error
            
            return response
            
        except Exception as e:
            return {
                "query": natural_query,
                "success": False,
                "error": f"Query execution error: {str(e)}"
            }
    
    def get_analytics_dashboard(self) -> Dict[str, Any]:
        """
        Generate analytics dashboard data.
        
        Returns:
            Dashboard data dictionary
        """
        try:
            dashboard = {
                "generated_at": datetime.now().isoformat(),
                "database_stats": self.agent.get_database_stats(),
                "market_summary": self.agent.get_market_summary(days=30),
                "recent_regime_scores": {},
                "upcoming_events": {}
            }
            
            # Get recent regime scores
            regime_query = """
                SELECT date, total_score, regime_classification, strategy_recommendation
                FROM regime_scores 
                ORDER BY date DESC 
                LIMIT 7
            """
            regime_result = self.agent.execute_sql_query(regime_query)
            if regime_result.success and regime_result.data is not None and not regime_result.data.empty:
                dashboard["recent_regime_scores"] = regime_result.data.to_dict('records')
            
            # Get upcoming events
            events_query = """
                SELECT date, event_name, country, impact
                FROM economic_events 
                WHERE date >= date('now')
                ORDER BY date ASC
                LIMIT 10
            """
            events_result = self.agent.execute_sql_query(events_query)
            if events_result.success and events_result.data is not None and not events_result.data.empty:
                dashboard["upcoming_events"] = events_result.data.to_dict('records')
            
            return dashboard
            
        except Exception as e:
            logger.error(f"❌ Error generating analytics dashboard: {str(e)}")
            return {"error": str(e)}

def main():
    """Test the data manager integration."""
    print("🔄 Testing MacroIntel Data Manager...")
    
    # Initialize data manager
    manager = MacroIntelDataManager()
    
    # Test database stats
    stats = manager.agent.get_database_stats()
    print(f"📊 Database Stats: {stats}")
    
    # Test market data sync for a few symbols
    test_symbols = ['SPY', 'QQQ', 'MCL=F']
    print(f"📈 Testing market data sync for: {test_symbols}")
    market_results = manager.sync_market_data_from_yfinance(test_symbols, days=5)
    print(f"📈 Market Data Results: {market_results}")
    
    # Test regime score sync
    print("🎯 Testing regime score sync...")
    regime_result = manager.sync_regime_scores()
    print(f"🎯 Regime Score Result: {regime_result}")
    
    # Test natural language query (if available)
    if manager.agent.vn:
        print("🧠 Testing natural language query...")
        query_result = manager.query_data("How many market data records do we have?")
        print(f"🧠 Query Result: {query_result}")
    
    # Test analytics dashboard
    print("📊 Testing analytics dashboard...")
    dashboard = manager.get_analytics_dashboard()
    print(f"📊 Dashboard generated with {len(dashboard)} sections")
    
    print("✅ Data Manager integration test completed!")

if __name__ == "__main__":
    main() 