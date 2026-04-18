"""
Alembic-free migration helper.
Reads schema.sql and applies it to the configured database.
Usage: python scripts/init_db.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.core.database import engine, Base

async def main():
    print("Creating all database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully.")

if __name__ == "__main__":
    asyncio.run(main())
