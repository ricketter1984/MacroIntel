"""
MacroIntel SQLAlchemy ORM Models

Defines database models for economic events, news headlines, and regime scores.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class EconomicEvent(Base):
    """Economic event model for storing economic calendar data."""
    
    __tablename__ = 'economic_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD format
    time = Column(String(8), nullable=False)  # HH:MM format
    event_name = Column(Text, nullable=False)
    impact_level = Column(String(20))  # High, Medium, Low
    forecast = Column(String(50))
    actual = Column(String(50))
    category = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<EconomicEvent(id={self.id}, event='{self.event_name}', date='{self.date}')>"
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'date': self.date,
            'time': self.time,
            'event_name': self.event_name,
            'impact_level': self.impact_level,
            'forecast': self.forecast,
            'actual': self.actual,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class NewsHeadline(Base):
    """News headline model for storing market news data."""
    
    __tablename__ = 'news_headlines'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    source = Column(String(100), nullable=False)
    symbol = Column(String(20), index=True)  # Stock/crypto symbol
    headline = Column(Text, nullable=False)
    summary = Column(Text)
    sentiment = Column(String(20))  # Positive, Negative, Neutral
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<NewsHeadline(id={self.id}, symbol='{self.symbol}', source='{self.source}')>"
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'source': self.source,
            'symbol': self.symbol,
            'headline': self.headline,
            'summary': self.summary,
            'sentiment': self.sentiment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class RegimeScore(Base):
    """Market regime score model for storing regime analysis data."""
    
    __tablename__ = 'regime_scores'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    total_score = Column(Float, nullable=False)
    volatility = Column(Float, nullable=False)
    structure = Column(Float, nullable=False)
    momentum = Column(Float, nullable=False)
    breadth = Column(Float, nullable=False)
    institutional = Column(Float, nullable=False)
    strategy = Column(String(100))
    instrument = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<RegimeScore(id={self.id}, score={self.total_score}, timestamp='{self.timestamp}')>"
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'total_score': self.total_score,
            'volatility': self.volatility,
            'structure': self.structure,
            'momentum': self.momentum,
            'breadth': self.breadth,
            'institutional': self.institutional,
            'strategy': self.strategy,
            'instrument': self.instrument,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Create indexes for better performance
Index('idx_economic_events_date', EconomicEvent.date)
Index('idx_news_headlines_symbol', NewsHeadline.symbol)
Index('idx_news_headlines_timestamp', NewsHeadline.timestamp)
Index('idx_regime_scores_timestamp', RegimeScore.timestamp) 