#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Price Analyzer - Technical Indicators Service

محاسبه شاخص‌های تکنیکال برای تحلیل قیمت طلا

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25
"""

import pandas as pd
import numpy as np
from typing import Dict


class TechnicalIndicatorsService:
    """سرویس محاسبه شاخص‌های تکنیکال"""
    
    def calculate_sma(self, data: pd.Series, period: int = 20) -> pd.Series:
        """محاسبه میانگین متحرک ساده (SMA)"""
        return data.rolling(window=period).mean()
    
    def calculate_ema(self, data: pd.Series, period: int = 20) -> pd.Series:
        """محاسبه میانگین متحرک نمایی (EMA)"""
        return data.ewm(span=period, adjust=False).mean()
    
    def calculate_rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        """محاسبه RSI (Relative Strength Index)"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(
        self, 
        data: pd.Series, 
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Dict[str, pd.Series]:
        """محاسبه MACD"""
        ema_fast = self.calculate_ema(data, fast_period)
        ema_slow = self.calculate_ema(data, slow_period)
        macd_line = ema_fast - ema_slow
        signal_line = self.calculate_ema(macd_line, signal_period)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def calculate_bollinger_bands(
        self,
        data: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """محاسبه باندهای بولینگر"""
        middle_band = self.calculate_sma(data, period)
        std = data.rolling(window=period).std()
        upper_band = middle_band + (std_dev * std)
        lower_band = middle_band - (std_dev * std)
        
        return {
            'upper': upper_band,
            'middle': middle_band,
            'lower': lower_band
        }
    
    def calculate_all_indicators(
        self,
        df: pd.DataFrame,
        price_column: str = 'close'
    ) -> pd.DataFrame:
        """محاسبه همه اندیکاتورها"""
        result = df.copy()
        prices = df[price_column]
        
        # Moving Averages
        result['sma_20'] = self.calculate_sma(prices, 20)
        result['sma_50'] = self.calculate_sma(prices, 50)
        result['ema_12'] = self.calculate_ema(prices, 12)
        result['ema_26'] = self.calculate_ema(prices, 26)
        
        # RSI
        result['rsi'] = self.calculate_rsi(prices, 14)
        
        # MACD
        macd_data = self.calculate_macd(prices)
        result['macd'] = macd_data['macd']
        result['macd_signal'] = macd_data['signal']
        result['macd_histogram'] = macd_data['histogram']
        
        # Bollinger Bands
        bb_data = self.calculate_bollinger_bands(prices)
        result['bb_upper'] = bb_data['upper']
        result['bb_middle'] = bb_data['middle']
        result['bb_lower'] = bb_data['lower']
        
        return result
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """تولید سیگنال‌های خرید/فروش"""
        result = df.copy()
        
        # RSI signals
        result['rsi_signal'] = 'neutral'
        result.loc[result['rsi'] > 70, 'rsi_signal'] = 'overbought'
        result.loc[result['rsi'] < 30, 'rsi_signal'] = 'oversold'
        
        # MACD signals
        result['macd_signal_type'] = 'neutral'
        result.loc[result['macd'] > result['macd_signal'], 'macd_signal_type'] = 'bullish'
        result.loc[result['macd'] < result['macd_signal'], 'macd_signal_type'] = 'bearish'
        
        # Bollinger Bands signals
        result['bb_signal'] = 'neutral'
        result.loc[result['close'] > result['bb_upper'], 'bb_signal'] = 'overbought'
        result.loc[result['close'] < result['bb_lower'], 'bb_signal'] = 'oversold'
        
        return result


if __name__ == "__main__":
    print("✅ Technical Indicators Service loaded!")
