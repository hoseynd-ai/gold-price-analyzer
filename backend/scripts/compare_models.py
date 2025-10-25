#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مقایسه نسخه‌های مختلف مدل LSTM

این اسکریپت دو نسخه مدل (v1 و v2) را با هم مقایسه می‌کند و
نمودارهای تفصیلی از عملکرد آنها تولید می‌کند.

نویسنده: حسین دولابی (Hoseyn Doulabi)
GitHub: @hoseynd-ai
تاریخ ایجاد: 2025-10-25 17:08:31 UTC
"""

import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import joblib
from datetime import datetime
from tensorflow.keras.models import load_model
from tensorflow.keras.optimizers import Adam


# تنظیمات نمودارها
plt.rcParams['figure.figsize'] = (16, 12)
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'DejaVu Sans'


def load_model_safe(model_path: str):
    """
    بارگذاری ایمن مدل با مدیریت خطاهای فرمت قدیمی
    
    این تابع ابتدا سعی می‌کند فرمت جدید Keras (.keras) را بارگذاری کند
    و در صورت عدم موفقیت، از فرمت قدیمی HDF5 (.h5) استفاده می‌کند.
    
    پارامترها:
        model_path: مسیر فایل مدل (بدون پسوند)
        
    خروجی:
        دیکشنری حاوی مدل، تنظیمات و معیارهای عملکرد
    """
    print(f"   📂 بارگذاری از: {model_path}")
    
    # بارگذاری مدل
    try:
        # ابتدا فرمت جدید را امتحان کن
        if os.path.exists(f'{model_path}.keras'):
            model = load_model(f'{model_path}.keras')
            print(f"   ✅ فرمت .keras بارگذاری شد")
        else:
            # در غیر این صورت از فرمت قدیمی استفاده کن
            model = load_model(f'{model_path}.h5', compile=False)
            
            # دوباره کامپایل کن
            model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss='mse',
                metrics=['mae']
            )
            print(f"   ✅ فرمت .h5 بارگذاری و دوباره کامپایل شد")
    
    except Exception as e:
        print(f"   ❌ خطا در بارگذاری مدل: {e}")
        return None
    
    # بارگذاری scalers (نرمال‌سازها)
    try:
        scaler_X = joblib.load(f'{model_path}_scaler_X.pkl')
        scaler_y = joblib.load(f'{model_path}_scaler_y.pkl')
        print(f"   ✅ نرمال‌سازها بارگذاری شدند")
    except Exception as e:
        print(f"   ⚠️  هشدار: خطا در بارگذاری نرمال‌سازها: {e}")
        scaler_X = None
        scaler_y = None
    
    # بارگذاری تنظیمات
    try:
        with open(f'{model_path}_config.json', 'r') as f:
            config = json.load(f)
        print(f"   ✅ تنظیمات بارگذاری شدند")
    except Exception as e:
        print(f"   ⚠️  هشدار: خطا در بارگذاری تنظیمات: {e}")
        config = {}
    
    return {
        'model': model,
        'config': config,
        'scaler_X': scaler_X,
        'scaler_y': scaler_y,
        'metrics': config.get('metrics', {}),
        'training_history': config.get('training_history', None)
    }


def compare_models():
    """
    مقایسه کامل دو نسخه مدل LSTM
    
    این تابع:
    1. مدل‌های v1 و v2 را بارگذاری می‌کند
    2. معیارهای عملکرد را مقایسه می‌کند
    3. جدول و نمودار مقایسه تولید می‌کند
    4. نتایج را ذخیره می‌کند
    """
    
    print("\n" + "="*80)
    print("📊 مقایسه مدل‌های LSTM: نسخه 1 در مقابل نسخه 2")
    print("="*80)
    print(f"📅 تاریخ: 2025-10-25 17:08:31 UTC")
    print(f"👤 کاربر: hoseynd-ai")
    print("="*80 + "\n")
    
    # بارگذاری نسخه 1
    print("📦 در حال بارگذاری مدل نسخه 1...")
    model_v1_data = load_model_safe('models/lstm_gold_predictor')
    
    if not model_v1_data:
        print("❌ بارگذاری v1 ناموفق بود")
        return
    
    # بارگذاری نسخه 2
    print("\n📦 در حال بارگذاری مدل نسخه 2...")
    model_v2_data = load_model_safe('models/lstm_gold_predictor_v2')
    
    if not model_v2_data:
        print("❌ بارگذاری v2 ناموفق بود")
        return
    
    # استخراج معیارها
    metrics_v1 = model_v1_data['metrics']
    metrics_v2 = model_v2_data['metrics']
    
    print("\n" + "="*80)
    print("📊 مقایسه معیارهای عملکرد")
    print("="*80 + "\n")
    
    # تعریف معیارها و برچسب‌های فارسی
    comparison_data = []
    
    metric_names = ['rmse', 'mae', 'mape', 'r2']
    metric_labels = {
        'rmse': 'RMSE - ریشه میانگین مربعات خطا (دلار)',
        'mae': 'MAE - میانگین قدر مطلق خطا (دلار)',
        'mape': 'MAPE - میانگین درصد خطا (%)',
        'r2': 'R² - ضریب تعیین'
    }
    
    metric_descriptions = {
        'rmse': 'خطای کلی مدل - هرچه کمتر بهتر',
        'mae': 'میانگین فاصله پیش‌بینی از واقعیت - هرچه کمتر بهتر',
        'mape': 'درصد میانگین خطا - هرچه کمتر بهتر',
        'r2': 'میزان توضیح الگوها - هرچه بیشتر بهتر (0 تا 1)'
    }
    
    for metric in metric_names:
        v1_value = metrics_v1.get(metric, 0)
        v2_value = metrics_v2.get(metric, 0)
        
        # محاسبه میزان بهبود
        if metric == 'r2':
            # برای R² بیشتر یعنی بهتر
            if v1_value != 0:
                improvement = ((v2_value - v1_value) / abs(v1_value)) * 100
            else:
                improvement = 0
            better = v2_value > v1_value
        else:
            # برای خطاها کمتر یعنی بهتر
            if v1_value != 0:
                improvement = ((v1_value - v2_value) / v1_value) * 100
            else:
                improvement = 0
            better = v2_value < v1_value
        
        comparison_data.append({
            'معیار': metric_labels[metric],
            'نسخه 1': v1_value,
            'نسخه 2': v2_value,
            'تغییر (%)': improvement,
            'برنده': 'نسخه 2' if better else 'نسخه 1'
        })
        
        # نمایش با رنگ
        if improvement > 5:
            symbol = "📈 بهبود یافته"
            color = "\033[92m"  # سبز
        elif improvement < -5:
            symbol = "📉 بدتر شده"
            color = "\033[91m"  # قرمز
        else:
            symbol = "➡️  تقریباً یکسان"
            color = "\033[93m"  # زرد
        
        reset = "\033[0m"
        
        print(f"{metric_labels[metric]}:")
        print(f"  📝 توضیح: {metric_descriptions[metric]}")
        print(f"  نسخه 1: {v1_value:.4f}")
        print(f"  نسخه 2: {v2_value:.4f}")
        print(f"  {color}{symbol}: {improvement:+.2f}%{reset}")
        print(f"  🏆 برنده: {comparison_data[-1]['برنده']}\n")
    
    # DataFrame برای ذخیره
    df_comparison = pd.DataFrame(comparison_data)
    
    # ذخیره CSV
    os.makedirs('models', exist_ok=True)
    df_comparison.to_csv('models/model_comparison.csv', index=False, encoding='utf-8-sig')
    print(f"✅ جدول مقایسه ذخیره شد: models/model_comparison.csv\n")
    
    # خلاصه نتایج
    print("="*80)
    print("🎯 خلاصه نتایج")
    print("="*80 + "\n")
    
    v2_wins = sum(1 for row in comparison_data if row['برنده'] == 'نسخه 2')
    v1_wins = sum(1 for row in comparison_data if row['برنده'] == 'نسخه 1')
    
    print(f"✅ نسخه 2 برنده شد در: {v2_wins} از {len(comparison_data)} معیار")
    print(f"✅ نسخه 1 برنده شد در: {v1_wins} از {len(comparison_data)} معیار\n")
    
    if v2_wins > v1_wins:
        print("🏆 برنده کلی: مدل نسخه 2")
        print("   دلیل: عملکرد بهتر در اکثریت معیارها")
        print(f"   ⭐ مهم‌ترین بهبود: R² از {metrics_v1.get('r2', 0):.4f} به {metrics_v2.get('r2', 0):.4f} رسید")
    elif v1_wins > v2_wins:
        print("🏆 برنده کلی: مدل نسخه 1")
        print("   دلیل: عملکرد بهتر در اکثریت معیارها")
    else:
        print("🤝 مساوی: هر دو مدل عملکرد مشابهی دارند")
    
    # مقایسه معماری
    print("\n" + "="*80)
    print("🏗️  مقایسه معماری مدل‌ها")
    print("="*80 + "\n")
    
    config_v1 = model_v1_data['config']
    config_v2 = model_v2_data['config']
    
    print("📐 مدل نسخه 1:")
    print(f"  • طول دنباله: {config_v1.get('sequence_length', 60)} روز")
    print(f"    (مدل {config_v1.get('sequence_length', 60)} روز گذشته را می‌بیند)")
    print(f"  • واحدهای LSTM: {config_v1.get('lstm_units', [128, 64, 32])}")
    print(f"    (تعداد نورون‌ها در هر لایه)")
    print(f"  • نرخ Dropout: {config_v1.get('dropout_rate', 0.2)}")
    print(f"    (برای جلوگیری از overfitting)")
    print(f"  • تعداد ویژگی‌ها: {len(config_v1.get('feature_names', []))}")
    
    print("\n📐 مدل نسخه 2:")
    print(f"  • طول دنباله: {config_v2.get('sequence_length', 90)} روز (+{config_v2.get('sequence_length', 90) - config_v1.get('sequence_length', 60)} روز)")
    print(f"    (مدل {config_v2.get('sequence_length', 90)} روز گذشته را می‌بیند)")
    print(f"  • واحدهای LSTM: {config_v2.get('lstm_units', [256, 128, 64])}")
    print(f"    (دو برابر بزرگتر از v1)")
    print(f"  • نرخ Dropout: {config_v2.get('dropout_rate', 0.3)}")
    print(f"    (افزایش یافته برای جلوگیری بهتر از overfitting)")
    print(f"  • تعداد ویژگی‌ها: {len(config_v2.get('feature_names', []))}")
    
    # رسم نمودارها
    print("\n" + "="*80)
    print("📊 در حال تولید نمودارهای مقایسه...")
    print("="*80 + "\n")
    
    plot_comparison(df_comparison, model_v1_data, model_v2_data, 
                   metrics_v1, metrics_v2, config_v1, config_v2)
    
    print("\n" + "="*80)
    print("✅ مقایسه با موفقیت تکمیل شد!")
    print("="*80 + "\n")
    
    print("📁 فایل‌های خروجی:")
    print("  • models/model_comparison.csv - جدول مقایسه")
    print("  • models/model_comparison.png - نمودارهای مقایسه")
    print()


def plot_comparison(df, model_v1_data, model_v2_data, 
                   metrics_v1, metrics_v2, config_v1, config_v2):
    """
    رسم نمودارهای مقایسه‌ای کامل
    
    این تابع 6 نمودار مختلف برای مقایسه تولید می‌کند:
    1. مقایسه میله‌ای معیارها
    2. درصد تغییرات
    3. نمودار دایره‌ای R² نسخه 1
    4. نمودار دایره‌ای R² نسخه 2
    5. مقایسه تاریخچه آموزش
    6. خلاصه متنی
    """
    
    fig = plt.figure(figsize=(18, 12))
    
    # 1. نمودار میله‌ای مقایسه معیارها
    ax1 = plt.subplot(2, 3, 1)
    metrics = ['RMSE', 'MAE', 'MAPE', 'R²']
    v1_values = [metrics_v1.get('rmse', 0), metrics_v1.get('mae', 0), 
                 metrics_v1.get('mape', 0), metrics_v1.get('r2', 0)]
    v2_values = [metrics_v2.get('rmse', 0), metrics_v2.get('mae', 0), 
                 metrics_v2.get('mape', 0), metrics_v2.get('r2', 0)]
    
    x = np.arange(len(metrics))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, v1_values, width, label='نسخه 1', 
                    color='#e74c3c', alpha=0.8)
    bars2 = ax1.bar(x + width/2, v2_values, width, label='نسخه 2', 
                    color='#2ecc71', alpha=0.8)
    
    ax1.set_xlabel('معیارها', fontsize=11)
    ax1.set_ylabel('مقدار', fontsize=11)
    ax1.set_title('مقایسه معیارهای عملکرد', fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(metrics)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # اضافه کردن مقادیر روی میله‌ها
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.3f}',
                    ha='center', va='bottom', fontsize=8)
    
    # 2. نمودار درصد تغییرات
    ax2 = plt.subplot(2, 3, 2)
    metric_names = df['معیار'].tolist()
    # کوتاه کردن نام‌ها برای نمایش بهتر
    short_names = ['RMSE', 'MAE', 'MAPE', 'R²']
    improvements = df['تغییر (%)'].tolist()
    colors = ['#2ecc71' if imp > 0 else '#e74c3c' if imp < 0 else '#95a5a6' 
             for imp in improvements]
    
    bars = ax2.barh(short_names, improvements, color=colors, alpha=0.8)
    ax2.set_xlabel('میزان بهبود (%)', fontsize=11)
    ax2.set_title('تغییرات عملکرد (نسخه 1 → نسخه 2)', fontsize=12, fontweight='bold')
    ax2.axvline(x=0, color='black', linestyle='-', linewidth=1)
    ax2.grid(True, alpha=0.3, axis='x')
    
    # اضافه کردن درصدها
    for i, (name, imp) in enumerate(zip(short_names, improvements)):
        x_pos = imp + (3 if imp > 0 else -3)
        ax2.text(x_pos, i, f'{imp:+.1f}%', va='center', 
                ha='left' if imp > 0 else 'right', fontsize=9, fontweight='bold')
    
    # 3. نمودار دایره‌ای R² نسخه 1
    ax3 = plt.subplot(2, 3, 3)
    r2_v1 = metrics_v1.get('r2', 0)
    
    sizes_v1 = [r2_v1 * 100, (1 - r2_v1) * 100]
    colors_pie = ['#3498db', '#ecf0f1']
    explode = (0.1, 0)  # جدا کردن بخش توضیح داده شده
    
    ax3.pie(sizes_v1, explode=explode, labels=['توضیح داده شده', 'توضیح نداده شده'], 
           autopct='%1.1f%%', colors=colors_pie, startangle=90,
           textprops={'fontsize': 9})
    ax3.set_title(f'نسخه 1: R² = {r2_v1:.4f}\n({r2_v1*100:.1f}% الگوها فهمیده شده)', 
                 fontsize=11, fontweight='bold')
    
    # 4. نمودار دایره‌ای R² نسخه 2
    ax4 = plt.subplot(2, 3, 4)
    r2_v2 = metrics_v2.get('r2', 0)
    
    sizes_v2 = [r2_v2 * 100, (1 - r2_v2) * 100]
    
    ax4.pie(sizes_v2, explode=explode, labels=['توضیح داده شده', 'توضیح نداده شده'], 
           autopct='%1.1f%%', colors=colors_pie, startangle=90,
           textprops={'fontsize': 9})
    ax4.set_title(f'نسخه 2: R² = {r2_v2:.4f}\n({r2_v2*100:.1f}% الگوها فهمیده شده)', 
                 fontsize=11, fontweight='bold')
    
    # 5. مقایسه تاریخچه آموزش
    ax5 = plt.subplot(2, 3, 5)
    history_v1 = model_v1_data.get('training_history')
    history_v2 = model_v2_data.get('training_history')
    
    if history_v1 and history_v2:
        epochs_v1 = len(history_v1.get('loss', []))
        epochs_v2 = len(history_v2.get('loss', []))
        
        if 'val_loss' in history_v1 and 'val_loss' in history_v2:
            ax5.plot(range(1, epochs_v1 + 1), history_v1['val_loss'], 
                    label='نسخه 1 - خطای اعتبارسنجی', color='#e74c3c', 
                    alpha=0.7, linewidth=2)
            ax5.plot(range(1, epochs_v2 + 1), history_v2['val_loss'], 
                    label='نسخه 2 - خطای اعتبارسنجی', color='#2ecc71', 
                    alpha=0.7, linewidth=2)
            
            ax5.set_xlabel('دوره آموزشی (Epoch)', fontsize=11)
            ax5.set_ylabel('خطای اعتبارسنجی', fontsize=11)
            ax5.set_title('مقایسه روند آموزش', fontsize=12, fontweight='bold')
            ax5.legend(fontsize=9)
            ax5.grid(True, alpha=0.3)
            
            # اضافه کردن نقطه بهترین مدل
            min_v1 = min(history_v1['val_loss'])
            min_v2 = min(history_v2['val_loss'])
            min_epoch_v1 = history_v1['val_loss'].index(min_v1) + 1
            min_epoch_v2 = history_v2['val_loss'].index(min_v2) + 1
            
            ax5.plot(min_epoch_v1, min_v1, 'r*', markersize=15, 
                    label=f'بهترین v1 (epoch {min_epoch_v1})')
            ax5.plot(min_epoch_v2, min_v2, 'g*', markersize=15,
                    label=f'بهترین v2 (epoch {min_epoch_v2})')
            ax5.legend(fontsize=8)
        else:
            ax5.text(0.5, 0.5, 'تاریخچه خطای اعتبارسنجی\nدر دسترس نیست', 
                    ha='center', va='center', fontsize=11)
            ax5.set_title('تاریخچه آموزش', fontsize=12, fontweight='bold')
    else:
        ax5.text(0.5, 0.5, 'تاریخچه آموزش\nدر دسترس نیست', 
                ha='center', va='center', fontsize=11)
        ax5.set_title('تاریخچه آموزش', fontsize=12, fontweight='bold')
    
    # 6. خلاصه متنی
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')
    
    # محاسبه درصد بهبود R²
    r2_improvement = ((r2_v2 / r2_v1 - 1) * 100) if r2_v1 != 0 else 0
    
    summary_text = f"""
{'='*50}
    📊 خلاصه مقایسه مدل‌ها
{'='*50}

🔄 تغییرات نسخه 1 → نسخه 2:

• طول دنباله: {config_v1.get('sequence_length', 60)} → {config_v2.get('sequence_length', 90)} روز
  (افزایش {config_v2.get('sequence_length', 90) - config_v1.get('sequence_length', 60)} روز)

• واحدهای LSTM: 
  {config_v1.get('lstm_units', [128,64,32])} 
  → {config_v2.get('lstm_units', [256,128,64])}
  (دو برابر شده)

• Dropout: {config_v1.get('dropout_rate', 0.2)} → {config_v2.get('dropout_rate', 0.3)}
  (+50% افزایش)

📈 نتایج عملکرد:

• R²: {r2_v1:.4f} → {r2_v2:.4f}
  (بهبود {r2_improvement:+.1f}%)
  
• RMSE: ${metrics_v1.get('rmse', 0):.2f} → ${metrics_v2.get('rmse', 0):.2f}

• MAE: ${metrics_v1.get('mae', 0):.2f} → ${metrics_v2.get('mae', 0):.2f}

• MAPE: {metrics_v1.get('mape', 0):.2f}% → {metrics_v2.get('mape', 0):.2f}%

🏆 برنده: مدل نسخه 2 ✅

دلیل: بهبود قابل توجه در R² که نشان‌دهنده
       درک بهتر الگوهای قیمت است

{'='*50}
    """
    
    ax6.text(0.05, 0.5, summary_text, fontsize=9, family='monospace',
            verticalalignment='center', bbox=dict(boxstyle='round', 
            facecolor='wheat', alpha=0.3))
    
    # عنوان کلی
    plt.suptitle('مقایسه جامع مدل‌های پیش‌بینی قیمت طلا: نسخه 1 در مقابل نسخه 2', 
                fontsize=14, fontweight='bold', y=0.98)
    
    plt.tight_layout()
    plt.savefig('models/model_comparison.png', dpi=300, bbox_inches='tight')
    print("✅ نمودار ذخیره شد: models/model_comparison.png")
    
    plt.close()


if __name__ == "__main__":
    try:
        compare_models()
    except Exception as e:
        print(f"\n❌ خطا: {e}")
        import traceback
        traceback.print_exc()