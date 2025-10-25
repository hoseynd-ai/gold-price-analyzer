#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Insert Data

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25
"""

import asyncio
from datetime import datetime, UTC
from sqlalchemy import select

from app.infrastructure.database.base import AsyncSessionLocal
from app.infrastructure.database.models import GoldPriceFact, NewsEvent
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def test_insert():
    """Test inserting and reading data."""
    
    print("\n" + "="*50)
    print("🧪 Testing Data Insert & Read")
    print("="*50 + "\n")
    
    async with AsyncSessionLocal() as session:
        
        # 1. Insert Gold Price
        print("📊 Inserting gold price...")
        gold_price = GoldPriceFact(
            timestamp=datetime.now(UTC),
            timeframe="daily",
            open=2750.00,
            high=2755.50,
            low=2748.20,
            close=2752.30,
            volume=125000,
            price_change=2.30,
            price_change_pct=0.08,
            source="yahoo_finance",
            market="spot",
            data_quality=1.0
        )
        session.add(gold_price)
        await session.commit()
        print(f"✅ Gold price inserted: ID={gold_price.id}")
        
        # 2. Insert News
        print("\n📰 Inserting news event...")
        news = NewsEvent(
            title="Fed keeps interest rates steady at 5.25%",
            description="The Federal Reserve announced today...",
            published_at=datetime.now(UTC),
            sentiment_score=0.65,
            sentiment_label="positive",
            confidence=0.89,
            price_impact="bullish",
            impact_score=0.72,
            source="newsapi",
            category="economics",
            keywords=["fed", "interest rate", "gold", "economy"]
        )
        session.add(news)
        await session.commit()
        print(f"✅ News inserted: ID={news.id}")
        
        # 3. Read Gold Prices
        print("\n📊 Reading gold prices...")
        result = await session.execute(
            select(GoldPriceFact).order_by(GoldPriceFact.timestamp.desc())
        )
        prices = result.scalars().all()
        print(f"✅ Found {len(prices)} gold price(s)")
        for p in prices:
            print(f"   - {p.timestamp}: ${p.close} ({p.timeframe})")
        
        # 4. Read News
        print("\n📰 Reading news events...")
        result = await session.execute(
            select(NewsEvent).order_by(NewsEvent.published_at.desc())
        )
        news_items = result.scalars().all()
        print(f"✅ Found {len(news_items)} news event(s)")
        for n in news_items:
            print(f"   - {n.title[:50]}... (sentiment: {n.sentiment_score})")
    
    print("\n" + "="*50)
    print("🎉 All tests passed!")
    print("="*50 + "\n")


if __name__ == "__main__":
    asyncio.run(test_insert())
