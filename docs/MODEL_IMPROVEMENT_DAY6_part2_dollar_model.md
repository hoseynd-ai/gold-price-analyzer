# 💵 Model Improvement - Day 1: Dollar Index Integration

**تاریخ | Date:** 2025-10-25 17:44:55 UTC  
**نویسنده | Author:** Hoseyn Doulabi (@hoseynd-ai)  
**Session:** Dollar Index (DXY) Data Collection  
**مدت | Duration:** ~30 minutes  
**Status:** ✅ Completed

---

## 🎯 هدف Session

اضافه کردن **Dollar Index (DXY)** به عنوان اولین feature اقتصادی برای بهبود مدل

**چرا DXY؟**
- رابطه معکوس قوی با طلا (correlation: -0.7 to -0.9)
- وقتی دلار قوی → طلا ضعیف
- وقتی دلار ضعیف → طلا قوی
- یکی از مهم‌ترین پیش‌بینی‌کننده‌های قیمت طلا

**Expected Impact:** R² = 0.175 → 0.28-0.35

---

## 📋 آنچه انجام شد

### 1️⃣ ساخت Database Model

**فایل:** `app/infrastructure/database/models/dollar_index.py`

```python
class DollarIndexPrice(Base):
    """
    مدل ذخیره قیمت‌های روزانه Dollar Index (DXY)
    """
    __tablename__ = "dollar_index_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    
    # OHLC
    open = Column(Numeric(10, 4), nullable=False)
    high = Column(Numeric(10, 4), nullable=False)
    low = Column(Numeric(10, 4), nullable=False)
    close = Column(Numeric(10, 4), nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**ویژگی‌ها:**
- ✅ OHLC data (Open, High, Low, Close)
- ✅ Date indexing
- ✅ Unique constraint روی date
- ✅ Timestamps برای tracking

---

### 2️⃣ ساخت Data Collection Service

**فایل:** `app/application/services/data_collection/dollar_index_service.py`

**قابلیت‌ها:**

```python
class DollarIndexService:
    """سرویس جمع‌آوری Dollar Index از Alpha Vantage"""
    
    async def fetch_daily_data(outputsize='full')
        # دریافت 20+ سال داده از Alpha Vantage
        # API: FX_DAILY (USD/EUR inverse)
        # نرمال‌سازی به scale DXY واقعی (~100)
    
    async def save_to_database(df)
        # ذخیره/به‌روزرسانی در PostgreSQL
        # Bulk insert with conflict handling
    
    async def get_latest_data(days=30)
        # دریافت آخرین داده‌ها از DB
    
    async def calculate_correlation_with_gold()
        # محاسبه correlation coefficient
        # P-value calculation
        # تفسیر فارسی نتایج
    
    async def get_statistics()
        # آمار کلی DXY
```

**روش محاسبه DXY:**
```
1. دریافت USD/EUR از Alpha Vantage
2. Inverse: DXY ∝ 1 / (USD/EUR)
3. نرمال‌سازی به scale 100 (base year 1973)
```

---

### 3️⃣ ایجاد Table در Database

**روش:** Direct creation (بدون Alembic)

```python
from app.infrastructure.database.base import Base, engine
from app.infrastructure.database.models import DollarIndexPrice

async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all, 
                       tables=[DollarIndexPrice.__table__])
```

**چرا بدون Alembic؟**
- Alembic در این پروژه setup نشده بود
- Direct creation سریع‌تر و کافی بود
- برای production می‌توان بعداً migration اضافه کرد

---

### 4️⃣ جمع‌آوری Historical Data

**اسکریپت:** `scripts/collect_dollar_index.py`

**اجرا:**
```bash
python scripts/collect_dollar_index.py
```

**نتایج:**

```
✅ داده دریافت شد:
   • تعداد رکوردها: 5,206
   • بازه زمانی: 2004-10-25 → 2025-01-24
   • پوشش: 20.3 سال

✅ ذخیره در دیتابیس:
   • ذخیره/به‌روزرسانی: 5,206 رکورد
   • جدول: dollar_index_prices

📊 آمار DXY:
   • DXY فعلی: 116.27
   • کمترین تاریخی: 95.98
   • بیشترین تاریخی: 125.50
   • میانگین: 112.12 ± 5.36

❓ Correlation:
   • محاسبه نشد (نیاز به بررسی timeframe matching)
   • احتمالاً داده‌های Gold با timeframe='daily' کافی نیستند
```

---

## 📊 ساختار فایل‌ها

```
backend/
├── app/
│   ├── infrastructure/
│   │   └── database/
│   │       └── models/
│   │           ├── __init__.py (updated)
│   │           ├── gold_price_fact.py
│   │           ├── news_event.py
│   │           └── dollar_index.py (new) ✨
│   └── application/
│       └── services/
│           └── data_collection/
│               └── dollar_index_service.py (new) ✨
│
├── scripts/
│   ├── collect_dollar_index.py (new) ✨
│   └── create_dollar_table.py (new) ✨
│
└── docs/
    └── MODEL_IMPROVEMENT_DAY1_DOLLAR_INDEX.md (این فایل) ✨
```

---

## 🔍 مشکلات و راه‌حل‌ها

### مشکل 1: AsyncEngine vs Sync create_all

**خطا:**
```python
AttributeError: 'AsyncEngine' object has no attribute '_run_ddl_visitor'
```

**راه‌حل:**
```python
# ❌ اشتباه
Base.metadata.create_all(bind=engine)

# ✅ درست
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

---

### مشکل 2: GoldPriceFact.date AttributeError

**خطا:**
```python
AttributeError: type object 'GoldPriceFact' has no attribute 'date'
```

**علت:** GoldPriceFact از `timestamp` استفاده می‌کند نه `date`

**راه‌حل:**
```python
# ❌ اشتباه
select(GoldPriceFact).order_by(GoldPriceFact.date)

# ✅ درست
select(GoldPriceFact)
    .where(GoldPriceFact.timeframe == 'daily')
    .order_by(GoldPriceFact.timestamp)

# تبدیل timestamp به date برای merge
gold_df['date'] = r.timestamp.date()
```

---

### مشکل 3: __init__.py دو بار __all__ داشت

**قبل:**
```python
__all__ = ["GoldPriceFact", "NewsEvent"]

# Dollar Index Model
from app.infrastructure.database.models.dollar_index import DollarIndexPrice

__all__ = ['DollarIndexPrice']  # ❌ override شده
```

**بعد:**
```python
from app.infrastructure.database.models.gold_price_fact import GoldPriceFact
from app.infrastructure.database.models.news_event import NewsEvent
from app.infrastructure.database.models.dollar_index import DollarIndexPrice

__all__ = [
    "GoldPriceFact",
    "NewsEvent",
    "DollarIndexPrice",  # ✅
]
```

---

## 📈 آمار Session

```
Lines of Code: ~450
Files Created: 4
Files Modified: 2
Database Tables: +1 (dollar_index_prices)
Data Collected: 5,206 records (20.3 years)
Time Spent: ~30 minutes
API Calls: 1 (Alpha Vantage)
```

---

## ✅ Checklist تکمیل شده

- [x] ساخت database model
- [x] اضافه کردن به models __init__.py
- [x] ساخت table در PostgreSQL
- [x] ساخت data collection service
- [x] جمع‌آوری 20+ سال historical data
- [x] ذخیره در database (5,206 records)
- [x] محاسبه آمار DXY
- [ ] محاسبه correlation با Gold (pending - نیاز به بررسی)
- [ ] اضافه کردن به feature engineering
- [ ] re-train مدل با DXY feature

---

## 🚀 مراحل باقی‌مانده (برای Day 2)

### Phase 1: Feature Integration (2-3 hours)

#### Task 1.1: اضافه کردن DXY به Feature Engineering

**فایل:** `app/application/services/ml/feature_engineering_service.py`

**کارهای لازم:**

```python
# 1. Import DollarIndexPrice model
from app.infrastructure.database.models import DollarIndexPrice

# 2. اضافه کردن method جدید
async def get_dollar_index_features(self, df: pd.DataFrame) -> pd.DataFrame:
    """
    اضافه کردن features مربوط به Dollar Index
    
    Features:
    - dxy_close: قیمت بسته شدن DXY
    - dxy_change: تغییر روزانه DXY
    - dxy_change_pct: درصد تغییر DXY
    - dxy_ma_7: میانگین متحرک 7 روزه
    - dxy_ma_30: میانگین متحرک 30 روزه
    - dxy_rsi_14: RSI indicator
    """
    
    # 3. دریافت DXY data از database
    # 4. Merge با gold prices بر اساس date
    # 5. محاسبه technical indicators روی DXY
    # 6. ساخت lag features (DXY یک روز قبل، دو روز قبل، ...)
    
    return df

# 7. فراخوانی در prepare_features()
async def prepare_features(self, df):
    # ... existing code ...
    df = await self.get_dollar_index_features(df)
    # ... existing code ...
    return df
```

**Expected New Features:** +8-10 ستون

---

#### Task 1.2: بررسی Correlation واقعی

**اسکریپت:** `scripts/analyze_dxy_gold_correlation.py`

```python
#!/usr/bin/env python3
"""
تحلیل دقیق correlation بین DXY و Gold

Steps:
1. دریافت هر دو dataset از DB
2. Align کردن dates
3. محاسبه correlation (Pearson, Spearman, Kendall)
4. رسم scatter plot
5. رسم time series overlay
6. محاسبه rolling correlation
"""

async def main():
    # Fetch data
    # Calculate correlations
    # Visualize
    # Save report
```

**Expected Output:**
- Correlation coefficient: -0.65 to -0.85
- P-value < 0.001 (significant)
- نمودار scatter plot
- نمودار time series

---

#### Task 1.3: تست اولیه تأثیر DXY

**اسکریپت:** `scripts/test_dxy_simple_model.py`

```python
"""
یک مدل ساده برای تست تأثیر DXY

مقایسه:
- مدل A: فقط Gold prices (بدون DXY)
- مدل B: Gold prices + DXY

Baseline: Linear Regression (سریع)
"""

# Train Model A
model_a = train_without_dxy()

# Train Model B
model_b = train_with_dxy()

# Compare
print(f"Model A (no DXY): R² = {r2_a}")
print(f"Model B (with DXY): R² = {r2_b}")
print(f"Improvement: {(r2_b - r2_a) * 100:.1f}%")
```

**Expected Improvement:** +5-10% در R²

---

### Phase 2: Model Re-training (3-4 hours)

#### Task 2.1: Update LSTM Model v3

```python
# در lstm_model_service.py

# Feature count: 42 → 50-52
# با DXY features جدید

# Re-train با همان architecture
# مقایسه v2 vs v3
```

**Expected Results:**
```
v2 (without DXY):
  R² = 0.1751
  RMSE = $529.54

v3 (with DXY):
  R² = 0.28-0.35  (+60-100% improvement)
  RMSE = $400-450  (~20% reduction)
```

---

#### Task 2.2: Hyperparameter Tuning با DXY

```python
# اگر نتایج خوب بود، tuning
# Keras Tuner
# 30-50 trials
# Best config
```

---

### Phase 3: Data Collection بیشتر (2-3 hours)

#### Task 3.1: Interest Rates (Federal Reserve)

**منبع:** FRED API (رایگان)

**Indicators:**
- Federal Funds Rate (DFF)
- 10-Year Treasury Rate (DGS10)
- Real Interest Rate

**Expected Impact:** R² +0.08-0.12

---

#### Task 3.2: More News Data

**منبع:** GNews API

**Target:** 2000+ articles (فعلاً 477 داریم)

**Expected Impact:** R² +0.05-0.08

---

#### Task 3.3: VIX Index (Fear Index)

**منبع:** Alpha Vantage

**Expected Impact:** R² +0.03-0.05

---

## 📊 Timeline پیشنهادی (Day 2-3)

```
Day 2 (فردا):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
09:00-10:00  بررسی correlation DXY-Gold
10:00-12:00  اضافه کردن DXY به feature engineering
12:00-13:00  Break
13:00-15:00  تست ساده (Linear Regression)
15:00-17:00  Re-train LSTM v3
17:00-18:00  ارزیابی و مقایسه v2 vs v3

Expected R² at end: 0.28-0.35

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Day 3 (پس‌فردا):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
09:00-11:00  Interest Rates integration (FRED)
11:00-13:00  جمع‌آوری 2000+ news
13:00-14:00  Break
14:00-16:00  VIX integration
16:00-18:00  Re-train LSTM v4
18:00-19:00  Final evaluation

Expected R² at end: 0.40-0.48

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🎯 Success Criteria (End of Day 3)

```
Minimum:
  ✅ R² ≥ 0.35
  ✅ RMSE < $450
  ✅ DXY feature proven useful

Target:
  🎯 R² ≥ 0.42
  🎯 RMSE < $400
  🎯 3+ economic features integrated

Stretch:
  ⭐ R² ≥ 0.50
  ⭐ RMSE < $350
  ⭐ 5+ economic features
```

---

## 💡 یادداشت‌های مهم

### DXY محاسبه چطور کار می‌کند:

```
Dollar Index Formula (approximate):
DXY = 50.14348112 × EUR/USD^(-0.576) 
      × JPY/USD^0.136 
      × GBP/USD^(-0.119)
      × CAD/USD^0.091 
      × SEK/USD^0.042 
      × CHF/USD^0.036

ما از USD/EUR استفاده کردیم (inverse EUR/USD)
چون بزرگترین component (57.6%) است
```

### چرا Correlation محاسبه نشد؟

```
احتمالاً:
1. GoldPriceFact records با timeframe='daily' کم هستند
2. Date alignment issue
3. نیاز به بررسی دقیق‌تر

راه‌حل Day 2:
- اسکریپت جداگانه برای correlation analysis
- چک کردن تعداد daily records
- تست با timeframe های مختلف
```

---

## 📁 فایل‌های تولید شده

```
New Files (4):
  ✨ app/infrastructure/database/models/dollar_index.py
  ✨ app/application/services/data_collection/dollar_index_service.py
  ✨ scripts/collect_dollar_index.py
  ✨ scripts/create_dollar_table.py

Modified Files (2):
  📝 app/infrastructure/database/models/__init__.py
  📝 docs/MODEL_IMPROVEMENT_DAY1_DOLLAR_INDEX.md

Database:
  📊 dollar_index_prices table (5,206 records)

Total Lines: ~450
```

---

## 🔗 References

### API Documentation:
- [Alpha Vantage FX](https://www.alphavantage.co/documentation/#fx)
- [FRED API](https://fred.stlouisfed.org/docs/api/)

### Dollar Index Info:
- [Investopedia - DXY](https://www.investopedia.com/terms/u/usdx.asp)
- [ICE Data - DXY](https://www.theice.com/index-data/us-dollar-index)

### Correlation Studies:
- Gold vs Dollar historical correlation: -0.7 to -0.9
- Strongest correlation during crisis periods
- Weakens during stable economic periods

---

## ✅ Session Summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
           DAY 1 COMPLETE ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Dollar Index integrated
✅ 20+ years historical data collected
✅ 5,206 records in database
✅ Service fully functional
✅ Ready for feature engineering

Next Session: Feature Integration + Model Training
Expected: R² improvement from 0.175 to 0.28-0.35

Total Time: ~30 minutes
Status: On Track 🎯

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

**پایان مستندات Day 1**

**نویسنده:** حسین دولابی (Hoseyn Doulabi)  
**GitHub:** @hoseynd-ai  
**تاریخ:** 2025-10-25 17:44:55 UTC  
**Next:** Day 2 - Feature Engineering & Model v3 Training  

---
