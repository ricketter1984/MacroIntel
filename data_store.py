"""
MacroIntel Data Store Module

Provides persistent storage for MacroIntel using SQLAlchemy ORM.
Manages economic events, news headlines, and regime scores.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, desc

from models import EconomicEvent, NewsHeadline, RegimeScore
from database.session import SessionLocal, init_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MacroIntelDataStore:
    """Main data store class for MacroIntel persistent storage using SQLAlchemy ORM."""
    
    def __init__(self):
        """Initialize the data store and ensure database is set up."""
        init_database()
        logger.info("MacroIntel Data Store initialized with SQLAlchemy ORM")
    
    def _get_session(self) -> Session:
        """Get a new database session."""
        return SessionLocal()
    
    def insert_economic_event(self, event_data: Dict[str, Any]) -> int:
        """Insert a new economic event record."""
        session = self._get_session()
        try:
            event = EconomicEvent(
                date=event_data.get('date'),
                time=event_data.get('time'),
                event_name=event_data.get('event_name'),
                impact_level=event_data.get('impact_level'),
                forecast=event_data.get('forecast'),
                actual=event_data.get('actual'),
                category=event_data.get('category')
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            logger.info(f"Inserted economic event with ID: {event.id}")
            return event.id
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error inserting economic event: {e}")
            raise
        finally:
            session.close()
    
    def insert_news_headline(self, headline_data: Dict[str, Any]) -> int:
        """Insert a new news headline record."""
        session = self._get_session()
        try:
            # Convert timestamp string to datetime if needed
            timestamp = headline_data.get('timestamp')
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            headline = NewsHeadline(
                timestamp=timestamp,
                source=headline_data.get('source'),
                symbol=headline_data.get('symbol'),
                headline=headline_data.get('headline'),
                summary=headline_data.get('summary'),
                sentiment=headline_data.get('sentiment')
            )
            session.add(headline)
            session.commit()
            session.refresh(headline)
            logger.info(f"Inserted news headline with ID: {headline.id}")
            return headline.id
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error inserting news headline: {e}")
            raise
        finally:
            session.close()
    
    def insert_regime_score(self, score_data: Dict[str, Any]) -> int:
        """Insert a new regime score record."""
        session = self._get_session()
        try:
            # Convert timestamp string to datetime if needed
            timestamp = score_data.get('timestamp')
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            score = RegimeScore(
                timestamp=timestamp,
                total_score=score_data.get('total_score'),
                volatility=score_data.get('volatility'),
                structure=score_data.get('structure'),
                momentum=score_data.get('momentum'),
                breadth=score_data.get('breadth'),
                institutional=score_data.get('institutional'),
                strategy=score_data.get('strategy'),
                instrument=score_data.get('instrument')
            )
            session.add(score)
            session.commit()
            session.refresh(score)
            logger.info(f"Inserted regime score with ID: {score.id}")
            return score.id
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error inserting regime score: {e}")
            raise
        finally:
            session.close()
    
    def get_economic_events_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Fetch all economic events for a given date."""
        session = self._get_session()
        try:
            events = session.query(EconomicEvent).filter(
                EconomicEvent.date == date
            ).order_by(EconomicEvent.time).all()
            
            return [event.to_dict() for event in events]
            
        except SQLAlchemyError as e:
            logger.error(f"Error fetching economic events for date {date}: {e}")
            raise
        finally:
            session.close()
    
    def get_latest_regime_score(self) -> Optional[Dict[str, Any]]:
        """Fetch the most recent regime score."""
        session = self._get_session()
        try:
            latest_score = session.query(RegimeScore).order_by(
                desc(RegimeScore.timestamp)
            ).first()
            
            return latest_score.to_dict() if latest_score else None
            
        except SQLAlchemyError as e:
            logger.error(f"Error fetching latest regime score: {e}")
            raise
        finally:
            session.close()
    
    def get_recent_news_by_symbol(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent news headlines for a specific symbol."""
        session = self._get_session()
        try:
            headlines = session.query(NewsHeadline).filter(
                NewsHeadline.symbol == symbol.upper()
            ).order_by(desc(NewsHeadline.timestamp)).limit(limit).all()
            
            return [headline.to_dict() for headline in headlines]
            
        except SQLAlchemyError as e:
            logger.error(f"Error fetching news for symbol {symbol}: {e}")
            raise
        finally:
            session.close()
    
    def get_regime_scores_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Fetch regime scores within a date range."""
        session = self._get_session()
        try:
            # Convert date strings to datetime objects
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            
            scores = session.query(RegimeScore).filter(
                and_(
                    RegimeScore.timestamp >= start_dt,
                    RegimeScore.timestamp <= end_dt
                )
            ).order_by(RegimeScore.timestamp).all()
            
            return [score.to_dict() for score in scores]
            
        except SQLAlchemyError as e:
            logger.error(f"Error fetching regime scores for date range {start_date} to {end_date}: {e}")
            raise
        finally:
            session.close()
    
    def get_headlines_by_symbol(self, symbol: str, days: int = 7) -> List[Dict[str, Any]]:
        """Fetch headlines for a symbol within the last N days."""
        session = self._get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            headlines = session.query(NewsHeadline).filter(
                and_(
                    NewsHeadline.symbol == symbol.upper(),
                    NewsHeadline.timestamp >= cutoff_date
                )
            ).order_by(desc(NewsHeadline.timestamp)).all()
            
            return [headline.to_dict() for headline in headlines]
            
        except SQLAlchemyError as e:
            logger.error(f"Error fetching headlines for symbol {symbol} in last {days} days: {e}")
            raise
        finally:
            session.close()
    
    def get_events_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Fetch economic events for a specific date."""
        return self.get_economic_events_by_date(date)
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        session = self._get_session()
        try:
            stats = {
                'economic_events': session.query(EconomicEvent).count(),
                'news_headlines': session.query(NewsHeadline).count(),
                'regime_scores': session.query(RegimeScore).count()
            }
            return stats
            
        except SQLAlchemyError as e:
            logger.error(f"Error fetching database stats: {e}")
            raise
        finally:
            session.close()
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Remove data older than specified days."""
        session = self._get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Clean up old news headlines
            old_headlines = session.query(NewsHeadline).filter(
                NewsHeadline.timestamp < cutoff_date
            ).delete()
            
            # Clean up old regime scores
            old_scores = session.query(RegimeScore).filter(
                RegimeScore.timestamp < cutoff_date
            ).delete()
            
            session.commit()
            logger.info(f"Cleaned up {old_headlines} old headlines and {old_scores} old regime scores")
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error cleaning up old data: {e}")
            raise
        finally:
            session.close()

# Global data store instance
data_store = MacroIntelDataStore()

# Convenience functions for backward compatibility
def insert_economic_event(event_data: Dict[str, Any]) -> int:
    """Insert a new economic event record."""
    return data_store.insert_economic_event(event_data)

def insert_news_headline(headline_data: Dict[str, Any]) -> int:
    """Insert a new news headline record."""
    return data_store.insert_news_headline(headline_data)

def insert_regime_score(score_data: Dict[str, Any]) -> int:
    """Insert a new regime score record."""
    return data_store.insert_regime_score(score_data)

def get_economic_events_by_date(date: str) -> List[Dict[str, Any]]:
    """Fetch all economic events for a given date."""
    return data_store.get_economic_events_by_date(date)

def get_latest_regime_score() -> Optional[Dict[str, Any]]:
    """Fetch the most recent regime score."""
    return data_store.get_latest_regime_score()

def get_recent_news_by_symbol(symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch recent news headlines for a specific symbol."""
    return data_store.get_recent_news_by_symbol(symbol, limit)

def get_regime_scores_by_date_range(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Fetch regime scores within a date range."""
    return data_store.get_regime_scores_by_date_range(start_date, end_date)

def get_headlines_by_symbol(symbol: str, days: int = 7) -> List[Dict[str, Any]]:
    """Fetch headlines for a symbol within the last N days."""
    return data_store.get_headlines_by_symbol(symbol, days)

def get_events_by_date(date: str) -> List[Dict[str, Any]]:
    """Fetch economic events for a specific date."""
    return data_store.get_events_by_date(date)

def insert_mock_headline_for_testing():
    """Insert a mock headline for testing purposes."""
    mock_headline = {
        'timestamp': datetime.now().isoformat(),
        'source': 'Test Source',
        'symbol': 'DIA',
        'headline': 'Test headline for DIA',
        'summary': 'This is a test summary for testing purposes',
        'sentiment': 'Neutral'
    }
    return insert_news_headline(mock_headline)
