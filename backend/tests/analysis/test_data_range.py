#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Historical Data Range

Author: Hoseyn Doulabi (@hoseynd-ai)
"""

import asyncio
from datetime import datetime
from sqlalchemy import select, func
from app.infrastructure.database.base import AsyncSessionLocal
from app.infrastructure.database.models import GoldPriceFact


async def main():
    print("\n" + "="*70)
    print("📅 Historical Data Range Analysis")
    print("="*70 + "\n")
    
    async with AsyncSessionLocal() as session:
        # Current data range
        result = await session.execute(
            select(
                GoldPriceFact.source,
                func.min(GoldPriceFact.timestamp).label('oldest'),
                func.max(GoldPriceFact.timestamp).label('newest'),
                func.count(GoldPriceFact.id).label('count')
            )
            .where(GoldPriceFact.source == 'alpha_vantage_gld')
            .group_by(GoldPriceFact.source)
        )
        
        data = result.first()
        
        if data:
            oldest = data.oldest
            newest = data.newest
            count = data.count
            days_span = (newest - oldest).days
            
            print("📊 Current GLD Data:")
            print(f"   Oldest: {oldest.date()} ({oldest.strftime('%A')})")
            print(f"   Newest: {newest.date()} ({newest.strftime('%A')})")
            print(f"   Span:   {days_span} days")
            print(f"   Count:  {count} candles")
            print()
            
            # Calculate how far back we can go
            print("="*70)
            print("📅 Alpha Vantage Capabilities:")
            print("="*70)
            print()
            print("✅ compact (current):  100 days (last ~3 months)")
            print("   └─ Already fetched ✓")
            print()
            print("✅ full (available):   20+ years (back to ~1999)")
            print("   └─ Can fetch ~7,000+ days")
            print()
            print("⚠️  Rate Limit: 5 calls/min, 500 calls/day")
            print("   └─ 'full' needs only 1 call!")
            print()
        else:
            print("❌ No GLD data found!")
            print("   Run: python test_alpha_vantage.py first")
    
    print("="*70)
    print("💡 Recommendation:")
    print("="*70)
    print()
    print("For ML & Prediction, we need MORE historical data!")
    print()
    print("Options:")
    print("  1️⃣  Fetch FULL dataset (20+ years)")
    print("     └─ Best for training ML models")
    print("     └─ Only 1 API call")
    print("     └─ ~7,000 candles")
    print()
    print("  2️⃣  Keep compact (100 days)")
    print("     └─ Limited training data")
    print("     └─ Good for testing only")
    print()
    
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
