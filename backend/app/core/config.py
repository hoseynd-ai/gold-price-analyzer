#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application Configuration

تنظیمات اصلی برنامه از environment variables

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-23
Updated: 2025-10-25 16:16:30 UTC
"""

from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from .env file
    
    همه تنظیمات برنامه از فایل .env خوانده می‌شود
    """
    
    # ============================================================================
    # Application Info
    # ============================================================================
    APP_NAME: str = "Gold Price Analyzer"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # ============================================================================
    # Database Configuration (PostgreSQL)
    # ============================================================================
    POSTGRES_USER: str = Field(
        default="admin",
        description="PostgreSQL username"
    )
    POSTGRES_PASSWORD: str = Field(
        default="admin123",
        description="PostgreSQL password"
    )
    POSTGRES_HOST: str = Field(
        default="localhost",
        description="PostgreSQL host"
    )
    POSTGRES_PORT: int = Field(
        default=5432,
        description="PostgreSQL port"
    )
    POSTGRES_DB: str = Field(
        default="gold_analyzer",
        description="PostgreSQL database name"
    )
    
    # Database Pool Settings
    DATABASE_POOL_SIZE: int = Field(
        default=5,
        description="Database connection pool size"
    )
    DATABASE_MAX_OVERFLOW: int = Field(
        default=10,
        description="Maximum overflow connections"
    )
    DATABASE_POOL_TIMEOUT: int = Field(
        default=30,
        description="Pool timeout in seconds"
    )
    DATABASE_ECHO: bool = Field(
        default=False,
        description="Echo SQL queries (for debugging)"
    )
    
    @property
    def DATABASE_URL(self) -> str:
        """Build database URL from components"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Synchronous database URL for SQLAlchemy"""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # ============================================================================
    # Redis Configuration
    # ============================================================================
    REDIS_HOST: str = Field(
        default="localhost",
        description="Redis host"
    )
    REDIS_PORT: int = Field(
        default=6379,
        description="Redis port"
    )
    REDIS_DB: int = Field(
        default=0,
        description="Redis database number"
    )
    REDIS_PASSWORD: Optional[str] = Field(
        default=None,
        description="Redis password (optional)"
    )
    
    @property
    def REDIS_URL(self) -> str:
        """Build Redis URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # ============================================================================
    # API Keys (External Services)
    # ============================================================================
    
    # Alpha Vantage (for GLD ETF data)
    ALPHA_VANTAGE_API_KEY: str = Field(
        default="demo",
        description="Alpha Vantage API key for stock data"
    )
    
    # NewsAPI (for historical news collection)
    NEWSAPI_KEY: Optional[str] = Field(
        default=None,
        description="NewsAPI.org API key for historical news"
    )
    
    # Future APIs (placeholders)
    OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        description="OpenAI API key (future use)"
    )
    
    # ============================================================================
    # FastAPI Configuration
    # ============================================================================
    API_V1_PREFIX: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    
    # ============================================================================
    # ML/AI Configuration
    # ============================================================================
    
    # FinBERT Model
    FINBERT_MODEL_NAME: str = "ProsusAI/finbert"
    FINBERT_MAX_LENGTH: int = 512
    FINBERT_BATCH_SIZE: int = 8
    
    # LSTM Model
    LSTM_SEQUENCE_LENGTH: int = 60
    LSTM_PREDICTION_HORIZON: int = 1
    LSTM_EPOCHS: int = 100
    LSTM_BATCH_SIZE: int = 32
    
    # ============================================================================
    # Data Collection Configuration
    # ============================================================================
    
    # News Collection
    NEWS_FETCH_INTERVAL_HOURS: int = 6
    NEWS_MAX_AGE_DAYS: int = 30
    
    # Gold Price Collection
    GOLD_PRICE_FETCH_INTERVAL_MINUTES: int = 60
    
    # ============================================================================
    # Logging Configuration
    # ============================================================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or console
    
    # ============================================================================
    # Cache Configuration
    # ============================================================================
    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    
    # ============================================================================
    # Security
    # ============================================================================
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT and encryption"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # ============================================================================
    # Pydantic Configuration
    # ============================================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='allow'  # اجازه field های اضافی
    )


# ============================================================================
# Create settings instance
# ============================================================================
settings = Settings()


# ============================================================================
# Helper functions
# ============================================================================

def get_settings() -> Settings:
    """Get application settings"""
    return settings


def is_production() -> bool:
    """Check if running in production"""
    return settings.ENVIRONMENT.lower() == "production"


def is_development() -> bool:
    """Check if running in development"""
    return settings.ENVIRONMENT.lower() == "development"


# ============================================================================
# Validate critical settings on import
# ============================================================================

def validate_settings():
    """Validate critical settings"""
    errors = []
    
    # Check database
    if not settings.POSTGRES_USER or not settings.POSTGRES_PASSWORD:
        errors.append("Database credentials not configured")
    
    # Check API keys (warnings only)
    if not settings.ALPHA_VANTAGE_API_KEY or settings.ALPHA_VANTAGE_API_KEY == "demo":
        print("⚠️  Warning: Using demo Alpha Vantage API key (limited)")
    
    if not settings.NEWSAPI_KEY:
        print("⚠️  Warning: NewsAPI key not configured (historical news collection disabled)")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")


# Validate on import
try:
    validate_settings()
except ValueError as e:
    print(f"❌ Configuration Error: {e}")
    # Don't raise in development
    if is_production():
        raise


# ============================================================================
# Export
# ============================================================================

__all__ = [
    'settings',
    'Settings',
    'get_settings',
    'is_production',
    'is_development',
]
