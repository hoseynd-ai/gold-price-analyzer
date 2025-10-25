#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug Gold Candle Converter

Author: Hoseyn Doulabi (@hoseynd-ai)
"""

import asyncio
from app.application.services.data_collection.gold_candle_converter import GoldCandleConverter
from app.core.logging import setup_logging

setup_logging()


async def main():
    print("\n" + "="*60)
    print("🔍 Debugging Gold Candle Converter")
    print("="*60 + "\n")
    
    # Check GLD candles first
    from sqlalchemy import select, func
    from app.infrastructure.database.base import AsyncSessionLocal
    from app.infrastructure.database.models import GoldPriceFact
    
    async with AsyncSessionLocal() as session:
        # Count GLD candles
        result = await session.execute(
            select(func.count(GoldPriceFact.id)).where(
                GoldPriceFact.source == 'alpha_vantage_gld'
            )
        )
        gld_count = result.scalar()
        
        # Count converted candles
        result = await session.execute(
            select(func.count(GoldPriceFact.id)).where(
                GoldPriceFact.source == 'alpha_vantage_gold_converted'
            )
        )
        converted_count = result.scalar()
        
        print(f"📊 GLD Candles: {gld_count}")
        print(f"📈 Converted Candles: {converted_count}\n")
        
        if gld_count == 0:
            print("❌ No GLD candles found!")
            print("   Run: python test_alpha_vantage.py first")
            return
        
        if converted_count > 0:
            print("⚠️  Already converted! Let's check them:")
            result = await session.execute(
                select(GoldPriceFact)
                .where(GoldPriceFact.source == 'alpha_vantage_gold_converted')
                .order_by(GoldPriceFact.timestamp.desc())
                .limit(5)
            )
            converted = result.scalars().all()
            
            print("\n📈 Sample Converted Candles:")
            for c in converted:
                print(f"   {c.timestamp.date()}: ${c.close:,.2f}")
            return
    
    # Try conversion
    print("🔄 Trying conversion...")
    try:
        converter = GoldCandleConverter()
        
        # Manual calculation
        factor = await converter.calculate_current_conversion_factor()
        print(f"✅ Conversion Factor: {factor}\n")
        
        # Convert
        saved = await converter.convert_and_save_gld_candles()
        print(f"✅ Converted: {saved} candles\n")
        
    except Exception as e:
        print(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
    
    print("="*60)
    print("🎉 Debug Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
