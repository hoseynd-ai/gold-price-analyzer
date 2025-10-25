#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Price Analyzer - Gold Price Fact Model

Time-series fact table for gold prices.
Supports hourly, daily, weekly, monthly timeframes.

Author: Hoseyn Doulabi (@hoseynd-ai)
Project Manager: Hoseyn Doulabi
Repository: https://github.com/hoseynd-ai/gold-price-analyzer
Created: 2025-10-25
License: MIT
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    DECIMAL,
    DateTime,
    Integer,
    Index,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from app.infrastructure.database.base import Base


class GoldPriceFact(Base):
    """
    Gold Price Fact Table (Time-Series).
    
    Central fact table storing gold price data across multiple timeframes.
    Optimized for time-series queries and analytics.
    
    Timeframes:
        - hourly: Hour-by-hour data
        - daily: Daily OHLCV data
        - weekly: Weekly aggregated data
        - monthly: Monthly aggregated data
    
    Author: Hoseyn Doulabi (@hoseynd-ai)
    Created: 2025-10-25
    
    Example:
        >>> from datetime import datetime
        >>> price = GoldPriceFact(
        ...     timestamp=datetime.utcnow(),
        ...     timeframe='daily',
        ...     open=2750.00,
        ...     high=2755.50,
        ...     low=2748.20,
        ...     close=2752.30,
        ...     volume=125000,
        ...     source='yahoo_finance'
        ... )
    """
    
    __tablename__ = "gold_price_facts"
    
    # ====================================
    # Primary Key
    # ====================================
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    
    # ====================================
    # Time Dimensions
    # ====================================
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="زمان دقیق (UTC)"
    )
    
    timeframe = Column(
        String(20),
        nullable=False,
        index=True,
        comment="بازه زمانی: hourly, daily, weekly, monthly"
    )
    
    # ====================================
    # OHLCV Data (Open, High, Low, Close, Volume)
    # ====================================
    open = Column(
        DECIMAL(10, 2),
        comment="قیمت باز شدن (USD per ounce)"
    )
    
    high = Column(
        DECIMAL(10, 2),
        comment="بالاترین قیمت"
    )
    
    low = Column(
        DECIMAL(10, 2),
        comment="پایین‌ترین قیمت"
    )
    
    close = Column(
        DECIMAL(10, 2),
        nullable=False,
        comment="قیمت بسته شدن"
    )
    
    volume = Column(
        BigInteger,
        comment="حجم معاملات"
    )
    
    # ====================================
    # Calculated Fields
    # ====================================
    price_change = Column(
        DECIMAL(10, 2),
        comment="تغییر قیمت نسبت به قبل"
    )
    
    price_change_pct = Column(
        DECIMAL(5, 2),
        comment="درصد تغییر قیمت"
    )
    
    # ====================================
    # ML Features (Pre-computed)
    # ====================================
    news_sentiment_score = Column(
        DECIMAL(3, 2),
        comment="امتیاز احساسات اخبار (-1 to +1)"
    )
    
    news_event_count = Column(
        Integer,
        default=0,
        comment="تعداد اخبار مرتبط در این بازه"
    )
    
    # ====================================
    # Metadata
    # ====================================
    source = Column(
        String(50),
        default="yahoo_finance",
        comment="منبع داده: yahoo_finance, fred, etc"
    )
    
    market = Column(
        String(50),
        default="spot",
        comment="نوع بازار: spot, futures, etc"
    )
    
    data_quality = Column(
        DECIMAL(3, 2),
        default=1.0,
        comment="کیفیت داده (0.0 to 1.0)"
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
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="زمان آخرین بروزرسانی"
    )
    
    # ====================================
    # Indexes for Performance
    # ====================================
    __table_args__ = (
        # Composite index for common queries
        Index(
            'ix_gold_price_facts_timestamp_timeframe',
            'timestamp',
            'timeframe'
        ),
        
        # Unique constraint: یک timestamp + timeframe + source
        UniqueConstraint(
            'timestamp',
            'timeframe',
            'source',
            name='uq_gold_price_facts_time_tf_source'
        ),
        
        # Index for sorting by created_at
        Index('ix_gold_price_facts_created_at', 'created_at'),
    )
    
    # ====================================
    # Methods
    # ====================================
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<GoldPriceFact("
            f"id={self.id}, "
            f"timestamp={self.timestamp}, "
            f"timeframe={self.timeframe}, "
            f"close={self.close}"
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
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "timeframe": self.timeframe,
            "open": float(self.open) if self.open else None,
            "high": float(self.high) if self.high else None,
            "low": float(self.low) if self.low else None,
            "close": float(self.close) if self.close else None,
            "volume": self.volume,
            "price_change": float(self.price_change) if self.price_change else None,
            "price_change_pct": float(self.price_change_pct) if self.price_change_pct else None,
            "news_sentiment_score": float(self.news_sentiment_score) if self.news_sentiment_score else None,
            "news_event_count": self.news_event_count,
            "source": self.source,
            "market": self.market,
            "data_quality": float(self.data_quality) if self.data_quality else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GoldPriceFact":
        """
        Create instance from dictionary.
        
        Args:
            data: Dictionary with model data
            
        Returns:
            GoldPriceFact: New instance
            
        Author: Hoseyn Doulabi (@hoseynd-ai)
        Created: 2025-10-25
        """
        return cls(**data)
