#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test GLD to Gold Conversion

Author: Hoseyn Doulabi (@hoseynd-ai)
"""

from app.application.services.data_collection.real_gold_service import RealGoldService
from app.application.services.data_collection.alpha_vantage_service import AlphaVantageService
from app.core.logging import setup_logging

setup_logging()


def main():
    print("\n" + "="*60)
    print("💰 Testing GLD to Gold Conversion")
    print("="*60 + "\n")
    
    # Get real gold price
    real_service = RealGoldService()
    real_gold_price = real_service.get_current_price()
    print(f"📊 Real Gold Price (spot): ${real_gold_price:,.2f}/oz\n")
    
    # Get GLD price
    av_service = AlphaVantageService()
    gld_quote = av_service.get_current_quote()
    
    if gld_quote:
        gld_price = gld_quote['price']
        print(f"📈 GLD ETF Price: ${gld_price:.2f}\n")
        
        # Calculate conversion factor
        conversion_factor = real_gold_price / gld_price
        
        print("="*60)
        print("🔍 Conversion Analysis:")
        print(f"   Real Gold: ${real_gold_price:,.2f}/oz")
        print(f"   GLD Price: ${gld_price:.2f}")
        print(f"   Factor:    {conversion_factor:.2f}x")
        print(f"   ")
        print(f"   Formula: Gold Price = GLD × {conversion_factor:.2f}")
        print("="*60)
        
        # Test conversion
        print(f"\n✅ Converted GLD to Gold:")
        print(f"   GLD ${gld_price:.2f} × {conversion_factor:.2f} = ${gld_price * conversion_factor:,.2f}")
        print(f"   Real Gold Price: ${real_gold_price:,.2f}")
        print(f"   Difference: ${abs(real_gold_price - (gld_price * conversion_factor)):,.2f}")
    else:
        print("❌ Failed to get GLD quote")
    
    print("\n" + "="*60)
    print("🎉 Conversion Test Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
