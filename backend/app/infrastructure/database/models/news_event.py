#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Price Analyzer - News Event Model

Stores news articles with sentiment analysis.

Author: Hoseyn Doulabi (@hoseynd-ai)
Project Manager: Hoseyn Doulabi
Repository: https://github.com/hoseynd-ai/gold-price-analyzer
Created: 2025-10-25
License: MIT
"""

from typing import Dict, Any
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    DECIMAL,
    DateTime,
    Index,
)
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY

from app.infrastructure.database.base import Base


class NewsEvent(Base):
    """
    News Event Model.
    
    Stores news articles related to gold market with sentiment analysis.
    
    Author: Hoseyn Doulabi (@hoseynd-ai)
    Created: 2025-10-25
    
    Example:
        >>> from datetime import datetime
        >>> news = NewsEvent(
        ...     title="Fed keeps interest rates steady",
        ...     published_at=datetime.utcnow(),
        ...     sentiment_score=0.65,
        ...     sentiment_label='positive',
        ...     source='newsapi'
        ... )
    """
    
    __tablename__ = "news_events"
    
    # ====================================
    # Primary Key
    # ====================================
    id = Column(
        BigInteger, 
        primary_key=True, 
        index=True, 
        autoincrement=True
    )
    
    # ====================================
    # News Content
    # ====================================
    title = Column(
        Text, 
        nullable=False, 
        comment="عنوان خبر"
    )
    
    description = Column(
        Text, 
        comment="خلاصه خبر"
    )
    
    content = Column(
        Text, 
        comment="متن کامل خبر"
    )
    
    url = Column(
        Text, 
        comment="لینک خبر"
    )
    
    image_url = Column(
        Text, 
        comment="لینک تصویر"
    )
    
    # ====================================
    # Time
    # ====================================
    published_at = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="زمان انتشار خبر"
    )
    
    # ====================================
    # Sentiment Analysis (ML)
    # ====================================
    sentiment_score = Column(
        DECIMAL(3, 2),
        comment="امتیاز احساسات: -1 (منفی) to +1 (مثبت)"
    )
    
    sentiment_label = Column(
        String(20),
        comment="برچسب: positive, negative, neutral"
    )
    
    confidence = Column(
        DECIMAL(3, 2),
        comment="اطمینان ML (0 to 1)"
    )
    
    # ====================================
    # Impact on Gold Price
    # ====================================
    price_impact = Column(
        String(20),
        comment="تأثیر: bullish, bearish, neutral"
    )
    
    impact_score = Column(
        DECIMAL(3, 2),
        comment="میزان تأثیر (0 to 1)"
    )
    
    # ====================================
    # Source & Metadata
    # ====================================
    source = Column(
        String(100),
        comment="منبع: newsapi, reuters_rss, bloomberg_rss"
    )
    
    category = Column(
        String(50),
        comment="دسته: economics, politics, markets"
    )
    
    author = Column(
        String(200), 
        comment="نویسنده"
    )
    
    keywords = Column(
        PG_ARRAY(Text),
        comment="کلمات کلیدی"
    )
    
    # ====================================
    # Timestamps
    # ====================================
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="زمان ایجاد رکورد"
    )
    
    # ====================================
    # Indexes for Performance
    # ====================================
    __table_args__ = (
        # Index for time-based queries
        Index('ix_news_events_published_at', 'published_at'),
        
        # Index for sentiment filtering
        Index('ix_news_events_sentiment_score', 'sentiment_score'),
        
        # Index for source filtering
        Index('ix_news_events_source', 'source'),
        
        # Composite index for time + source queries
        Index('ix_news_events_published_source', 'published_at', 'source'),
    )
    
    # ====================================
    # Methods
    # ====================================
    def __repr__(self) -> str:
        """String representation."""
        title_preview = self.title[:50] if self.title else "No title"
        return (
            f"<NewsEvent("
            f"id={self.id}, "
            f"title='{title_preview}...', "
            f"sentiment={self.sentiment_score}"
            f")>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            dict: Model data as dictionary
            
        Author: Hoseyn Doulabi (@hoseynd-ai)
        Created: 2025-10-25
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "url": self.url,
            "image_url": self.image_url,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "sentiment_score": float(self.sentiment_score) if self.sentiment_score else None,
            "sentiment_label": self.sentiment_label,
            "confidence": float(self.confidence) if self.confidence else None,
            "price_impact": self.price_impact,
            "impact_score": float(self.impact_score) if self.impact_score else None,
            "source": self.source,
            "category": self.category,
            "author": self.author,
            "keywords": self.keywords,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NewsEvent":
        """
        Create instance from dictionary.
        
        Args:
            data: Dictionary with model data
            
        Returns:
            NewsEvent: New instance
            
        Author: Hoseyn Doulabi (@hoseynd-ai)
        Created: 2025-10-25
        """
        return cls(**data)
