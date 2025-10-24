#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Price Analyzer - Health Check Endpoint

Health check and system status endpoints.

Author: Hoseyn Doulabi (@hoseynd-ai)
Project Manager: Hoseyn Doulabi
Repository: https://github.com/hoseynd-ai/gold-price-analyzer
Created: 2025-10-24
Version: 1.0.0
License: MIT
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check if the API is running and healthy.",
)
async def health_check() -> JSONResponse:
    """
    Health check endpoint.
    
    Returns the current status of the API and its services.
    
    Author: Hoseyn Doulabi (@hoseynd-ai)
    Created: 2025-10-24
    """
    logger.info("health_check_requested")
    
    health_data: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "app": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        },
        "author": "Hoseyn Doulabi (@hoseynd-ai)",
        "project_manager": "Hoseyn Doulabi",
        "github": "https://github.com/hoseynd-ai/gold-price-analyzer",
        "services": {
            "api": "operational",
            "database": "pending_connection",
            "redis": "pending_connection",
        },
    }
    
    return JSONResponse(
        content=health_data,
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/ping",
    status_code=status.HTTP_200_OK,
    summary="Ping",
    description="Simple ping endpoint to check API responsiveness.",
)
async def ping() -> Dict[str, str]:
    """
    Ping endpoint.
    
    Simple endpoint to check if the API is responding.
    
    Author: Hoseyn Doulabi (@hoseynd-ai)
    Created: 2025-10-24
    """
    return {
        "ping": "pong",
        "author": "Hoseyn Doulabi (@hoseynd-ai)",
        "timestamp": datetime.utcnow().isoformat(),
    }
