#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collect Dollar Index Historical Data

جمع‌آوری داده‌های تاریخی Dollar Index از Alpha Vantage

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25 21:06:12 UTC
"""

import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import asyncio
from datetime import datetime
from app.application.services.data_collection.dollar_index_service import DollarIndexService


async def main():
    print("\n" + "="*80)
    print("💵 Dollar Index (DXY) Historical Data Collection")
    print("="*80)
    print(f"📅 UTC: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👤 User: hoseynd-ai")
    print("="*80 + "\n")
    
    service = DollarIndexService()
    
    print("📥 Step 1: Fetching Dollar Index data from Alpha Vantage...")
    print("   (این شامل 20+ سال داده می‌شود)\n")
    
    df = await service.fetch_daily_data(outputsize='full')
    
    if df is None:
        print("❌ خطا در دریافت داده")
        print("\n💡 نکات:")
        print("   • Alpha Vantage API key رو چک کنید")
        print("   • محدودیت rate limit (5 calls/min, 500 calls/day)")
        print("   • اتصال اینترنت رو بررسی کنید")
        return
    
    print(f"✅ داده با موفقیت دریافت شد!")
    print(f"   📊 تعداد رکوردها: {len(df):,}")
    print(f"   📅 بازه زمانی: {df.index.min().date()} → {df.index.max().date()}")
    print(f"   📆 پوشش: {(df.index.max() - df.index.min()).days / 365:.1f} سال")
    
    print(f"\n📊 نمونه داده (5 روز اخیر):")
    print(df.tail().to_string())
    
    print(f"\n💾 Step 2: ذخیره در دیتابیس...")
    saved = await service.save_to_database(df)
    print(f"✅ ذخیره/به‌روزرسانی شد: {saved:,} رکورد")
    
    print(f"\n🔗 Step 3: محاسبه همبستگی با قیمت طلا...")
    corr_stats = await service.calculate_correlation_with_gold()
    
    if corr_stats['correlation'] is not None:
        print(f"✅ تحلیل همبستگی:")
        print(f"   📈 ضریب همبستگی: {corr_stats['correlation']:.4f}")
        print(f"   📊 P-value: {corr_stats['p_value']:.6f}")
        print(f"   📝 تعداد نمونه: {corr_stats['samples']:,}")
        print(f"   💡 تفسیر: همبستگی {corr_stats['interpretation']}")
        
        if corr_stats['correlation'] < -0.5:
            print(f"\n   ✅ عالی! همبستگی معکوس قوی تأیید شد")
            print(f"   این یعنی Dollar Index یک feature عالی برای مدل است")
            print(f"   انتظار می‌رود R² مدل حدود 0.1-0.15 بهبود پیدا کند")
        elif corr_stats['correlation'] < -0.3:
            print(f"\n   ✅ خوب! همبستگی معکوس متوسط")
            print(f"   Dollar Index می‌تواند به مدل کمک کند")
    else:
        print(f"⚠️  داده کافی برای محاسبه همبستگی نیست")
    
    print(f"\n📈 Step 4: آمار کلی...")
    stats = await service.get_statistics()
    print(f"   📊 DXY فعلی: {stats['dxy_stats']['current']:.2f}")
    print(f"   📉 کمترین تاریخی: {stats['dxy_stats']['min']:.2f}")
    print(f"   📈 بیشترین تاریخی: {stats['dxy_stats']['max']:.2f}")
    print(f"   📊 میانگین: {stats['dxy_stats']['mean']:.2f} ± {stats['dxy_stats']['std']:.2f}")
    
    print("\n" + "="*80)
    print("✅ جمع‌آوری داده‌های Dollar Index با موفقیت تکمیل شد!")
    print("="*80)
    print(f"\n📁 داده ذخیره شد در: dollar_index_prices table")
    print(f"🔗 آماده استفاده در feature engineering")
    print(f"\n💡 مرحله بعدی:")
    print(f"   • اضافه کردن DXY به feature_engineering_service.py")
    print(f"   • Re-train مدل با feature جدید")
    print(f"   • انتظار بهبود R² به ~0.28-0.35")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
