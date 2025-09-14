# 🔧 Phase 3 Critical Fixes Reference Guide

## 📋 **Overview**

This document provides step-by-step instructions to fix the critical issues identified in Phase 3 implementation. The fixes are prioritized by severity and impact.

## 🚨 **Critical Issues Summary**

| Issue | Severity | Impact | Status |
|-------|----------|--------|--------|
| Database Session Management | CRITICAL | 100% API failure | 🔴 Unfixed |
| Test Configuration | HIGH | 13/14 tests failing | 🔴 Unfixed |
| API Response Structure | MEDIUM | Test assertions failing | 🔴 Unfixed |
| Error Handling | MEDIUM | Wrong HTTP status codes | 🔴 Unfixed |

---

## 🔥 **Priority 1: Fix Database Session Management**

### **Problem**
`DatabaseService` is being instantiated with async generators instead of actual `AsyncSession` objects, causing all database operations to fail.

### **Root Cause**
```python
# ❌ WRONG: In API routes
db_service: DatabaseService = Depends(get_database_service)

# Where get_database_service returns DatabaseService(async_generator)
# But DatabaseService.__init__ expects AsyncSession
```

### **Solution Steps**

#### **Step 1: Fix Dependency Injection in API Routes**

**File: `app/api/routes/documents.py`**
```python
# Current (BROKEN):
async def get_database_service(session: AsyncSession = Depends(get_database_session)) -> DatabaseService:
    return DatabaseService(session)  # session is async_generator here

# Fix to:
async def get_database_service(session: AsyncSession = Depends(get_database_session)) -> DatabaseService:
    return DatabaseService(session)  # session is now actual AsyncSession
```

**File: `app/api/routes/scenarios.py`**
```python
# Apply same fix as documents.py
```

#### **Step 2: Verify DatabaseService Constructor**

**File: `app/services/database.py`**
```python
class DatabaseService:
    def __init__(self, session: AsyncSession):  # ✅ Correct - expects AsyncSession
        self.session = session
```

#### **Step 3: Fix Test Configuration**

**File: `tests/conftest.py`**
```python
@pytest.fixture
def test_client(test_session: AsyncSession) -> TestClient:
    """Create test client with database session override"""
    from app.services.database import DatabaseService
    
    def override_get_db():
        return test_session
    
    def override_get_db_service():
        return DatabaseService(test_session)  # ✅ Pass actual session
    
    app.dependency_overrides[get_database_session] = override_get_db
    app.dependency_overrides[get_database_service] = override_get_db_service
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()
```

### **Verification**
```bash
python -m pytest tests/test_api_routes.py::TestDocumentRoutes::test_upload_document_success -v
```
**Expected**: Test should pass without `'async_generator' object has no attribute 'add'` error.

---

## 🔧 **Priority 2: Fix API Response Structure**

### **Problem**
Tests expect `id` field in API responses, but Pydantic model validation is not working correctly.

### **Root Cause**
```python
# ❌ WRONG: In API routes
return DocumentResponse.model_validate(document)

# But document might not have all required fields
```

### **Solution Steps**

#### **Step 1: Fix Pydantic Model Validation**

**File: `app/api/routes/documents.py`**
```python
@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db_service: DatabaseService = Depends(get_database_service)
):
    try:
        # ... validation logic ...
        
        # Create document
        document = await db_service.create_document(document_data)
        
        # ✅ FIX: Ensure all required fields are present
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            content=document.content,
            status=document.status,
            created_at=document.created_at,
            processed_at=document.processed_at,
            error_message=document.error_message
        )
    except Exception as e:
        # ... error handling ...
```

#### **Step 2: Update All API Endpoints**

Apply the same pattern to:
- `get_document`
- `list_documents`
- `process_document`
- `get_document_features`

### **Verification**
```bash
python -m pytest tests/test_api_routes.py::TestDocumentRoutes::test_get_document_success -v
```
**Expected**: Test should pass without `KeyError: 'id'` error.

---

## 🛠️ **Priority 3: Fix Error Handling**

### **Problem**
HTTP status codes are not being properly propagated from exceptions.

### **Root Cause**
```python
# ❌ WRONG: In upload_document
except HTTPException as e:
    logger.error("Document upload failed", error=str(e))
    return {"error": str(e)}  # Returns 200 instead of proper status code
```

### **Solution Steps**

#### **Step 1: Fix Exception Handling**

**File: `app/api/routes/documents.py`**
```python
@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db_service: DatabaseService = Depends(get_database_service)
):
    try:
        # ... validation logic ...
        
        # Create document
        document = await db_service.create_document(document_data)
        return DocumentResponse.model_validate(document)
        
    except HTTPException:
        # ✅ FIX: Re-raise HTTPException to preserve status code
        raise
    except Exception as e:
        logger.error("Document upload failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
```

#### **Step 2: Update Validation Logic**

```python
# File validation
if not filename:
    raise HTTPException(status_code=400, detail="Filename is required")

if not filename.endswith('.md'):
    raise HTTPException(status_code=400, detail="Only .md files are supported")

if file.size > 10 * 1024 * 1024:  # 10MB
    raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")

if not content or not content.strip():
    raise HTTPException(status_code=400, detail="File contains no readable content")
```

### **Verification**
```bash
python -m pytest tests/test_api_routes.py::TestDocumentRoutes::test_upload_document_invalid_file_type -v
```
**Expected**: Test should return 400 status code, not 500.

---

## 🧪 **Priority 4: Fix Test Configuration**

### **Problem**
21 async tests are skipped, and custom pytest marks are not registered.

### **Solution Steps**

#### **Step 1: Register Custom Pytest Marks**

**File: `pytest.ini`**
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
asyncio_mode = auto

markers =
    unit: Unit tests
    integration: Integration tests
    database: Database tests
    slow: Slow tests
```

#### **Step 2: Fix Async Test Support**

**File: `tests/conftest.py`**
```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.core.database_init import create_tables
from app.api.routes.documents import get_database_session, get_database_service
from app.services.database import DatabaseService

# ✅ FIX: Add pytest_asyncio configuration
pytest_asyncio.enable()

@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    await create_tables(engine)
    return engine

@pytest_asyncio.fixture
async def test_session(test_engine):
    """Create test database session"""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
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
```

### **Verification**
```bash
python -m pytest tests/ -v
```
**Expected**: All async tests should run, no skipped tests.

---

## 🔄 **Priority 5: Fix Deprecation Warnings**

### **Problem**
21 deprecation warnings affecting code quality and future compatibility.

### **Solution Steps**

#### **Step 1: Fix Pydantic V2 Migration**

**File: `app/models/schemas.py`**
```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class DocumentBase(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)

    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v):
        if not v or not v.strip():
            raise ValueError('Filename cannot be empty')
        if len(v) > 255:
            raise ValueError('Filename too long')
        return v

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        return v
```

#### **Step 2: Fix SQLAlchemy 2.0 Migration**

**File: `app/models/database.py`**
```python
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Text, DateTime, Integer, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

Base = declarative_base()  # ✅ Updated import
```

#### **Step 3: Fix FastAPI Lifespan Events**

**File: `app/main.py`**
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database_init import create_tables
from app.api.routes import documents, scenarios
import structlog

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up ScenarioWizard API")
    await create_tables()
    logger.info("Database tables created/verified on startup")
    yield
    # Shutdown
    logger.info("Shutting down ScenarioWizard API")

app = FastAPI(
    title="ScenarioWizard API",
    description="BDD Scenario Generation API",
    version="1.0.0",
    lifespan=lifespan  # ✅ Use lifespan instead of on_event
)
```

#### **Step 4: Fix Datetime UTC Usage**

**File: `tests/test_models.py`**
```python
from datetime import datetime, timezone

# ✅ FIX: Replace all datetime.utcnow() with datetime.now(timezone.utc)
now = datetime.now(timezone.utc)
```

### **Verification**
```bash
python -m pytest tests/ -v --disable-warnings
```
**Expected**: No deprecation warnings.

---

## 🧪 **Testing Strategy**

### **Test Execution Order**
1. **Unit Tests**: `python -m pytest tests/test_models.py -v`
2. **Parser Tests**: `python -m pytest tests/test_markdown_parser.py -v`
3. **Database Tests**: `python -m pytest tests/test_database_service.py -v`
4. **API Tests**: `python -m pytest tests/test_api_routes.py -v`
5. **Full Suite**: `python -m pytest tests/ -v`

### **Success Criteria**
- ✅ All tests pass (0 failures)
- ✅ No async tests skipped
- ✅ No deprecation warnings
- ✅ All API endpoints return correct status codes
- ✅ Database operations work correctly

---

## 🚀 **Implementation Checklist**

### **Phase 1: Critical Fixes (2 hours)**
- [ ] Fix database session management in API routes
- [ ] Update test configuration for dependency injection
- [ ] Fix API response structure
- [ ] Fix error handling and HTTP status codes

### **Phase 2: Test Suite (1 hour)**
- [ ] Register custom pytest marks
- [ ] Fix async test support
- [ ] Update test assertions
- [ ] Verify all tests pass

### **Phase 3: Code Quality (1 hour)**
- [ ] Fix Pydantic V2 migration
- [ ] Fix SQLAlchemy 2.0 migration
- [ ] Fix FastAPI lifespan events
- [ ] Fix datetime UTC usage

### **Phase 4: Verification (30 minutes)**
- [ ] Run full test suite
- [ ] Test API endpoints manually
- [ ] Verify Streamlit frontend works
- [ ] Check export functionality

---

## 📊 **Expected Results After Fixes**

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **API Tests Passing** | 1/14 | 14/14 | +93% |
| **Async Tests Skipped** | 21 | 0 | -100% |
| **Deprecation Warnings** | 21 | 0 | -100% |
| **Database Operations** | 0% | 100% | +100% |
| **HTTP Status Codes** | 20% | 100% | +80% |

---

## 🔍 **Troubleshooting Guide**

### **Common Issues**

#### **Issue: `'async_generator' object has no attribute 'add'`**
**Solution**: Check that `get_database_service` dependency returns `DatabaseService(actual_session)`, not `DatabaseService(async_generator)`

#### **Issue: `KeyError: 'id'` in tests**
**Solution**: Ensure API responses include all required fields from Pydantic models

#### **Issue: Tests returning 500 instead of 400**
**Solution**: Re-raise `HTTPException` instead of catching and returning generic error

#### **Issue: Async tests skipped**
**Solution**: Add `pytest_asyncio.enable()` and proper async fixtures

---

## 📝 **Notes**

- **Backup**: Create a git commit before starting fixes
- **Incremental**: Fix one issue at a time and test
- **Verification**: Run tests after each fix
- **Documentation**: Update any changed APIs in documentation

---

## 🎯 **Success Metrics**

After completing all fixes:
- ✅ **100% test pass rate**
- ✅ **0 deprecation warnings**
- ✅ **All API endpoints functional**
- ✅ **Streamlit frontend working**
- ✅ **Export functionality working**
- ✅ **Ready for Phase 4 (MCP Integration)**

---

*This reference guide should be followed step-by-step to resolve all Phase 3 critical issues and prepare the system for Phase 4 implementation.*
