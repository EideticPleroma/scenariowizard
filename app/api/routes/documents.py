from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import structlog

from app.models.schemas import DocumentCreate, DocumentResponse, FeatureResponse, ScenarioResponse
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
        # Validate filename
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # Validate file type
        if not file.filename.endswith('.md'):
            raise HTTPException(status_code=400, detail="Only .md files are supported")

        # Read file content
        content = await file.read()
        
        # Validate file size (10MB limit)
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")
        
        # Validate content is not empty
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        content_str = content.decode('utf-8')
        
        # Validate content is valid UTF-8
        if not content_str.strip():
            raise HTTPException(status_code=400, detail="File contains no readable content")

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
    documents = await db_service.list_documents()
    return [DocumentResponse.from_orm(doc) for doc in documents]

@router.post("/{document_id}/process")
async def process_document(
    document_id: str,
    session: AsyncSession = Depends(get_database_session)
):
    """Process a document to extract features and generate scenarios"""
    try:
        db_service = DatabaseService(session)
        document = await db_service.get_document(document_id)

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Update status to processing
        await db_service.update_document_status(document_id, "processing")

        # Parse the document
        parser = MarkdownParser()
        parsed_data = parser.parse_document(document.content)

        # Create features from parsed data
        for feature_data in parsed_data.get("features", []):
            feature_data["document_id"] = document_id
            await db_service.create_feature(feature_data)

        # Update document status to completed
        await db_service.update_document_status(document_id, "completed")

        logger.info("Document processed", document_id=document_id, features_created=len(parsed_data.get("features", [])))

        return {"status": "success", "features_created": len(parsed_data.get("features", []))}

    except Exception as e:
        # Update document status to failed
        await db_service.update_document_status(document_id, "failed", str(e))
        logger.error("Document processing failed", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@router.get("/{document_id}/features", response_model=List[FeatureResponse])
async def get_document_features(
    document_id: str,
    session: AsyncSession = Depends(get_database_session)
):
    """Get features for a document"""
    db_service = DatabaseService(session)
    features = await db_service.get_features_by_document(document_id)
    return [FeatureResponse.from_orm(feature) for feature in features]
