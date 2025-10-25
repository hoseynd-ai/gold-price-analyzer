#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Real Gold Service

Author: Hoseyn Doulabi (@hoseynd-ai)
"""

import asyncio
from app.application.services.data_collection.real_gold_service import RealGoldService
from app.core.logging import setup_logging

setup_logging()


async def main():
    print("\n" + "="*60)
    print("💰 Testing Real Gold Price Service")
    print("="*60 + "\n")
    
    service = RealGoldService()
    
    # 1. Get current price
    print("📊 Fetching REAL gold price...")
    price = service.get_current_price()
    print(f"✅ Current Gold Price: ${price:,.2f}\n")
    
    # 2. Save current price
    print("💾 Saving current price...")
    saved = await service.save_current_price()
    print(f"✅ Saved: {saved}\n")
    
    # 3. Generate realistic historical data
    print("📊 Generating 30 days of realistic data...")
    count = await service.generate_realistic_historical_data(days=30)
    print(f"✅ Generated {count} realistic records\n")
    
    # 4. Show stats
    from sqlalchemy import select, func
    from app.infrastructure.database.base import AsyncSessionLocal
    from app.infrastructure.database.models import GoldPriceFact
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.count(GoldPriceFact.id))
        )
        total = result.scalar()
        
        result = await session.execute(
            select(GoldPriceFact)
            .order_by(GoldPriceFact.timestamp.desc())
            .limit(15)
        )
        latest = result.scalars().all()
    
    print("="*60)
    print(f"📊 Total records in database: {total}")
    print("\n📈 Latest 15 prices:")
    for p in latest:
        change_emoji = "📈" if p.price_change_pct > 0 else "📉" if p.price_change_pct < 0 else "➡️"
        print(f"  {p.timestamp.date()} {p.timeframe:7s}: ${p.close:7,.2f} {change_emoji} {p.price_change_pct:+.2f}% ({p.source})")
    
    print("\n" + "="*60)
    print("🎉 Test Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
