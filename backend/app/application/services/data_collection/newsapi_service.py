#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NewsAPI Service for Historical News Collection

جمع‌آوری اخبار تاریخی طلا از NewsAPI.org

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25 16:09:04 UTC
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import select

from app.infrastructure.database.base import AsyncSessionLocal
from app.infrastructure.database.models import NewsEvent
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class NewsAPIService:
    """
    سرویس جمع‌آوری اخبار تاریخی از NewsAPI
    
    Features:
    - دریافت اخبار از 1 ماه گذشته (free tier)
    - فیلتر کردن اخبار مرتبط با طلا
    - ذخیره در database
    - حذف duplicate ها
    
    Rate Limits (Free):
    - 100 requests/day
    - 1000 requests/month
    - News from last 1 month only
    """
    
    BASE_URL = "https://newsapi.org/v2/everything"
    
    # کلمات کلیدی طلا (بهترین‌ها)
    GOLD_KEYWORDS = [
        "gold price",
        "gold market",
        "gold trading",
        "precious metals gold",
        "gold investment",
        "gold bullion",
        "gold futures",
        "spot gold",
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize NewsAPI service
        
        Args:
            api_key: NewsAPI key (از .env یا manual)
        """
        self.api_key = api_key or settings.NEWSAPI_KEY
        
        if not self.api_key:
            logger.error("newsapi_key_not_configured")
            raise ValueError("NewsAPI key not found in .env")
        
        logger.info("newsapi_service_initialized")
    
    async def fetch_news(
        self,
        keyword: str,
        from_date: datetime,
        to_date: datetime,
        language: str = 'en',
        page_size: int = 100
    ) -> List[Dict]:
        """
        دریافت اخبار با یک keyword
        
        Args:
            keyword: کلمه کلیدی
            from_date: از تاریخ
            to_date: تا تاریخ
            language: زبان
            page_size: تعداد در هر صفحه (max: 100)
            
        Returns:
            لیست اخبار
        """
        logger.info("fetching_news",
                   keyword=keyword,
                   from_date=from_date.date(),
                   to_date=to_date.date())
        
        params = {
            'q': keyword,
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d'),
            'language': language,
            'sortBy': 'relevancy',  # یا 'publishedAt' یا 'popularity'
            'apiKey': self.api_key,
            'pageSize': page_size
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'ok':
                articles = data.get('articles', [])
                logger.info("news_fetched",
                           keyword=keyword,
                           count=len(articles),
                           total_results=data.get('totalResults', 0))
                return articles
            else:
                error_msg = data.get('message', 'Unknown error')
                logger.error("newsapi_error",
                           keyword=keyword,
                           error=error_msg)
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error("request_error", keyword=keyword, error=str(e))
            return []
    
    async def fetch_historical_news(
        self,
        days_back: int = 30,
        keywords: Optional[List[str]] = None
    ) -> int:
        """
        جمع‌آوری اخبار تاریخی
        
        Args:
            days_back: چند روز عقب (max: 30 for free tier)
            keywords: لیست کلمات کلیدی (پیش‌فرض: GOLD_KEYWORDS)
            
        Returns:
            تعداد اخبار جدید ذخیره شده
        """
        # Free tier فقط 1 ماه اخیر
        if days_back > 30:
            logger.warning("free_tier_limit",
                          requested=days_back,
                          limited_to=30)
            days_back = 30
        
        to_date = datetime.utcnow()
        from_date = to_date - timedelta(days=days_back)
        
        logger.info("starting_historical_fetch",
                   from_date=from_date.date(),
                   to_date=to_date.date(),
                   days=days_back)
        
        keywords_to_use = keywords or self.GOLD_KEYWORDS
        all_articles = []
        
        # جمع‌آوری با هر keyword
        for i, keyword in enumerate(keywords_to_use, 1):
            print(f"📰 [{i}/{len(keywords_to_use)}] Searching: '{keyword}'...")
            
            articles = await self.fetch_news(
                keyword=keyword,
                from_date=from_date,
                to_date=to_date
            )
            
            all_articles.extend(articles)
            print(f"   ✅ Found: {len(articles)} articles")
            
            # کمی صبر کنیم (rate limit)
            if i < len(keywords_to_use):
                import asyncio
                await asyncio.sleep(1)
        
        # حذف duplicate
        print(f"\n🔄 Removing duplicates...")
        unique_articles = self._deduplicate_articles(all_articles)
        print(f"   ✅ Unique articles: {len(unique_articles)}")
        
        # ذخیره
        print(f"\n💾 Saving to database...")
        saved = await self._save_articles(unique_articles)
        
        logger.info("historical_fetch_complete",
                   total_fetched=len(all_articles),
                   unique=len(unique_articles),
                   saved=saved)
        
        return saved
    
    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        حذف اخبار تکراری بر اساس URL
        
        Args:
            articles: لیست اخبار
            
        Returns:
            لیست بدون تکرار
        """
        seen_urls = set()
        seen_titles = set()
        unique = []
        
        for article in articles:
            url = article.get('url', '')
            title = article.get('title', '')
            
            # چک URL
            if url and url not in seen_urls:
                seen_urls.add(url)
                
                # چک title (برای اخباری که URL های مختلف دارن)
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    unique.append(article)
        
        return unique
    
    async def _save_articles(self, articles: List[Dict]) -> int:
        """
        ذخیره اخبار در database
        
        Args:
            articles: لیست اخبار
            
        Returns:
            تعداد اخبار ذخیره شده
        """
        saved_count = 0
        skipped_count = 0
        
        async with AsyncSessionLocal() as session:
            for article in articles:
                try:
                    url = article.get('url')
                    title = article.get('title')
                    
                    if not url or not title:
                        continue
                    
                    # چک وجود در database
                    result = await session.execute(
                        select(NewsEvent).where(NewsEvent.url == url)
                    )
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        skipped_count += 1
                        continue
                    
                    # Parse تاریخ
                    published_at_str = article.get('publishedAt', '')
                    try:
                        published_at = datetime.fromisoformat(
                            published_at_str.replace('Z', '+00:00')
                        )
                    except:
                        published_at = datetime.utcnow()
                    
                    # ساخت NewsEvent
                    news_event = NewsEvent(
                        title=title[:500],
                        description=article.get('description', '')[:2000] or '',
                        url=url[:500],
                        source='newsapi',
                        author=article.get('author', 'Unknown')[:200] or 'Unknown',
                        published_at=published_at,
                        category='market',
                        sentiment_score=None,  # بعداً با FinBERT
                        sentiment_label=None,
                        confidence=None
                    )
                    
                    session.add(news_event)
                    saved_count += 1
                    
                except Exception as e:
                    logger.warning("save_article_error",
                                 title=article.get('title', 'N/A')[:50],
                                 error=str(e))
                    continue
            
            await session.commit()
        
        logger.info("articles_saved",
                   saved=saved_count,
                   skipped=skipped_count)
        
        return saved_count


if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("\n" + "="*70)
        print("🧪 Testing NewsAPI Service")
        print("="*70 + "\n")
        
        service = NewsAPIService()
        
        # تست با 7 روز گذشته
        saved = await service.fetch_historical_news(days_back=7)
        
        print(f"\n✅ Test complete! Saved {saved} articles\n")
    
    asyncio.run(test())
