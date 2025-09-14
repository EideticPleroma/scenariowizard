"""
Database initialization and migration utilities
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

from app.models.database import Base
from app.services.database import DATABASE_URL, engine

async def create_tables():
    """Create all database tables"""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully")

async def drop_tables():
    """Drop all database tables (for development/testing)"""
    async with engine.begin() as conn:
        # Drop all tables
        await conn.run_sync(Base.metadata.drop_all)
        print("Database tables dropped successfully")

async def reset_database():
    """Drop and recreate all tables"""
    await drop_tables()
    await create_tables()

async def check_database():
    """Check database connection and table status"""
    try:
        async with engine.begin() as conn:
            # Basic connectivity check
            result = await conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")

            # Check if tables exist
            for table_name in Base.metadata.tables.keys():
                table_exists = await conn.run_sync(
                    lambda sync_conn: text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                )
                if table_exists:
                    print(f"✅ Table '{table_name}' exists")
                else:
                    print(f"❌ Table '{table_name}' missing")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

    return True

async def init_database():
    """Initialize the database with tables and basic setup"""
    print(f"Using database: {DATABASE_URL}")
    await create_tables()
    await check_database()

if __name__ == "__main__":
    asyncio.run(init_database())
