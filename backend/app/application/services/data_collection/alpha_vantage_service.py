#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Price Analyzer - Alpha Vantage Service

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25
"""

from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
import requests

from app.core.config import settings
from app.core.logging import get_logger
from app.infrastructure.database.base import AsyncSessionLocal
from app.infrastructure.database.models import GoldPriceFact

logger = get_logger(__name__)


class AlphaVantageService:
    """Alpha Vantage Service for Gold OHLCV Data."""
    
    BASE_URL = "https://www.alphavantage.co/query"
    SYMBOL = "GLD"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Alpha Vantage Service."""
        self.api_key = api_key or settings.ALPHA_VANTAGE_API_KEY
        
        if not self.api_key:
            logger.error("alpha_vantage_api_key_missing")
            raise ValueError("Alpha Vantage API key is required")
        
        logger.info("alpha_vantage_service_initialized")
    
    def fetch_daily_time_series(self, outputsize: str = "compact") -> Dict[str, Any]:
        """Fetch daily time series data."""
        logger.info("fetching_alpha_vantage_daily", symbol=self.SYMBOL)
        
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': self.SYMBOL,
            'outputsize': outputsize,
            'apikey': self.api_key,
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if "Error Message" in data:
                    logger.error("alpha_vantage_error", error=data["Error Message"])
                    return {}
                
                if "Note" in data:
                    logger.warning("alpha_vantage_rate_limit", note=data["Note"])
                    return {}
                
                if "Time Series (Daily)" in data:
                    logger.info("alpha_vantage_data_fetched", days=len(data["Time Series (Daily)"]))
                    return data
                
                logger.warning("alpha_vantage_unexpected_response")
                return {}
            
            logger.error("alpha_vantage_request_failed", status=response.status_code)
            return {}
            
        except Exception as e:
            logger.error("alpha_vantage_fetch_error", error=str(e))
            return {}
    
    def parse_time_series_to_candles(self, time_series_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Alpha Vantage time series to candle format."""
        if "Time Series (Daily)" not in time_series_data:
            return []
        
        candles = []
        
        for date_str, daily_data in time_series_data["Time Series (Daily)"].items():
            try:
                timestamp = datetime.strptime(date_str, "%Y-%m-%d").replace(
                    hour=0, minute=0, second=0, microsecond=0, tzinfo=UTC
                )
                
                open_price = float(daily_data["1. open"])
                high_price = float(daily_data["2. high"])
                low_price = float(daily_data["3. low"])
                close_price = float(daily_data["4. close"])
                volume = int(daily_data["5. volume"])
                
                price_change = close_price - open_price
                price_change_pct = (price_change / open_price) * 100 if open_price != 0 else 0
                
                candle = {
                    'timestamp': timestamp,
                    'timeframe': 'daily',
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume,
                    'price_change': price_change,
                    'price_change_pct': round(price_change_pct, 2),
                    'source': 'alpha_vantage_gld',
                    'market': 'etf',
                    'data_quality': 1.0,
                }
                
                candles.append(candle)
                
            except Exception as e:
                logger.error("parse_candle_error", date=date_str, error=str(e))
                continue
        
        return candles
    
    async def fetch_and_save_daily_candles(self, outputsize: str = "compact") -> int:
        """Fetch daily candles and save to database."""
        logger.info("fetching_and_saving_daily_candles")
        
        data = self.fetch_daily_time_series(outputsize=outputsize)
        
        if not data:
            logger.warning("no_data_to_save")
            return 0
        
        candles = self.parse_time_series_to_candles(data)
        
        if not candles:
            logger.warning("no_candles_parsed")
            return 0
        
        saved_count = 0
        
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            
            for candle_data in candles:
                try:
                    existing = await session.execute(
                        select(GoldPriceFact).where(
                            GoldPriceFact.timestamp == candle_data['timestamp'],
                            GoldPriceFact.timeframe == 'daily',
                            GoldPriceFact.source == 'alpha_vantage_gld'
                        )
                    )
                    
                    if existing.scalar_one_or_none():
                        continue
                    
                    candle = GoldPriceFact(**candle_data)
                    session.add(candle)
                    saved_count += 1
                    
                except Exception as e:
                    logger.error("save_candle_error", error=str(e))
                    continue
            
            await session.commit()
        
        logger.info("daily_candles_saved", saved=saved_count)
        return saved_count
    
    def get_current_quote(self) -> Optional[Dict[str, Any]]:
        """Get current quote for GLD."""
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': self.SYMBOL,
            'apikey': self.api_key,
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if "Global Quote" in data and data["Global Quote"]:
                    quote = data["Global Quote"]
                    
                    return {
                        'price': float(quote.get("05. price", 0)),
                        'change': float(quote.get("09. change", 0)),
                        'change_percent': quote.get("10. change percent", "0%"),
                        'volume': int(quote.get("06. volume", 0)),
                    }
            
            return None
            
        except Exception as e:
            logger.error("get_quote_error", error=str(e))
            return None
