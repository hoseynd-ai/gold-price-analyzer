#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detailed News Service Test

Author: Hoseyn Doulabi (@hoseynd-ai)
"""

import sys
import asyncio
from datetime import datetime, UTC, timedelta

sys.path.insert(0, '/Users/husseindoulabi/Desktop/gold-price-analyzer/backend')

from app.application.services.data_collection.news_service import NewsService
from app.core.logging import setup_logging

setup_logging()


async def main():
    print("\n" + "="*70)
    print("📰 Detailed News Collection Test")
    print("="*70 + "\n")
    
    service = NewsService()
    
    # Test 1: Fetch more news (7 days back)
    print("📥 Test 1: Fetching news from last 7 days (168 hours)...")
    print("⏳ This may take 30-60 seconds...\n")
    
    saved = await service.fetch_and_save_news(hours_back=168, filter_gold=True)
    print(f"✅ Saved {saved} new articles\n")
    
    # Test 2: Statistics
    print("="*70)
    print("📊 Test 2: Database Statistics")
    print("="*70)
    
    stats = await service.get_news_stats()
    
    print(f"\n📈 Total Articles: {stats['total']}")
    
    if stats['oldest'] and stats['newest']:
        days_span = (stats['newest'] - stats['oldest']).days
        print(f"📅 Date Range: {stats['oldest'].date()} to {stats['newest'].date()}")
        print(f"🕐 Span: {days_span} days")
    
    print(f"\n📦 By Source:")
    for source, count in stats['by_source'].items():
        source_name = service.RSS_FEEDS.get(source, {}).get('name', source)
        percentage = (count / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"   • {source_name:<30} {count:>3} ({percentage:.1f}%)")
    
    # Test 3: Latest from each source
    print("\n" + "="*70)
    print("📰 Test 3: Latest News by Source")
    print("="*70 + "\n")
    
    for source_key in service.RSS_FEEDS.keys():
        articles = await service.get_latest_news(limit=3, source=source_key)
        
        if articles:
            source_name = service.RSS_FEEDS[source_key]['name']
            print(f"📡 {source_name} ({len(articles)} articles):")
            
            for i, article in enumerate(articles, 1):
                print(f"   {i}. {article.title[:60]}...")
                print(f"      📅 {article.published_at.strftime('%Y-%m-%d %H:%M UTC')}")
            print()
    
    # Test 4: Recent 24h articles
    print("="*70)
    print("📰 Test 4: News from Last 24 Hours")
    print("="*70 + "\n")
    
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=24)
    
    recent = await service.get_news_by_timerange(start_time, end_time)
    
    print(f"Found {len(recent)} articles in last 24 hours:\n")
    
    for i, article in enumerate(recent[:10], 1):
        hours_ago = (end_time - article.published_at).total_seconds() / 3600
        print(f"{i}. {article.title[:60]}...")
        print(f"   🕐 {hours_ago:.1f} hours ago | Source: {article.source}")
    
    # Test 5: Keyword analysis
    print("\n" + "="*70)
    print("📊 Test 5: Keyword Analysis")
    print("="*70 + "\n")
    
    all_articles = await service.get_latest_news(limit=100)
    
    keyword_count = {}
    for article in all_articles:
        text = f"{article.title} {article.description}".lower()
        
        for keyword in service.GOLD_KEYWORDS:
            if keyword.lower() in text:
                keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
    
    print("Top 10 Keywords Found:")
    sorted_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)
    
    for i, (keyword, count) in enumerate(sorted_keywords[:10], 1):
        print(f"   {i:2}. {keyword:<20} {count:>3} articles")
    
    print("\n" + "="*70)
    print("🎉 Detailed Test Complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
