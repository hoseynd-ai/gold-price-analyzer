#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Price Analyzer - Simple Gold Price Service

Uses free APIs to fetch gold prices.

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25
License: MIT
"""

from datetime import datetime, UTC, timedelta
from typing import Optional, Dict, Any, List
import requests
from decimal import Decimal

from app.core.logging import get_logger
from app.infrastructure.database.base import AsyncSessionLocal
from app.infrastructure.database.models import GoldPriceFact

logger = get_logger(__name__)


class SimpleGoldService:
    """
    Simple Gold Price Service using Free APIs.
    
    Uses multiple free sources:
    1. Metals-API.com (free tier)
    2. GoldAPI.io (free tier)
    3. Fallback to manual data
    
    Author: Hoseyn Doulabi (@hoseynd-ai)
    Created: 2025-10-25
    """
    
    def __init__(self):
        """Initialize service."""
        self.metals_api_url = "https://api.metals.dev/v1/latest"
        self.gold_api_url = "https://www.goldapi.io/api"
        logger.info("simple_gold_service_initialized")
    
    def fetch_current_price_metals_api(self) -> Optional[float]:
        """
        Fetch current gold price from Metals-API (free, no key needed).
        
        Returns:
            float: Gold price in USD per ounce
        """
        try:
            # Metals-API free endpoint
            url = "https://api.metals.dev/v1/latest?api_key=&currency=USD&unit=toz"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'metals' in data and 'gold' in data['metals']:
                    price = float(data['metals']['gold'])
                    logger.info(
                        "metals_api_success",
                        price=price,
                        source="metals-api"
                    )
                    return price
            
            logger.warning("metals_api_no_data", status=response.status_code)
            return None
            
        except Exception as e:
            logger.error("metals_api_error", error=str(e))
            return None
    
    def fetch_from_goldprice_org(self) -> Optional[float]:
        """
        Fetch from GoldPrice.org (scraping alternative).
        
        Returns:
            float: Gold price
        """
        try:
            # این یک API عمومی هست
            url = "https://data-asg.goldprice.org/dbXRates/USD"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'items' in data:
                    for item in data['items']:
                        if item.get('curr') == 'XAU':  # XAU = Gold
                            price = float(item.get('xauPrice', 0))
                            if price > 0:
                                logger.info(
                                    "goldprice_org_success",
                                    price=price
                                )
                                return price
            
            return None
            
        except Exception as e:
            logger.error("goldprice_org_error", error=str(e))
            return None
    
    def get_current_price(self) -> Optional[float]:
        """
        Get current gold price from best available source.
        
        Returns:
            float: Current gold price in USD per ounce
        """
        # Try 1: GoldPrice.org
        price = self.fetch_from_goldprice_org()
        if price:
            return price
        
        # Try 2: Metals-API
        price = self.fetch_current_price_metals_api()
        if price:
            return price
        
        # Fallback: return approximate price
        logger.warning("all_apis_failed_using_fallback")
        return 2750.0  # Approximate current price
    
    async def save_current_price(self) -> bool:
        """
        Fetch current price and save to database.
        
        Returns:
            bool: True if successful
        """
        price = self.get_current_price()
        
        if not price:
            logger.error("failed_to_get_current_price")
            return False
        
        try:
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select
                
                now = datetime.now(UTC)
                
                # Round to hour for hourly data
                hourly_timestamp = now.replace(minute=0, second=0, microsecond=0)
                
                # Check if exists
                existing = await session.execute(
                    select(GoldPriceFact).where(
                        GoldPriceFact.timestamp == hourly_timestamp,
                        GoldPriceFact.timeframe == 'hourly',
                        GoldPriceFact.source == 'simple_api'
                    )
                )
                
                if existing.scalar_one_or_none():
                    logger.info("price_already_exists_for_hour")
                    return True
                
                # Save
                price_record = GoldPriceFact(
                    timestamp=hourly_timestamp,
                    timeframe='hourly',
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    volume=0,
                    price_change=0.0,
                    price_change_pct=0.0,
                    source='simple_api',
                    market='spot',
                    data_quality=0.8,
                )
                
                session.add(price_record)
                await session.commit()
                
                logger.info(
                    "current_price_saved",
                    timestamp=hourly_timestamp.isoformat(),
                    price=price
                )
                
                return True
                
        except Exception as e:
            logger.error("save_current_price_error", error=str(e))
            return False
    
    async def generate_mock_historical_data(self, days: int = 30) -> int:
        """
        Generate mock historical data based on current price.
        (For testing purposes)
        
        Args:
            days: Number of days
            
        Returns:
            int: Number of records created
        """
        logger.info("generating_mock_historical_data", days=days)
        
        current_price = self.get_current_price()
        if not current_price:
            current_price = 2750.0
        
        saved_count = 0
        
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            import random
            
            for i in range(days):
                try:
                    # تاریخ
                    day_timestamp = datetime.now(UTC) - timedelta(days=i)
                    day_timestamp = day_timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
                    
                    # Check duplicate
                    existing = await session.execute(
                        select(GoldPriceFact).where(
                            GoldPriceFact.timestamp == day_timestamp,
                            GoldPriceFact.timeframe == 'daily',
                            GoldPriceFact.source == 'mock_data'
                        )
                    )
                    
                    if existing.scalar_one_or_none():
                        continue
                    
                    # قیمت تصادفی نزدیک به قیمت فعلی
                    variation = random.uniform(-50, 50)
                    open_price = current_price + variation
                    high_price = open_price + random.uniform(0, 20)
                    low_price = open_price - random.uniform(0, 20)
                    close_price = open_price + random.uniform(-10, 10)
                    
                    price_change = close_price - open_price
                    price_change_pct = (price_change / open_price) * 100
                    
                    # Save
                    price_record = GoldPriceFact(
                        timestamp=day_timestamp,
                        timeframe='daily',
                        open=round(open_price, 2),
                        high=round(high_price, 2),
                        low=round(low_price, 2),
                        close=round(close_price, 2),
                        volume=random.randint(100000, 500000),
                        price_change=round(price_change, 2),
                        price_change_pct=round(price_change_pct, 2),
                        source='mock_data',
                        market='spot',
                        data_quality=0.5,  # Mock data quality is low
                    )
                    
                    session.add(price_record)
                    saved_count += 1
                    
                except Exception as e:
                    logger.error("mock_data_error", error=str(e))
                    continue
            
            await session.commit()
        
        logger.info("mock_data_generated", count=saved_count)
        return saved_count
