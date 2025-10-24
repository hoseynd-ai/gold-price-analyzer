#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Price Analyzer - API v1 Router

Main API router for version 1.

Author: Hoseyn Doulabi (@hoseynd-ai)
Project Manager: Hoseyn Doulabi
Created: 2025-10-24
License: MIT
"""

from fastapi import APIRouter

from app.presentation.api.v1.endpoints import health

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["Health"])
