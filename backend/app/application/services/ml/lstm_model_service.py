#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Price Analyzer - LSTM Model Service

مدل LSTM برای پیش‌بینی قیمت طلا بر اساس:
- قیمت‌های گذشته (OHLCV)
- اندیکاتورهای تکنیکال (RSI, MACD, BB)
- احساسات اخبار (FinBERT sentiment)

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25 15:46:25 UTC
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Tuple, Dict, Any, Optional
import joblib
import json
import os

from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam

from app.core.logging import get_logger
from app.application.services.ml.feature_engineering_service import FeatureEngineeringService

logger = get_logger(__name__)


class LSTMGoldPricePredictor:
    """
    مدل LSTM برای پیش‌بینی قیمت طلا
    
    این مدل:
    1. از 42 feature استفاده می‌کند
    2. با 21 سال داده train می‌شود
    3. قیمت 1, 7, 30 روز آینده را پیش‌بینی می‌کند
    
    Author: Hoseyn Doulabi (@hoseynd-ai)
    Created: 2025-10-25 15:46:25 UTC
    """
    
    def __init__(
        self,
        sequence_length: int = 60,
        prediction_horizon: int = 1,
        lstm_units: list = [128, 64, 32],
        dropout_rate: float = 0.2
    ):
        """
        Initialize LSTM model
        
        Args:
            sequence_length: چند روز گذشته رو ببینه (پیش‌فرض: 60 روز)
            prediction_horizon: چند روز آینده پیش‌بینی کنه (1, 7, 30)
            lstm_units: تعداد units در هر لایه LSTM
            dropout_rate: نرخ dropout برای جلوگیری از overfitting
        """
        self.sequence_length = sequence_length
        self.prediction_horizon = prediction_horizon
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        
        self.model = None
        self.scaler_X = MinMaxScaler(feature_range=(0, 1))
        self.scaler_y = MinMaxScaler(feature_range=(0, 1))
        
        self.feature_names = None
        self.training_history = None
        self.metrics = {}
        
        logger.info("lstm_model_initialized",
                   sequence_length=sequence_length,
                   prediction_horizon=prediction_horizon,
                   lstm_units=lstm_units)
    
    def create_sequences(
        self, 
        X: np.ndarray, 
        y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        ساخت sequences برای LSTM
        
        LSTM نیاز داره که داده‌ها به صورت توالی (sequence) باشن.
        مثلاً: برای پیش‌بینی قیمت فردا، 60 روز گذشته رو می‌بینه.
        
        Args:
            X: Features (5197, 42)
            y: Target (5197, 1)
            
        Returns:
            X_seq: (samples, sequence_length, features)
            y_seq: (samples, 1)
        """
        logger.info("creating_sequences", 
                   X_shape=X.shape,
                   sequence_length=self.sequence_length)
        
        X_seq = []
        y_seq = []
        
        for i in range(self.sequence_length, len(X)):
            # آخرین sequence_length روز
            X_seq.append(X[i - self.sequence_length:i])
            # قیمت target
            y_seq.append(y[i])
        
        X_seq = np.array(X_seq)
        y_seq = np.array(y_seq)
        
        logger.info("sequences_created",
                   X_seq_shape=X_seq.shape,
                   y_seq_shape=y_seq.shape)
        
        return X_seq, y_seq
    
    def build_model(self, input_shape: Tuple[int, int]) -> keras.Model:
        """
        ساخت معماری LSTM
        
        معماری:
        1. Bidirectional LSTM (می‌تونه از دو طرف ببینه)
        2. Dropout layers (جلوگیری از overfitting)
        3. Dense layers (fully connected)
        
        Args:
            input_shape: (sequence_length, n_features)
            
        Returns:
            Compiled Keras model
        """
        logger.info("building_model", input_shape=input_shape)
        
        model = Sequential([
            # لایه اول: Bidirectional LSTM
            Bidirectional(
                LSTM(
                    self.lstm_units[0],
                    return_sequences=True
                ),
                input_shape=input_shape
            ),
            Dropout(self.dropout_rate),
            
            # لایه دوم: LSTM
            LSTM(self.lstm_units[1], return_sequences=True),
            Dropout(self.dropout_rate),
            
            # لایه سوم: LSTM
            LSTM(self.lstm_units[2], return_sequences=False),
            Dropout(self.dropout_rate),
            
            # لایه‌های Dense
            Dense(32, activation='relu'),
            Dropout(self.dropout_rate),
            
            Dense(16, activation='relu'),
            
            # خروجی: 1 عدد (قیمت پیش‌بینی شده)
            Dense(1)
        ])
        
        # Build model برای محاسبه params
        model.build(input_shape=(None,) + input_shape)
        
        # Compile
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        logger.info("model_built", 
                   total_params=model.count_params(),
                   layers=len(model.layers))
        
        return model
    
    def train(
        self,
        X: pd.DataFrame,
        y: pd.DataFrame,
        validation_split: float = 0.2,
        epochs: int = 100,
        batch_size: int = 32
    ) -> Dict[str, Any]:
        """
        آموزش مدل LSTM
        
        Args:
            X: Features DataFrame
            y: Target DataFrame
            validation_split: درصد داده برای validation
            epochs: تعداد epochs
            batch_size: اندازه batch
            
        Returns:
            دیکشنری شامل metrics و history
        """
        logger.info("starting_training",
                   X_shape=X.shape,
                   y_shape=y.shape,
                   epochs=epochs)
        
        # ذخیره نام features
        self.feature_names = X.columns.tolist()
        
        # تبدیل به numpy
        X_array = X.values
        y_array = y.values
        
        # Scaling
        logger.info("scaling_data")
        X_scaled = self.scaler_X.fit_transform(X_array)
        y_scaled = self.scaler_y.fit_transform(y_array)
        
        # ساخت sequences
        X_seq, y_seq = self.create_sequences(X_scaled, y_scaled)
        
        # Split train/validation
        split_idx = int(len(X_seq) * (1 - validation_split))
        X_train = X_seq[:split_idx]
        y_train = y_seq[:split_idx]
        X_val = X_seq[split_idx:]
        y_val = y_seq[split_idx:]
        
        logger.info("data_split",
                   train_samples=len(X_train),
                   val_samples=len(X_val))
        
        # ساخت model
        input_shape = (X_train.shape[1], X_train.shape[2])
        self.model = self.build_model(input_shape)
        
        # ایجاد پوشه models
        os.makedirs('models', exist_ok=True)
        
        # Callbacks
        callbacks = [
            # Early stopping اگر val_loss بهبود نیافت
            EarlyStopping(
                monitor='val_loss',
                patience=15,
                restore_best_weights=True,
                verbose=1
            ),
            
            # ذخیره بهترین model
            ModelCheckpoint(
                'models/lstm_best_model.h5',
                monitor='val_loss',
                save_best_only=True,
                verbose=1
            ),
            
            # کاهش learning rate
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=0.00001,
                verbose=1
            )
        ]
        
        # Training
        logger.info("training_started")
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        self.training_history = history.history
        logger.info("training_completed",
                   final_loss=history.history['loss'][-1],
                   final_val_loss=history.history['val_loss'][-1])
        
        # Evaluation
        metrics = self.evaluate(X_val, y_val)
        
        return {
            'history': history.history,
            'metrics': metrics,
            'train_samples': len(X_train),
            'val_samples': len(X_val)
        }
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        ارزیابی مدل
        
        Args:
            X: Features
            y: True values
            
        Returns:
            دیکشنری metrics
        """
        logger.info("evaluating_model")
        
        # Scaling
        if len(X.shape) == 2:
            X_scaled = self.scaler_X.transform(X)
            y_scaled = self.scaler_y.transform(y)
            X_seq, y_seq = self.create_sequences(X_scaled, y_scaled)
        else:
            X_seq = X
            y_seq = y
        
        # Prediction
        y_pred_scaled = self.model.predict(X_seq, verbose=0)
        
        # Inverse transform
        y_pred = self.scaler_y.inverse_transform(y_pred_scaled)
        y_true = self.scaler_y.inverse_transform(y_seq)
        
        # Metrics
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        
        # MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        
        metrics = {
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'r2': float(r2),
            'mape': float(mape)
        }
        
        self.metrics = metrics
        
        logger.info("evaluation_complete",
                   rmse=rmse,
                   mae=mae,
                   r2=r2,
                   mape=mape)
        
        return metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        پیش‌بینی قیمت
        
        Args:
            X: Features DataFrame
            
        Returns:
            پیش‌بینی قیمت
        """
        logger.info("making_prediction", X_shape=X.shape)
        
        # Scaling
        X_scaled = self.scaler_X.transform(X.values)
        
        # اگر X کمتر از sequence_length باشه، نمی‌تونیم predict کنیم
        if len(X_scaled) < self.sequence_length:
            logger.warning("insufficient_data_for_prediction",
                         required=self.sequence_length,
                         got=len(X_scaled))
            return None
        
        # آخرین sequence
        X_seq = X_scaled[-self.sequence_length:].reshape(1, self.sequence_length, -1)
        
        # Prediction
        y_pred_scaled = self.model.predict(X_seq, verbose=0)
        y_pred = self.scaler_y.inverse_transform(y_pred_scaled)
        
        logger.info("prediction_made", predicted_price=y_pred[0][0])
        
        return y_pred[0][0]
    
    def predict_future(
        self, 
        X: pd.DataFrame, 
        days: int = 7
    ) -> np.ndarray:
        """
        پیش‌بینی چند روز آینده
        
        Args:
            X: Features DataFrame (آخرین داده‌ها)
            days: تعداد روزهای آینده
            
        Returns:
            آرایه پیش‌بینی‌ها
        """
        logger.info("predicting_future", days=days)
        
        predictions = []
        
        for day in range(days):
            # پیش‌بینی روز بعد
            pred = self.predict(X)
            predictions.append(pred)
            
            # برای پیش‌بینی روز بعدی، باید از prediction استفاده کنیم
            # (در حال حاضر فقط یک روز پیش‌بینی می‌کنیم)
            # این بخش می‌تونه پیچیده‌تر بشه
            
        return np.array(predictions)
    
    def save_model(self, path: str = 'models/lstm_gold_predictor'):
        """
        ذخیره مدل و تنظیمات
        
        Args:
            path: مسیر ذخیره
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # ذخیره Keras model
        self.model.save(f'{path}.h5')
        
        # ذخیره scalers
        joblib.dump(self.scaler_X, f'{path}_scaler_X.pkl')
        joblib.dump(self.scaler_y, f'{path}_scaler_y.pkl')
        
        # ذخیره config
        config = {
            'sequence_length': self.sequence_length,
            'prediction_horizon': self.prediction_horizon,
            'lstm_units': self.lstm_units,
            'dropout_rate': self.dropout_rate,
            'feature_names': self.feature_names,
            'metrics': self.metrics,
            'training_history': self.training_history
        }
        
        with open(f'{path}_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info("model_saved", path=path)
    
    def load_model_weights(self, path: str = 'models/lstm_gold_predictor'):
        """
        بارگذاری مدل
        
        Args:
            path: مسیر بارگذاری
        """
        # بارگذاری Keras model
        self.model = load_model(f'{path}.h5')
        
        # بارگذاری scalers
        self.scaler_X = joblib.load(f'{path}_scaler_X.pkl')
        self.scaler_y = joblib.load(f'{path}_scaler_y.pkl')
        
        # بارگذاری config
        with open(f'{path}_config.json', 'r') as f:
            config = json.load(f)
        
        self.sequence_length = config['sequence_length']
        self.prediction_horizon = config['prediction_horizon']
        self.lstm_units = config['lstm_units']
        self.dropout_rate = config['dropout_rate']
        self.feature_names = config['feature_names']
        self.metrics = config['metrics']
        self.training_history = config['training_history']
        
        logger.info("model_loaded", path=path)
    
    def plot_training_history(self):
        """
        رسم نمودار training history
        """
        import matplotlib.pyplot as plt
        
        if self.training_history is None:
            logger.warning("no_training_history")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Loss
        ax1.plot(self.training_history['loss'], label='Training Loss')
        ax1.plot(self.training_history['val_loss'], label='Validation Loss')
        ax1.set_title('Model Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss (MSE)')
        ax1.legend()
        ax1.grid(True)
        
        # MAE
        ax2.plot(self.training_history['mae'], label='Training MAE')
        ax2.plot(self.training_history['val_mae'], label='Validation MAE')
        ax2.set_title('Model MAE')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('MAE')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig('models/training_history.png', dpi=300)
        plt.close()
        
        logger.info("training_history_plotted")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧠 LSTM Gold Price Predictor - Training")
    print("="*70 + "\n")
    
    # 1. آماده‌سازی داده
    print("📊 Step 1: Preparing data...")
    DATABASE_URL = "postgresql+psycopg2://admin:admin123@localhost:5432/gold_analyzer"
    
    feature_service = FeatureEngineeringService(DATABASE_URL)
    X, y = feature_service.prepare_ml_dataset(prediction_horizon=1)
    
    print(f"✅ Data ready: X{X.shape}, y{y.shape}")
    
    # 2. ساخت مدل
    print("\n🧠 Step 2: Creating LSTM model...")
    model = LSTMGoldPricePredictor(
        sequence_length=60,
        prediction_horizon=1,
        lstm_units=[128, 64, 32],
        dropout_rate=0.2
    )
    
    # 3. آموزش
    print("\n🚀 Step 3: Training model...")
    print("⏱️  This may take 10-30 minutes...")
    
    results = model.train(
        X, y,
        validation_split=0.2,
        epochs=100,
        batch_size=32
    )
    
    # 4. نتایج
    print("\n" + "="*70)
    print("📊 Training Results:")
    print("="*70)
    print(f"\nMetrics:")
    for metric, value in results['metrics'].items():
        print(f"  {metric}: {value:.4f}")
    
    print(f"\nSamples:")
    print(f"  Train: {results['train_samples']}")
    print(f"  Validation: {results['val_samples']}")
    
    # 5. ذخیره
    print("\n💾 Saving model...")
    model.save_model('models/lstm_gold_predictor')
    
    # 6. رسم نمودار
    print("📊 Plotting training history...")
    model.plot_training_history()
    
    print("\n" + "="*70)
    print("✅ Training Complete!")
    print("="*70 + "\n")