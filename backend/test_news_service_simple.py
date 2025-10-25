#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test News Service - Simple Version

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25
"""

import sys
import asyncio
from datetime import datetime, UTC

# Add current directory to path
sys.path.insert(0, '/Users/husseindoulabi/Desktop/gold-price-analyzer/backend')

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
    
    # Test RSS fetch first
    print("🧪 Testing RSS Feed Access...")
    print("-" * 70)
    
    for key, info in service.RSS_FEEDS.items():
        print(f"\n📡 Fetching {info['name']}...")
        feed = service.fetch_rss_feed(info['url'])
        
        if feed and feed.entries:
            print(f"   ✅ Success! Found {len(feed.entries)} entries")
            print(f"   📰 Latest: {feed.entries[0].get('title', 'No title')[:60]}...")
        else:
            print(f"   ⚠️  No entries or fetch failed")
    
    print("\n" + "="*70 + "\n")
    
    # Fetch and save news
    print("📥 Fetching gold-related news from last 48 hours...")
    print("⏳ This may take 15-30 seconds...\n")
    
    try:
        saved = await service.fetch_and_save_news(hours_back=48, filter_gold=True)
        print(f"\n✅ Successfully saved {saved} new gold-related articles!\n")
    except Exception as e:
        print(f"\n❌ Error saving news: {e}\n")
        import traceback
        traceback.print_exc()
        return
    
    # Get statistics
    print("="*70)
    print("📊 News Database Statistics")
    print("="*70)
    
    try:
        stats = await service.get_news_stats()
        
        print(f"\n📈 Total Articles: {stats['total']}")
        
        if stats['oldest'] and stats['newest']:
            print(f"📅 Date Range: {stats['oldest'].date()} to {stats['newest'].date()}")
        
        print("\n📦 By Source:")
        for source, count in stats['by_source'].items():
            source_name = service.RSS_FEEDS.get(source, {}).get('name', source)
            print(f"   • {source_name}: {count} articles")
    except Exception as e:
        print(f"\n⚠️  Could not get stats: {e}")
    
    # Show latest news
    print("\n" + "="*70)
    print("📰 Latest 10 Gold Market News")
    print("="*70 + "\n")
    
    try:
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
                
                print()
        else:
            print("⚠️  No articles found in database")
            print("\nThis is normal if:")
            print("  • First time running (no data yet)")
            print("  • No new gold news in last 48 hours")
            print("  • RSS feeds temporarily down")
    except Exception as e:
        print(f"\n❌ Error fetching articles: {e}")
        import traceback
        traceback.print_exc()
    
    print("="*70)
    print("🎉 News Service Test Complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
