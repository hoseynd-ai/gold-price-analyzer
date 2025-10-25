#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Price Analyzer - GLD to Gold Converter

Converts GLD ETF prices to actual Gold spot prices.

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25
License: MIT
"""

from datetime import datetime, UTC
from typing import List, Dict, Any
from sqlalchemy import select

from app.core.logging import get_logger
from app.infrastructure.database.base import AsyncSessionLocal
from app.infrastructure.database.models import GoldPriceFact

logger = get_logger(__name__)


class GoldCandleConverter:
    """
    GLD to Gold Converter.
    
    Converts GLD ETF candlesticks to Gold spot price candles.
    
    Author: Hoseyn Doulabi (@hoseynd-ai)
    Created: 2025-10-25
    """
    
    CONVERSION_FACTOR = 10.89
    
    def __init__(self, conversion_factor: float = None):
        """
        Initialize converter.
        
        Args:
            conversion_factor: Custom conversion factor (default: 10.89)
        """
        self.conversion_factor = conversion_factor or self.CONVERSION_FACTOR
        logger.info("gold_candle_converter_initialized", factor=self.conversion_factor)
    
    async def calculate_current_conversion_factor(self) -> float:
        """
        Calculate current conversion factor from latest data.
        
        Returns:
            float: Current conversion factor
        """
        try:
            from app.application.services.data_collection.real_gold_service import RealGoldService
            from app.application.services.data_collection.alpha_vantage_service import AlphaVantageService
            
            real_service = RealGoldService()
            real_gold = real_service.get_current_price()
            
            av_service = AlphaVantageService()
            gld_quote = av_service.get_current_quote()
            
            if gld_quote and real_gold:
                factor = real_gold / gld_quote['price']
                logger.info("conversion_factor_calculated", factor=round(factor, 2))
                return round(factor, 2)
            
            logger.warning("using_default_conversion_factor")
            return self.CONVERSION_FACTOR
            
        except Exception as e:
            logger.error("calculate_conversion_error", error=str(e))
            return self.CONVERSION_FACTOR
    
    def convert_gld_candle_to_gold(self, gld_candle: GoldPriceFact) -> Dict[str, Any]:
        """
        Convert a single GLD candle to Gold candle.
        
        Args:
            gld_candle: GLD candle from database
            
        Returns:
            dict: Converted gold candle data
        """
        return {
            'timestamp': gld_candle.timestamp,
            'timeframe': gld_candle.timeframe,
            'open': round(float(gld_candle.open) * self.conversion_factor, 2),
            'high': round(float(gld_candle.high) * self.conversion_factor, 2),
            'low': round(float(gld_candle.low) * self.conversion_factor, 2),
            'close': round(float(gld_candle.close) * self.conversion_factor, 2),
            'volume': gld_candle.volume,
            'price_change': round(float(gld_candle.price_change) * self.conversion_factor, 2),
            'price_change_pct': gld_candle.price_change_pct,
            'source': 'alpha_vantage_gold_converted',
            'market': 'spot',
            'data_quality': 0.95,
        }
    
    async def convert_and_save_gld_candles(self) -> int:
        """
        Convert all GLD candles to Gold candles and save.
        
        Returns:
            int: Number of candles converted and saved
        """
        logger.info("converting_gld_candles_to_gold")
        
        self.conversion_factor = await self.calculate_current_conversion_factor()
        
        saved_count = 0
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(GoldPriceFact)
                .where(GoldPriceFact.source == 'alpha_vantage_gld')
                .order_by(GoldPriceFact.timestamp.desc())
            )
            gld_candles = result.scalars().all()
            
            logger.info("gld_candles_found", count=len(gld_candles))
            
            for gld_candle in gld_candles:
                try:
                    existing = await session.execute(
                        select(GoldPriceFact).where(
                            GoldPriceFact.timestamp == gld_candle.timestamp,
                            GoldPriceFact.timeframe == gld_candle.timeframe,
                            GoldPriceFact.source == 'alpha_vantage_gold_converted'
                        )
                    )
                    
                    if existing.scalar_one_or_none():
                        logger.debug("gold_candle_exists", timestamp=gld_candle.timestamp.isoformat())
                        continue
                    
                    gold_candle_data = self.convert_gld_candle_to_gold(gld_candle)
                    
                    gold_candle = GoldPriceFact(**gold_candle_data)
                    session.add(gold_candle)
                    saved_count += 1
                    
                except Exception as e:
                    logger.error("convert_candle_error", error=str(e))
                    continue
            
            await session.commit()
        
        logger.info("gld_candles_converted", saved=saved_count, factor=self.conversion_factor)
        
        return saved_count
