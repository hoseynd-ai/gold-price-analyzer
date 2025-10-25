#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Price Data Visualization

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25
"""

import asyncio
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import select
from app.infrastructure.database.base import AsyncSessionLocal
from app.infrastructure.database.models import GoldPriceFact


async def fetch_gold_data():
    """Fetch gold candle data from database."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(GoldPriceFact)
            .where(GoldPriceFact.source == 'alpha_vantage_gold_converted')
            .order_by(GoldPriceFact.timestamp.asc())
        )
        candles = result.scalars().all()
    
    # Convert to DataFrame
    data = {
        'timestamp': [c.timestamp for c in candles],
        'open': [float(c.open) for c in candles],
        'high': [float(c.high) for c in candles],
        'low': [float(c.low) for c in candles],
        'close': [float(c.close) for c in candles],
        'volume': [c.volume for c in candles],
    }
    
    return pd.DataFrame(data)


async def main():
    print("\n" + "="*70)
    print("📊 Gold Price Data Visualization")
    print("="*70 + "\n")
    
    print("📥 Fetching data from database...")
    df = await fetch_gold_data()
    
    print(f"✅ Loaded {len(df)} candles")
    print(f"📅 From: {df['timestamp'].min().date()}")
    print(f"📅 To:   {df['timestamp'].max().date()}")
    print()
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=('Gold Spot Price (USD/oz)', 'Volume')
    )
    
    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Gold Price',
            increasing_line_color='green',
            decreasing_line_color='red',
        ),
        row=1, col=1
    )
    
    # Volume bars
    colors = ['green' if close >= open else 'red' 
              for close, open in zip(df['close'], df['open'])]
    
    fig.add_trace(
        go.Bar(
            x=df['timestamp'],
            y=df['volume'],
            name='Volume',
            marker_color=colors,
            showlegend=False
        ),
        row=2, col=1
    )
    
    # Layout
    fig.update_layout(
        title={
            'text': '💰 Gold Price Analysis (Alpha Vantage Data)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_rangeslider_visible=False,
        height=800,
        template='plotly_dark',
        hovermode='x unified',
        font=dict(size=12),
    )
    
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Price (USD/oz)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    # Add annotations
    latest_price = df['close'].iloc[-1]
    min_price = df['low'].min()
    max_price = df['high'].max()
    
    fig.add_annotation(
        text=f"Latest: ${latest_price:,.2f}<br>Range: ${min_price:,.2f} - ${max_price:,.2f}",
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        bgcolor="rgba(0,0,0,0.5)",
        bordercolor="white",
        borderwidth=1,
        font=dict(size=12, color="white"),
        align="left"
    )
    
    # Save to HTML
    output_file = "gold_price_chart.html"
    fig.write_html(output_file)
    
    print("="*70)
    print("🎉 Visualization Complete!")
    print("="*70)
    print(f"\n📊 Chart saved to: {output_file}")
    print(f"\n💡 Open in browser:")
    print(f"   open {output_file}")
    print()
    
    # Statistics
    print("="*70)
    print("📊 Statistics:")
    print("="*70)
    print(f"   Records:      {len(df):,}")
    print(f"   Latest Price: ${latest_price:,.2f}")
    print(f"   Highest:      ${max_price:,.2f}")
    print(f"   Lowest:       ${min_price:,.2f}")
    print(f"   Range:        ${max_price - min_price:,.2f}")
    print(f"   Avg Volume:   {df['volume'].mean():,.0f}")
    print()
    
    # Price changes
    df['price_change_pct'] = df['close'].pct_change() * 100
    positive_days = (df['price_change_pct'] > 0).sum()
    negative_days = (df['price_change_pct'] < 0).sum()
    
    print("📈 Price Movement:")
    print(f"   Up days:   {positive_days} ({positive_days/len(df)*100:.1f}%)")
    print(f"   Down days: {negative_days} ({negative_days/len(df)*100:.1f}%)")
    print(f"   Biggest gain: {df['price_change_pct'].max():.2f}%")
    print(f"   Biggest drop: {df['price_change_pct'].min():.2f}%")
    print()
    
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
