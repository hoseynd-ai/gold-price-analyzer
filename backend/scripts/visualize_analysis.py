#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Price Analyzer - Complete Analysis Visualization

نمودارسازی کامل:
- تحلیل FinBERT Sentiment
- شاخص‌های تکنیکال
- همبستگی Sentiment با قیمت

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import create_engine, text

from app.application.services.ml.technical_indicators_service import TechnicalIndicatorsService


# Database configuration
DATABASE_URL = "postgresql+psycopg2://admin:admin123@localhost:5432/gold_analyzer"


def load_data_from_database():
    """بارگذاری داده‌ها از Database"""
    print("📊 Loading data from database...")
    
    engine = create_engine(DATABASE_URL)
    
    # Load gold prices
    query_prices = """
    SELECT 
        timestamp,
        open,
        high,
        low,
        close,
        volume
    FROM gold_price_facts
    WHERE timeframe = 'daily'
        AND source = 'converted'
    ORDER BY timestamp ASC;
    """
    
    df_prices = pd.read_sql(query_prices, engine)
    df_prices['timestamp'] = pd.to_datetime(df_prices['timestamp'])
    
    # Load news with sentiment
    query_news = """
    SELECT 
        published_at,
        title,
        sentiment_score,
        sentiment_label,
        confidence
    FROM news_events
    WHERE sentiment_score IS NOT NULL
    ORDER BY published_at ASC;
    """
    
    df_news = pd.read_sql(query_news, engine)
    df_news['published_at'] = pd.to_datetime(df_news['published_at'])
    
    print(f"✅ Loaded {len(df_prices)} price records")
    print(f"✅ Loaded {len(df_news)} news articles")
    
    return df_prices, df_news


def calculate_technical_indicators(df_prices):
    """محاسبه شاخص‌های تکنیکال"""
    print("📈 Calculating technical indicators...")
    
    service = TechnicalIndicatorsService()
    df_with_indicators = service.calculate_all_indicators(df_prices)
    df_with_signals = service.generate_signals(df_with_indicators)
    
    print("✅ Technical indicators calculated")
    
    return df_with_signals


def create_sentiment_chart(df_news):
    """نمودار تحلیل احساسات"""
    print("🎨 Creating sentiment analysis chart...")
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=(
            '📰 Sentiment Timeline',
            '📊 Sentiment Distribution'
        ),
        row_heights=[0.6, 0.4],
        vertical_spacing=0.12
    )
    
    # Row 1: Timeline
    colors = {
        'positive': '#2ecc71',
        'negative': '#e74c3c',
        'neutral': '#95a5a6'
    }
    
    for label in ['positive', 'negative', 'neutral']:
        mask = df_news['sentiment_label'] == label
        fig.add_trace(
            go.Scatter(
                x=df_news[mask]['published_at'],
                y=df_news[mask]['sentiment_score'],
                mode='markers+lines',
                name=label.capitalize(),
                marker=dict(
                    size=10,
                    color=colors[label],
                    line=dict(width=1, color='white')
                ),
                line=dict(width=2, color=colors[label])
            ),
            row=1, col=1
        )
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=1)
    
    # Row 2: Distribution
    sentiment_counts = df_news['sentiment_label'].value_counts()
    fig.add_trace(
        go.Bar(
            x=sentiment_counts.index,
            y=sentiment_counts.values,
            marker_color=[colors[label] for label in sentiment_counts.index],
            text=sentiment_counts.values,
            textposition='auto'
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        title_text="📊 FinBERT Sentiment Analysis Results",
        title_font_size=18,
        height=800,
        showlegend=True,
        hovermode='closest'
    )
    
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_yaxes(title_text="Sentiment Score", row=1, col=1)
    fig.update_xaxes(title_text="Sentiment Label", row=2, col=1)
    fig.update_yaxes(title_text="Count", row=2, col=1)
    
    # Save
    output_file = "sentiment_analysis.html"
    fig.write_html(output_file)
    print(f"✅ Saved: {output_file}")
    
    return fig


def create_technical_indicators_chart(df):
    """نمودار شاخص‌های تکنیکال"""
    print("🎨 Creating technical indicators chart...")
    
    fig = make_subplots(
        rows=4, cols=1,
        subplot_titles=(
            '💰 Gold Price with Bollinger Bands & Moving Averages',
            '📊 RSI (Relative Strength Index)',
            '📈 MACD',
            '📉 Volume'
        ),
        row_heights=[0.4, 0.2, 0.2, 0.2],
        vertical_spacing=0.05,
        specs=[
            [{"secondary_y": False}],
            [{"secondary_y": False}],
            [{"secondary_y": False}],
            [{"secondary_y": False}]
        ]
    )
    
    # Row 1: Candlestick + Bollinger Bands + MAs
    fig.add_trace(
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Gold Price',
            increasing_line_color='#2ecc71',
            decreasing_line_color='#e74c3c'
        ),
        row=1, col=1
    )
    
    # Bollinger Bands
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['bb_upper'],
            mode='lines',
            name='BB Upper',
            line=dict(color='rgba(255, 0, 0, 0.3)', width=1, dash='dash')
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['bb_middle'],
            mode='lines',
            name='BB Middle (SMA 20)',
            line=dict(color='rgba(0, 0, 255, 0.5)', width=2)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['bb_lower'],
            mode='lines',
            name='BB Lower',
            line=dict(color='rgba(0, 255, 0, 0.3)', width=1, dash='dash'),
            fill='tonexty',
            fillcolor='rgba(0, 100, 200, 0.1)'
        ),
        row=1, col=1
    )
    
    # Moving Averages
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['sma_50'],
            mode='lines',
            name='SMA 50',
            line=dict(color='orange', width=2)
        ),
        row=1, col=1
    )
    
    # Row 2: RSI
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['rsi'],
            mode='lines',
            name='RSI',
            line=dict(color='purple', width=2)
        ),
        row=2, col=1
    )
    
    # RSI levels
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1,
                  annotation_text="Overbought", annotation_position="right")
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1,
                  annotation_text="Oversold", annotation_position="right")
    
    # Row 3: MACD
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['macd'],
            mode='lines',
            name='MACD',
            line=dict(color='blue', width=2)
        ),
        row=3, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['macd_signal'],
            mode='lines',
            name='Signal',
            line=dict(color='red', width=2)
        ),
        row=3, col=1
    )
    
    # MACD Histogram
    colors_hist = ['green' if val >= 0 else 'red' for val in df['macd_histogram']]
    fig.add_trace(
        go.Bar(
            x=df['timestamp'],
            y=df['macd_histogram'],
            name='Histogram',
            marker_color=colors_hist,
            opacity=0.5
        ),
        row=3, col=1
    )
    
    # Row 4: Volume
    fig.add_trace(
        go.Bar(
            x=df['timestamp'],
            y=df['volume'],
            name='Volume',
            marker_color='rgba(0, 150, 255, 0.5)'
        ),
        row=4, col=1
    )
    
    # Update layout
    fig.update_layout(
        title_text="📊 Technical Analysis Dashboard",
        title_font_size=18,
        height=1200,
        showlegend=True,
        hovermode='x unified',
        xaxis_rangeslider_visible=False
    )
    
    fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
    fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])
    fig.update_yaxes(title_text="MACD", row=3, col=1)
    fig.update_yaxes(title_text="Volume", row=4, col=1)
    
    # Save
    output_file = "technical_indicators.html"
    fig.write_html(output_file)
    print(f"✅ Saved: {output_file}")
    
    return fig


def create_combined_analysis(df_prices, df_news):
    """ترکیب Sentiment + Technical Analysis"""
    print("🎨 Creating combined analysis chart...")
    
    # Aggregate daily sentiment
    df_news['date'] = df_news['published_at'].dt.date
    daily_sentiment = df_news.groupby('date').agg({
        'sentiment_score': 'mean',
        'title': 'count'
    }).reset_index()
    daily_sentiment.columns = ['date', 'avg_sentiment', 'news_count']
    daily_sentiment['date'] = pd.to_datetime(daily_sentiment['date'])
    
    # Merge with prices
    df_prices['date'] = df_prices['timestamp'].dt.date
    df_prices['date'] = pd.to_datetime(df_prices['date'])
    
    df_merged = pd.merge(
        df_prices[['date', 'close']],
        daily_sentiment,
        on='date',
        how='left'
    )
    
    # Create chart
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=(
            '💰 Gold Price & News Sentiment',
            '📊 Sentiment vs Price Change Correlation'
        ),
        specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
        row_heights=[0.6, 0.4],
        vertical_spacing=0.12
    )
    
    # Row 1: Price & Sentiment overlay
    fig.add_trace(
        go.Scatter(
            x=df_merged['date'],
            y=df_merged['close'],
            mode='lines',
            name='Gold Price',
            line=dict(color='gold', width=3)
        ),
        row=1, col=1, secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            x=df_merged['date'],
            y=df_merged['avg_sentiment'],
            mode='lines+markers',
            name='Avg Sentiment',
            line=dict(color='blue', width=2),
            marker=dict(size=8)
        ),
        row=1, col=1, secondary_y=True
    )
    
    # Row 2: Scatter plot
    df_merged_clean = df_merged.dropna()
    if len(df_merged_clean) > 0:
        fig.add_trace(
            go.Scatter(
                x=df_merged_clean['avg_sentiment'],
                y=df_merged_clean['close'],
                mode='markers',
                name='Data Points',
                marker=dict(
                    size=10,
                    color=df_merged_clean['news_count'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="News Count")
                ),
                text=df_merged_clean['date'],
                hovertemplate='<b>Date:</b> %{text}<br>' +
                              '<b>Sentiment:</b> %{x:.3f}<br>' +
                              '<b>Price:</b> $%{y:.2f}<br>' +
                              '<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Trendline
        if len(df_merged_clean) > 1:
            z = np.polyfit(
                df_merged_clean['avg_sentiment'].dropna(),
                df_merged_clean['close'].dropna(),
                1
            )
            p = np.poly1d(z)
            x_trend = np.linspace(
                df_merged_clean['avg_sentiment'].min(),
                df_merged_clean['avg_sentiment'].max(),
                100
            )
            
            corr = df_merged_clean['avg_sentiment'].corr(df_merged_clean['close'])
            
            fig.add_trace(
                go.Scatter(
                    x=x_trend,
                    y=p(x_trend),
                    mode='lines',
                    name=f'Trendline (r={corr:.3f})',
                    line=dict(color='red', width=2, dash='dash')
                ),
                row=2, col=1
            )
    
    # Update layout
    fig.update_layout(
        title_text="🔗 Sentiment-Price Correlation Analysis",
        title_font_size=18,
        height=900,
        showlegend=True,
        hovermode='closest'
    )
    
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_yaxes(title_text="Gold Price (USD)", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Sentiment Score", row=1, col=1, secondary_y=True)
    fig.update_xaxes(title_text="Average Sentiment Score", row=2, col=1)
    fig.update_yaxes(title_text="Gold Price (USD)", row=2, col=1)
    
    # Save
    output_file = "combined_analysis.html"
    fig.write_html(output_file)
    print(f"✅ Saved: {output_file}")
    
    return fig


def main():
    """اجرای اصلی"""
    print("\n" + "="*60)
    print("🏆 GOLD PRICE ANALYZER - COMPLETE VISUALIZATION")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"👨‍💻 Author: Hoseyn Doulabi (@hoseynd-ai)")
    print("="*60 + "\n")
    
    try:
        # Load data
        df_prices, df_news = load_data_from_database()
        
        # Calculate indicators
        df_with_indicators = calculate_technical_indicators(df_prices)
        
        # Create visualizations
        create_sentiment_chart(df_news)
        create_technical_indicators_chart(df_with_indicators)
        create_combined_analysis(df_prices, df_news)
        
        print("\n" + "="*60)
        print("✅ ALL VISUALIZATIONS CREATED SUCCESSFULLY!")
        print("="*60)
        print("\n📁 Generated files:")
        print("  1. sentiment_analysis.html")
        print("  2. technical_indicators.html")
        print("  3. combined_analysis.html")
        print("\n💡 Open these files in your browser to view the charts!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()