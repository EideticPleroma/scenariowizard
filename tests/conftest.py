"""
Test configuration and fixtures
"""

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient
import tempfile
import os

from app.main import app
from app.models.database import Base
from app.services.database import get_database_session
from app.api.routes.documents import get_database_service

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncSession:
    """Create test database session"""
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session

@pytest.fixture
def test_client(test_session: AsyncSession) -> TestClient:
    """Create test client with database session override"""
    from app.services.database import DatabaseService
    
    def override_get_db():
        return test_session
    
    def override_get_db_service():
        return DatabaseService(test_session)
    
    app.dependency_overrides[get_database_session] = override_get_db
    app.dependency_overrides[get_database_service] = override_get_db_service
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture
async def async_test_client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with database session override"""
    def override_get_db():
        return test_session
    
    app.dependency_overrides[get_database_session] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture
def sample_markdown_content():
    """Sample markdown content for testing"""
    return """# User Story: User Login

## User Stories
- As a user, I want to log into the application
- As a user, I want to reset my password
- As a user, I want to log out of the application

## Acceptance Criteria
- User can enter email and password
- System validates credentials
- User is redirected to dashboard on success
- Error message shown for invalid credentials
- Password field is masked

## Feature: User Authentication
This feature handles user authentication including login, logout, and password reset functionality.
"""

@pytest.fixture
def sample_document_data():
    """Sample document data for testing"""
    return {
        "filename": "test_user_stories.md",
        "content": """# User Story: User Login

## User Stories
- As a user, I want to log into the application

## Acceptance Criteria
- User can enter email and password
- System validates credentials
""",
        "status": "pending"
    }

@pytest.fixture
def sample_feature_data():
    """Sample feature data for testing"""
    return {
        "title": "User Authentication",
        "user_stories": "As a user, I want to log into the application",
        "acceptance_criteria": "User can enter email and password"
    }

@pytest.fixture
def sample_scenario_data():
    """Sample scenario data for testing"""
    return {
        "content": """Feature: User Authentication
Scenario: Valid login
  Given I am on the login page
  When I enter valid credentials
  Then I should be logged in""",
        "test_type": "unit"
    }

@pytest.fixture
def temp_file():
    """Create a temporary file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Test Document
## User Stories
- Test user story
## Acceptance Criteria
- Test criteria
""")
        temp_path = f.name
    
    yield temp_path
    
    # Clean up
    os.unlink(temp_path)
