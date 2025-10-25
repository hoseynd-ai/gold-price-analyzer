#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXY vs Gold Price Visualization

نمودار مقایسه‌ای Dollar Index و قیمت طلا

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25 17:47:48 UTC
"""

import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import select

from app.infrastructure.database.base import AsyncSessionLocal
from app.infrastructure.database.models import DollarIndexPrice, GoldPriceFact
from app.core.logging import get_logger

logger = get_logger(__name__)


async def fetch_data(days: int = 365):
    """
    دریافت داده‌های DXY و Gold از دیتابیس
    
    Args:
        days: تعداد روزهای اخیر
        
    Returns:
        tuple: (dxy_df, gold_df)
    """
    cutoff_date = datetime.utcnow().date() - timedelta(days=days)
    
    async with AsyncSessionLocal() as session:
        # دریافت DXY
        result_dxy = await session.execute(
            select(DollarIndexPrice)
            .where(DollarIndexPrice.date >= cutoff_date)
            .order_by(DollarIndexPrice.date)
        )
        dxy_records = result_dxy.scalars().all()
        
        # دریافت Gold
        result_gold = await session.execute(
            select(GoldPriceFact)
            .where(
                GoldPriceFact.timeframe == 'daily',
                GoldPriceFact.timestamp >= datetime.combine(cutoff_date, datetime.min.time())
            )
            .order_by(GoldPriceFact.timestamp)
        )
        gold_records = result_gold.scalars().all()
    
    # تبدیل به DataFrame
    dxy_df = pd.DataFrame([{
        'date': r.date,
        'dxy_open': float(r.open),
        'dxy_high': float(r.high),
        'dxy_low': float(r.low),
        'dxy_close': float(r.close)
    } for r in dxy_records])
    
    gold_df = pd.DataFrame([{
        'date': r.timestamp.date(),
        'gold_open': float(r.open) if r.open else None,
        'gold_high': float(r.high) if r.high else None,
        'gold_low': float(r.low) if r.low else None,
        'gold_close': float(r.close)
    } for r in gold_records])
    
    if not dxy_df.empty:
        dxy_df['date'] = pd.to_datetime(dxy_df['date'])
    if not gold_df.empty:
        gold_df['date'] = pd.to_datetime(gold_df['date'])
    
    return dxy_df, gold_df


def create_visualization(dxy_df, gold_df, days=365):
    """
    ساخت نمودار تعاملی با Plotly
    
    Args:
        dxy_df: DataFrame داده‌های DXY
        gold_df: DataFrame داده‌های Gold
        days: تعداد روزهای نمایش
    """
    
    # Merge data
    merged = pd.merge(dxy_df, gold_df, on='date', how='inner')
    
    if merged.empty:
        print("⚠️  هیچ داده مشترکی بین DXY و Gold پیدا نشد!")
        return None
    
    # محاسبه correlation
    correlation = merged['dxy_close'].corr(merged['gold_close'])
    
    # ساخت figure با 3 subplot
    fig = make_subplots(
        rows=3, cols=1,
        row_heights=[0.4, 0.4, 0.2],
        subplot_titles=(
            f'قیمت طلا (Gold Price) - {days} روز اخیر',
            f'شاخص دلار (Dollar Index - DXY) - {days} روز اخیر',
            f'همبستگی معکوس (Inverse Correlation: {correlation:.3f})'
        ),
        vertical_spacing=0.08,
        specs=[
            [{"secondary_y": False}],
            [{"secondary_y": False}],
            [{"secondary_y": True}]
        ]
    )
    
    # ====================================
    # نمودار 1: قیمت طلا (Candlestick)
    # ====================================
    fig.add_trace(
        go.Candlestick(
            x=merged['date'],
            open=merged['gold_open'],
            high=merged['gold_high'],
            low=merged['gold_low'],
            close=merged['gold_close'],
            name='Gold Price',
            increasing_line_color='#FFD700',
            decreasing_line_color='#B8860B',
            increasing_fillcolor='rgba(255, 215, 0, 0.3)',
            decreasing_fillcolor='rgba(184, 134, 11, 0.3)'
        ),
        row=1, col=1
    )
    
    # میانگین متحرک طلا
    merged['gold_ma_20'] = merged['gold_close'].rolling(20).mean()
    merged['gold_ma_50'] = merged['gold_close'].rolling(50).mean()
    
    fig.add_trace(
        go.Scatter(
            x=merged['date'],
            y=merged['gold_ma_20'],
            name='Gold MA(20)',
            line=dict(color='#FF6B6B', width=1, dash='dash'),
            opacity=0.7
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=merged['date'],
            y=merged['gold_ma_50'],
            name='Gold MA(50)',
            line=dict(color='#4ECDC4', width=1, dash='dash'),
            opacity=0.7
        ),
        row=1, col=1
    )
    
    # ====================================
    # نمودار 2: Dollar Index (Candlestick)
    # ====================================
    fig.add_trace(
        go.Candlestick(
            x=merged['date'],
            open=merged['dxy_open'],
            high=merged['dxy_high'],
            low=merged['dxy_low'],
            close=merged['dxy_close'],
            name='DXY',
            increasing_line_color='#2ECC71',
            decreasing_line_color='#E74C3C',
            increasing_fillcolor='rgba(46, 204, 113, 0.3)',
            decreasing_fillcolor='rgba(231, 76, 60, 0.3)'
        ),
        row=2, col=1
    )
    
    # میانگین متحرک DXY
    merged['dxy_ma_20'] = merged['dxy_close'].rolling(20).mean()
    merged['dxy_ma_50'] = merged['dxy_close'].rolling(50).mean()
    
    fig.add_trace(
        go.Scatter(
            x=merged['date'],
            y=merged['dxy_ma_20'],
            name='DXY MA(20)',
            line=dict(color='#9B59B6', width=1, dash='dash'),
            opacity=0.7
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=merged['date'],
            y=merged['dxy_ma_50'],
            name='DXY MA(50)',
            line=dict(color='#3498DB', width=1, dash='dash'),
            opacity=0.7
        ),
        row=2, col=1
    )
    
    # ====================================
    # نمودار 3: Overlay (نرمال شده) + Correlation
    # ====================================
    
    # نرمال‌سازی به 0-100
    gold_normalized = ((merged['gold_close'] - merged['gold_close'].min()) / 
                      (merged['gold_close'].max() - merged['gold_close'].min())) * 100
    
    dxy_normalized = ((merged['dxy_close'] - merged['dxy_close'].min()) / 
                     (merged['dxy_close'].max() - merged['dxy_close'].min())) * 100
    
    # Gold normalized
    fig.add_trace(
        go.Scatter(
            x=merged['date'],
            y=gold_normalized,
            name='Gold (نرمال شده)',
            line=dict(color='#FFD700', width=2),
            fill='tonexty',
            fillcolor='rgba(255, 215, 0, 0.1)'
        ),
        row=3, col=1,
        secondary_y=False
    )
    
    # DXY normalized
    fig.add_trace(
        go.Scatter(
            x=merged['date'],
            y=dxy_normalized,
            name='DXY (نرمال شده)',
            line=dict(color='#2ECC71', width=2),
            fill='tonexty',
            fillcolor='rgba(46, 204, 113, 0.1)'
        ),
        row=3, col=1,
        secondary_y=False
    )
    
    # Rolling correlation
    merged['rolling_corr'] = merged['gold_close'].rolling(30).corr(merged['dxy_close'])
    
    fig.add_trace(
        go.Scatter(
            x=merged['date'],
            y=merged['rolling_corr'],
            name='Rolling Corr (30d)',
            line=dict(color='#E74C3C', width=2, dash='dot'),
            yaxis='y4'
        ),
        row=3, col=1,
        secondary_y=True
    )
    
    # ====================================
    # Layout و تنظیمات
    # ====================================
    fig.update_xaxes(title_text="تاریخ", row=3, col=1)
    fig.update_yaxes(title_text="قیمت (USD/oz)", row=1, col=1)
    fig.update_yaxes(title_text="DXY Index", row=2, col=1)
    fig.update_yaxes(title_text="نرمال شده (0-100)", row=3, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Correlation", row=3, col=1, secondary_y=True)
    
    # تنظیمات کلی
    fig.update_layout(
        title={
            'text': f'<b>تحلیل مقایسه‌ای: شاخص دلار (DXY) vs قیمت طلا</b><br>'
                   f'<sub>Correlation: {correlation:.4f} | '
                   f'تاریخ: {merged["date"].min().date()} تا {merged["date"].max().date()} | '
                   f'تعداد نمونه: {len(merged):,}</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        height=1400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified',
        template='plotly_white',
        font=dict(family="Arial", size=12)
    )
    
    # حذف rangeslider از candlestick
    fig.update_xaxes(rangeslider_visible=False)
    
    # اضافه کردن annotations
    fig.add_annotation(
        text=f"<b>همبستگی کلی: {correlation:.4f}</b><br>"
             f"{'همبستگی معکوس قوی ✅' if correlation < -0.5 else 'همبستگی ضعیف ⚠️'}<br>"
             f"<i>هر چه DXY بالاتر → Gold پایین‌تر</i>",
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="#333",
        borderwidth=2,
        font=dict(size=12, color="#333"),
        align="left"
    )
    
    return fig, merged, correlation


async def main():
    print("\n" + "="*80)
    print("📊 Dollar Index vs Gold Price - Visual Analysis")
    print("="*80)
    print(f"📅 UTC: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👤 User: hoseynd-ai")
    print("="*80 + "\n")
    
    # انتخاب بازه زمانی
    print("📅 انتخاب بازه زمانی:")
    print("  1. 30 روز اخیر")
    print("  2. 90 روز اخیر")
    print("  3. 180 روز اخیر (6 ماه)")
    print("  4. 365 روز اخیر (1 سال)")
    print("  5. 730 روز اخیر (2 سال)")
    print("  6. تمام داده‌ها (20+ سال)")
    
    choice = input("\n👉 انتخاب کنید (1-6) [پیش‌فرض: 4]: ").strip() or "4"
    
    days_map = {
        '1': 30,
        '2': 90,
        '3': 180,
        '4': 365,
        '5': 730,
        '6': 7300  # ~20 years
    }
    
    days = days_map.get(choice, 365)
    
    print(f"\n📥 در حال دریافت {days} روز داده از دیتابیس...")
    
    # دریافت داده
    dxy_df, gold_df = await fetch_data(days)
    
    print(f"✅ DXY: {len(dxy_df):,} رکورد")
    print(f"✅ Gold: {len(gold_df):,} رکورد")
    
    if dxy_df.empty or gold_df.empty:
        print("\n❌ داده کافی در دیتابیس یافت نشد!")
        return
    
    print(f"\n📊 در حال ساخت نمودار...")
    
    # ساخت نمودار
    fig, merged, correlation = create_visualization(dxy_df, gold_df, days)
    
    if fig is None:
        return
    
    # ذخیره
    output_file = f'dxy_vs_gold_{days}days.html'
    fig.write_html(output_file)
    
    print(f"\n✅ نمودار ذخیره شد: {output_file}")
    print(f"\n📊 آمار:")
    print(f"   • تعداد نقاط داده مشترک: {len(merged):,}")
    print(f"   • بازه زمانی: {merged['date'].min().date()} تا {merged['date'].max().date()}")
    print(f"   • همبستگی کلی: {correlation:.4f}")
    
    if correlation < -0.5:
        print(f"   • ✅ همبستگی معکوس قوی تأیید شد!")
        print(f"   • 💡 DXY یک feature عالی برای پیش‌بینی طلا است")
    elif correlation < -0.3:
        print(f"   • ✅ همبستگی معکوس متوسط")
        print(f"   • 💡 DXY می‌تواند به مدل کمک کند")
    else:
        print(f"   • ⚠️  همبستگی ضعیف یا نامشخص")
    
    # آمار بیشتر
    print(f"\n📈 آمار قیمت طلا:")
    print(f"   • فعلی: ${merged.iloc[-1]['gold_close']:.2f}")
    print(f"   • کمترین: ${merged['gold_close'].min():.2f}")
    print(f"   • بیشترین: ${merged['gold_close'].max():.2f}")
    print(f"   • میانگین: ${merged['gold_close'].mean():.2f}")
    
    print(f"\n📉 آمار DXY:")
    print(f"   • فعلی: {merged.iloc[-1]['dxy_close']:.2f}")
    print(f"   • کمترین: {merged['dxy_close'].min():.2f}")
    print(f"   • بیشترین: {merged['dxy_close'].max():.2f}")
    print(f"   • میانگین: {merged['dxy_close'].mean():.2f}")
    
    print("\n" + "="*80)
    print("✅ تحلیل تکمیل شد!")
    print("="*80)
    print(f"\n📁 فایل خروجی: {output_file}")
    print(f"💡 برای مشاهده، فایل را در مرورگر باز کنید")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
