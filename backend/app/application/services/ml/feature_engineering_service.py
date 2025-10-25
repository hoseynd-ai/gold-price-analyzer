#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Price Analyzer - Feature Engineering Service

ترکیب تمام داده‌ها برای ML Training:
- قیمت‌های تاریخی (OHLCV)
- اندیکاتورهای تکنیکال (RSI, MACD, BB)
- احساسات اخبار (Sentiment scores)

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25 15:32:52 UTC
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple, Optional
from sqlalchemy import create_engine, text

from app.application.services.ml.technical_indicators_service import TechnicalIndicatorsService
from app.core.logging import get_logger

logger = get_logger(__name__)


class FeatureEngineeringService:
    """
    سرویس آماده‌سازی داده برای Machine Learning
    
    این سرویس تمام داده‌های مورد نیاز برای training را ترکیب می‌کند:
    1. قیمت‌های تاریخی (OHLCV)
    2. اندیکاتورهای تکنیکال
    3. Sentiment scores از اخبار
    4. Features مهندسی شده (engineered)
    """
    
    def __init__(self, database_url: str):
        """
        Initialize service
        
        Args:
            database_url: PostgreSQL connection string
        """
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.indicators_service = TechnicalIndicatorsService()
        
        logger.info("feature_engineering_service_initialized")
    
    def load_price_data(self, start_date: Optional[str] = None) -> pd.DataFrame:
        """
        بارگذاری داده‌های قیمت از database
        
        Args:
            start_date: تاریخ شروع (اختیاری)
            
        Returns:
            DataFrame با ستون‌های: timestamp, open, high, low, close, volume
        """
        logger.info("loading_price_data", start_date=start_date)
        
        query = """
        SELECT 
            timestamp,
            open,
            high,
            low,
            close,
            volume
        FROM gold_price_facts
        WHERE timeframe = 'daily'
            AND source = 'alpha_vantage_gold_converted'
        """
        
        if start_date:
            query += f" AND timestamp >= '{start_date}'"
        
        query += " ORDER BY timestamp ASC;"
        
        df = pd.read_sql(query, self.engine)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        logger.info("price_data_loaded", records=len(df))
        return df
    
    def load_sentiment_data(self, start_date: Optional[str] = None) -> pd.DataFrame:
        """
        بارگذاری sentiment scores از اخبار
        
        Args:
            start_date: تاریخ شروع (اختیاری)
            
        Returns:
            DataFrame با ستون‌های: date, sentiment_score, news_count
        """
        logger.info("loading_sentiment_data", start_date=start_date)
        
        query = """
        SELECT 
            DATE(published_at) as date,
            AVG(sentiment_score) as sentiment_score,
            COUNT(*) as news_count
        FROM news_events
        WHERE sentiment_score IS NOT NULL
        """
        
        if start_date:
            query += f" AND published_at >= '{start_date}'"
        
        query += " GROUP BY DATE(published_at) ORDER BY date ASC;"
        
        df = pd.read_sql(query, self.engine)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        
        logger.info("sentiment_data_loaded", records=len(df))
        return df
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        اضافه کردن اندیکاتورهای تکنیکال
        
        Args:
            df: DataFrame با قیمت‌ها
            
        Returns:
            DataFrame با اندیکاتورها
        """
        logger.info("calculating_technical_indicators")
        
        # محاسبه اندیکاتورها
        df_with_indicators = self.indicators_service.calculate_all_indicators(df)
        
        # حذف NaN ها (از اول که اندیکاتورها هنوز محاسبه نشدن)
        df_with_indicators = df_with_indicators.dropna()
        
        logger.info("technical_indicators_added", 
                   indicators=['RSI', 'MACD', 'BB', 'SMA', 'EMA'])
        
        return df_with_indicators
    
    def add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        اضافه کردن features مهندسی شده از قیمت
        
        Args:
            df: DataFrame اصلی
            
        Returns:
            DataFrame با features جدید
        """
        logger.info("engineering_price_features")
        
        # 1. Returns (بازده)
        df['returns'] = df['close'].pct_change()
        df['returns_5d'] = df['close'].pct_change(5)
        df['returns_10d'] = df['close'].pct_change(10)
        df['returns_20d'] = df['close'].pct_change(20)
        
        # 2. Volatility (نوسانات)
        df['volatility_5d'] = df['returns'].rolling(5).std()
        df['volatility_10d'] = df['returns'].rolling(10).std()
        df['volatility_20d'] = df['returns'].rolling(20).std()
        
        # 3. Price Range
        df['high_low_ratio'] = df['high'] / df['low']
        df['close_open_ratio'] = df['close'] / df['open']
        
        # 4. Volume features
        df['volume_sma_5'] = df['volume'].rolling(5).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_5']
        
        # 5. Lag features (قیمت‌های روزهای قبل)
        for lag in [1, 2, 3, 5, 7]:
            df[f'close_lag_{lag}'] = df['close'].shift(lag)
            df[f'returns_lag_{lag}'] = df['returns'].shift(lag)
        
        logger.info("price_features_added", 
                   features=['returns', 'volatility', 'ratios', 'lags'])
        
        return df
    
    def merge_sentiment_data(
        self, 
        df_price: pd.DataFrame, 
        df_sentiment: pd.DataFrame
    ) -> pd.DataFrame:
        """
        ترکیب داده‌های قیمت و sentiment
        
        Args:
            df_price: DataFrame قیمت‌ها
            df_sentiment: DataFrame sentiment
            
        Returns:
            DataFrame ترکیب شده
        """
        logger.info("merging_sentiment_data")
        
        # تبدیل index به date (بدون ساعت)
        df_price_copy = df_price.copy()
        df_price_copy['date'] = df_price_copy.index.date
        df_price_copy['date'] = pd.to_datetime(df_price_copy['date'])
        
        # Merge
        df_merged = df_price_copy.merge(
            df_sentiment,
            left_on='date',
            right_index=True,
            how='left'
        )
        
        # حذف ستون date اضافی
        df_merged = df_merged.drop('date', axis=1)
        
        # پر کردن NaN های sentiment با 0 (روزهایی که خبر نبوده)
        df_merged['sentiment_score'] = df_merged['sentiment_score'].fillna(0)
        df_merged['news_count'] = df_merged['news_count'].fillna(0)
        
        # اضافه کردن features sentiment
        df_merged['sentiment_lag_1'] = df_merged['sentiment_score'].shift(1)
        df_merged['sentiment_lag_3'] = df_merged['sentiment_score'].shift(3)
        df_merged['sentiment_ma_5'] = df_merged['sentiment_score'].rolling(5).mean()
        
        logger.info("sentiment_data_merged", 
                   sentiment_days=df_sentiment.shape[0],
                   total_days=df_merged.shape[0])
        
        return df_merged
    
    def create_target_variable(
        self, 
        df: pd.DataFrame, 
        horizon: int = 1
    ) -> pd.DataFrame:
        """
        ساخت target variable برای پیش‌بینی
        
        Args:
            df: DataFrame اصلی
            horizon: چند روز آینده (1 = فردا، 7 = 1 هفته، 30 = 1 ماه)
            
        Returns:
            DataFrame با target variable
        """
        logger.info("creating_target_variable", horizon=horizon)
        
        # Target: قیمت N روز آینده
        df[f'target_price_{horizon}d'] = df['close'].shift(-horizon)
        
        # Target: بازده N روز آینده
        df[f'target_return_{horizon}d'] = (
            df[f'target_price_{horizon}d'] / df['close'] - 1
        )
        
        # Target: جهت حرکت (صعودی/نزولی)
        df[f'target_direction_{horizon}d'] = (
            df[f'target_return_{horizon}d'] > 0
        ).astype(int)
        
        logger.info("target_variable_created",
                   target_price=f'target_price_{horizon}d',
                   target_return=f'target_return_{horizon}d',
                   target_direction=f'target_direction_{horizon}d')
        
        return df
    
    def prepare_ml_dataset(
        self,
        start_date: Optional[str] = None,
        prediction_horizon: int = 1
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        آماده‌سازی کامل dataset برای ML
        
        این تابع:
        1. داده‌های قیمت را می‌خواند
        2. اندیکاتورها را محاسبه می‌کند
        3. Features قیمت را اضافه می‌کند
        4. Sentiment را merge می‌کند
        5. Target variable را می‌سازد
        6. داده را split می‌کند
        
        Args:
            start_date: تاریخ شروع (اختیاری)
            prediction_horizon: چند روز آینده پیش‌بینی شود
            
        Returns:
            (X, y) - Features و Target
        """
        logger.info("preparing_ml_dataset",
                   start_date=start_date,
                   horizon=prediction_horizon)
        
        # 1. بارگذاری قیمت‌ها
        df_price = self.load_price_data(start_date)
        logger.info("step_1_price_loaded", shape=df_price.shape)
        
        # 2. اندیکاتورها
        df_price = self.add_technical_indicators(df_price)
        logger.info("step_2_indicators_added", shape=df_price.shape)
        
        # 3. Price features
        df_price = self.add_price_features(df_price)
        logger.info("step_3_features_added", shape=df_price.shape)
        
        # 4. Sentiment
        df_sentiment = self.load_sentiment_data(start_date)
        df_complete = self.merge_sentiment_data(df_price, df_sentiment)
        logger.info("step_4_sentiment_merged", shape=df_complete.shape)
        
        # 5. Target variable
        df_complete = self.create_target_variable(df_complete, prediction_horizon)
        logger.info("step_5_target_created", shape=df_complete.shape)
        
        # 6. حذف NaN ها
        df_complete = df_complete.dropna()
        logger.info("step_6_nans_removed", shape=df_complete.shape)
        
        # 7. جداسازی X و y
        target_cols = [
            f'target_price_{prediction_horizon}d',
            f'target_return_{prediction_horizon}d',
            f'target_direction_{prediction_horizon}d'
        ]
        
        feature_cols = [col for col in df_complete.columns if col not in target_cols]
        
        X = df_complete[feature_cols]
        y = df_complete[[f'target_price_{prediction_horizon}d']]
        
        logger.info("ml_dataset_ready",
                   X_shape=X.shape,
                   y_shape=y.shape,
                   features=len(feature_cols))
        
        return X, y
    
    def get_feature_names(self, X: pd.DataFrame) -> dict:
        """
        دریافت لیست features به تفکیک دسته
        
        Args:
            X: DataFrame features
            
        Returns:
            دیکشنری features
        """
        feature_groups = {
            'price': [],
            'technical': [],
            'sentiment': [],
            'engineered': []
        }
        
        for col in X.columns:
            if col in ['open', 'high', 'low', 'close', 'volume']:
                feature_groups['price'].append(col)
            elif any(ind in col for ind in ['rsi', 'macd', 'bb', 'sma', 'ema']):
                feature_groups['technical'].append(col)
            elif 'sentiment' in col or 'news' in col:
                feature_groups['sentiment'].append(col)
            else:
                feature_groups['engineered'].append(col)
        
        return feature_groups


if __name__ == "__main__":
    # تست
    print("\n" + "="*70)
    print("🧪 Testing Feature Engineering Service")
    print("="*70 + "\n")
    
    DATABASE_URL = "postgresql+psycopg2://admin:admin123@localhost:5432/gold_analyzer"
    
    service = FeatureEngineeringService(DATABASE_URL)
    
    # آماده‌سازی dataset
    X, y = service.prepare_ml_dataset(prediction_horizon=1)
    
    print(f"\n📊 Dataset Ready:")
    print(f"   X shape: {X.shape}")
    print(f"   y shape: {y.shape}")
    print(f"   Features: {X.shape[1]}")
    
    # نمایش feature groups
    feature_groups = service.get_feature_names(X)
    print(f"\n📋 Feature Groups:")
    for group, features in feature_groups.items():
        print(f"   {group}: {len(features)} features")
    
    print("\n" + "="*70)
    print("✅ Feature Engineering Service Test Complete!")
    print("="*70 + "\n")
