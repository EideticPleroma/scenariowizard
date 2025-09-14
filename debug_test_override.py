#!/usr/bin/env python3
"""
Debug script to test FastAPI dependency override
"""

import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.services.database import get_database_session, DatabaseService
from app.api.routes.documents import get_database_service

async def test_override():
    """Test FastAPI dependency override"""
    
    # Create test engine and session
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as test_session:
        print(f"✅ Test session created: {type(test_session)}")
        
        # Test the override functions
        def override_get_db():
            print("🔍 override_get_db called")
            return test_session
        
        def override_get_db_service():
            print("🔍 override_get_db_service called")
            return DatabaseService(test_session)
        
        # Apply overrides
        app.dependency_overrides[get_database_session] = override_get_db
        app.dependency_overrides[get_database_service] = override_get_db_service
        
        print("✅ Overrides applied")
        
        # Test with TestClient
        with TestClient(app) as client:
            print("✅ TestClient created")
            
            # Make a simple request to see what happens
            try:
                response = client.get("/api/v1/documents/")
                print(f"✅ GET /api/v1/documents/ returned: {response.status_code}")
            except Exception as e:
                print(f"❌ Error in GET request: {e}")
            
            # Test upload endpoint
            try:
                files = {"file": ("test.md", "test content", "text/markdown")}
                response = client.post("/api/v1/documents/upload", files=files)
                print(f"✅ POST /api/v1/documents/upload returned: {response.status_code}")
                if response.status_code != 200:
                    print(f"❌ Response content: {response.text}")
            except Exception as e:
                print(f"❌ Error in POST request: {e}")
        
        # Clear overrides
        app.dependency_overrides.clear()
        print("✅ Overrides cleared")

if __name__ == "__main__":
    asyncio.run(test_override())
