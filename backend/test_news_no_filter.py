#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test News Without Gold Filter

Author: Hoseyn Doulabi (@hoseynd-ai)
"""

import sys
import asyncio

sys.path.insert(0, '/Users/husseindoulabi/Desktop/gold-price-analyzer/backend')

from app.application.services.data_collection.news_service import NewsService
from app.core.logging import setup_logging

setup_logging()


async def main():
    print("\n" + "="*70)
    print("📰 Testing News Collection WITHOUT Gold Filter")
    print("="*70 + "\n")
    
    service = NewsService()
    
    # Test RSS feeds directly
    print("🧪 Testing RSS Feed Accessibility:")
    print("-" * 70 + "\n")
    
    for key, info in service.RSS_FEEDS.items():
        print(f"📡 {info['name']}")
        print(f"   URL: {info['url']}")
        
        feed = service.fetch_rss_feed(info['url'])
        
        if feed and feed.entries:
            print(f"   ✅ Success! Found {len(feed.entries)} total entries")
            
            # Show first 3 titles
            print(f"   📰 Sample headlines:")
            for i, entry in enumerate(feed.entries[:3], 1):
                title = entry.get('title', 'No title')[:60]
                print(f"      {i}. {title}...")
            
            # Check how many are gold-related
            gold_count = 0
            for entry in feed.entries:
                title = entry.get('title', '')
                desc = entry.get('summary', entry.get('description', ''))
                if service.is_gold_related(title, desc):
                    gold_count += 1
            
            print(f"   🏆 Gold-related: {gold_count} out of {len(feed.entries)}")
        else:
            print(f"   ❌ Failed to fetch or empty feed")
        
        print()
    
    print("="*70)
    print("📥 Fetching ALL news (no gold filter) from last 7 days...")
    print("="*70 + "\n")
    
    # Fetch without filter
    saved = await service.fetch_and_save_news(hours_back=168, filter_gold=False)
    
    print(f"\n✅ Saved {saved} articles (all topics)\n")
    
    # Statistics
    stats = await service.get_news_stats()
    
    print("="*70)
    print("📊 Final Statistics")
    print("="*70)
    print(f"\n📈 Total Articles: {stats['total']}")
    print(f"\n📦 By Source:")
    for source, count in stats['by_source'].items():
        source_name = service.RSS_FEEDS.get(source, {}).get('name', source)
        print(f"   • {source_name}: {count}")
    
    # Show sample
    print("\n📰 Sample Articles (all topics):")
    print("-" * 70)
    
    articles = await service.get_latest_news(limit=10)
    
    for i, article in enumerate(articles[:10], 1):
        # Check if gold-related
        is_gold = service.is_gold_related(article.title, article.description or '')
        emoji = "🏆" if is_gold else "📰"
        
        print(f"\n{i}. {emoji} {article.title[:60]}...")
        print(f"   Source: {article.source} | {article.published_at.strftime('%Y-%m-%d %H:%M UTC')}")
        
        if is_gold:
            print(f"   ✅ Gold-related!")
    
    print("\n" + "="*70)
    print("🎉 Test Complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
