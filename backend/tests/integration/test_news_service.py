#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test News Service

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25
"""

import asyncio
from datetime import datetime, UTC
from app.application.services.data_collection.news_service import NewsService
from app.core.logging import setup_logging

setup_logging()


async def main():
    print("\n" + "="*70)
    print("📰 Gold Price Analyzer - News Collection Service Test")
    print("="*70)
    print(f"🕐 UTC Time: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👤 User: hoseynd-ai")
    print("="*70 + "\n")
    
    service = NewsService()
    
    # Show RSS feeds
    print("📡 RSS Feeds Configuration:")
    print("-" * 70)
    for key, info in service.RSS_FEEDS.items():
        print(f"\n✓ {info['name']}")
        print(f"  URL: {info['url']}")
        print(f"  Category: {info['category']}")
        print(f"  Source Key: {key}")
    print("\n" + "="*70 + "\n")
    
    # Fetch news
    print("📥 Fetching gold-related news from last 48 hours...")
    print("⏳ This may take 15-30 seconds...\n")
    
    saved = await service.fetch_and_save_news(hours_back=48, filter_gold=True)
    
    print(f"✅ Successfully saved {saved} new gold-related articles!\n")
    
    # Get statistics
    print("="*70)
    print("📊 News Database Statistics")
    print("="*70)
    
    stats = await service.get_news_stats()
    
    print(f"\n📈 Total Articles: {stats['total']}")
    
    if stats['oldest'] and stats['newest']:
        print(f"📅 Date Range: {stats['oldest'].date()} to {stats['newest'].date()}")
    
    print("\n📦 By Source:")
    for source, count in stats['by_source'].items():
        source_name = service.RSS_FEEDS.get(source, {}).get('name', source)
        print(f"   • {source_name}: {count} articles")
    
    # Show latest news
    print("\n" + "="*70)
    print("📰 Latest 10 Gold Market News")
    print("="*70 + "\n")
    
    articles = await service.get_latest_news(limit=10)
    
    if articles:
        for i, article in enumerate(articles, 1):
            print(f"{i}. 📌 {article.title}")
            print(f"   🗓️  {article.published_at.strftime('%Y-%m-%d %H:%M UTC')}")
            print(f"   🏷️  Source: {article.source} | Category: {article.category}")
            print(f"   👤 Author: {article.author}")
            print(f"   🔗 {article.url}")
            
            if article.description:
                desc = article.description[:200].replace('\n', ' ').strip()
                print(f"   📝 {desc}...")
            
            if article.sentiment_score:
                emoji = "📈" if article.sentiment_score > 0 else "📉" if article.sentiment_score < 0 else "➡️"
                print(f"   {emoji} Sentiment: {article.sentiment_label} ({article.sentiment_score})")
            
            print()
    else:
        print("⚠️  No articles found in database")
        print("\nPossible reasons:")
        print("  • No new gold-related news in last 48 hours")
        print("  • RSS feeds temporarily unavailable")
        print("  • Network connectivity issues")
        print("  • Strict keyword filtering")
        print("\nTry running again or check RSS feed URLs manually.")
    
    print("="*70)
    print("🎉 News Service Test Complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
