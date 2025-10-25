# 📊 Day 5 (Part 2) - LSTM Model Improvement & News Collection

**تاریخ | Date:** 2025-10-25 16:27:20 UTC  
**نویسنده | Author:** Hoseyn Doulabi (@hoseynd-ai)  
**Session:** Model Training & Improvement  
**مدت | Duration:** ~2 hours  

---

## 🎯 خلاصه اجرایی

در این session:
1. ✅ مدل LSTM اولیه train شد (R²=0.053)
2. ✅ نتایج تحلیل و مشکلات شناسایی شد
3. ✅ NewsAPI برای جمع‌آوری اخبار تاریخی اضافه شد
4. ✅ 477 خبر جمع‌آوری و با FinBERT تحلیل شد
5. ⏳ مدل بهبود یافته در حال training (الان)

---

## 📋 فهرست

1. [Training اولیه](#training-اولیه)
2. [تحلیل نتایج](#تحلیل-نتایج)
3. [راه‌های بهبود](#راههای-بهبود)
4. [NewsAPI Integration](#newsapi-integration)
5. [جمع‌آوری اخبار](#جمعآوری-اخبار)
6. [Improved Training](#improved-training)
7. [فایل‌های ساخته شده](#فایلهای-ساخته-شده)

---

## 🧠 Training اولیه

### دستور اجرا:
```bash
cd ~/desktop/gold-price-analyzer/backend
source venv/bin/activate
python scripts/train_lstm_model.py
```

### نتایج Training اول:

```
📊 Dataset:
  • X shape: (5,197, 42) - 5197 samples, 42 features
  • y shape: (5,197, 1)  - target: قیمت فردا
  • Train samples: 4,109
  • Validation samples: 1,028

🧠 Model Architecture:
  • Sequence length: 60 days
  • LSTM layers: 3 (128→64→32 units)
  • Dropout: 20%
  • Total params: ~200K

📊 Performance Metrics:
  • RMSE: $566.94
  • MAE: $417.48
  • MAPE: 15.76%
  • R²: 0.0533 ⚠️  (خیلی پایین!)

⏱️  Training time: ~15 minutes
✅ Early stopped at epoch 16
```

---

## 📊 تحلیل نتایج

### مشکلات شناسایی شده:

#### 1️⃣ R² خیلی پایین (0.053)

**یعنی چی؟**
```
مدل فقط 5.3% از الگوهای قیمت رو یاد گرفته
94.7% باقی‌مونده رو نفهمیده!

علت:
- داده sentiment خیلی کم (فقط 6 روز!)
- مدل ساده‌ست
- قیمت طلا خیلی volatile و تصادفیه
```

#### 2️⃣ RMSE بالا ($567)

**یعنی چی؟**
```
به طور متوسط $417 خطا (MAE)
ولی بعضی وقت‌ها تا $1000+ هم اشتباه می‌کنه!

مثال:
- قیمت واقعی: $2,750
- مدل گفت: $3,500 ❌ (خطای $750!)
```

#### 3️⃣ MAPE قابل قبول (15.76%)

**یعنی چی؟**
```
به طور متوسط 15.76% خطا

برای بازار مالی:
< 10%: عالی ⭐⭐⭐
10-20%: خوب ⭐⭐  ← ما اینجاییم
> 20%: ضعیف ⭐

نتیجه: مدل "قابل قبول" است ولی نه عالی
```

---

## 🚀 راه‌های بهبود

### طرح بهبود (Improvement Plan):

```
Priority 1: جمع‌آوری اخبار بیشتر ⭐⭐⭐
  Current: 6 روز اخبار
  Target: 30+ روز (200-500 خبر)
  Impact: R² می‌تونه تا 0.3-0.5 بره

Priority 2: بهبود Architecture ⭐⭐
  Changes:
  - Sequence: 60 → 90 days
  - Units: [128,64,32] → [256,128,64]
  - Dropout: 0.2 → 0.3
  - Epochs: 50 → 100

Priority 3: Feature Engineering ⭐
  - اضافه کردن Dollar Index
  - اضافه کردن Oil Price
  - اضافه کردن VIX (fear index)
```

---

## 📰 NewsAPI Integration

### مرحله 1: دریافت API Key

```
1. رفتن به: https://newsapi.org/
2. ثبت‌نام رایگان
3. دریافت API key
4. اضافه کردن به .env
```

**API Key دریافت شده:**
```
hc_h_49eaab5cc1df450cbe56ec7a57125201
```

### مرحله 2: اضافه کردن به .env

```bash
cd ~/desktop/gold-price-analyzer/backend
nano .env
```

**افزوده شده:**
```bash
# NewsAPI Key (for historical news collection)
NEWSAPI_KEY=49eaab5cc1df450cbe56ec7a57125201
```

### مرحله 3: به‌روزرسانی config.py

**فایل:** `backend/app/core/config.py`

**تغییرات:**

```python
# افزوده شده:
DATABASE_POOL_SIZE: int = 5
DATABASE_MAX_OVERFLOW: int = 10
DATABASE_POOL_TIMEOUT: int = 30
DATABASE_ECHO: bool = False

# NewsAPI
NEWSAPI_KEY: Optional[str] = None

# Pydantic config
model_config = SettingsConfigDict(
    env_file=".env",
    extra='allow'  # ← اضافه شد
)
```

**دلیل:**
- بدون `extra='allow'` → خطای validation
- بدون `DATABASE_POOL_SIZE` → خطای AttributeError

---

## 🗂️ فایل‌های ساخته شده

### 1️⃣ NewsAPI Service

**مسیر:**
```
backend/app/application/services/data_collection/newsapi_service.py
```

**اندازه:** 350 lines

**کلاس اصلی:**
```python
class NewsAPIService:
    """
    جمع‌آوری اخبار تاریخی از NewsAPI.org
    
    Features:
    - دریافت اخبار از 1 ماه گذشته
    - فیلتر اخبار طلا
    - حذف duplicate
    - ذخیره در database
    
    Rate Limits (Free):
    - 100 requests/day
    - Last 1 month only
    """
    
    GOLD_KEYWORDS = [
        "gold price",
        "gold market",
        "gold trading",
        "precious metals gold",
        "gold investment",
        "gold bullion",
        "gold futures",
        "spot gold",
    ]
    
    async def fetch_historical_news(days_back=30)
    async def fetch_news(keyword, from_date, to_date)
    def _deduplicate_articles(articles)
    async def _save_articles(articles)
```

---

### 2️⃣ News Collection Script

**مسیر:**
```
backend/scripts/collect_news_newsapi.py
```

**اندازه:** 115 lines

**عملکرد:**
```python
async def main():
    # 1. جمع‌آوری از NewsAPI
    newsapi_service = NewsAPIService()
    saved = await newsapi_service.fetch_historical_news(days_back=30)
    
    # 2. تحلیل sentiment
    sentiment_service = SentimentAnalysisService()
    analyzed = await sentiment_service.analyze_all_news()
    
    # 3. نمایش آمار
    stats = await news_service.get_news_stats()
    # ...
```

---

### 3️⃣ Improved Training Script

**مسیر:**
```
backend/scripts/train_lstm_improved.py
```

**اندازه:** 85 lines

**بهبودها:**
```python
model = LSTMGoldPricePredictor(
    sequence_length=90,        # 60 → 90
    lstm_units=[256, 128, 64], # بزرگتر شد
    dropout_rate=0.3           # 0.2 → 0.3
)

results = model.train(
    epochs=100,  # 50 → 100
    batch_size=32
)
```

---

## 📊 جمع‌آوری اخبار

### اجرا:

```bash
cd ~/desktop/gold-price-analyzer/backend
source venv/bin/activate

python scripts/collect_news_newsapi.py
```

### نتایج:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📰 Historical News Collection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 Step 1: Fetching from NewsAPI...

📰 [1/8] Searching: 'gold price'...
   ✅ Found: 87 articles

📰 [2/8] Searching: 'gold market'...
   ✅ Found: 65 articles

📰 [3/8] Searching: 'gold trading'...
   ✅ Found: 52 articles

... (total 8 keywords)

🔄 Removing duplicates...
   ✅ Unique articles: 461

💾 Saving to database...
   ✅ Saved: 461 new articles

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Step 2: FinBERT Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Analyzing batch 1/58: 100%|████████| 58/58 [05:23<00:00]

✅ Analyzed: 461 articles

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Final Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 Total Articles: 477
📅 Date Range: 2025-09-25 → 2025-10-25
   Coverage: 30 days

📦 By Source:
   • newsapi: 461 articles
   • manual: 16 articles

😊 Sentiment Distribution:
   😊 Positive: 160 (33.5%) - avg: +0.81
   😐 Neutral: 201 (42.1%) - avg: +0.06
   😟 Negative: 116 (24.3%) - avg: -0.79
   
   📊 Overall sentiment: +0.105

✅ Ready for improved training!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### آمار جمع‌آوری:

```
Before:
  • Total news: 16
  • Date range: 3 days
  • Sentiment coverage: خیلی کم

After:
  • Total news: 477 (+461 جدید)
  • Date range: 30 days
  • Sentiment coverage: خوب
  
Improvement:
  • 29x more data! 🚀
  • 10x more date coverage
```

---

## 🧠 Improved Training (در حال اجرا)

### دستور:

```bash
python scripts/train_lstm_improved.py
```

### تغییرات:

```
Model v1 (قبل):
  Sequence: 60 days
  LSTM: [128, 64, 32]
  Dropout: 0.2
  Epochs: 50
  
Model v2 (بعد):
  Sequence: 90 days     (+50%)
  LSTM: [256, 128, 64]  (2x bigger)
  Dropout: 0.3          (+50%)
  Epochs: 100           (2x more)
```

### انتظارات:

```
Expected Improvements:

R² Score:
  Before: 0.053
  Target: 0.3-0.5 (5-10x better!)
  
RMSE:
  Before: $566
  Target: $300-400 (30-40% better)
  
MAPE:
  Before: 15.76%
  Target: 10-12% (20-30% better)
```

**⏱️  در حال training... (30-60 دقیقه)**

---

## 🐛 مشکلات و راه‌حل‌ها

### مشکل 1: Pydantic Validation Error

**خطا:**
```
ValidationError: Extra inputs are not permitted
Field: newsapi_key
```

**علت:**
`Settings` class فیلد `NEWSAPI_KEY` نداشت.

**راه‌حل:**
```python
# در config.py اضافه شد:
NEWSAPI_KEY: Optional[str] = None

model_config = SettingsConfigDict(
    extra='allow'  # اجازه field های اضافی
)
```

---

### مشکل 2: DATABASE_POOL_SIZE Missing

**خطا:**
```
AttributeError: 'Settings' object has no attribute 'DATABASE_POOL_SIZE'
```

**علت:**
فایل `base.py` انتظار داشت ولی تعریف نشده بود.

**راه‌حل:**
```python
# اضافه شد به config.py:
DATABASE_POOL_SIZE: int = 5
DATABASE_MAX_OVERFLOW: int = 10
DATABASE_POOL_TIMEOUT: int = 30
DATABASE_ECHO: bool = False
```

---

### مشکل 3: Sentiment Stats TypeError

**خطا:**
```python
TypeError: unsupported operand type(s) for +: 'int' and 'dict'
```

**کد اشتباه:**
```python
total = sum(sentiment_stats['by_label'].values())
# چون values() شامل dict هاست نه int!
```

**راه‌حل:**
```python
total = sum(
    label_data['count'] 
    for label_data in sentiment_stats['by_label'].values()
)
```

---

## 📁 ساختار فایل‌های جدید

```
backend/
├── app/
│   ├── core/
│   │   └── config.py                        ✅ Updated
│   │
│   └── application/services/
│       ├── ml/
│       │   ├── feature_engineering_service.py    ✅ New
│       │   ├── lstm_model_service.py             ✅ New
│       │   └── technical_indicators_service.py   ✅ Existing
│       │
│       └── data_collection/
│           └── newsapi_service.py                ✅ New
│
├── scripts/
│   ├── train_lstm_model.py                  ✅ New
│   ├── train_lstm_improved.py               ✅ New
│   ├── collect_news_newsapi.py              ✅ New
│   └── predict_gold_price.py                ✅ New (not used yet)
│
├── models/
│   ├── lstm_gold_predictor.h5               ✅ Saved
│   ├── lstm_gold_predictor_config.json      ✅ Saved
│   ├── lstm_gold_predictor_scaler_X.pkl     ✅ Saved
│   ├── lstm_gold_predictor_scaler_y.pkl     ✅ Saved
│   └── training_history.png                 ✅ Saved
│
└── .env                                      ✅ Updated
```

---

## 📊 آمار کلی Session

### کدنویسی:
```
Files created: 7
Lines of code: ~1,500
Time spent: ~2 hours
```

### داده:
```
News before: 16
News after: 477 (+461)
Coverage: 3 days → 30 days
Sentiment analyzed: 477 articles
```

### Machine Learning:
```
Model v1 trained: ✅
  - R²: 0.053
  - RMSE: $566
  - Training time: 15 min

Model v2 training: ⏳ (in progress)
  - Expected R²: 0.3-0.5
  - Expected RMSE: $300-400
  - Training time: 30-60 min
```

---

## 🎯 وضعیت فعلی

### ✅ کامل شده:

```
✅ LSTM Model v1 trained and saved
✅ NewsAPI integration complete
✅ 477 news articles collected
✅ All news analyzed with FinBERT
✅ Feature engineering service ready
✅ Improved training script ready
⏳ Model v2 training in progress...
```

### ⏳ در حال انجام:

```
⏳ LSTM Model v2 training
   - Started: 2025-10-25 16:27:20 UTC
   - ETA: 30-60 minutes
   - Expected: Much better R² score
```

### 🔮 مراحل بعدی:

```
1. ⏳ Wait for improved training to complete
2. 📊 Compare v1 vs v2 performance
3. 🔮 Test predictions with new model
4. 🌐 Build API endpoint for predictions
5. 📱 Create frontend dashboard
```

---

## 🔑 نکات کلیدی برای ادامه کار

### اگر session قطع شد:

```bash
# 1. چک وضعیت Docker
docker-compose ps

# 2. چک database
cd ~/desktop/gold-price-analyzer/backend
source venv/bin/activate

python -c "
from app.application.services.data_collection.news_service import NewsService
import asyncio

async def check():
    service = NewsService()
    stats = await service.get_news_stats()
    print(f'Total news: {stats[\"total\"]}')
    
asyncio.run(check())
"

# 3. چک saved models
ls -lh models/

# Expected:
# lstm_gold_predictor.h5
# lstm_gold_predictor_v2.h5 (after training)
```

### دستورات مهم:

```bash
# جمع‌آوری اخبار بیشتر
python scripts/collect_news_newsapi.py

# Training مدل
python scripts/train_lstm_improved.py

# پیش‌بینی
python scripts/predict_gold_price.py

# مشاهده آمار
python -c "from app.core.config import settings; print(settings.NEWSAPI_KEY)"
```

---

## 📚 منابع

### Repository:
```
https://github.com/hoseynd-ai/gold-price-analyzer
```

### مستندات:
```
docs/
├── GOLD_PRICE_ANALYZER_COMPLETE_BLUEPRINT.md
├── day5/
│   ├── DAY5_COMPLETE_SESSION.md           (صبح)
│   └── DAY5_MODEL_IMPROVEMENT.md          (این فایل - عصر)
```

### API Keys:
```
NewsAPI: https://newsapi.org/
  - Free tier: 100 req/day
  - Historical: 1 month
  - Current key: 49eaab5c... (در .env)
```

---

## ✅ Checklist

### امروز (Day 5 - Part 2):

- [x] مدل LSTM v1 train شد
- [x] نتایج تحلیل شد (R²=0.053)
- [x] مشکلات شناسایی شد
- [x] NewsAPI API key گرفته شد
- [x] NewsAPI service ساخته شد
- [x] 461 خبر جدید جمع شد
- [x] همه با FinBERT تحلیل شدن
- [x] config.py به‌روز شد
- [x] Improved training script آماده شد
- [x] مدل v2 در حال training
- [x] مستندات کامل نوشته شد

### فردا (Day 6):

- [ ] بررسی نتایج مدل v2
- [ ] مقایسه v1 vs v2
- [ ] تست predictions
- [ ] ساخت API endpoint
- [ ] نمودار comparison
- [ ] deployment planning

---

**پایان مستندات Session**

**نویسنده:** حسین دولابی (Hoseyn Doulabi)  
**GitHub:** @hoseynd-ai  
**Repository:** https://github.com/hoseynd-ai/gold-price-analyzer  
**تاریخ:** 2025-10-25 16:27:20 UTC  
**نسخه:** 1.0.0 - Complete  
**وضعیت:** Training in progress...  

---

**💡 یادآوری:**
این مستندات شامل تمام جزئیات session است. اگر کار قطع شد:
1. بخوانید این فایل را
2. چک کنید database (477 news)
3. چک کنید models/ directory
4. ادامه دهید از جایی که training تمام شده

**🚀 Model v2 is training... Please wait!**
