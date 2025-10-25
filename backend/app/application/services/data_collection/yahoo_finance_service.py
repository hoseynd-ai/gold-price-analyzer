#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Price Analyzer - Yahoo Finance Service

Fetches gold price data from Yahoo Finance.

Author: Hoseyn Doulabi (@hoseynd-ai)
Project Manager: Hoseyn Doulabi
Repository: https://github.com/hoseynd-ai/gold-price-analyzer
Created: 2025-10-25
License: MIT
"""

from datetime import datetime, UTC, timedelta
from typing import List, Dict, Any, Optional
import yfinance as yf
import pandas as pd

from app.core.logging import get_logger
from app.infrastructure.database.base import AsyncSessionLocal
from app.infrastructure.database.models import GoldPriceFact

logger = get_logger(__name__)


class YahooFinanceService:
    """
    Yahoo Finance Service for Gold Price Data.
    
    Fetches gold price data (GC=F) from Yahoo Finance.
    
    Symbols:
        - GC=F: Gold Futures
        - GLD: SPDR Gold Trust ETF
    
    Author: Hoseyn Doulabi (@hoseynd-ai)
    Created: 2025-10-25
    
    Example:
        >>> service = YahooFinanceService()
        >>> await service.fetch_and_save_daily_prices(days=30)
    """
    
    def __init__(self, symbol: str = "GC=F"):
        """
        Initialize Yahoo Finance Service.
        
        Args:
            symbol: Yahoo Finance symbol (default: GC=F for Gold Futures)
        """
        self.symbol = symbol
        self.source = "yahoo_finance"
        logger.info(
            "yahoo_finance_service_initialized",
            symbol=symbol,
            author="Hoseyn Doulabi (@hoseynd-ai)"
        )
    
    def fetch_historical_data(
        self,
        period: str = "1mo",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical gold price data.
        
        Args:
            period: Data period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '5y')
            interval: Data interval ('1m', '5m', '1h', '1d', '1wk', '1mo')
        
        Returns:
            pd.DataFrame: Historical price data
            
        Author: Hoseyn Doulabi (@hoseynd-ai)
        Created: 2025-10-25
        """
        logger.info(
            "fetching_yahoo_finance_data",
            symbol=self.symbol,
            period=period,
            interval=interval
        )
        
        try:
            # دریافت داده
            ticker = yf.Ticker(self.symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.warning("yahoo_finance_no_data", symbol=self.symbol)
                return pd.DataFrame()
            
            logger.info(
                "yahoo_finance_data_fetched",
                symbol=self.symbol,
                rows=len(data)
            )
            
            return data
            
        except Exception as e:
            logger.error(
                "yahoo_finance_fetch_failed",
                symbol=self.symbol,
                error=str(e),
                exc_info=True
            )
            return pd.DataFrame()
    
    def _convert_to_price_dict(
        self,
        row: pd.Series,
        timestamp: datetime,
        timeframe: str
    ) -> Dict[str, Any]:
        """
        Convert pandas row to GoldPriceFact dictionary.
        
        Args:
            row: Pandas series row
            timestamp: Timestamp
            timeframe: Timeframe (hourly, daily, etc.)
        
        Returns:
            dict: Dictionary for GoldPriceFact model
            
        Author: Hoseyn Doulabi (@hoseynd-ai)
        Created: 2025-10-25
        """
        # محاسبه تغییر قیمت
        price_change = row['Close'] - row['Open']
        price_change_pct = (price_change / row['Open']) * 100 if row['Open'] != 0 else 0
        
        return {
            'timestamp': timestamp,
            'timeframe': timeframe,
            'open': float(row['Open']),
            'high': float(row['High']),
            'low': float(row['Low']),
            'close': float(row['Close']),
            'volume': int(row['Volume']) if pd.notna(row['Volume']) else 0,
            'price_change': float(price_change),
            'price_change_pct': round(float(price_change_pct), 2),
            'source': self.source,
            'market': 'futures',
            'data_quality': 1.0,
        }
    
    async def fetch_and_save_daily_prices(
        self,
        days: int = 30
    ) -> int:
        """
        Fetch and save daily gold prices.
        
        Args:
            days: Number of days to fetch (max 730)
        
        Returns:
            int: Number of records saved
            
        Author: Hoseyn Doulabi (@hoseynd-ai)
        Created: 2025-10-25
        """
        logger.info(
            "fetching_daily_prices",
            days=days,
            symbol=self.symbol
        )
        
        # دریافت داده
        period = f"{days}d" if days <= 59 else f"{days//30}mo"
        data = self.fetch_historical_data(period=period, interval="1d")
        
        if data.empty:
            logger.warning("no_daily_data_to_save")
            return 0
        
        # ذخیره در database
        saved_count = 0
        
        async with AsyncSessionLocal() as session:
            for timestamp, row in data.iterrows():
                try:
                    # تبدیل timestamp
                    if isinstance(timestamp, pd.Timestamp):
                        timestamp = timestamp.to_pydatetime()
                    
                    # اطمینان از timezone
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=UTC)
                    
                    # ساخت dictionary
                    price_data = self._convert_to_price_dict(
                        row,
                        timestamp,
                        'daily'
                    )
                    
                    # چک کردن وجود داده
                    from sqlalchemy import select
                    existing = await session.execute(
                        select(GoldPriceFact).where(
                            GoldPriceFact.timestamp == timestamp,
                            GoldPriceFact.timeframe == 'daily',
                            GoldPriceFact.source == self.source
                        )
                    )
                    
                    if existing.scalar_one_or_none():
                        logger.debug(
                            "price_already_exists",
                            timestamp=timestamp.isoformat()
                        )
                        continue
                    
                    # ذخیره
                    price = GoldPriceFact(**price_data)
                    session.add(price)
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(
                        "failed_to_save_price",
                        timestamp=str(timestamp),
                        error=str(e)
                    )
                    continue
            
            # Commit همه
            await session.commit()
        
        logger.info(
            "daily_prices_saved",
            total_fetched=len(data),
            saved=saved_count,
            author="Hoseyn Doulabi (@hoseynd-ai)"
        )
        
        return saved_count
    
    async def fetch_and_save_hourly_prices(
        self,
        days: int = 7
    ) -> int:
        """
        Fetch and save hourly gold prices.
        
        Args:
            days: Number of days to fetch (max 730)
        
        Returns:
            int: Number of records saved
            
        Author: Hoseyn Doulabi (@hoseynd-ai)
        Created: 2025-10-25
        """
        logger.info(
            "fetching_hourly_prices",
            days=days,
            symbol=self.symbol
        )
        
        # دریافت داده
        period = f"{days}d"
        data = self.fetch_historical_data(period=period, interval="1h")
        
        if data.empty:
            logger.warning("no_hourly_data_to_save")
            return 0
        
        # ذخیره در database
        saved_count = 0
        
        async with AsyncSessionLocal() as session:
            for timestamp, row in data.iterrows():
                try:
                    # تبدیل timestamp
                    if isinstance(timestamp, pd.Timestamp):
                        timestamp = timestamp.to_pydatetime()
                    
                    # اطمینان از timezone
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=UTC)
                    
                    # ساخت dictionary
                    price_data = self._convert_to_price_dict(
                        row,
                        timestamp,
                        'hourly'
                    )
                    
                    # چک کردن وجود داده
                    from sqlalchemy import select
                    existing = await session.execute(
                        select(GoldPriceFact).where(
                            GoldPriceFact.timestamp == timestamp,
                            GoldPriceFact.timeframe == 'hourly',
                            GoldPriceFact.source == self.source
                        )
                    )
                    
                    if existing.scalar_one_or_none():
                        continue
                    
                    # ذخیره
                    price = GoldPriceFact(**price_data)
                    session.add(price)
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(
                        "failed_to_save_hourly_price",
                        timestamp=str(timestamp),
                        error=str(e)
                    )
                    continue
            
            # Commit همه
            await session.commit()
        
        logger.info(
            "hourly_prices_saved",
            total_fetched=len(data),
            saved=saved_count,
            author="Hoseyn Doulabi (@hoseynd-ai)"
        )
        
        return saved_count
    
    def get_current_price(self) -> Optional[float]:
        """
        Get current gold price.
        
        Returns:
            float: Current price or None
            
        Author: Hoseyn Doulabi (@hoseynd-ai)
        Created: 2025-10-25
        """
        try:
            ticker = yf.Ticker(self.symbol)
            data = ticker.history(period="1d", interval="1m")
            
            if not data.empty:
                current_price = float(data['Close'].iloc[-1])
                logger.info(
                    "current_price_fetched",
                    symbol=self.symbol,
                    price=current_price
                )
                return current_price
            
            return None
            
        except Exception as e:
            logger.error(
                "failed_to_get_current_price",
                symbol=self.symbol,
                error=str(e)
            )
            return None
