#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Price Analyzer - Database Base

SQLAlchemy async base, engine and session management.

Author: Hoseyn Doulabi (@hoseynd-ai)
Project Manager: Hoseyn Doulabi
Repository: https://github.com/hoseynd-ai/gold-price-analyzer
Created: 2025-10-25
License: MIT
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ====================================
# Engine Setup
# ====================================
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# ====================================
# Session Factory
# ====================================
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# ====================================
# Base Class for Models
# ====================================
Base = declarative_base()


# ====================================
# Dependency for FastAPI
# ====================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async database session dependency.
    
    Usage in FastAPI endpoint:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    
    Author: Hoseyn Doulabi (@hoseynd-ai)
    Created: 2025-10-25
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("database_session_error", error=str(e), exc_info=True)
            raise
        finally:
            await session.close()


# ====================================
# Database Lifecycle
# ====================================
async def init_db() -> None:
    """
    Initialize database - create all tables.
    
    Call this on application startup.
    
    Author: Hoseyn Doulabi (@hoseynd-ai)
    Created: 2025-10-25
    """
    logger.info("database_initializing")
    
    async with engine.begin() as conn:
        # Import all models here to ensure they're registered
        from app.infrastructure.database.models import (
            gold_price_fact,
            news_event,
        )
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("database_initialized", tables=len(Base.metadata.tables))


async def close_db() -> None:
    """
    Close database connections.
    
    Call this on application shutdown.
    
    Author: Hoseyn Doulabi (@hoseynd-ai)
    Created: 2025-10-25
    """
    logger.info("database_closing")
    await engine.dispose()
    logger.info("database_closed")


async def check_db_connection() -> bool:
    """
    Check database connection health.
    
    Returns:
        bool: True if connection is healthy
        
    Author: Hoseyn Doulabi (@hoseynd-ai)
    Created: 2025-10-25
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("database_connection_healthy")
        return True
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))
        return False