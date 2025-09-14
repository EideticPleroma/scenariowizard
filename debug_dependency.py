#!/usr/bin/env python3
"""
Debug script to test dependency injection
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.database import get_database_session, DatabaseService
from app.api.routes.documents import get_database_service

async def test_dependency_injection():
    """Test the dependency injection pattern"""
    
    # Create test engine
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Test 1: Direct session creation
    print("Test 1: Direct session creation")
    async with async_session() as session:
        db_service = DatabaseService(session)
        print(f"✅ DatabaseService created with session: {type(session)}")
        print(f"✅ DatabaseService.session type: {type(db_service.session)}")
    
    # Test 2: Using get_database_session generator
    print("\nTest 2: Using get_database_session generator")
    async for session in get_database_session():
        print(f"✅ Generator yielded session: {type(session)}")
        db_service = DatabaseService(session)
        print(f"✅ DatabaseService created with yielded session: {type(db_service.session)}")
        break  # Only test first yield
    
    # Test 3: Using get_database_service dependency
    print("\nTest 3: Using get_database_service dependency")
    async for session in get_database_session():
        db_service = await get_database_service(session)
        print(f"✅ get_database_service returned: {type(db_service)}")
        print(f"✅ DatabaseService.session type: {type(db_service.session)}")
        break  # Only test first yield

if __name__ == "__main__":
    asyncio.run(test_dependency_injection())
