#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetch Full Historical GLD Data (20+ years)

Author: Hoseyn Doulabi (@hoseynd-ai)
"""

import asyncio
from app.application.services.data_collection.alpha_vantage_service import AlphaVantageService
from app.application.services.data_collection.gold_candle_converter import GoldCandleConverter
from app.core.logging import setup_logging

setup_logging()


async def main():
    print("\n" + "="*70)
    print("📊 Fetching FULL Historical Gold Data (20+ years)")
    print("="*70 + "\n")
    
    print("⏳ This will take ~30 seconds...")
    print("📥 Fetching data from Alpha Vantage...")
    print()
    
    # Fetch full dataset
    service = AlphaVantageService()
    saved = await service.fetch_and_save_daily_candles(outputsize="full")
    
    print(f"\n✅ Saved {saved} GLD candles")
    print()
    
    # Convert to Gold
    print("🔄 Converting GLD to Gold spot prices...")
    converter = GoldCandleConverter()
    converted = await converter.convert_and_save_gld_candles()
    
    print(f"✅ Converted {converted} Gold candles")
    print()
    
    # Summary
    from sqlalchemy import select, func
    from app.infrastructure.database.base import AsyncSessionLocal
    from app.infrastructure.database.models import GoldPriceFact
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(
                func.min(GoldPriceFact.timestamp),
                func.max(GoldPriceFact.timestamp),
                func.count(GoldPriceFact.id)
            )
            .where(GoldPriceFact.source == 'alpha_vantage_gold_converted')
        )
        
        oldest, newest, count = result.first()
        days_span = (newest - oldest).days
    
    print("="*70)
    print("🎉 Full Historical Data Ready!")
    print("="*70)
    print(f"\n📊 Gold Spot Price Data:")
    print(f"   From:  {oldest.date()} ({oldest.year})")
    print(f"   To:    {newest.date()} ({newest.year})")
    print(f"   Span:  {days_span} days (~{days_span//365} years)")
    print(f"   Count: {count:,} candles")
    print()
    print("✅ Ready for:")
    print("   → Machine Learning Training")
    print("   → Technical Analysis")
    print("   → Long-term Trend Analysis")
    print("   → Prediction Models")
    print()
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
