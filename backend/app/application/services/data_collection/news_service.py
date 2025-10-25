#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Price Analyzer - News Collection Service

Collects gold-related news from multiple RSS feeds.

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25
License: MIT
"""

from datetime import datetime, UTC, timedelta
from typing import List, Dict, Any, Optional
import feedparser
import requests
from bs4 import BeautifulSoup

from app.core.logging import get_logger
from app.infrastructure.database.base import AsyncSessionLocal
from app.infrastructure.database.models.news_event import NewsEvent

logger = get_logger(__name__)


class NewsService:
    """
    News Collection Service for Gold Market.
    
    Fetches news from multiple RSS feeds:
    - Kitco News (Gold-specific)
    - World Gold Council (Industry news)
    - Reuters Commodities (Market news)
    
    Author: Hoseyn Doulabi (@hoseynd-ai)
    Created: 2025-10-25
    """
    
    RSS_FEEDS = {
        'kitco': {
            'url': 'https://www.kitco.com/rss/gold.xml',
            'name': 'Kitco Gold News',
            'category': 'gold_market',
        },
        'goldorg': {
            'url': 'https://www.gold.org/feed',
            'name': 'World Gold Council',
            'category': 'gold_industry',
        },
        'reuters': {
            'url': 'https://www.reuters.com/rssfeed/commoditiesNews',
            'name': 'Reuters Commodities',
            'category': 'commodities',
        },
    }
    
    GOLD_KEYWORDS = [
        'gold', 'precious metal', 'bullion', 'xau',
        'gold price', 'gold market', 'gold trading',
        'federal reserve', 'inflation', 'interest rate',
        'dollar', 'usd', 'treasury', 'fed', 'central bank',
        'safe haven', 'hedge', 'commodities',
    ]
    
    def __init__(self):
        """Initialize News Service."""
        logger.info("news_service_initialized", feeds=len(self.RSS_FEEDS))
    
    def fetch_rss_feed(self, feed_url: str) -> Optional[feedparser.FeedParserDict]:
        """
        Fetch RSS feed from URL.
        
        Args:
            feed_url: RSS feed URL
            
        Returns:
            Parsed feed or None if failed
        """
        try:
            logger.info("fetching_rss_feed", url=feed_url)
            
            headers = {
                'User-Agent': 'Gold Price Analyzer/1.0 (+https://github.com/hoseynd-ai/gold-price-analyzer)'
            }
            
            response = requests.get(feed_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                
                if feed.bozo:
                    logger.warning("rss_parse_warning", 
                                 url=feed_url,
                                 exception=str(feed.bozo_exception))
                
                logger.info("rss_feed_fetched", 
                           url=feed_url, 
                           entries=len(feed.entries))
                
                return feed
            else:
                logger.warning("rss_fetch_failed", 
                              url=feed_url, 
                              status=response.status_code)
                return None
                
        except requests.exceptions.Timeout:
            logger.error("rss_fetch_timeout", url=feed_url)
            return None
        except Exception as e:
            logger.error("rss_fetch_error", url=feed_url, error=str(e))
            return None
    
    def is_gold_related(self, title: str, description: str) -> bool:
        """
        Check if article is gold-related using keywords.
        
        Args:
            title: Article title
            description: Article description
            
        Returns:
            True if article mentions gold-related keywords
        """
        text = f"{title} {description}".lower()
        
        for keyword in self.GOLD_KEYWORDS:
            if keyword.lower() in text:
                logger.debug("gold_keyword_found", keyword=keyword)
                return True
        
        return False
    
    def parse_feed_entry(self, entry: Any, source: str) -> Optional[Dict[str, Any]]:
        """
        Parse RSS feed entry to NewsEvent format.
        
        Args:
            entry: feedparser entry object
            source: Source identifier (kitco, goldorg, reuters)
            
        Returns:
            Dictionary with NewsEvent fields or None if parsing failed
        """
        try:
            # Parse published date
            published = entry.get('published_parsed') or entry.get('updated_parsed')
            if published:
                pub_date = datetime(*published[:6], tzinfo=UTC)
            else:
                pub_date = datetime.now(UTC)
            
            # Extract content
            content = ''
            if entry.get('content'):
                content = entry.content[0].get('value', '')
            elif entry.get('summary'):
                content = entry.summary
            
            # Extract image URL
            image_url = None
            if entry.get('media_content'):
                image_url = entry.media_content[0].get('url')
            elif entry.get('media_thumbnail'):
                image_url = entry.media_thumbnail[0].get('url')
            
            # Build news data
            news_data = {
                'title': entry.get('title', 'No Title')[:500],
                'description': entry.get('summary', entry.get('description', ''))[:1000],
                'content': content,
                'url': entry.get('link', ''),
                'image_url': image_url,
                'published_at': pub_date,
                'source': source,
                'author': entry.get('author', 'Unknown')[:200],
                'category': self.RSS_FEEDS[source]['category'],
                
                # Sentiment fields (to be calculated later by ML)
                'sentiment_score': None,
                'sentiment_label': None,
                'confidence': None,
                'price_impact': None,
                'impact_score': None,
            }
            
            return news_data
            
        except Exception as e:
            logger.error("parse_entry_error", 
                        source=source, 
                        error=str(e),
                        entry_title=entry.get('title', 'Unknown')[:50])
            return None
    
    async def fetch_and_save_news(self, 
                                  hours_back: int = 24, 
                                  filter_gold: bool = True) -> int:
        """
        Fetch news from all RSS feeds and save to database.
        
        Args:
            hours_back: How many hours back to fetch (default: 24)
            filter_gold: Only save gold-related articles (default: True)
            
        Returns:
            Number of articles saved
        """
        logger.info("fetching_news", 
                   hours_back=hours_back, 
                   filter_gold=filter_gold,
                   sources=list(self.RSS_FEEDS.keys()))
        
        cutoff_time = datetime.now(UTC) - timedelta(hours=hours_back)
        saved_count = 0
        skipped_old = 0
        skipped_not_gold = 0
        skipped_duplicate = 0
        
        for source_key, source_info in self.RSS_FEEDS.items():
            try:
                logger.info("processing_source", 
                           source=source_key,
                           name=source_info['name'])
                
                # Fetch feed
                feed = self.fetch_rss_feed(source_info['url'])
                
                if not feed or not feed.entries:
                    logger.warning("no_entries", source=source_key)
                    continue
                
                logger.info("processing_entries", 
                           source=source_key,
                           count=len(feed.entries))
                
                # Process entries
                async with AsyncSessionLocal() as session:
                    for entry in feed.entries:
                        try:
                            # Parse entry
                            news_data = self.parse_feed_entry(entry, source_key)
                            
                            if not news_data:
                                continue
                            
                            # Skip old articles
                            if news_data['published_at'] < cutoff_time:
                                skipped_old += 1
                                logger.debug("article_too_old", 
                                           title=news_data['title'][:50],
                                           published=news_data['published_at'])
                                continue
                            
                            # Filter gold-related
                            if filter_gold:
                                if not self.is_gold_related(
                                    news_data['title'], 
                                    news_data['description']
                                ):
                                    skipped_not_gold += 1
                                    logger.debug("not_gold_related", 
                                               title=news_data['title'][:50])
                                    continue
                            
                            # Check if exists (by URL)
                            from sqlalchemy import select
                            result = await session.execute(
                                select(NewsEvent).where(
                                    NewsEvent.url == news_data['url']
                                )
                            )
                            
                            existing = result.scalar_one_or_none()
                            if existing:
                                skipped_duplicate += 1
                                logger.debug("news_exists", 
                                           url=news_data['url'],
                                           id=existing.id)
                                continue
                            
                            # Save new article
                            news = NewsEvent(**news_data)
                            session.add(news)
                            saved_count += 1
                            
                            logger.info("news_saved", 
                                      title=news_data['title'][:50],
                                      source=source_key,
                                      published=news_data['published_at'])
                            
                        except Exception as e:
                            logger.error("process_entry_error", 
                                       source=source_key, 
                                       error=str(e),
                                       exc_info=True)
                            continue
                    
                    await session.commit()
                
            except Exception as e:
                logger.error("fetch_source_error", 
                           source=source_key, 
                           error=str(e),
                           exc_info=True)
                continue
        
        logger.info("news_fetch_complete", 
                   saved=saved_count,
                   skipped_old=skipped_old,
                   skipped_not_gold=skipped_not_gold,
                   skipped_duplicate=skipped_duplicate)
        
        return saved_count
    
    async def get_latest_news(self, limit: int = 10, 
                             source: Optional[str] = None) -> List[NewsEvent]:
        """
        Get latest news articles from database.
        
        Args:
            limit: Maximum number of articles to return
            source: Filter by source (optional)
            
        Returns:
            List of NewsEvent objects
        """
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            
            query = select(NewsEvent).order_by(NewsEvent.published_at.desc())
            
            if source:
                query = query.where(NewsEvent.source == source)
            
            query = query.limit(limit)
            
            result = await session.execute(query)
            articles = result.scalars().all()
            
            logger.info("latest_news_fetched", 
                       count=len(articles),
                       source=source)
            
            return articles
    
    async def get_news_by_timerange(self, 
                                    start_time: datetime,
                                    end_time: datetime) -> List[NewsEvent]:
        """
        Get news articles within time range.
        
        Args:
            start_time: Start datetime (UTC)
            end_time: End datetime (UTC)
            
        Returns:
            List of NewsEvent objects
        """
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            
            result = await session.execute(
                select(NewsEvent)
                .where(NewsEvent.published_at >= start_time)
                .where(NewsEvent.published_at <= end_time)
                .order_by(NewsEvent.published_at.desc())
            )
            
            articles = result.scalars().all()
            
            logger.info("news_by_timerange_fetched",
                       count=len(articles),
                       start=start_time,
                       end=end_time)
            
            return articles
    
    async def get_news_stats(self) -> Dict[str, Any]:
        """
        Get news database statistics.
        
        Returns:
            Dictionary with statistics
        """
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select, func
            
            # Total count
            result = await session.execute(
                select(func.count(NewsEvent.id))
            )
            total = result.scalar()
            
            # By source
            result = await session.execute(
                select(
                    NewsEvent.source,
                    func.count(NewsEvent.id)
                ).group_by(NewsEvent.source)
            )
            by_source = {source: count for source, count in result.all()}
            
            # Date range
            result = await session.execute(
                select(
                    func.min(NewsEvent.published_at),
                    func.max(NewsEvent.published_at)
                )
            )
            min_date, max_date = result.first()
            
            stats = {
                'total': total,
                'by_source': by_source,
                'oldest': min_date,
                'newest': max_date,
            }
            
            logger.info("news_stats_calculated", stats=stats)
            
            return stats
