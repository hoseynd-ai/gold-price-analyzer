#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحلیل احساسات سبک | Lightweight Sentiment Analysis

بدون نیاز به دانلود مدل سنگین!
No heavy model download needed!

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25
"""

from typing import Dict, Any, List
from textblob import TextBlob
import re

from app.core.logging import get_logger
from app.infrastructure.database.base import AsyncSessionLocal
from app.infrastructure.database.models.news_event import NewsEvent

logger = get_logger(__name__)


class SentimentAnalysisLite:
    """
    تحلیل احساسات سبک | Lightweight Sentiment Analyzer
    
    استفاده از TextBlob (سریع و بدون دانلود)
    Uses TextBlob (fast, no download)
    
    مزایا | Advantages:
    - ✅ بدون دانلود مدل | No model download
    - ✅ سریع | Fast
    - ✅ مناسب برای توسعه | Good for development
    
    معایب | Disadvantages:
    - ⚠️  دقت کمتر از FinBERT | Less accurate than FinBERT
    
    Author: Hoseyn Doulabi (@hoseynd-ai)
    """
    
    # کلمات کلیدی مثبت | Positive keywords
    POSITIVE_KEYWORDS = [
        'surge', 'rise', 'gain', 'boost', 'increase', 'rally',
        'bullish', 'buy', 'strong', 'growth', 'positive',
        'up', 'higher', 'support', 'demand', 'favorable'
    ]
    
    # کلمات کلیدی منفی | Negative keywords
    NEGATIVE_KEYWORDS = [
        'fall', 'drop', 'decline', 'loss', 'decrease', 'crash',
        'bearish', 'sell', 'weak', 'negative', 'down', 'lower',
        'pressure', 'concern', 'uncertainty', 'risk', 'unfavorable'
    ]
    
    def __init__(self):
        """مقداردهی اولیه | Initialize"""
        logger.info("sentiment_lite_initialized")
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        تحلیل احساسات متن | Analyze text sentiment
        
        Args:
            text: متن ورودی | Input text
            
        Returns:
            dict: نتیجه تحلیل | Analysis result
        """
        try:
            # تحلیل با TextBlob | Analyze with TextBlob
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # شمارش کلمات کلیدی | Count keywords
            text_lower = text.lower()
            positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text_lower)
            negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in text_lower)
            
            # تنظیم امتیاز بر اساس کلمات کلیدی | Adjust score by keywords
            keyword_boost = (positive_count - negative_count) * 0.1
            adjusted_score = polarity + keyword_boost
            adjusted_score = max(-1.0, min(1.0, adjusted_score))  # Clamp to [-1, 1]
            
            # تعیین برچسب | Determine label
            if adjusted_score > 0.1:
                label = 'positive'
            elif adjusted_score < -0.1:
                label = 'negative'
            else:
                label = 'neutral'
            
            # محاسبه اطمینان | Calculate confidence
            confidence = abs(adjusted_score) * subjectivity
            confidence = max(0.0, min(1.0, confidence))
            
            # تعیین تأثیر قیمت | Determine price impact
            if adjusted_score > 0.5:
                price_impact = 'very_bullish'
            elif adjusted_score > 0.1:
                price_impact = 'bullish'
            elif adjusted_score < -0.5:
                price_impact = 'very_bearish'
            elif adjusted_score < -0.1:
                price_impact = 'bearish'
            else:
                price_impact = 'neutral'
            
            impact_score = abs(adjusted_score) * confidence
            
            result = {
                'label': label,
                'score': round(adjusted_score, 3),
                'confidence': round(confidence, 3),
                'price_impact': price_impact,
                'impact_score': round(impact_score, 3),
                'keyword_counts': {
                    'positive': positive_count,
                    'negative': negative_count
                }
            }
            
            logger.debug("sentiment_analyzed_lite",
                        text=text[:50],
                        label=label,
                        score=round(adjusted_score, 2))
            
            return result
            
        except Exception as e:
            logger.error("sentiment_analysis_lite_error",
                        text=text[:50],
                        error=str(e))
            raise
    
    async def analyze_all_news(self, force_reanalyze: bool = False) -> int:
        """
        تحلیل تمام اخبار | Analyze all news
        
        Args:
            force_reanalyze: تحلیل مجدد | Re-analyze
            
        Returns:
            int: تعداد تحلیل شده | Count analyzed
        """
        logger.info("analyzing_all_news_lite", force_reanalyze=force_reanalyze)
        
        analyzed_count = 0
        
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            
            query = select(NewsEvent)
            
            if not force_reanalyze:
                query = query.where(NewsEvent.sentiment_score == None)
            
            result = await session.execute(query)
            news_articles = result.scalars().all()
            
            logger.info("news_articles_found", count=len(news_articles))
            
            for news in news_articles:
                try:
                    text = f"{news.title}. {news.description or ''}"
                    sentiment = self.analyze_text(text)
                    
                    news.sentiment_score = sentiment['score']
                    news.sentiment_label = sentiment['label']
                    news.confidence = sentiment['confidence']
                    news.price_impact = sentiment['price_impact']
                    news.impact_score = sentiment['impact_score']
                    
                    analyzed_count += 1
                    
                    logger.info("news_analyzed_lite",
                               id=news.id,
                               title=news.title[:50],
                               sentiment=sentiment['label'],
                               score=round(sentiment['score'], 2))
                    
                except Exception as e:
                    logger.error("news_analysis_lite_error",
                               id=news.id,
                               error=str(e))
                    continue
            
            await session.commit()
        
        logger.info("all_news_analyzed_lite", count=analyzed_count)
        return analyzed_count
    
    async def get_sentiment_statistics(self) -> Dict[str, Any]:
        """آمار احساسات | Sentiment statistics"""
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select, func
            
            result = await session.execute(
                select(func.count(NewsEvent.id))
                .where(NewsEvent.sentiment_score != None)
            )
            total = result.scalar()
            
            result = await session.execute(
                select(
                    NewsEvent.sentiment_label,
                    func.count(NewsEvent.id),
                    func.avg(NewsEvent.sentiment_score)
                )
                .where(NewsEvent.sentiment_label != None)
                .group_by(NewsEvent.sentiment_label)
            )
            by_label = {
                label: {
                    'count': count,
                    'avg_score': float(avg_score) if avg_score else 0
                }
                for label, count, avg_score in result.all()
            }
            
            result = await session.execute(
                select(func.avg(NewsEvent.sentiment_score))
                .where(NewsEvent.sentiment_score != None)
            )
            avg_score = result.scalar()
            
            return {
                'total_analyzed': total,
                'by_label': by_label,
                'avg_sentiment_score': float(avg_score) if avg_score else 0,
            }
