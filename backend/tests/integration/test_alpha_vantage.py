#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Alpha Vantage Service

Author: Hoseyn Doulabi (@hoseynd-ai)
"""

import asyncio
from app.application.services.data_collection.alpha_vantage_service import AlphaVantageService
from app.core.logging import setup_logging
from app.core.config import settings

setup_logging()


async def main():
    print("\n" + "="*60)
    print("📊 Testing Alpha Vantage Service")
    print("="*60 + "\n")
    
    # Check API key
    print(f"🔑 Checking API Key...")
    if not settings.ALPHA_VANTAGE_API_KEY:
        print("❌ Alpha Vantage API Key not found!")
        return
    
    print(f"✅ API Key found: {settings.ALPHA_VANTAGE_API_KEY[:10]}...\n")
    
    service = AlphaVantageService()
    
    # 1. Get current quote
    print("📊 Fetching current GLD quote...")
    quote = service.get_current_quote()
    if quote:
        print(f"✅ GLD Price: ${quote['price']:.2f}")
        print(f"   Change: {quote['change']:+.2f} ({quote['change_percent']})")
        print(f"   💡 Gold ≈ GLD × 20 = ${quote['price'] * 20:.2f}/oz\n")
    else:
        print("⚠️  Failed to get quote\n")
    
    # 2. Fetch daily candles
    print("📊 Fetching daily candles (last 100 days)...")
    print("⏳ Please wait 10-15 seconds...")
    saved = await service.fetch_and_save_daily_candles(outputsize="compact")
    print(f"✅ Saved {saved} daily candles\n")
    
    # 3. Show stats
    from sqlalchemy import select, func
    from app.infrastructure.database.base import AsyncSessionLocal
    from app.infrastructure.database.models import GoldPriceFact
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.count(GoldPriceFact.id))
        )
        total = result.scalar()
        
        result = await session.execute(
            select(func.count(GoldPriceFact.id)).where(
                GoldPriceFact.source == 'alpha_vantage_gld'
            )
        )
        av_count = result.scalar()
        
        result = await session.execute(
            select(GoldPriceFact)
            .where(GoldPriceFact.source == 'alpha_vantage_gld')
            .order_by(GoldPriceFact.timestamp.desc())
            .limit(10)
        )
        latest = result.scalars().all()
    
    print("="*60)
    print(f"📊 Total records: {total}")
    print(f"📈 Alpha Vantage GLD: {av_count}")
    
    if latest:
        print("\n📈 Latest 10 GLD Candles:")
        print("   Date       | Open   | High   | Low    | Close  | Change | ≈Gold")
        print("   " + "-"*70)
        for p in latest:
            emoji = "📈" if p.price_change_pct > 0 else "📉" if p.price_change_pct < 0 else "➡️"
            gold = p.close * 20
            print(f"   {p.timestamp.date()} | ${p.open:6.2f} | ${p.high:6.2f} | ${p.low:6.2f} | ${p.close:6.2f} | {emoji} {p.price_change_pct:+.2f}% | ${gold:7,.0f}")
    
    print("\n" + "="*60)
    print("🎉 Test Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
