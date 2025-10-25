#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Gold Candle Converter

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25
"""

import asyncio
from app.application.services.data_collection.gold_candle_converter import GoldCandleConverter
from app.core.logging import setup_logging

setup_logging()


async def main():
    print("\n" + "="*60)
    print("💰 Testing Gold Candle Converter")
    print("="*60 + "\n")
    
    converter = GoldCandleConverter()
    
    # Convert all GLD candles to Gold
    print("📊 Converting GLD candles to Gold spot prices...")
    saved = await converter.convert_and_save_gld_candles()
    print(f"✅ Converted and saved {saved} gold candles\n")
    
    # Show results
    from sqlalchemy import select, func
    from app.infrastructure.database.base import AsyncSessionLocal
    from app.infrastructure.database.models import GoldPriceFact
    
    async with AsyncSessionLocal() as session:
        # Count by source
        result = await session.execute(
            select(
                GoldPriceFact.source,
                func.count(GoldPriceFact.id)
            ).group_by(GoldPriceFact.source)
        )
        counts = result.all()
        
        # Get latest converted candles
        result = await session.execute(
            select(GoldPriceFact)
            .where(GoldPriceFact.source == 'alpha_vantage_gold_converted')
            .order_by(GoldPriceFact.timestamp.desc())
            .limit(10)
        )
        latest = result.scalars().all()
    
    print("="*60)
    print("📊 Database Summary:")
    for source, count in counts:
        print(f"   {source}: {count} candles")
    
    if latest:
        print("\n📈 Latest 10 GOLD Candles (Converted from GLD):")
        print("   Date       | Open     | High     | Low      | Close    | Change")
        print("   " + "-"*70)
        for p in latest:
            emoji = "📈" if p.price_change_pct > 0 else "📉" if p.price_change_pct < 0 else "➡️"
            print(f"   {p.timestamp.date()} | ${p.open:8,.2f} | ${p.high:8,.2f} | ${p.low:8,.2f} | ${p.close:8,.2f} | {emoji} {p.price_change_pct:+.2f}%")
    
    print("\n" + "="*60)
    print("🎉 Converter Test Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
