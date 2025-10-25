# برنامه روز ۴ - Day 4 Plan

**تاریخ شروع | Start Date:** 2025-10-25 09:01:42 UTC  
**نویسنده | Author:** حسین دولابی (Hoseyn Doulabi) (@hoseynd-ai)  
**وضعیت | Status:** 🔜 آماده شروع | Ready to Start

---

## 🎯 اهداف | Goals

### فارسی:
1. **تحلیل احساسات اخبار**
   - استفاده از FinBERT
   - تحلیل 16 خبر موجود
   - ذخیره نتایج

2. **شاخص‌های تکنیکال**
   - RSI, MACD, Bollinger Bands
   - Moving Averages
   - سیگنال‌های خرید/فروش

3. **ترکیب و تست**
   - Sentiment + Technical correlation
   - Prediction model
   - Backtesting

### English:
1. **News Sentiment Analysis**
   - Using FinBERT
   - Analyze 16 existing articles
   - Save results

2. **Technical Indicators**
   - RSI, MACD, Bollinger Bands
   - Moving Averages
   - Buy/Sell signals

3. **Integration & Testing**
   - Sentiment + Technical correlation
   - Prediction model
   - Backtesting

---

## 📦 پیش‌نیازها | Prerequisites

### فارسی:

**کتابخانه‌های مورد نیاز:**
```bash
pip install transformers torch
pip install ta pandas-ta
pip install scikit-learn
pip install plotly kaleido
```

**داده‌های موجود:**
- ✅ 100 روز قیمت طلا (OHLCV)
- ✅ 16 خبر با توزیع زمانی
- ✅ Database آماده

### English:

**Required Libraries:**
```bash
pip install transformers torch
pip install ta pandas-ta
pip install scikit-learn
pip install plotly kaleido
```

**Available Data:**
- ✅ 100 days gold prices (OHLCV)
- ✅ 16 news articles with time distribution
- ✅ Database ready

---

## 🚀 فاز ۱: Sentiment Analysis

### معماری | Architecture

```
Input: News Article
    ↓
FinBERT Model (ProsusAI/finbert)
    ↓
Sentiment Score (-1 to +1)
    ↓
Save to Database
    ↓
Correlate with Price Movement
```

### فایل‌ها | Files

```
app/application/services/ml/
├── __init__.py
├── sentiment_analysis_service.py
└── models/
    └── finbert/  (auto-downloaded)

tests/integration/
└── test_sentiment_analysis.py
```

---

## 📊 فاز ۲: Technical Indicators

### شاخص‌ها | Indicators

**1. RSI (Relative Strength Index)**
```
فارسی: شاخص قدرت نسبی
محدوده: 0-100
> 70: اشباع خرید (Overbought)
< 30: اشباع فروش (Oversold)
```

**2. MACD (Moving Average Convergence Divergence)**
```
فارسی: همگرایی/واگرایی میانگین متحرک
سیگنال خرید: MACD > Signal
سیگنال فروش: MACD < Signal
```

**3. Bollinger Bands**
```
فارسی: باندهای بولینگر
3 خط: Upper, Middle (SMA), Lower
قیمت نزدیک Upper: احتمال برگشت
قیمت نزدیک Lower: احتمال صعود
```

---

## 🎨 نمودارها | Visualizations

### پلن‌شده | Planned

1. **Sentiment Timeline**
   - محور X: زمان
   - محور Y: Sentiment Score
   - رنگ: مثبت/منفی/خنثی

2. **Price + Indicators**
   - Candlestick chart
   - RSI overlay
   - MACD histogram
   - Bollinger Bands

3. **Correlation Heatmap**
   - Sentiment vs Price Change
   - Technical signals vs Returns
   - Combined score

---

## ⏱️ جدول زمانی | Timeline

| زمان | وظیفه | وضعیت |
|------|-------|-------|
| ساعت 1-2 | Sentiment Analysis | 🔜 آماده |
| ساعت 3-4 | Technical Indicators | ⏳ در انتظار |
| ساعت 5-6 | Integration | ⏳ در انتظار |
| ساعت 6+ | Testing & Docs | ⏳ در انتظار |

---

## 📝 یادداشت‌ها | Notes

### فارسی:
- همه کدها با کامنت فارسی
- مستندات دوزبانه
- تست‌های کامل
- خطاهای احتمالی و راه‌حل‌ها

### English:
- All code with Persian comments
- Bilingual documentation
- Complete tests
- Potential errors & solutions

---

**آماده شروع! | Ready to Start!** 🚀

*این فایل در طول روز آپدیت می‌شود | This file will be updated throughout the day*

---
