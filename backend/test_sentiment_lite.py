#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تست سریع Sentiment Lite | Quick Sentiment Lite Test

Author: Hoseyn Doulabi (@hoseynd-ai)
"""

import sys
import asyncio

sys.path.insert(0, '/Users/husseindoulabi/Desktop/gold-price-analyzer/backend')

from app.application.services.ml.sentiment_analysis_lite import SentimentAnalysisLite
from app.core.logging import setup_logging

setup_logging()


async def main():
    print("\n" + "="*70)
    print("⚡ تست سریع تحلیل احساسات | Quick Sentiment Analysis Test")
    print("="*70)
    print("🚀 نسخه سبک (بدون دانلود مدل) | Lite Version (No Model Download)")
    print("="*70 + "\n")
    
    service = SentimentAnalysisLite()
    
    # تست نمونه‌ها | Test samples
    print("📝 تست متن‌های نمونه | Test Sample Texts")
    print("-" * 70 + "\n")
    
    samples = [
        "Gold prices surge to $2,100 amid inflation concerns",
        "Federal Reserve keeps interest rates steady",
        "Gold market faces uncertainty as dollar strengthens",
        "Central banks increase gold reserves significantly",
        "Gold falls sharply as investors sell safe-haven assets",
    ]
    
    for i, text in enumerate(samples, 1):
        print(f"{i}. {text}")
        result = service.analyze_text(text)
        
        emoji = "📈" if result['label'] == 'positive' else "📉" if result['label'] == 'negative' else "➡️"
        
        print(f"   {emoji} احساسات | Sentiment: {result['label']}")
        print(f"   امتیاز | Score: {result['score']:+.3f}")
        print(f"   اطمینان | Confidence: {result['confidence']:.3f}")
        print(f"   تأثیر | Impact: {result['price_impact']}")
        print()
    
    # تحلیل اخبار دیتابیس | Analyze database news
    print("="*70)
    print("📰 تحلیل اخبار دیتابیس | Analyzing Database News")
    print("="*70 + "\n")
    
    analyzed = await service.analyze_all_news(force_reanalyze=True)
    print(f"✅ تحلیل شد | Analyzed: {analyzed} خبر | articles\n")
    
    # آمار | Statistics
    print("="*70)
    print("📊 آمار احساسات | Sentiment Statistics")
    print("="*70 + "\n")
    
    stats = await service.get_sentiment_statistics()
    
    print(f"📈 کل | Total: {stats['total_analyzed']}")
    print(f"📊 میانگین | Avg Score: {stats['avg_sentiment_score']:+.3f}")
    print()
    
    print("📋 بر اساس برچسب | By Label:")
    for label, data in stats['by_label'].items():
        emoji = "📈" if label == 'positive' else "📉" if label == 'negative' else "➡️"
        pct = (data['count'] / stats['total_analyzed'] * 100) if stats['total_analyzed'] > 0 else 0
        print(f"   {emoji} {label:>10}: {data['count']:>2} ({pct:>5.1f}%) | Avg: {data['avg_score']:+.3f}")
    
    print("\n" + "="*70)
    print("🎉 تست کامل شد! | Test Complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
