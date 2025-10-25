#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dollar Index (DXY) Data Collection Service

جمع‌آوری داده‌های شاخص دلار آمریکا (DXY) از Alpha Vantage

چرا مهمه:
- رابطه معکوس قوی با طلا (correlation: -0.7 to -0.9)
- وقتی دلار قوی میشه، طلا ضعیف میشه
- یکی از مهم‌ترین عوامل پیش‌بینی قیمت طلا

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25 17:40:00 UTC
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.infrastructure.database.base import get_db, AsyncSessionLocal
from app.infrastructure.database.models import DollarIndexPrice
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DollarIndexService:
    """
    سرویس جمع‌آوری و مدیریت داده‌های Dollar Index
    
    Dollar Index (DXY):
    - شاخص ارزش دلار در برابر سبد ارزهای جهانی
    - شامل: EUR, JPY, GBP, CAD, SEK, CHF
    - وزن بیشترین: یورو (57.6%)
    
    Features:
    - جمع‌آوری داده روزانه از Alpha Vantage
    - ذخیره در database
    - محاسبه تغییرات روزانه
    - Correlation با قیمت طلا
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Dollar Index service
        
        Args:
            api_key: Alpha Vantage API key
        """
        self.api_key = api_key or settings.ALPHA_VANTAGE_API_KEY
        
        if not self.api_key or self.api_key == "demo":
            logger.warning("alpha_vantage_demo_key",
                          message="Using demo key - limited functionality")
        
        logger.info("dollar_index_service_initialized")
    
    async def fetch_daily_data(
        self,
        outputsize: str = 'full'
    ) -> Optional[pd.DataFrame]:
        """
        دریافت داده‌های روزانه Dollar Index
        
        Args:
            outputsize: 'compact' (100 days) or 'full' (20+ years)
            
        Returns:
            DataFrame با ستون‌های: date, open, high, low, close, volume
        """
        logger.info("fetching_dollar_index_data", outputsize=outputsize)
        
        params = {
            'function': 'FX_DAILY',
            'from_symbol': 'USD',
            'to_symbol': 'EUR',  # EUR = بزرگترین component DXY
            'outputsize': outputsize,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # چک کردن خطا
            if 'Error Message' in data:
                logger.error("api_error", error=data['Error Message'])
                return None
            
            if 'Note' in data:
                logger.warning("api_rate_limit", message=data['Note'])
                return None
            
            # Parse time series
            time_series_key = 'Time Series FX (Daily)'
            if time_series_key not in data:
                logger.error("unexpected_response_format", keys=list(data.keys()))
                return None
            
            time_series = data[time_series_key]
            
            # تبدیل به DataFrame
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            # تغییر نام ستون‌ها
            df.columns = ['open', 'high', 'low', 'close']
            
            # تبدیل به float
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # محاسبه DXY inverse (چون ما USD/EUR داریم)
            # DXY بالا = دلار قوی = EUR/USD پایین
            for col in ['open', 'high', 'low', 'close']:
                df[col] = 1 / df[col]
            
            # نرمال‌سازی به مقیاس DXY واقعی (~100)
            # DXY base = 100 در سال 1973
            df = df * 100
            
            logger.info("dollar_index_data_fetched",
                       records=len(df),
                       date_range=f"{df.index.min()} to {df.index.max()}")
            
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error("request_error", error=str(e))
            return None
        except Exception as e:
            logger.error("unexpected_error", error=str(e))
            return None
    
    async def save_to_database(self, df: pd.DataFrame) -> int:
        """
        ذخیره داده‌ها در database
        
        Args:
            df: DataFrame حاوی داده‌های DXY
            
        Returns:
            تعداد رکوردهای ذخیره شده
        """
        logger.info("saving_dollar_index_to_db", records=len(df))
        
        saved_count = 0
        updated_count = 0
        
        async with AsyncSessionLocal() as session:
            for date, row in df.iterrows():
                try:
                    # چک وجود
                    result = await session.execute(
                        select(DollarIndexPrice).where(
                            DollarIndexPrice.date == date.date()
                        )
                    )
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        # به‌روزرسانی
                        existing.open = float(row['open'])
                        existing.high = float(row['high'])
                        existing.low = float(row['low'])
                        existing.close = float(row['close'])
                        existing.updated_at = datetime.utcnow()
                        updated_count += 1
                    else:
                        # ساخت جدید
                        dxy_price = DollarIndexPrice(
                            date=date.date(),
                            open=float(row['open']),
                            high=float(row['high']),
                            low=float(row['low']),
                            close=float(row['close'])
                        )
                        session.add(dxy_price)
                        saved_count += 1
                    
                except Exception as e:
                    logger.warning("save_record_error",
                                 date=str(date.date()),
                                 error=str(e))
                    continue
            
            await session.commit()
        
        logger.info("dollar_index_saved",
                   saved=saved_count,
                   updated=updated_count,
                   total=saved_count + updated_count)
        
        return saved_count + updated_count
    
    async def get_latest_data(
        self,
        days: int = 30
    ) -> Optional[pd.DataFrame]:
        """
        دریافت آخرین داده‌ها از database
        
        Args:
            days: تعداد روزهای اخیر
            
        Returns:
            DataFrame داده‌ها
        """
        async with AsyncSessionLocal() as session:
            cutoff_date = datetime.utcnow().date() - timedelta(days=days)
            
            result = await session.execute(
                select(DollarIndexPrice)
                .where(DollarIndexPrice.date >= cutoff_date)
                .order_by(DollarIndexPrice.date.desc())
            )
            
            records = result.scalars().all()
            
            if not records:
                return None
            
            # تبدیل به DataFrame
            data = [{
                'date': r.date,
                'open': r.open,
                'high': r.high,
                'low': r.low,
                'close': r.close
            } for r in records]
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()
            
            return df
    
    async def calculate_correlation_with_gold(self) -> Dict:
        """
        محاسبه همبستگی با قیمت طلا
        
        Returns:
            دیکشنری شامل correlation coefficient و p-value
        """
        from app.infrastructure.database.models import GoldPriceFact
        
        async with AsyncSessionLocal() as session:
            # دریافت DXY data
            result_dxy = await session.execute(
                select(DollarIndexPrice).order_by(DollarIndexPrice.date)
            )
            dxy_records = result_dxy.scalars().all()
            
            # دریافت Gold data - استفاده از timestamp بجای date
            result_gold = await session.execute(
                select(GoldPriceFact)
                .where(GoldPriceFact.timeframe == 'daily')  # فقط daily
                .order_by(GoldPriceFact.timestamp)
            )
            gold_records = result_gold.scalars().all()
            
            # تبدیل به DataFrame
            dxy_df = pd.DataFrame([{
                'date': r.date,
                'dxy_close': float(r.close)
            } for r in dxy_records])
            
            gold_df = pd.DataFrame([{
                'date': r.timestamp.date(),  # تبدیل timestamp به date
                'gold_close': float(r.close)
            } for r in gold_records])
            
            # Merge on date
            merged = pd.merge(dxy_df, gold_df, on='date', how='inner')
            
            if len(merged) < 30:
                logger.warning("insufficient_data_for_correlation",
                             records=len(merged))
                return {
                    'correlation': None,
                    'p_value': None,
                    'samples': len(merged),
                    'interpretation': 'داده کافی نیست'
                }
            
            # محاسبه correlation
            correlation = merged['dxy_close'].corr(merged['gold_close'])
            
            # محاسبه p-value
            from scipy.stats import pearsonr
            corr, p_value = pearsonr(merged['dxy_close'], merged['gold_close'])
            
            logger.info("correlation_calculated",
                       correlation=correlation,
                       p_value=p_value,
                       samples=len(merged))
            
            return {
                'correlation': float(correlation),
                'p_value': float(p_value),
                'samples': len(merged),
                'interpretation': self._interpret_correlation(correlation)
            }
    
    def _interpret_correlation(self, corr: float) -> str:
        """تفسیر همبستگی"""
        if corr is None:
            return "نامشخص"
        
        abs_corr = abs(corr)
        
        if abs_corr > 0.8:
            strength = "خیلی قوی"
        elif abs_corr > 0.6:
            strength = "قوی"
        elif abs_corr > 0.4:
            strength = "متوسط"
        elif abs_corr > 0.2:
            strength = "ضعیف"
        else:
            strength = "خیلی ضعیف"
        
        direction = "معکوس" if corr < 0 else "مستقیم"
        
        return f"{strength} و {direction}"
    
    async def get_statistics(self) -> Dict:
        """آمار کلی داده‌های DXY"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(DollarIndexPrice))
            records = result.scalars().all()
            
            if not records:
                return {'total': 0}
            
            df = pd.DataFrame([{
                'date': r.date,
                'close': float(r.close)
            } for r in records])
            
            return {
                'total_records': len(records),
                'date_range': {
                    'start': str(df['date'].min()),
                    'end': str(df['date'].max())
                },
                'dxy_stats': {
                    'current': float(df.iloc[-1]['close']),
                    'min': float(df['close'].min()),
                    'max': float(df['close'].max()),
                    'mean': float(df['close'].mean()),
                    'std': float(df['close'].std())
                }
            }


if __name__ == "__main__":
    import asyncio
    
    async def main():
        print("\n" + "="*70)
        print("💵 Dollar Index (DXY) Data Collection")
        print("="*70)
        print(f"📅 UTC: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"👤 User: hoseynd-ai")
        print("="*70 + "\n")
        
        service = DollarIndexService()
        
        # دریافت داده
        print("📥 Fetching Dollar Index data from Alpha Vantage...")
        df = await service.fetch_daily_data(outputsize='full')
        
        if df is not None:
            print(f"✅ Data fetched: {len(df)} records")
            print(f"📅 Date range: {df.index.min().date()} to {df.index.max().date()}")
            print(f"\n📊 Latest DXY values:")
            print(df.tail())
            
            # ذخیره
            print(f"\n💾 Saving to database...")
            saved = await service.save_to_database(df)
            print(f"✅ Saved/Updated: {saved} records")
            
            # Correlation
            print(f"\n🔗 Calculating correlation with Gold...")
            corr_stats = await service.calculate_correlation_with_gold()
            
            if corr_stats['correlation'] is not None:
                print(f"✅ Correlation: {corr_stats['correlation']:.4f}")
                print(f"   P-value: {corr_stats['p_value']:.6f}")
                print(f"   Samples: {corr_stats['samples']}")
                print(f"   تفسیر: {corr_stats['interpretation']}")
            
            # آمار
            print(f"\n📈 Statistics:")
            stats = await service.get_statistics()
            print(f"   Total records: {stats['total_records']}")
            print(f"   Current DXY: {stats['dxy_stats']['current']:.2f}")
            print(f"   Range: {stats['dxy_stats']['min']:.2f} - {stats['dxy_stats']['max']:.2f}")
            print(f"   Average: {stats['dxy_stats']['mean']:.2f}")
        else:
            print("❌ Failed to fetch data")
        
        print("\n" + "="*70 + "\n")
    
    asyncio.run(main())
