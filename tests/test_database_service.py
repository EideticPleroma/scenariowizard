"""
Tests for database service
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.database import DatabaseService
from app.models.database import Document, Feature, Scenario
from app.models.schemas import DocumentStatus, TestType


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseService:
    """Test database service operations"""

    async def test_create_document(self, test_session: AsyncSession, sample_document_data):
        """Test creating a document"""
        db_service = DatabaseService(test_session)
        
        document = await db_service.create_document(sample_document_data)
        
        assert document.id is not None
        assert document.filename == sample_document_data["filename"]
        assert document.content == sample_document_data["content"]
        assert document.status == sample_document_data["status"]
        assert document.created_at is not None

    async def test_get_document(self, test_session: AsyncSession, sample_document_data):
        """Test getting a document by ID"""
        db_service = DatabaseService(test_session)
        
        # Create document first
        document = await db_service.create_document(sample_document_data)
        document_id = document.id
        
        # Get document
        retrieved_document = await db_service.get_document(document_id)
        
        assert retrieved_document is not None
        assert retrieved_document.id == document_id
        assert retrieved_document.filename == sample_document_data["filename"]

    async def test_get_nonexistent_document(self, test_session: AsyncSession):
        """Test getting a document that doesn't exist"""
        db_service = DatabaseService(test_session)
        
        result = await db_service.get_document("nonexistent-id")
        
        assert result is None

    async def test_list_documents(self, test_session: AsyncSession, sample_document_data):
        """Test listing all documents"""
        db_service = DatabaseService(test_session)
        
        # Create multiple documents
        doc1_data = sample_document_data.copy()
        doc1_data["filename"] = "doc1.md"
        doc2_data = sample_document_data.copy()
        doc2_data["filename"] = "doc2.md"
        
        await db_service.create_document(doc1_data)
        await db_service.create_document(doc2_data)
        
        # List documents
        documents = await db_service.list_documents()
        
        assert len(documents) == 2
        assert any(doc.filename == "doc1.md" for doc in documents)
        assert any(doc.filename == "doc2.md" for doc in documents)

    async def test_update_document_status(self, test_session: AsyncSession, sample_document_data):
        """Test updating document status"""
        db_service = DatabaseService(test_session)
        
        # Create document
        document = await db_service.create_document(sample_document_data)
        document_id = document.id
        
        # Update status
        updated_document = await db_service.update_document_status(
            document_id, "processing", "Test error"
        )
        
        assert updated_document is not None
        assert updated_document.status == "processing"
        assert updated_document.error_message == "Test error"

    async def test_update_nonexistent_document_status(self, test_session: AsyncSession):
        """Test updating status of nonexistent document"""
        db_service = DatabaseService(test_session)
        
        result = await db_service.update_document_status(
            "nonexistent-id", "processing"
        )
        
        assert result is None

    async def test_create_feature(self, test_session: AsyncSession, sample_document_data, sample_feature_data):
        """Test creating a feature"""
        db_service = DatabaseService(test_session)
        
        # Create document first
        document = await db_service.create_document(sample_document_data)
        
        # Create feature
        feature_data = sample_feature_data.copy()
        feature_data["document_id"] = document.id
        
        feature = await db_service.create_feature(feature_data)
        
        assert feature.id is not None
        assert feature.title == sample_feature_data["title"]
        assert feature.document_id == document.id
        assert feature.created_at is not None

    async def test_create_scenario(self, test_session: AsyncSession, sample_document_data, sample_feature_data, sample_scenario_data):
        """Test creating a scenario"""
        db_service = DatabaseService(test_session)
        
        # Create document and feature first
        document = await db_service.create_document(sample_document_data)
        feature_data = sample_feature_data.copy()
        feature_data["document_id"] = document.id
        feature = await db_service.create_feature(feature_data)
        
        # Create scenario
        scenario_data = sample_scenario_data.copy()
        scenario_data["feature_id"] = feature.id
        
        scenario = await db_service.create_scenario(scenario_data)
        
        assert scenario.id is not None
        assert scenario.content == sample_scenario_data["content"]
        assert scenario.feature_id == feature.id
        assert scenario.test_type == sample_scenario_data["test_type"]
        assert scenario.created_at is not None

    async def test_get_features_by_document(self, test_session: AsyncSession, sample_document_data, sample_feature_data):
        """Test getting features by document ID"""
        db_service = DatabaseService(test_session)
        
        # Create document
        document = await db_service.create_document(sample_document_data)
        
        # Create features
        feature1_data = sample_feature_data.copy()
        feature1_data["document_id"] = document.id
        feature1_data["title"] = "Feature 1"
        
        feature2_data = sample_feature_data.copy()
        feature2_data["document_id"] = document.id
        feature2_data["title"] = "Feature 2"
        
        await db_service.create_feature(feature1_data)
        await db_service.create_feature(feature2_data)
        
        # Get features
        features = await db_service.get_features_by_document(document.id)
        
        assert len(features) == 2
        assert any(f.title == "Feature 1" for f in features)
        assert any(f.title == "Feature 2" for f in features)

    async def test_get_scenarios_by_feature(self, test_session: AsyncSession, sample_document_data, sample_feature_data, sample_scenario_data):
        """Test getting scenarios by feature ID"""
        db_service = DatabaseService(test_session)
        
        # Create document and feature
        document = await db_service.create_document(sample_document_data)
        feature_data = sample_feature_data.copy()
        feature_data["document_id"] = document.id
        feature = await db_service.create_feature(feature_data)
        
        # Create scenarios
        scenario1_data = sample_scenario_data.copy()
        scenario1_data["feature_id"] = feature.id
        scenario1_data["content"] = "Scenario 1"
        
        scenario2_data = sample_scenario_data.copy()
        scenario2_data["feature_id"] = feature.id
        scenario2_data["content"] = "Scenario 2"
        
        await db_service.create_scenario(scenario1_data)
        await db_service.create_scenario(scenario2_data)
        
        # Get scenarios
        scenarios = await db_service.get_scenarios_by_feature(feature.id)
        
        assert len(scenarios) == 2
        assert any(s.content == "Scenario 1" for s in scenarios)
        assert any(s.content == "Scenario 2" for s in scenarios)
