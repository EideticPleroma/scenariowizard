# Cline Kickoff Prompt - ScenarioWizard BDD Tool

## Project Context
You are working on **ScenarioWizard**, a BDD scenario generation tool that transforms user stories and acceptance criteria into executable Gherkin scenarios using AI. This is an MVP project with comprehensive documentation but minimal implementation.

## Current Status
- **Documentation**: EXCELLENT - Complete architecture, API reference, and implementation plan
- **Implementation**: MINIMAL - Only basic Streamlit placeholder UI exists
- **Branch**: `feature/implementation-phase-1` (ready for development)
- **Timeline**: 4-6 week MVP implementation

## Your Mission
Implement the core backend functionality following the established patterns and documentation. Focus on building the simplest thing that works first, then iterate.

## Implementation Priority (Week 1 Focus)

### 1. FastAPI Backend Setup
```python
# Create app/api/main.py
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import structlog

app = FastAPI(
    title="ScenarioWizard API",
    description="BDD Scenario Generation Tool",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
```

### 2. Database Models (SQLAlchemy)
```python
# Create app/models/database.py
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    content = Column(Text)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    features = relationship("Feature", back_populates="document", cascade="all, delete-orphan")

class Feature(Base):
    __tablename__ = "features"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"))
    title = Column(String(255), nullable=False)
    user_stories = Column(Text)
    acceptance_criteria = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="features")
    scenarios = relationship("Scenario", back_populates="feature", cascade="all, delete-orphan")

class Scenario(Base):
    __tablename__ = "scenarios"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    feature_id = Column(String, ForeignKey("features.id"))
    content = Column(Text, nullable=False)
    test_type = Column(String(50), default="unit")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    feature = relationship("Feature", back_populates="scenarios")
```

### 3. Pydantic Models
```python
# Create app/models/schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TestType(str, Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"

class DocumentBase(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: str
    status: DocumentStatus
    created_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

class FeatureBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    user_stories: str
    acceptance_criteria: str

class FeatureCreate(FeatureBase):
    document_id: str

class FeatureResponse(FeatureBase):
    id: str
    document_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ScenarioBase(BaseModel):
    content: str = Field(..., min_length=1)
    test_type: TestType = TestType.UNIT

class ScenarioCreate(ScenarioBase):
    feature_id: str

class ScenarioResponse(ScenarioBase):
    id: str
    feature_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### 4. Database Service
```python
# Create app/services/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete
from typing import List, Optional
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./scenario_wizard.db")

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_database_session():
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

class DatabaseService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_document(self, document_data: dict) -> Document:
        document = Document(**document_data)
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()
    
    async def create_feature(self, feature_data: dict) -> Feature:
        feature = Feature(**feature_data)
        self.session.add(feature)
        await self.session.commit()
        await self.session.refresh(feature)
        return feature
    
    async def create_scenario(self, scenario_data: dict) -> Scenario:
        scenario = Scenario(**scenario_data)
        self.session.add(scenario)
        await self.session.commit()
        await self.session.refresh(scenario)
        return scenario
```

### 5. Markdown Parser Service
```python
# Create app/services/parser.py
import markdown
from markdown.extensions import codehilite, fenced_code
from typing import List, Dict, Any
import re

class MarkdownParser:
    def __init__(self):
        self.md = markdown.Markdown(
            extensions=['codehilite', 'fenced_code', 'tables']
        )
    
    def parse_document(self, content: str) -> Dict[str, Any]:
        """Parse markdown content and extract structure"""
        try:
            # Extract user stories
            user_stories = self._extract_user_stories(content)
            
            # Extract acceptance criteria
            acceptance_criteria = self._extract_acceptance_criteria(content)
            
            # Extract features
            features = self._extract_features(content)
            
            return {
                "user_stories": user_stories,
                "acceptance_criteria": acceptance_criteria,
                "features": features,
                "raw_content": content
            }
        except Exception as e:
            raise ValueError(f"Failed to parse markdown: {e}")
    
    def _extract_user_stories(self, content: str) -> List[str]:
        """Extract user stories from markdown content"""
        pattern = r'##\s*User Stories?\s*\n(.*?)(?=\n##|\Z)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if not match:
            return []
        
        stories_text = match.group(1)
        stories = []
        
        # Extract individual stories
        story_pattern = r'-\s*(.+?)(?=\n-|\Z)'
        for match in re.finditer(story_pattern, stories_text, re.DOTALL):
            stories.append(match.group(1).strip())
        
        return stories
    
    def _extract_acceptance_criteria(self, content: str) -> List[str]:
        """Extract acceptance criteria from markdown content"""
        pattern = r'##\s*Acceptance Criteria\s*\n(.*?)(?=\n##|\Z)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if not match:
            return []
        
        criteria_text = match.group(1)
        criteria = []
        
        # Extract individual criteria
        criteria_pattern = r'-\s*(.+?)(?=\n-|\Z)'
        for match in re.finditer(criteria_pattern, criteria_text, re.DOTALL):
            criteria.append(match.group(1).strip())
        
        return criteria
    
    def _extract_features(self, content: str) -> List[Dict[str, str]]:
        """Extract features from markdown content"""
        features = []
        
        # Look for feature sections
        feature_pattern = r'##\s*Feature:\s*(.+?)\n(.*?)(?=\n##|\Z)'
        for match in re.finditer(feature_pattern, content, re.DOTALL | re.IGNORECASE):
            feature_title = match.group(1).strip()
            feature_content = match.group(2).strip()
            
            features.append({
                "title": feature_title,
                "content": feature_content
            })
        
        return features
```

### 6. API Routes
```python
# Create app/api/routes/documents.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import structlog

from app.models.schemas import DocumentCreate, DocumentResponse
from app.services.database import get_database_session, DatabaseService
from app.services.parser import MarkdownParser

router = APIRouter(prefix="/documents", tags=["documents"])
logger = structlog.get_logger()

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_database_session)
):
    """Upload a markdown document for processing"""
    try:
        # Validate file type
        if not file.filename.endswith('.md'):
            raise HTTPException(status_code=400, detail="Only .md files are supported")
        
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Create document
        db_service = DatabaseService(session)
        document_data = {
            "filename": file.filename,
            "content": content_str,
            "status": "pending"
        }
        
        document = await db_service.create_document(document_data)
        
        logger.info("Document uploaded", document_id=document.id, filename=file.filename)
        
        return DocumentResponse.from_orm(document)
        
    except Exception as e:
        logger.error("Document upload failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to upload document")

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    session: AsyncSession = Depends(get_database_session)
):
    """Get document by ID"""
    db_service = DatabaseService(session)
    document = await db_service.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse.from_orm(document)

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    session: AsyncSession = Depends(get_database_session)
):
    """List all documents"""
    db_service = DatabaseService(session)
    # Implementation for listing documents
    pass
```

### 7. Main FastAPI App
```python
# Update app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import documents

app = FastAPI(
    title="ScenarioWizard API",
    description="BDD Scenario Generation Tool",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Key Implementation Guidelines

### 1. Follow the Patterns
- Use the templates provided in `.cline_rules`
- Follow async/await patterns for all I/O operations
- Use proper error handling with structured logging
- Implement proper validation with Pydantic

### 2. Database Setup
- Use SQLite with async SQLAlchemy
- Create proper migrations with Alembic
- Use transactions for multi-table operations
- Implement proper relationships

### 3. Error Handling
- Use specific exception types
- Log errors with structured logging
- Return meaningful error messages
- Use appropriate HTTP status codes

### 4. Testing
- Write unit tests for core logic
- Test database operations
- Mock external services
- Use pytest with async support

## Next Steps After Week 1
1. **Week 2**: LLM Integration (Grok API)
2. **Week 3**: Frontend & Export functionality
3. **Week 4**: MCP Integration

## Resources
- **Documentation**: Check `docs/` directory for complete API reference
- **Architecture**: See `docs/developer-guide/architecture.md`
- **Implementation Plan**: See `planning/implementation/Phase_1_Core_Backend.md`

## Success Criteria
- [ ] FastAPI server running on port 8000
- [ ] Database models created and migrated
- [ ] Document upload endpoint working
- [ ] Markdown parsing functional
- [ ] Basic error handling implemented
- [ ] Unit tests passing

Start with the FastAPI setup and work through the database models. Focus on getting the core document upload and parsing working first. Use the patterns and templates provided in the rules files.

Remember: This is an MVP - build the simplest thing that works, then iterate!

