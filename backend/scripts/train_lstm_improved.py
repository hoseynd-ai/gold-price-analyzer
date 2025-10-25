#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Improved LSTM Training Script

بهبودها:
1. Sequence length بیشتر (90 روز)
2. Architecture بهتر (256→128→64)
3. Epochs بیشتر (100)
4. Dropout بیشتر (0.3)
5. Learning rate scheduling

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25 16:10:00 UTC
"""

import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from datetime import datetime
from app.application.services.ml.lstm_model_service import LSTMGoldPricePredictor
from app.application.services.ml.feature_engineering_service import FeatureEngineeringService


def main():
    print("\n" + "="*70)
    print("🚀 IMPROVED LSTM Training")
    print("="*70)
    print(f"📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("="*70 + "\n")
    
    # 1. Data
    print("📊 Preparing data...")
    DATABASE_URL = "postgresql+psycopg2://admin:admin123@localhost:5432/gold_analyzer"
    
    feature_service = FeatureEngineeringService(DATABASE_URL)
    X, y = feature_service.prepare_ml_dataset(prediction_horizon=1)
    
    print(f"✅ Data: X{X.shape}, y{y.shape}")
    
    # 2. Improved Model
    print("\n🧠 Creating IMPROVED model...")
    model = LSTMGoldPricePredictor(
        sequence_length=90,        # 60 → 90 (بیشتر ببینه)
        prediction_horizon=1,
        lstm_units=[256, 128, 64], # [128,64,32] → [256,128,64]
        dropout_rate=0.3           # 0.2 → 0.3 (کمتر overfit)
    )
    
    print("✅ Improvements:")
    print("   • Sequence: 60 → 90 days")
    print("   • Units: [128,64,32] → [256,128,64]")
    print("   • Dropout: 0.2 → 0.3")
    
    # 3. Training
    print("\n🚀 Training (may take 30-60 min)...")
    
    results = model.train(
        X, y,
        validation_split=0.2,
        epochs=100,            # 50 → 100
        batch_size=32
    )
    
    # 4. Results
    print("\n" + "="*70)
    print("📊 IMPROVED Results:")
    print("="*70)
    
    for metric, value in results['metrics'].items():
        if metric == 'rmse':
            print(f"   RMSE: ${value:.2f}")
        elif metric == 'mae':
            print(f"   MAE: ${value:.2f}")
        elif metric == 'mape':
            print(f"   MAPE: {value:.2f}%")
        elif metric == 'r2':
            print(f"   R²: {value:.4f} ← باید بهتر شده باشه!")
    
    # 5. Save
    print("\n💾 Saving improved model...")
    model.save_model('models/lstm_gold_predictor_v2')
    model.plot_training_history()
    
    print("\n✅ COMPLETE!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
