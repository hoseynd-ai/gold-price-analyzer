#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Database Connection & Create Tables

Author: Hoseyn Doulabi (@hoseynd-ai)
Created: 2025-10-25
"""

import asyncio
from app.infrastructure.database.base import init_db, check_db_connection, close_db
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def main():
    """Test database connection and create tables."""
    
    print("\n" + "="*50)
    print("🔧 Testing Database Connection")
    print("="*50 + "\n")
    
    # 1. Test connection
    logger.info("step_1_checking_connection")
    is_connected = await check_db_connection()
    
    if not is_connected:
        logger.error("connection_failed")
        print("❌ Database connection failed!")
        return
    
    print("✅ Database connection successful!\n")
    
    # 2. Create tables
    logger.info("step_2_creating_tables")
    print("📊 Creating tables...")
    
    try:
        await init_db()
        print("✅ Tables created successfully!\n")
    except Exception as e:
        logger.error("table_creation_failed", error=str(e))
        print(f"❌ Table creation failed: {e}\n")
        return
    
    # 3. Close connection
    logger.info("step_3_closing_connection")
    await close_db()
    print("✅ Database connection closed\n")
    
    print("="*50)
    print("🎉 All tests passed!")
    print("="*50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
