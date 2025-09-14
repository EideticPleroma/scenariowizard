# Phase 1: Core Backend Implementation

## Overview
**Duration**: Week 1  
**Goal**: Set up FastAPI backend with basic document processing and database storage

## Deliverables
- [ ] FastAPI application with basic endpoints
- [ ] Markdown parsing with markdown-it-py
- [ ] SQLite database for results storage
- [ ] Basic error handling and logging
- [ ] Docker containerization

## Implementation Details

### 1. Project Structure
```
qa-scenario-writer/
├── src/
│   ├── main.py                 # FastAPI application
│   ├── models/
│   │   ├── document.py         # Document data models
│   │   ├── feature.py          # Feature data models
│   │   └── scenario.py         # Scenario data models
│   ├── services/
│   │   ├── parser.py           # Markdown parsing
│   │   ├── database.py         # Database operations
│   │   └── validation.py       # Input validation
│   ├── api/
│   │   ├── documents.py        # Document endpoints
│   │   └── scenarios.py        # Scenario endpoints
│   └── utils/
│       ├── logging.py          # Logging configuration
│       └── exceptions.py       # Custom exceptions
├── tests/
│   ├── test_parser.py
│   ├── test_database.py
│   └── test_api.py
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

### 2. FastAPI Application Setup

#### main.py
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging

from src.api.documents import router as documents_router
from src.api.scenarios import router as scenarios_router
from src.utils.logging import setup_logging
from src.utils.exceptions import QAException

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="QA Scenario Writer API",
    description="Generate BDD scenarios from Markdown documents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents_router, prefix="/api/v1")
app.include_router(scenarios_router, prefix="/api/v1")

# Global exception handler
@app.exception_handler(QAException)
async def qa_exception_handler(request, exc):
    logger.error(f"QA Exception: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_type, "message": exc.message}
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3. Data Models

#### document.py
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Document(BaseModel):
    id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    content: str = Field(..., description="Document content")
    status: DocumentStatus = Field(default=DocumentStatus.UPLOADED)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class DocumentCreate(BaseModel):
    filename: str
    content: str

class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: DocumentStatus
    created_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
```

#### feature.py
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class UserStory(BaseModel):
    as_a: str = Field(..., description="User role")
    i_want: str = Field(..., description="Desired functionality")
    so_that: str = Field(..., description="Business value")
    acceptance_criteria: List[str] = Field(default_factory=list)

class Feature(BaseModel):
    id: str = Field(..., description="Unique feature identifier")
    document_id: str = Field(..., description="Parent document ID")
    title: str = Field(..., description="Feature title")
    description: str = Field(..., description="Feature description")
    user_stories: List[UserStory] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    priority: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FeatureCreate(BaseModel):
    document_id: str
    title: str
    description: str
    user_stories: List[UserStory]
    tags: List[str] = Field(default_factory=list)
    priority: Optional[str] = None
```

### 4. Database Service

#### database.py
```python
import sqlite3
import json
from typing import List, Optional
from datetime import datetime
import logging

from src.models.document import Document, DocumentCreate, DocumentStatus
from src.models.feature import Feature, FeatureCreate

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, db_path: str = "qa_scenarios.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    content TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'uploaded',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    error_message TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS features (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    user_stories TEXT,
                    tags TEXT,
                    priority TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scenarios (
                    id TEXT PRIMARY KEY,
                    feature_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    test_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (feature_id) REFERENCES features (id)
                )
            """)
    
    def create_document(self, document: DocumentCreate) -> Document:
        """Create a new document"""
        doc_id = f"doc_{datetime.utcnow().timestamp()}"
        doc = Document(
            id=doc_id,
            filename=document.filename,
            content=document.content,
            status=DocumentStatus.UPLOADED
        )
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO documents (id, filename, content, status, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (doc.id, doc.filename, doc.content, doc.status, doc.created_at))
        
        logger.info(f"Created document: {doc.id}")
        return doc
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get document by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            
            if row:
                return Document(
                    id=row["id"],
                    filename=row["filename"],
                    content=row["content"],
                    status=DocumentStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    processed_at=datetime.fromisoformat(row["processed_at"]) if row["processed_at"] else None,
                    error_message=row["error_message"]
                )
        return None
    
    def update_document_status(self, doc_id: str, status: DocumentStatus, error_message: str = None):
        """Update document status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE documents 
                SET status = ?, processed_at = ?, error_message = ?
                WHERE id = ?
            """, (status, datetime.utcnow(), error_message, doc_id))
        
        logger.info(f"Updated document {doc_id} status to {status}")
    
    def create_feature(self, feature: FeatureCreate) -> Feature:
        """Create a new feature"""
        feature_id = f"feat_{datetime.utcnow().timestamp()}"
        feat = Feature(
            id=feature_id,
            document_id=feature.document_id,
            title=feature.title,
            description=feature.description,
            user_stories=feature.user_stories,
            tags=feature.tags,
            priority=feature.priority
        )
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO features (id, document_id, title, description, user_stories, tags, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feat.id, feat.document_id, feat.title, feat.description,
                json.dumps([story.dict() for story in feat.user_stories]),
                json.dumps(feat.tags), feat.priority, feat.created_at
            ))
        
        logger.info(f"Created feature: {feat.id}")
        return feat
```

### 5. Markdown Parser Service

#### parser.py
```python
import re
from typing import List, Dict, Any
from markdown_it import MarkdownIt
import logging

from src.models.feature import Feature, UserStory
from src.services.validation import MarkdownValidator

logger = logging.getLogger(__name__)

class MarkdownParser:
    def __init__(self):
        self.md = MarkdownIt()
        self.validator = MarkdownValidator()
    
    def parse_document(self, content: str) -> List[Feature]:
        """Parse Markdown document and extract features"""
        logger.info("Parsing Markdown document")
        
        # Validate document structure
        validation_result = self.validator.validate_document(content)
        if not validation_result["valid"]:
            raise ValueError(f"Document validation failed: {validation_result['errors']}")
        
        # Extract features
        features = []
        sections = self._extract_sections(content)
        
        for section_title, section_content in sections.items():
            if self._is_feature_section(section_title):
                feature = self._parse_feature(section_title, section_content)
                if feature:
                    features.append(feature)
        
        logger.info(f"Extracted {len(features)} features from document")
        return features
    
    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract sections from Markdown content"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('## '):
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                current_section = line[3:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _is_feature_section(self, title: str) -> bool:
        """Check if section is a feature"""
        feature_keywords = ['feature', 'story', 'requirement', 'specification']
        return any(keyword in title.lower() for keyword in feature_keywords)
    
    def _parse_feature(self, title: str, content: str) -> Optional[Feature]:
        """Parse a single feature section"""
        try:
            # Extract user stories
            user_stories = self._extract_user_stories(content)
            
            # Extract acceptance criteria
            acceptance_criteria = self._extract_acceptance_criteria(content)
            
            # Add acceptance criteria to user stories
            for story in user_stories:
                story.acceptance_criteria = acceptance_criteria
            
            return Feature(
                id=f"feat_{hash(title)}",
                document_id="",  # Will be set by caller
                title=title,
                description=self._extract_description(content),
                user_stories=user_stories,
                tags=self._extract_tags(content)
            )
        except Exception as e:
            logger.error(f"Failed to parse feature '{title}': {e}")
            return None
    
    def _extract_user_stories(self, content: str) -> List[UserStory]:
        """Extract user stories from content"""
        stories = []
        pattern = r"As a (.+?), I want (.+?) so that (.+?)(?=\n|$)"
        
        for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
            stories.append(UserStory(
                as_a=match.group(1).strip(),
                i_want=match.group(2).strip(),
                so_that=match.group(3).strip()
            ))
        
        return stories
    
    def _extract_acceptance_criteria(self, content: str) -> List[str]:
        """Extract acceptance criteria from content"""
        criteria = []
        in_criteria_section = False
        
        for line in content.split('\n'):
            if "acceptance criteria" in line.lower():
                in_criteria_section = True
                continue
            elif in_criteria_section and line.strip().startswith('-'):
                criteria.append(line.strip()[1:].strip())
            elif in_criteria_section and line.strip() == '':
                continue
            elif in_criteria_section and not line.strip().startswith('-'):
                break
        
        return criteria
    
    def _extract_description(self, content: str) -> str:
        """Extract feature description from content"""
        lines = content.split('\n')
        description_lines = []
        
        for line in lines:
            if line.strip() and not line.startswith('As a') and not line.startswith('-'):
                description_lines.append(line.strip())
            elif line.startswith('As a'):
                break
        
        return ' '.join(description_lines)
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract tags from content"""
        tags = []
        for line in content.split('\n'):
            if line.strip().startswith('Tags:') or line.strip().startswith('tags:'):
                tag_line = line.split(':', 1)[1].strip()
                tags = [tag.strip() for tag in tag_line.split(',')]
                break
        return tags
```

### 6. API Endpoints

#### documents.py
```python
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
import uuid
import logging

from src.models.document import Document, DocumentCreate, DocumentResponse
from src.services.database import DatabaseService
from src.services.parser import MarkdownParser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

db = DatabaseService()
parser = MarkdownParser()

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a Markdown document for processing"""
    try:
        # Validate file type
        if not file.filename.endswith('.md'):
            raise HTTPException(status_code=400, detail="Only Markdown files are supported")
        
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Create document
        document_create = DocumentCreate(
            filename=file.filename,
            content=content_str
        )
        
        document = db.create_document(document_create)
        
        logger.info(f"Uploaded document: {document.id}")
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            status=document.status,
            created_at=document.created_at,
            processed_at=document.processed_at,
            error_message=document.error_message
        )
        
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """Get document by ID"""
    document = db.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        status=document.status,
        created_at=document.created_at,
        processed_at=document.processed_at,
        error_message=document.error_message
    )

@router.get("/", response_model=List[DocumentResponse])
async def list_documents():
    """List all documents"""
    # Implementation for listing documents
    pass
```

### 7. Docker Configuration

#### Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "main.py"]
```

#### docker-compose.yml
```yaml
version: '3.8'
services:
  qa-scenario-writer:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/qa_scenarios.db
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

### 8. Testing

#### test_parser.py
```python
import pytest
from src.services.parser import MarkdownParser

def test_parse_simple_document():
    parser = MarkdownParser()
    content = """
# User Authentication Feature

## User Story
As a user, I want to log in to the application so that I can access my personal dashboard.

## Acceptance Criteria
- User can enter email and password
- System validates credentials
- User is redirected to dashboard on success
"""
    
    features = parser.parse_document(content)
    assert len(features) == 1
    assert features[0].title == "User Authentication Feature"
    assert len(features[0].user_stories) == 1
    assert features[0].user_stories[0].as_a == "user"
```

## Success Criteria
- [ ] FastAPI application starts successfully
- [ ] Markdown documents can be uploaded and parsed
- [ ] Features are extracted correctly from documents
- [ ] SQLite database stores data properly
- [ ] Basic error handling works
- [ ] Docker container runs without issues
- [ ] All tests pass

## Next Phase
Phase 2 will add LLM integration for scenario generation using the Grok API.
