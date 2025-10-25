#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create Mock News for Testing

Author: Hoseyn Doulabi (@hoseynd-ai)
"""

import sys
import asyncio
from datetime import datetime, UTC, timedelta
import random

sys.path.insert(0, '/Users/husseindoulabi/Desktop/gold-price-analyzer/backend')

from sqlalchemy import select
from app.infrastructure.database.base import AsyncSessionLocal
from app.infrastructure.database.models.news_event import NewsEvent


# Mock news data
MOCK_NEWS = [
    {
        'title': 'Gold prices surge to $2,100 amid inflation concerns',
        'description': 'Gold reached new highs as investors seek safe-haven assets due to rising inflation fears and economic uncertainty.',
        'category': 'gold_market',
        'source': 'kitco',
    },
    {
        'title': 'Federal Reserve signals interest rate cuts in 2024',
        'description': 'The Fed chairman indicated potential rate cuts which could boost gold prices significantly in coming months.',
        'category': 'economics',
        'source': 'reuters',
    },
    {
        'title': 'Central banks increase gold reserves by 15%',
        'description': 'World central banks continue accumulating gold as part of diversification strategy amid dollar concerns.',
        'category': 'gold_market',
        'source': 'goldorg',
    },
    {
        'title': 'Gold mining output drops to 10-year low',
        'description': 'Global gold production decreased significantly due to operational challenges and environmental regulations.',
        'category': 'gold_industry',
        'source': 'kitco',
    },
    {
        'title': 'Dollar weakness pushes gold above $2,050',
        'description': 'Weaker USD index supports higher gold prices in international markets as investors seek alternatives.',
        'category': 'gold_market',
        'source': 'reuters',
    },
    {
        'title': 'India gold demand surges ahead of wedding season',
        'description': 'Indian consumers increase gold purchases for traditional wedding ceremonies, supporting global demand.',
        'category': 'gold_market',
        'source': 'goldorg',
    },
    {
        'title': 'Geopolitical tensions support safe-haven gold demand',
        'description': 'Rising global tensions drive investors toward gold as a safe-haven asset amid market volatility.',
        'category': 'gold_market',
        'source': 'reuters',
    },
    {
        'title': 'Gold ETF inflows reach $5 billion in Q3',
        'description': 'Institutional investors pour money into gold ETFs amid market uncertainty and inflation hedging.',
        'category': 'gold_market',
        'source': 'kitco',
    },
    {
        'title': 'Silver prices follow gold higher in precious metals rally',
        'description': 'Silver gains alongside gold as precious metals market strengthens on safe-haven demand.',
        'category': 'commodities',
        'source': 'reuters',
    },
    {
        'title': 'World Gold Council forecasts strong demand in 2024',
        'description': 'Industry body predicts continued robust demand from emerging markets and central bank purchases.',
        'category': 'gold_industry',
        'source': 'goldorg',
    },
    {
        'title': 'Chinese gold imports hit record high',
        'description': 'China imported record amounts of gold as domestic demand remains strong despite economic slowdown.',
        'category': 'gold_market',
        'source': 'kitco',
    },
    {
        'title': 'Gold breaks through $2,000 resistance level',
        'description': 'Technical analysts see further upside as gold breaks key psychological barrier on strong fundamentals.',
        'category': 'gold_market',
        'source': 'reuters',
    },
    {
        'title': 'Bitcoin falls as investors rotate back to gold',
        'description': 'Cryptocurrency weakness supports gold as investors seek more traditional safe-haven assets.',
        'category': 'commodities',
        'source': 'reuters',
    },
    {
        'title': 'Gold jewelry demand rises in Middle East',
        'description': 'Middle Eastern markets show strong physical gold demand for jewelry and investment.',
        'category': 'gold_market',
        'source': 'goldorg',
    },
    {
        'title': 'Mining companies face rising production costs',
        'description': 'Higher energy and labor costs squeeze profit margins for gold mining companies globally.',
        'category': 'gold_industry',
        'source': 'kitco',
    },
]


async def create_mock_news():
    """Create mock news articles for testing."""
    
    print("\n" + "="*70)
    print("📰 Creating Mock Gold News Articles for Testing")
    print("="*70)
    print(f"🕐 UTC Time: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👤 User: hoseynd-ai")
    print("="*70 + "\n")
    
    now = datetime.now(UTC)
    created_count = 0
    
    async with AsyncSessionLocal() as session:
        for i, news_data in enumerate(MOCK_NEWS):
            # Random time in last 7 days
            hours_ago = random.randint(1, 168)
            published_at = now - timedelta(hours=hours_ago)
            
            # Random sentiment
            sentiment_score = random.uniform(-0.5, 0.8)
            if sentiment_score > 0.3:
                sentiment_label = 'positive'
                price_impact = 'bullish'
            elif sentiment_score < -0.2:
                sentiment_label = 'negative'
                price_impact = 'bearish'
            else:
                sentiment_label = 'neutral'
                price_impact = 'neutral'
            
            # Create news event
            news = NewsEvent(
                title=news_data['title'],
                description=news_data['description'],
                content=news_data['description'] + ' Additional market analysis and commentary...',
                url=f"https://goldnews.example.com/article/{i+1}",
                published_at=published_at,
                source=news_data['source'],
                category=news_data['category'],
                author=random.choice(['John Smith', 'Sarah Johnson', 'Mike Chen', 'Emma Wilson']),
                sentiment_score=round(sentiment_score, 2),
                sentiment_label=sentiment_label,
                confidence=round(random.uniform(0.75, 0.95), 2),
                price_impact=price_impact,
                impact_score=round(abs(sentiment_score) * random.uniform(0.7, 1.0), 2),
            )
            
            # Check if exists
            result = await session.execute(
                select(NewsEvent).where(NewsEvent.url == news.url)
            )
            
            if not result.scalar_one_or_none():
                session.add(news)
                created_count += 1
                
                emoji = "📈" if sentiment_label == 'positive' else "📉" if sentiment_label == 'negative' else "➡️"
                
                print(f"✅ {i+1:2}. {news_data['title'][:55]}...")
                print(f"    📅 {published_at.strftime('%Y-%m-%d %H:%M UTC')}")
                print(f"    🏷️  {news_data['source']} | {news_data['category']}")
                print(f"    {emoji} Sentiment: {sentiment_label} ({sentiment_score:+.2f}) | Impact: {price_impact}")
                print()
        
        await session.commit()
    
    print("="*70)
    print(f"🎉 Successfully created {created_count} mock news articles!")
    print("="*70 + "\n")
    
    # Show statistics
    from sqlalchemy import func
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.count(NewsEvent.id))
        )
        total = result.scalar()
        
        result = await session.execute(
            select(
                NewsEvent.source,
                func.count(NewsEvent.id)
            ).group_by(NewsEvent.source)
        )
        by_source = result.all()
        
        result = await session.execute(
            select(
                NewsEvent.sentiment_label,
                func.count(NewsEvent.id)
            ).group_by(NewsEvent.sentiment_label)
        )
        by_sentiment = result.all()
    
    print("📊 Database Statistics:")
    print(f"   Total Articles: {total}\n")
    
    print("   By Source:")
    for source, count in by_source:
        print(f"     • {source}: {count}")
    
    print("\n   By Sentiment:")
    for sentiment, count in by_sentiment:
        emoji = "📈" if sentiment == 'positive' else "📉" if sentiment == 'negative' else "➡️"
        print(f"     {emoji} {sentiment}: {count}")
    
    print("\n" + "="*70)
    print("🎯 Ready to test News Service and Sentiment Analysis!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(create_mock_news())
