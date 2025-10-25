#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تست تحلیل احساسات | Sentiment Analysis Test

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25
"""

import sys
import asyncio

sys.path.insert(0, '/Users/husseindoulabi/Desktop/gold-price-analyzer/backend')

from app.application.services.ml.sentiment_analysis_service import SentimentAnalysisService
from app.core.logging import setup_logging

setup_logging()


async def main():
    print("\n" + "="*70)
    print("🤖 تست تحلیل احساسات اخبار | News Sentiment Analysis Test")
    print("="*70)
    print("⏰ 2025-10-25 13:04:19 UTC")
    print("👤 hoseynd-ai")
    print("="*70 + "\n")
    
    # ایجاد سرویس | Create service
    service = SentimentAnalysisService()
    
    # تست ۱: تحلیل متن‌های نمونه | Test 1: Sample texts
    print("📝 تست ۱: تحلیل متن‌های نمونه | Test 1: Sample Texts")
    print("-" * 70 + "\n")
    
    sample_texts = [
        "Gold prices surge to $2,100 amid inflation concerns",
        "Federal Reserve keeps interest rates steady",
        "Gold market faces uncertainty as dollar strengthens",
        "Central banks increase gold reserves by 15%",
        "Gold falls as investors sell safe-haven assets",
    ]
    
    for i, text in enumerate(sample_texts, 1):
        print(f"{i}. متن | Text: {text}")
        
        result = service.analyze_text(text)
        
        emoji = "📈" if result['label'] == 'positive' else "📉" if result['label'] == 'negative' else "➡️"
        
        print(f"   {emoji} احساسات | Sentiment: {result['label']}")
        print(f"   امتیاز | Score: {result['score']:+.3f}")
        print(f"   اطمینان | Confidence: {result['confidence']:.3f}")
        print(f"   تأثیر | Impact: {result['price_impact']} ({result['impact_score']:.3f})")
        print()
    
    # تست ۲: تحلیل اخبار دیتابیس | Test 2: Database news
    print("="*70)
    print("📰 تست ۲: تحلیل اخبار دیتابیس | Test 2: Database News")
    print("="*70 + "\n")
    
    analyzed = await service.analyze_all_news(force_reanalyze=True)
    print(f"✅ تحلیل شد | Analyzed: {analyzed} خبر | articles\n")
    
    # تست ۳: آمار | Test 3: Statistics
    print("="*70)
    print("📊 تست ۳: آمار احساسات | Test 3: Sentiment Statistics")
    print("="*70 + "\n")
    
    stats = await service.get_sentiment_statistics()
    
    print(f"📈 کل تحلیل شده | Total Analyzed: {stats['total_analyzed']}")
    print(f"📊 میانگین امتیاز | Avg Score: {stats['avg_sentiment_score']:+.3f}")
    print()
    
    print("📋 بر اساس برچسب | By Label:")
    for label, data in stats['by_label'].items():
        emoji = "📈" if label == 'positive' else "📉" if label == 'negative' else "➡️"
        percentage = (data['count'] / stats['total_analyzed'] * 100) if stats['total_analyzed'] > 0 else 0
        print(f"   {emoji} {label:>10}: {data['count']:>2} ({percentage:>5.1f}%) | Avg: {data['avg_score']:+.3f}")
    
    print("\n" + "="*70)
    print("🎉 تست کامل شد! | Test Complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
