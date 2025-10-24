#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Price Analyzer - Main Application

Author: Hoseyn Doulabi (@hoseynd-ai)
Project Manager: Hoseyn Doulabi
Repository: https://github.com/hoseynd-ai/gold-price-analyzer
Created: 2025-10-24
License: MIT

Copyright (c) 2025 Hoseyn Doulabi
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.presentation.api.v1 import api_router

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan."""
    logger.info(
        "application_startup",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        author="Hoseyn Doulabi (@hoseynd-ai)",
    )
    yield
    logger.info("application_shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    🏆 Gold Price Analyzer API
    
    AI-Powered Gold Price Analysis & Prediction System
    
    **Author & Project Manager:** Hoseyn Doulabi (@hoseynd-ai)
    **Repository:** https://github.com/hoseynd-ai/gold-price-analyzer
    **Started:** October 24, 2025
    
    ## Features
    
    * 📊 Real-time gold price data collection
    * 📰 News analysis with sentiment scoring
    * 💰 Interest rates & economic indicators
    * 🤖 ML-powered price predictions
    * 📈 Technical analysis & indicators
    
    ## Data Sources (All Free!)
    
    * Yahoo Finance (Gold prices)
    * FRED API (Interest rates, economic data)
    * NewsAPI & RSS Feeds (Financial news)
    * FinBERT (Sentiment analysis)
    
    ---
    
    © 2025 Hoseyn Doulabi. All rights reserved.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json",
    contact={
        "name": "Hoseyn Doulabi",
        "url": "https://github.com/hoseynd-ai",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return JSONResponse(
        content={
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "author": "Hoseyn Doulabi (@hoseynd-ai)",
            "description": "AI-Powered Gold Price Analysis & Prediction System",
            "docs": "/docs",
            "redoc": "/redoc",
            "github": "https://github.com/hoseynd-ai/gold-price-analyzer",
            "status": "running",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
