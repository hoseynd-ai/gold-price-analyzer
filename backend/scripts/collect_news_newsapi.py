#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collect Historical News using NewsAPI

جمع‌آوری اخبار تاریخی طلا از NewsAPI.org و تحلیل sentiment

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25 16:09:04 UTC
"""

import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import asyncio
from datetime import datetime
from app.application.services.data_collection.newsapi_service import NewsAPIService
from app.application.services.ml.sentiment_analysis_service import SentimentAnalysisService
from app.application.services.data_collection.news_service import NewsService


async def main():
    print("\n" + "="*70)
    print("📰 Historical News Collection with NewsAPI")
    print("="*70)
    print(f"📅 UTC: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👤 User: hoseynd-ai")
    print("="*70 + "\n")
    
    # 1. جمع‌آوری اخبار از NewsAPI
    print("🔍 Step 1: Fetching news from NewsAPI.org...")
    print("   (Free tier: last 30 days, 100 requests/day)\n")
    
    newsapi_service = NewsAPIService()
    
    try:
        saved = await newsapi_service.fetch_historical_news(days_back=30)
        
        print(f"\n✅ NewsAPI collection complete!")
        print(f"   New articles saved: {saved}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # 2. تحلیل sentiment با FinBERT
    print("\n" + "="*70)
    print("🤖 Step 2: Analyzing sentiment with FinBERT...")
    print("="*70 + "\n")
    
    sentiment_service = SentimentAnalysisService()
    
    print("🔄 Analyzing all news articles...")
    analyzed = await sentiment_service.analyze_all_news(force_reanalyze=False)
    
    print(f"\n✅ Sentiment analysis complete!")
    print(f"   Articles analyzed: {analyzed}")
    
    # 3. آمار نهایی
    print("\n" + "="*70)
    print("📊 Final Statistics")
    print("="*70 + "\n")
    
    news_service = NewsService()
    stats = await news_service.get_news_stats()
    
    print(f"📈 Total Articles in Database: {stats['total']}")
    
    if stats['oldest'] and stats['newest']:
        print(f"📅 Date Range: {stats['oldest'].date()} → {stats['newest'].date()}")
        days_span = (stats['newest'] - stats['oldest']).days
        print(f"   Span: {days_span} days")
    
    print(f"\n📦 By Source:")
    for source, count in stats['by_source'].items():
        print(f"   • {source}: {count} articles")
    
    # Sentiment stats
    sentiment_stats = await sentiment_service.get_sentiment_statistics()
    
    if sentiment_stats and 'by_label' in sentiment_stats:
        print(f"\n😊 Sentiment Distribution:")
        
        # محاسبه total (اصلاح شده)
        total_with_sentiment = sum(
            label_data['count'] 
            for label_data in sentiment_stats['by_label'].values()
        )
        
        for label in ['positive', 'neutral', 'negative']:
            label_data = sentiment_stats['by_label'].get(label, {})
            count = label_data.get('count', 0)
            avg_score = label_data.get('avg_score', 0)
            pct = (count / total_with_sentiment * 100) if total_with_sentiment > 0 else 0
            
            emoji = "😊" if label == 'positive' else "😐" if label == 'neutral' else "😟"
            print(f"   {emoji} {label.capitalize()}: {count} ({pct:.1f}%) - avg: {avg_score:+.2f}")
        
        print(f"\n   📊 Overall avg sentiment: {sentiment_stats.get('avg_sentiment_score', 0):+.3f}")

    
    # 4. خلاصه برای training
    print("\n" + "="*70)
    print("🎯 Ready for Model Training!")
    print("="*70)
    
    print(f"\n✅ Dataset Summary:")
    print(f"   • Total news: {stats['total']}")
    print(f"   • With sentiment: {sum(sentiment_stats['by_label'].values()) if sentiment_stats else 0}")
    print(f"   • Date coverage: ~{days_span if stats['oldest'] else 0} days")
    
    print(f"\n🚀 Next Step:")
    print(f"   Run improved training: python scripts/train_lstm_improved.py")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
