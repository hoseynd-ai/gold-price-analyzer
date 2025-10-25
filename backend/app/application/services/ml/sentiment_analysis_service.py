#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحلیل احساسات اخبار - News Sentiment Analysis Service

استفاده از مدل FinBERT برای تحلیل احساسات اخبار مالی
Uses FinBERT model for financial news sentiment analysis

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25
License: MIT
"""

from typing import Dict, Any, Optional, List
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from datetime import datetime, UTC

from app.core.logging import get_logger
from app.infrastructure.database.base import AsyncSessionLocal
from app.infrastructure.database.models.news_event import NewsEvent

logger = get_logger(__name__)


class SentimentAnalysisService:
    """
    سرویس تحلیل احساسات | Sentiment Analysis Service
    
    استفاده از FinBERT برای تحلیل احساسات اخبار مالی
    Uses FinBERT for financial news sentiment analysis
    
    مدل | Model: ProsusAI/finbert
    
    خروجی | Output:
        - positive (مثبت): 0.5 to 1.0
        - neutral (خنثی): -0.5 to 0.5
        - negative (منفی): -1.0 to -0.5
    
    Author: Hoseyn Doulabi (@hoseynd-ai)
    Created: 2025-10-25
    """
    
    MODEL_NAME = "ProsusAI/finbert"
    
    # نگاشت برچسب‌ها به امتیاز | Label to score mapping
    LABEL_SCORES = {
        'positive': 1.0,
        'neutral': 0.0,
        'negative': -1.0,
    }
    
    # آستانه‌های تصمیم‌گیری | Decision thresholds
    THRESHOLDS = {
        'very_bullish': 0.7,
        'bullish': 0.3,
        'neutral_upper': 0.3,
        'neutral_lower': -0.3,
        'bearish': -0.3,
        'very_bearish': -0.7,
    }
    
    def __init__(self, model_name: str = None):
        """
        مقداردهی اولیه | Initialize sentiment analyzer
        
        Args:
            model_name: نام مدل (پیش‌فرض: FinBERT) | Model name (default: FinBERT)
        """
        self.model_name = model_name or self.MODEL_NAME
        self.tokenizer = None
        self.model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        logger.info("sentiment_service_initialized", 
                   model=self.model_name,
                   device=self.device)
    
    def load_model(self):
        """
        بارگذاری مدل FinBERT | Load FinBERT model
        
        اولین بار چند دقیقه طول می‌کشد (دانلود مدل)
        First time takes a few minutes (downloading model)
        """
        if self.model is not None:
            logger.debug("model_already_loaded")
            return
        
        try:
            logger.info("loading_finbert_model", model=self.model_name)
            
            # بارگذاری tokenizer | Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # بارگذاری مدل | Load model
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name
            )
            
            # انتقال به GPU/CPU | Move to device
            self.model.to(self.device)
            self.model.eval()  # حالت ارزیابی | Evaluation mode
            
            logger.info("finbert_model_loaded", 
                       model=self.model_name,
                       device=self.device)
            
        except Exception as e:
            logger.error("model_load_error", error=str(e))
            raise
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        تحلیل احساسات یک متن | Analyze sentiment of text
        
        Args:
            text: متن ورودی (عنوان یا توضیحات خبر) | Input text (news title or description)
            
        Returns:
            dict: نتیجه تحلیل | Analysis result
            {
                'label': 'positive' | 'neutral' | 'negative',
                'score': float (-1.0 to 1.0),
                'confidence': float (0.0 to 1.0),
                'probabilities': {
                    'positive': float,
                    'neutral': float,
                    'negative': float
                },
                'price_impact': 'bullish' | 'bearish' | 'neutral',
                'impact_score': float (0.0 to 1.0)
            }
        """
        # بارگذاری مدل در صورت نیاز | Load model if needed
        if self.model is None:
            self.load_model()
        
        try:
            # Tokenize کردن ورودی | Tokenize input
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.device)
            
            # پیش‌بینی | Predict
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # استخراج احتمالات | Extract probabilities
            probs = predictions[0].cpu().numpy()
            
            # نگاشت به برچسب‌ها | Map to labels
            # FinBERT output order: [positive, negative, neutral]
            probabilities = {
                'positive': float(probs[0]),
                'negative': float(probs[1]),
                'neutral': float(probs[2]),
            }
            
            # یافتن برچسب با بیشترین احتمال | Find label with highest probability
            label = max(probabilities, key=probabilities.get)
            confidence = probabilities[label]
            
            # محاسبه امتیاز (-1 تا 1) | Calculate score (-1 to 1)
            score = (
                probabilities['positive'] * 1.0 +
                probabilities['neutral'] * 0.0 +
                probabilities['negative'] * -1.0
            )
            
            # تعیین تأثیر بر قیمت | Determine price impact
            price_impact, impact_score = self._calculate_price_impact(score, confidence)
            
            result = {
                'label': label,
                'score': round(score, 3),
                'confidence': round(confidence, 3),
                'probabilities': {k: round(v, 3) for k, v in probabilities.items()},
                'price_impact': price_impact,
                'impact_score': round(impact_score, 3),
            }
            
            logger.debug("sentiment_analyzed", 
                        text=text[:50],
                        label=label,
                        score=round(score, 2))
            
            return result
            
        except Exception as e:
            logger.error("sentiment_analysis_error", 
                        text=text[:50],
                        error=str(e))
            raise
    
    def _calculate_price_impact(self, score: float, confidence: float) -> tuple:
        """
        محاسبه تأثیر احتمالی بر قیمت | Calculate likely price impact
        
        Args:
            score: امتیاز احساسات (-1 تا 1) | Sentiment score (-1 to 1)
            confidence: اطمینان مدل (0 تا 1) | Model confidence (0 to 1)
            
        Returns:
            tuple: (price_impact, impact_score)
        """
        # تعیین جهت | Determine direction
        if score >= self.THRESHOLDS['very_bullish']:
            impact = 'very_bullish'
        elif score >= self.THRESHOLDS['bullish']:
            impact = 'bullish'
        elif score <= self.THRESHOLDS['very_bearish']:
            impact = 'very_bearish'
        elif score <= self.THRESHOLDS['bearish']:
            impact = 'bearish'
        else:
            impact = 'neutral'
        
        # محاسبه شدت تأثیر | Calculate impact magnitude
        # ترکیب امتیاز احساسات و اطمینان | Combine sentiment score and confidence
        impact_score = abs(score) * confidence
        
        return impact, impact_score
    
    async def analyze_news_article(self, news_id: int) -> Dict[str, Any]:
        """
        تحلیل احساسات یک خبر در دیتابیس | Analyze sentiment of a news article in database
        
        Args:
            news_id: شناسه خبر | News article ID
            
        Returns:
            dict: نتیجه تحلیل | Analysis result
        """
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            
            # خواندن خبر | Read news
            result = await session.execute(
                select(NewsEvent).where(NewsEvent.id == news_id)
            )
            news = result.scalar_one_or_none()
            
            if not news:
                raise ValueError(f"News article {news_id} not found")
            
            # ترکیب عنوان و توضیحات | Combine title and description
            text = f"{news.title}. {news.description or ''}"
            
            # تحلیل | Analyze
            sentiment = self.analyze_text(text)
            
            # بروزرسانی دیتابیس | Update database
            news.sentiment_score = sentiment['score']
            news.sentiment_label = sentiment['label']
            news.confidence = sentiment['confidence']
            news.price_impact = sentiment['price_impact']
            news.impact_score = sentiment['impact_score']
            
            await session.commit()
            
            logger.info("news_sentiment_updated",
                       news_id=news_id,
                       title=news.title[:50],
                       sentiment=sentiment['label'],
                       score=sentiment['score'])
            
            return sentiment
    
    async def analyze_all_news(self, force_reanalyze: bool = False) -> int:
        """
        تحلیل احساسات تمام اخبار | Analyze sentiment of all news articles
        
        Args:
            force_reanalyze: تحلیل مجدد اخبار قبلی | Re-analyze previously analyzed news
            
        Returns:
            int: تعداد اخبار تحلیل شده | Number of articles analyzed
        """
        logger.info("analyzing_all_news", force_reanalyze=force_reanalyze)
        
        analyzed_count = 0
        
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            
            # خواندن اخبار | Read news
            query = select(NewsEvent)
            
            if not force_reanalyze:
                # فقط اخباری که تحلیل نشده‌اند | Only unanalyzed news
                query = query.where(NewsEvent.sentiment_score == None)
            
            result = await session.execute(query)
            news_articles = result.scalars().all()
            
            logger.info("news_articles_found", count=len(news_articles))
            
            for news in news_articles:
                try:
                    # ترکیب عنوان و توضیحات | Combine title and description
                    text = f"{news.title}. {news.description or ''}"
                    
                    # تحلیل | Analyze
                    sentiment = self.analyze_text(text)
                    
                    # بروزرسانی | Update
                    news.sentiment_score = sentiment['score']
                    news.sentiment_label = sentiment['label']
                    news.confidence = sentiment['confidence']
                    news.price_impact = sentiment['price_impact']
                    news.impact_score = sentiment['impact_score']
                    
                    analyzed_count += 1
                    
                    logger.info("news_analyzed",
                               id=news.id,
                               title=news.title[:50],
                               sentiment=sentiment['label'],
                               score=round(sentiment['score'], 2))
                    
                except Exception as e:
                    logger.error("news_analysis_error",
                               id=news.id,
                               title=news.title[:50],
                               error=str(e))
                    continue
            
            await session.commit()
        
        logger.info("all_news_analyzed", count=analyzed_count)
        
        return analyzed_count
    
    async def get_sentiment_statistics(self) -> Dict[str, Any]:
        """
        آمار احساسات اخبار | Get sentiment statistics
        
        Returns:
            dict: آمار کامل | Complete statistics
        """
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select, func
            
            # تعداد کل | Total count
            result = await session.execute(
                select(func.count(NewsEvent.id))
                .where(NewsEvent.sentiment_score != None)
            )
            total = result.scalar()
            
            # بر اساس برچسب | By label
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
            
            # میانگین کلی | Overall average
            result = await session.execute(
                select(func.avg(NewsEvent.sentiment_score))
                .where(NewsEvent.sentiment_score != None)
            )
            avg_score = result.scalar()
            
            stats = {
                'total_analyzed': total,
                'by_label': by_label,
                'avg_sentiment_score': float(avg_score) if avg_score else 0,
            }
            
            logger.info("sentiment_stats_calculated", stats=stats)
            
            return stats
