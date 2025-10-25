# 🎯 Model Improvement Roadmap - Target: R² > 0.5

**تاریخ شروع | Start Date:** 2025-10-25 17:16:48 UTC  
**نویسنده | Author:** Hoseyn Doulabi (@hoseynd-ai)  
**هدف | Target:** R² ≥ 0.5 (Currently: 0.1751)  
**تخمین زمان | Estimated Time:** 2-3 days  

---

## 🎯 هدف نهایی

```
Current State:
  R²: 0.1751 (17.5% الگوها رو می‌فهمه)
  RMSE: $529.54
  MAE: $424.22
  MAPE: 16.69%

Target State:
  R²: ≥ 0.5 (50%+ الگوها رو بفهمه)
  RMSE: < $300
  MAE: < $250
  MAPE: < 10%

Gap to Fill:
  R² باید 2.85x بهتر بشه
  RMSE باید 43% کاهش پیدا کنه
```

---

## 📋 مراحل اجرایی (Step-by-Step)

### 🔴 Phase 1: Data Collection (High Impact)

**مدت زمان:** 4-6 hours  
**Impact:** R² = 0.175 → 0.35-0.40  

---

#### Task 1.1: جمع‌آوری اخبار تاریخی (2000+ articles)

**فعلی:** 477 articles (30 days)  
**هدف:** 2000+ articles (2-3 years)  

**منابع:**

```
1. NewsAPI (در دست اجرا)
   • Free: 100 req/day, 1 month history
   • Paid: Unlimited, 2 years history
   • Cost: $449/month
   
2. GNews API (رایگان) ⭐ پیشنهادی
   • Free: 100 req/day
   • History: 3 months
   • Sign up: https://gnews.io/
   
3. Bing News Search API
   • Free: 1000 req/month
   • History: 7 days only
   
4. RSS Feeds (رایگان و قدرتمند) ⭐⭐⭐
   • Reuters Gold RSS
   • Bloomberg Commodities
   • Kitco News Archive
   • World Gold Council
   
5. Web Scraping (آخرین راه‌حل)
   • Kitco.com archives
   • GoldPrice.org
   • Reuters.com
```

**Action Plan:**

```bash
# Step 1: GNews API integration
cd ~/desktop/gold-price-analyzer/backend

# 1. ثبت‌نام و دریافت API key
# https://gnews.io/ → Sign up → Get API key

# 2. اضافه به .env
echo "GNEWS_API_KEY=your_api_key_here" >> .env

# 3. ساخت service
nano app/application/services/data_collection/gnews_service.py
```

**Script برای جمع‌آوری:**

```bash
# بعد از ساخت service
python scripts/collect_all_historical_news.py --days 90 --target 2000
```

**Expected Output:**
```
Target: 2000+ articles
Sources: NewsAPI (477) + GNews (800+) + RSS (700+)
Coverage: 3 months (90 days)
Sentiment analyzed: All with FinBERT
```

---

#### Task 1.2: اضافه کردن Dollar Index (DXY)

**چرا مهمه:**
```
Dollar Index (DXY) و Gold رابطه معکوس قوی دارن!

Correlation: -0.7 to -0.9 (خیلی قوی)

وقتی Dollar بالا → Gold پایین
وقتی Dollar پایین → Gold بالا

این یکی از مهم‌ترین factorها برای پیش‌بینی طلاست!
```

**منبع داده:**
```
Alpha Vantage API (همون که داریم)
Symbol: DXY
Function: TIME_SERIES_DAILY
Free: 500 req/day ✅
```

**Action Plan:**

```bash
cd ~/desktop/gold-price-analyzer/backend

# 1. ساخت service
nano app/application/services/data_collection/dollar_index_service.py

# 2. جمع‌آوری 20 سال داده
python scripts/collect_dollar_index.py --years 20

# 3. اضافه به feature engineering
# در feature_engineering_service.py
```

**Expected Impact:**
```
R² improvement: +0.1 to +0.15
(because of strong correlation)
```

---

#### Task 1.3: اضافه کردن Interest Rates (نرخ بهره فدرال رزرو)

**چرا مهمه:**
```
Federal Reserve Interest Rate = مهم‌ترین عامل!

وقتی Fed نرخ بهره رو بالا می‌بره:
  → Dollar قوی میشه
  → Gold ضعیف میشه

وقتی Fed نرخ بهره رو پایین می‌یاره:
  → Dollar ضعیف میشه
  → Gold قوی میشه

این اطلاعات رایگان و قابل اعتماده!
```

**منبع داده:**
```
FRED API (Federal Reserve Economic Data)
Free: Unlimited ✅
Historical: از 1954!
Update: هر جلسه FOMC

Sign up: https://fred.stlouisfed.org/docs/api/api_key.html
```

**Action Plan:**

```bash
# 1. ثبت‌نام FRED
# https://fred.stlouisfed.org/ → Sign up → Get API key

# 2. اضافه به .env
echo "FRED_API_KEY=your_api_key_here" >> .env

# 3. ساخت service
nano app/application/services/data_collection/fred_service.py

# 4. جمع‌آوری:
#    - Federal Funds Rate (DFF)
#    - 10-Year Treasury Rate (DGS10)
#    - Inflation Rate (CPIAUCSL)
python scripts/collect_economic_indicators.py
```

**Expected Impact:**
```
R² improvement: +0.08 to +0.12
```

---

### 🟡 Phase 2: Feature Engineering (Medium Impact)

**مدت زمان:** 2-3 hours  
**Impact:** R² = 0.35 → 0.42  

---

#### Task 2.1: اضافه کردن VIX (Fear Index)

**چرا مهمه:**
```
VIX = Volatility Index = شاخص ترس بازار

وقتی VIX بالا (ترس زیاد):
  → سرمایه‌گذارها به طلا پناه می‌برن
  → Gold بالا میره

وقتی VIX پایین (آرامش):
  → طلا کم‌تقاضا میشه
  → Gold پایین میاد

Correlation: +0.5 to +0.7 (متوسط به قوی)
```

**منبع:**
```
Alpha Vantage: Symbol VIX
Yahoo Finance: ^VIX
```

---

#### Task 2.2: اضافه کردن Oil Price

**چرا مهمه:**
```
Oil (نفت) و Gold همبستگی مثبت دارن

وقتی Oil بالا:
  → نشانه تورم
  → Gold هم بالا (hedge تورم)

Correlation: +0.3 to +0.5 (متوسط)
```

**منبع:**
```
Alpha Vantage: WTI, BRENT
Symbol: CL=F (WTI), BZ=F (Brent)
```

---

#### Task 2.3: Feature Cross-correlation Analysis

**هدف:** حذف features زائد که فایده ندارن

```python
# در feature_engineering_service.py
def analyze_feature_importance():
    """
    تحلیل اهمیت هر feature
    حذف features با correlation < 0.1
    """
    
    # محاسبه correlation با target
    correlations = X.corrwith(y)
    
    # فقط features با |correlation| > 0.1
    important_features = correlations[abs(correlations) > 0.1]
    
    return important_features
```

---

### 🟢 Phase 3: Model Architecture (High Impact)

**مدت زمان:** 3-4 hours  
**Impact:** R² = 0.42 → 0.48  

---

#### Task 3.1: Attention Mechanism

**چرا مهمه:**
```
Attention به مدل می‌گه کدوم time steps مهم‌ترن

مثلاً:
  • اخبار Fed خیلی مهم‌تره از اخبار عادی
  • قیمت‌های اخیر مهم‌تر از 3 ماه پیش
  
Attention این وزن‌دهی رو یاد می‌گیره!
```

**Implementation:**

```python
from tensorflow.keras.layers import Attention, MultiHeadAttention

def build_lstm_with_attention():
    """مدل LSTM با Attention"""
    
    model = Sequential([
        # LSTM layers
        Bidirectional(LSTM(256, return_sequences=True)),
        Dropout(0.3),
        
        # Attention layer ⭐
        MultiHeadAttention(num_heads=4, key_dim=64),
        
        LSTM(128, return_sequences=True),
        Dropout(0.3),
        
        LSTM(64, return_sequences=False),
        Dropout(0.3),
        
        Dense(32, activation='relu'),
        Dense(1)
    ])
    
    return model
```

**Expected Impact:**
```
R² improvement: +0.05 to +0.08
```

---

#### Task 3.2: Ensemble Models

**چرا مهمه:**
```
به جای 1 مدل، 3-5 مدل مختلف train کن و
prediction ها رو با هم ترکیب کن!

Models:
  1. LSTM with attention
  2. GRU (مثل LSTM ولی سریع‌تر)
  3. CNN-LSTM hybrid
  4. Transformer
  
Final prediction = میانگین وزن‌دار پیش‌بینی‌ها

این روش variance رو کم می‌کنه و دقت رو بالا می‌بره!
```

**Expected Impact:**
```
R² improvement: +0.03 to +0.05
```

---

### 🔵 Phase 4: Hyperparameter Optimization (Medium Impact)

**مدت زمان:** 6-8 hours (automated)  
**Impact:** R² = 0.48 → 0.52  

---

#### Task 4.1: Keras Tuner

```python
import keras_tuner as kt

def build_model(hp):
    """مدل با hyperparameters قابل تنظیم"""
    
    # Hyperparameters to tune
    sequence_length = hp.Choice('sequence', [60, 90, 120, 180])
    lstm_units_1 = hp.Choice('lstm_1', [128, 256, 512])
    lstm_units_2 = hp.Choice('lstm_2', [64, 128, 256])
    dropout = hp.Float('dropout', 0.2, 0.5, step=0.1)
    learning_rate = hp.Float('lr', 1e-4, 1e-2, sampling='log')
    
    model = Sequential([
        Bidirectional(LSTM(lstm_units_1, return_sequences=True)),
        Dropout(dropout),
        LSTM(lstm_units_2, return_sequences=False),
        Dropout(dropout),
        Dense(32, activation='relu'),
        Dense(1)
    ])
    
    model.compile(
        optimizer=Adam(learning_rate=learning_rate),
        loss='mse',
        metrics=['mae']
    )
    
    return model

# Tuner
tuner = kt.BayesianOptimization(
    build_model,
    objective='val_loss',
    max_trials=50,
    directory='tuning',
    project_name='gold_lstm'
)

# Search
tuner.search(X_train, y_train, 
            validation_data=(X_val, y_val),
            epochs=50)

# بهترین config
best_config = tuner.get_best_hyperparameters()[0]
```

**Expected Impact:**
```
R² improvement: +0.02 to +0.04
```

---

## 📅 Timeline جزئی

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              DETAILED TIMELINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Day 1 (2025-10-26): Data Collection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
09:00-11:00  GNews API integration
11:00-13:00  Collect 2000+ news articles
13:00-14:00  Break
14:00-16:00  Dollar Index service + collection
16:00-18:00  FRED API + Interest rates
18:00-19:00  Data validation & cleanup

Expected R² at end of day: 0.35-0.40

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Day 2 (2025-10-27): Features & Architecture
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
09:00-10:00  VIX & Oil price integration
10:00-11:00  Feature engineering updates
11:00-12:00  Feature importance analysis
12:00-13:00  Break
13:00-15:00  LSTM with Attention implementation
15:00-17:00  Train model v3
17:00-18:00  Evaluate & compare

Expected R² at end of day: 0.42-0.48

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Day 3 (2025-10-28): Optimization & Ensemble
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
09:00-11:00  Keras Tuner setup
11:00-17:00  Hyperparameter search (automated)
17:00-18:00  Train best model
18:00-19:00  Ensemble model setup
19:00-21:00  Final training & evaluation

Expected R² at end of day: 0.50-0.55 🎯

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total: 3 days (~24 hours work)
Target: R² ≥ 0.5 ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 📊 Expected Improvements (Cumulative)

```
Starting point: R² = 0.1751

After Task 1.1 (2000+ news):        R² = 0.28  (+60%)
After Task 1.2 (Dollar Index):      R² = 0.35  (+25%)
After Task 1.3 (Interest Rates):    R² = 0.40  (+14%)
After Task 2.1-2.3 (VIX, Oil):      R² = 0.42  (+5%)
After Task 3.1 (Attention):         R² = 0.47  (+12%)
After Task 3.2 (Ensemble):          R² = 0.50  (+6%)
After Task 4.1 (Tuning):            R² = 0.52  (+4%)

Final: R² ≥ 0.50 🎯
```

---

## ✅ Success Criteria

```
Minimum Requirements:
  ✅ R² ≥ 0.50
  ✅ RMSE < $350
  ✅ MAPE < 12%

Stretch Goals:
  🎯 R² ≥ 0.55
  🎯 RMSE < $300
  🎯 MAPE < 10%
```

---

## 🚀 Let's Start NOW!

**بیایید همین الان شروع کنیم:**

```bash
Task 1.1: GNews API Integration
Estimated time: 2 hours
Start: 2025-10-25 17:16:48 UTC
Ready? 🎯
```

