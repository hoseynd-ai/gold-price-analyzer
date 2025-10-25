#!/usr/bin/env python3
import sys
from pathlib import Path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import asyncio
from app.infrastructure.database.base import Base, engine
from app.infrastructure.database.models import DollarIndexPrice
from sqlalchemy import inspect

async def main():
    print('🔨 Creating dollar_index_prices table...')
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print('✅ Table created successfully!')
    
    # Verify
    async with engine.connect() as conn:
        def check(connection):
            inspector = inspect(connection)
            return 'dollar_index_prices' in inspector.get_table_names()
        
        exists = await conn.run_sync(check)
        print(f'\n{"✅" if exists else "❌"} Table verification: {exists}')

if __name__ == "__main__":
    asyncio.run(main())
