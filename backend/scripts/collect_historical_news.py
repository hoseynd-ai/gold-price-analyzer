#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collect Historical Gold News

جمع‌آوری اخبار تاریخی طلا از 2 سال گذشته برای بهبود مدل

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25 15:58:58 UTC
"""

import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import asyncio
from datetime import datetime, timedelta
from app.application.services.data_collection.news_service import NewsService
from app.application.services.ml.sentiment_analysis_service import SentimentAnalysisService


async def collect_news_in_batches(months_back: int = 24):
    """
    جمع‌آوری اخبار به صورت batch (دسته‌بندی شده)
    
    Args:
        months_back: چند ماه عقب برگردیم (پیش‌فرض: 24 ماه = 2 سال)
    """
    print("\n" + "="*70)
    print("📰 Historical Gold News Collection")
    print("="*70)
    print(f"📅 UTC: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👤 User: hoseynd-ai")
    print("="*70 + "\n")
    
    news_service = NewsService()
    sentiment_service = SentimentAnalysisService()
    
    total_collected = 0
    total_analyzed = 0
    
    print(f"🎯 Target: Collect news from last {months_back} months")
    print(f"📊 Strategy: Collect in monthly batches to avoid rate limits\n")
    
    # جمع‌آوری به صورت ماهانه
    for month_offset in range(months_back):
        print(f"\n{'='*70}")
        print(f"📅 Month {month_offset + 1}/{months_back}")
        print(f"{'='*70}\n")
        
        # محاسبه بازه زمانی
        end_date = datetime.utcnow() - timedelta(days=30 * month_offset)
        start_date = end_date - timedelta(days=30)
        
        print(f"📅 Date range: {start_date.date()} to {end_date.date()}")
        
        try:
            # جمع‌آوری اخبار (آخرین 30 روز × ماه)
            hours_back = 24 * 30 * (month_offset + 1)
            
            print(f"📥 Fetching news (looking back {hours_back} hours)...")
            saved = await news_service.fetch_and_save_news(
                hours_back=hours_back,
                filter_gold=True
            )
            
            total_collected += saved
            print(f"✅ Collected: {saved} articles")
            
            # تحلیل احساسات
            if saved > 0:
                print(f"🤖 Analyzing sentiment...")
                analyzed = await sentiment_service.analyze_all_news(force_reanalyze=False)
                total_analyzed += analyzed
                print(f"✅ Analyzed: {analyzed} articles")
            
            # آمار کلی تا الان
            print(f"\n📊 Progress:")
            print(f"   Total collected: {total_collected} articles")
            print(f"   Total analyzed: {total_analyzed} articles")
            
            # صبر کردن برای rate limit (5 ثانیه)
            if month_offset < months_back - 1:
                print(f"\n⏳ Waiting 5 seconds for rate limit...")
                await asyncio.sleep(5)
            
        except Exception as e:
            print(f"❌ Error in month {month_offset + 1}: {e}")
            continue
    
    # آمار نهایی
    print("\n" + "="*70)
    print("📊 COLLECTION COMPLETE!")
    print("="*70)
    
    # دریافت آمار از database
    stats = await news_service.get_news_stats()
    
    print(f"\n📈 Final Database Stats:")
    print(f"   Total articles: {stats['total']}")
    print(f"   Date range: {stats['oldest'].date() if stats['oldest'] else 'N/A'} to {stats['newest'].date() if stats['newest'] else 'N/A'}")
    
    print(f"\n📦 By Source:")
    for source, count in stats['by_source'].items():
        source_name = news_service.RSS_FEEDS.get(source, {}).get('name', source)
        print(f"   • {source_name}: {count} articles")
    
    # آمار sentiment
    print(f"\n😊 Sentiment Distribution:")
    sentiment_stats = await sentiment_service.get_sentiment_statistics()
    if sentiment_stats and 'by_label' in sentiment_stats:
        for label, count in sentiment_stats['by_label'].items():
            emoji = "😊" if label == 'positive' else "😟" if label == 'negative' else "😐"
            print(f"   {emoji} {label}: {count} articles")
    
    print("\n" + "="*70)
    print("✅ Ready for improved model training!")
    print("="*70 + "\n")


async def quick_collect_recent(days: int = 90):
    """
    جمع‌آوری سریع اخبار 90 روز اخیر
    
    این تابع برای شروع سریع است
    """
    print("\n" + "="*70)
    print("📰 Quick News Collection (Last 90 Days)")
    print("="*70 + "\n")
    
    news_service = NewsService()
    sentiment_service = SentimentAnalysisService()
    
    print(f"📥 Fetching news from last {days} days...")
    saved = await news_service.fetch_and_save_news(
        hours_back=24 * days,
        filter_gold=True
    )
    
    print(f"✅ Collected: {saved} articles")
    
    if saved > 0:
        print(f"\n🤖 Analyzing sentiment with FinBERT...")
        analyzed = await sentiment_service.analyze_all_news(force_reanalyze=True)
        print(f"✅ Analyzed: {analyzed} articles")
    
    # آمار
    stats = await news_service.get_news_stats()
    print(f"\n📊 Total in database: {stats['total']} articles")
    
    print("\n✅ Quick collection complete!\n")


def main():
    """اجرای اصلی"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect historical gold news')
    parser.add_argument(
        '--mode',
        choices=['quick', 'full'],
        default='quick',
        help='Collection mode: quick (90 days) or full (24 months)'
    )
    parser.add_argument(
        '--months',
        type=int,
        default=24,
        help='Number of months to collect (for full mode)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='Number of days to collect (for quick mode)'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'quick':
        print("🚀 Starting QUICK collection (90 days)...")
        asyncio.run(quick_collect_recent(args.days))
    else:
        print("🚀 Starting FULL collection (24 months)...")
        asyncio.run(collect_news_in_batches(args.months))


if __name__ == "__main__":
    main()
