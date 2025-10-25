#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dollar Index Price Model

مدل دیتابیس برای ذخیره قیمت‌های روزانه Dollar Index (DXY)

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25 17:29:12 UTC
"""

from sqlalchemy import Column, Integer, Date, Numeric, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

from app.infrastructure.database.base import Base


class DollarIndexPrice(Base):
    """
    مدل ذخیره قیمت‌های روزانه Dollar Index (DXY)
    
    Dollar Index (DXY):
    - شاخص ارزش دلار آمریکا در برابر سبد 6 ارز اصلی جهانی
    - Basket: EUR (57.6%), JPY (13.6%), GBP (11.9%), CAD (9.1%), SEK (4.2%), CHF (3.6%)
    - Base year: 1973 (Index = 100)
    - رابطه معکوس قوی با طلا (correlation: -0.7 to -0.9)
    
    Use Cases:
    - Feature برای پیش‌بینی قیمت طلا
    - تحلیل تأثیر قدرت دلار روی بازار طلا
    - Correlation analysis
    """
    __tablename__ = "dollar_index_prices"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Date (unique - یک رکورد برای هر روز)
    date = Column(
        Date, 
        unique=True, 
        nullable=False, 
        index=True,
        comment="تاریخ روز معاملاتی"
    )
    
    # OHLC Data
    open = Column(
        Numeric(10, 4), 
        nullable=False,
        comment="قیمت باز شدن (Opening Price)"
    )
    
    high = Column(
        Numeric(10, 4), 
        nullable=False,
        comment="بالاترین قیمت روز (High)"
    )
    
    low = Column(
        Numeric(10, 4), 
        nullable=False,
        comment="پایین‌ترین قیمت روز (Low)"
    )
    
    close = Column(
        Numeric(10, 4), 
        nullable=False,
        comment="قیمت بسته شدن (Closing Price)"
    )
    
    # Metadata
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="زمان ایجاد رکورد"
    )
    
    updated_at = Column(
        DateTime(timezone=True), 
        onupdate=func.now(),
        comment="زمان آخرین به‌روزرسانی"
    )
    
    def __repr__(self):
        return f"<DollarIndexPrice(date={self.date}, close={self.close})>"
    
    @property
    def change(self) -> float:
        """محاسبه تغییر روزانه"""
        if self.open and self.close:
            return float(self.close - self.open)
        return 0.0
    
    @property
    def change_percent(self) -> float:
        """محاسبه درصد تغییر روزانه"""
        if self.open and self.close and self.open != 0:
            return float((self.close - self.open) / self.open * 100)
        return 0.0
    
    def to_dict(self):
        """تبدیل به dictionary"""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'open': float(self.open) if self.open else None,
            'high': float(self.high) if self.high else None,
            'low': float(self.low) if self.low else None,
            'close': float(self.close) if self.close else None,
            'change': self.change,
            'change_percent': self.change_percent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
