#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Price Analyzer - Kitco Gold Service

Uses Kitco's data for accurate gold prices.

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25
License: MIT
"""

from datetime import datetime, UTC
from typing import Optional
import requests
from bs4 import BeautifulSoup

from app.core.logging import get_logger

logger = get_logger(__name__)


class KitcoGoldService:
    """
    Kitco Gold Price Service.
    
    Fetches live gold prices from Kitco.com
    
    Author: Hoseyn Doulabi (@hoseynd-ai)
    Created: 2025-10-25
    """
    
    def __init__(self):
        """Initialize Kitco service."""
        self.base_url = "https://www.kitco.com/gold-price-today-usa/"
        logger.info("kitco_service_initialized")
    
    def get_current_price(self) -> Optional[float]:
        """
        Get current gold price from Kitco.
        
        Returns:
            float: Current gold price in USD per ounce
        """
        try:
            # Kitco JSON API
            api_url = "https://www.kitco.com/market/json/spot.json"
            
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Kitco returns price in their format
                if 'gold' in data:
                    price = float(data['gold']['bid'])
                    
                    logger.info(
                        "kitco_price_fetched",
                        price=price,
                        source="kitco_api"
                    )
                    
                    return price
            
            logger.warning("kitco_api_failed", status=response.status_code)
            return None
            
        except Exception as e:
            logger.error("kitco_fetch_error", error=str(e))
            return None


# تست سریع
if __name__ == "__main__":
    service = KitcoGoldService()
    price = service.get_current_price()
    print(f"Current Gold Price: ${price:.2f}" if price else "Failed")
