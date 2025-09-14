"""
Tests for API routes
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
import io


@pytest.mark.integration
class TestDocumentRoutes:
    """Test document API routes"""

    def test_health_check(self, test_client: TestClient):
        """Test health check endpoint"""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"

    def test_root_endpoint(self, test_client: TestClient):
        """Test root endpoint"""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data

    def test_upload_document_success(self, test_client: TestClient, sample_markdown_content):
        """Test successful document upload"""
        files = {
            "file": ("test.md", io.BytesIO(sample_markdown_content.encode()), "text/markdown")
        }
        
        response = test_client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["filename"] == "test.md"
        assert data["status"] == "pending"
        assert data["content"] == sample_markdown_content

    def test_upload_document_invalid_file_type(self, test_client: TestClient):
        """Test uploading invalid file type"""
        files = {
            "file": ("test.txt", io.BytesIO(b"test content"), "text/plain")
        }
        
        response = test_client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "Only .md files are supported" in data["detail"]

    def test_upload_document_no_filename(self, test_client: TestClient):
        """Test uploading file without filename"""
        files = {
            "file": (None, io.BytesIO(b"test content"), "text/markdown")
        }
        
        response = test_client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_upload_document_empty_file(self, test_client: TestClient):
        """Test uploading empty file"""
        files = {
            "file": ("test.md", io.BytesIO(b""), "text/markdown")
        }
        
        response = test_client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "File is empty" in data["detail"]

    def test_upload_document_too_large(self, test_client: TestClient):
        """Test uploading file that's too large"""
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        files = {
            "file": ("test.md", io.BytesIO(large_content), "text/markdown")
        }
        
        response = test_client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == 413
        data = response.json()
        assert "File too large" in data["detail"]

    def test_upload_document_empty_content(self, test_client: TestClient):
        """Test uploading file with only whitespace"""
        files = {
            "file": ("test.md", io.BytesIO(b"   \n\t   "), "text/markdown")
        }
        
        response = test_client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "File contains no readable content" in data["detail"]

    def test_get_document_success(self, test_client: TestClient, sample_markdown_content):
        """Test getting document by ID"""
        # First upload a document
        files = {
            "file": ("test.md", io.BytesIO(sample_markdown_content.encode()), "text/markdown")
        }
        upload_response = test_client.post("/api/v1/documents/upload", files=files)
        document_id = upload_response.json()["id"]
        
        # Get the document
        response = test_client.get(f"/api/v1/documents/{document_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == document_id
        assert data["filename"] == "test.md"

    def test_get_document_not_found(self, test_client: TestClient):
        """Test getting document that doesn't exist"""
        response = test_client.get("/api/v1/documents/nonexistent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert "Document not found" in data["detail"]

    def test_list_documents(self, test_client: TestClient, sample_markdown_content):
        """Test listing all documents"""
        # Upload multiple documents
        files1 = {
            "file": ("test1.md", io.BytesIO(sample_markdown_content.encode()), "text/markdown")
        }
        files2 = {
            "file": ("test2.md", io.BytesIO(sample_markdown_content.encode()), "text/markdown")
        }
        
        test_client.post("/api/v1/documents/upload", files=files1)
        test_client.post("/api/v1/documents/upload", files=files2)
        
        # List documents
        response = test_client.get("/api/v1/documents/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(doc["filename"] == "test1.md" for doc in data)
        assert any(doc["filename"] == "test2.md" for doc in data)

    def test_process_document_success(self, test_client: TestClient, sample_markdown_content):
        """Test processing a document"""
        # First upload a document
        files = {
            "file": ("test.md", io.BytesIO(sample_markdown_content.encode()), "text/markdown")
        }
        upload_response = test_client.post("/api/v1/documents/upload", files=files)
        document_id = upload_response.json()["id"]
        
        # Process the document
        response = test_client.post(f"/api/v1/documents/{document_id}/process")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "features_created" in data

    def test_process_document_not_found(self, test_client: TestClient):
        """Test processing document that doesn't exist"""
        response = test_client.post("/api/v1/documents/nonexistent-id/process")
        
        assert response.status_code == 404
        data = response.json()
        assert "Document not found" in data["detail"]

    def test_get_document_features(self, test_client: TestClient, sample_markdown_content):
        """Test getting features for a document"""
        # First upload and process a document
        files = {
            "file": ("test.md", io.BytesIO(sample_markdown_content.encode()), "text/markdown")
        }
        upload_response = test_client.post("/api/v1/documents/upload", files=files)
        document_id = upload_response.json()["id"]
        
        test_client.post(f"/api/v1/documents/{document_id}/process")
        
        # Get features
        response = test_client.get(f"/api/v1/documents/{document_id}/features")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_document_features_not_found(self, test_client: TestClient):
        """Test getting features for document that doesn't exist"""
        response = test_client.get("/api/v1/documents/nonexistent-id/features")
        
        assert response.status_code == 404
        data = response.json()
        assert "Document not found" in data["detail"]


@pytest.mark.integration
class TestAsyncDocumentRoutes:
    """Test document API routes with async client"""

    async def test_upload_document_async(self, async_test_client: AsyncClient, sample_markdown_content):
        """Test async document upload"""
        files = {
            "file": ("test.md", io.BytesIO(sample_markdown_content.encode()), "text/markdown")
        }
        
        response = await async_test_client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["filename"] == "test.md"

    async def test_get_document_async(self, async_test_client: AsyncClient, sample_markdown_content):
        """Test async document retrieval"""
        # First upload a document
        files = {
            "file": ("test.md", io.BytesIO(sample_markdown_content.encode()), "text/markdown")
        }
        upload_response = await async_test_client.post("/api/v1/documents/upload", files=files)
        document_id = upload_response.json()["id"]
        
        # Get the document
        response = await async_test_client.get(f"/api/v1/documents/{document_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == document_id
