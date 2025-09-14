"""
Tests for Pydantic models
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.schemas import (
    DocumentBase, DocumentCreate, DocumentResponse,
    FeatureBase, FeatureCreate, FeatureResponse,
    ScenarioBase, ScenarioCreate, ScenarioResponse,
    DocumentStatus, TestType
)


@pytest.mark.unit
class TestDocumentModels:
    """Test document-related Pydantic models"""

    def test_document_base_valid(self):
        """Test valid DocumentBase creation"""
        doc = DocumentBase(
            filename="test.md",
            content="# Test Document\nSome content"
        )
        
        assert doc.filename == "test.md"
        assert doc.content == "# Test Document\nSome content"

    def test_document_base_invalid_filename_empty(self):
        """Test DocumentBase with empty filename"""
        with pytest.raises(ValidationError):
            DocumentBase(
                filename="",
                content="# Test Document"
            )

    def test_document_base_invalid_filename_too_long(self):
        """Test DocumentBase with filename too long"""
        with pytest.raises(ValidationError):
            DocumentBase(
                filename="x" * 256,  # Too long
                content="# Test Document"
            )

    def test_document_base_invalid_content_empty(self):
        """Test DocumentBase with empty content"""
        with pytest.raises(ValidationError):
            DocumentBase(
                filename="test.md",
                content=""
            )

    def test_document_create_inherits_base(self):
        """Test DocumentCreate inherits from DocumentBase"""
        doc = DocumentCreate(
            filename="test.md",
            content="# Test Document"
        )
        
        assert doc.filename == "test.md"
        assert doc.content == "# Test Document"

    def test_document_response_with_all_fields(self):
        """Test DocumentResponse with all fields"""
        now = datetime.utcnow()
        doc = DocumentResponse(
            id="test-id",
            filename="test.md",
            content="# Test Document",
            status=DocumentStatus.PENDING,
            created_at=now,
            processed_at=now,
            error_message="Test error"
        )
        
        assert doc.id == "test-id"
        assert doc.filename == "test.md"
        assert doc.content == "# Test Document"
        assert doc.status == DocumentStatus.PENDING
        assert doc.created_at == now
        assert doc.processed_at == now
        assert doc.error_message == "Test error"

    def test_document_response_with_optional_fields(self):
        """Test DocumentResponse with optional fields as None"""
        now = datetime.utcnow()
        doc = DocumentResponse(
            id="test-id",
            filename="test.md",
            content="# Test Document",
            status=DocumentStatus.PENDING,
            created_at=now
        )
        
        assert doc.id == "test-id"
        assert doc.processed_at is None
        assert doc.error_message is None


@pytest.mark.unit
class TestFeatureModels:
    """Test feature-related Pydantic models"""

    def test_feature_base_valid(self):
        """Test valid FeatureBase creation"""
        feature = FeatureBase(
            title="User Authentication",
            user_stories="As a user, I want to log in",
            acceptance_criteria="User can enter credentials"
        )
        
        assert feature.title == "User Authentication"
        assert feature.user_stories == "As a user, I want to log in"
        assert feature.acceptance_criteria == "User can enter credentials"

    def test_feature_base_invalid_title_empty(self):
        """Test FeatureBase with empty title"""
        with pytest.raises(ValidationError):
            FeatureBase(
                title="",
                user_stories="As a user, I want to log in",
                acceptance_criteria="User can enter credentials"
            )

    def test_feature_base_invalid_title_too_long(self):
        """Test FeatureBase with title too long"""
        with pytest.raises(ValidationError):
            FeatureBase(
                title="x" * 256,  # Too long
                user_stories="As a user, I want to log in",
                acceptance_criteria="User can enter credentials"
            )

    def test_feature_create_with_document_id(self):
        """Test FeatureCreate with document_id"""
        feature = FeatureCreate(
            title="User Authentication",
            user_stories="As a user, I want to log in",
            acceptance_criteria="User can enter credentials",
            document_id="doc-123"
        )
        
        assert feature.document_id == "doc-123"

    def test_feature_response_with_all_fields(self):
        """Test FeatureResponse with all fields"""
        now = datetime.utcnow()
        feature = FeatureResponse(
            id="feature-123",
            title="User Authentication",
            user_stories="As a user, I want to log in",
            acceptance_criteria="User can enter credentials",
            document_id="doc-123",
            created_at=now
        )
        
        assert feature.id == "feature-123"
        assert feature.document_id == "doc-123"
        assert feature.created_at == now


@pytest.mark.unit
class TestScenarioModels:
    """Test scenario-related Pydantic models"""

    def test_scenario_base_valid(self):
        """Test valid ScenarioBase creation"""
        scenario = ScenarioBase(
            content="Feature: User Login\nScenario: Valid login",
            test_type=TestType.UNIT
        )
        
        assert scenario.content == "Feature: User Login\nScenario: Valid login"
        assert scenario.test_type == TestType.UNIT

    def test_scenario_base_default_test_type(self):
        """Test ScenarioBase with default test type"""
        scenario = ScenarioBase(
            content="Feature: User Login\nScenario: Valid login"
        )
        
        assert scenario.test_type == TestType.UNIT

    def test_scenario_base_invalid_content_empty(self):
        """Test ScenarioBase with empty content"""
        with pytest.raises(ValidationError):
            ScenarioBase(
                content="",
                test_type=TestType.UNIT
            )

    def test_scenario_create_with_feature_id(self):
        """Test ScenarioCreate with feature_id"""
        scenario = ScenarioCreate(
            content="Feature: User Login\nScenario: Valid login",
            test_type=TestType.INTEGRATION,
            feature_id="feature-123"
        )
        
        assert scenario.feature_id == "feature-123"
        assert scenario.test_type == TestType.INTEGRATION

    def test_scenario_response_with_all_fields(self):
        """Test ScenarioResponse with all fields"""
        now = datetime.utcnow()
        scenario = ScenarioResponse(
            id="scenario-123",
            content="Feature: User Login\nScenario: Valid login",
            test_type=TestType.E2E,
            feature_id="feature-123",
            created_at=now
        )
        
        assert scenario.id == "scenario-123"
        assert scenario.feature_id == "feature-123"
        assert scenario.test_type == TestType.E2E
        assert scenario.created_at == now


@pytest.mark.unit
class TestEnums:
    """Test enum types"""

    def test_document_status_enum(self):
        """Test DocumentStatus enum values"""
        assert DocumentStatus.PENDING == "pending"
        assert DocumentStatus.PROCESSING == "processing"
        assert DocumentStatus.COMPLETED == "completed"
        assert DocumentStatus.FAILED == "failed"

    def test_test_type_enum(self):
        """Test TestType enum values"""
        assert TestType.UNIT == "unit"
        assert TestType.INTEGRATION == "integration"
        assert TestType.E2E == "e2e"

    def test_enum_serialization(self):
        """Test enum serialization in models"""
        doc = DocumentResponse(
            id="test-id",
            filename="test.md",
            content="# Test Document",
            status=DocumentStatus.COMPLETED,
            created_at=datetime.utcnow()
        )
        
        # Should serialize to string value
        assert doc.status == "completed"
        
        scenario = ScenarioResponse(
            id="scenario-123",
            content="Feature: Test",
            test_type=TestType.INTEGRATION,
            feature_id="feature-123",
            created_at=datetime.utcnow()
        )
        
        assert scenario.test_type == "integration"


@pytest.mark.unit
class TestModelValidation:
    """Test model validation edge cases"""

    def test_document_response_from_orm(self):
        """Test DocumentResponse creation from ORM object"""
        # This would typically be used with SQLAlchemy objects
        # For testing, we'll create a mock object with the right attributes
        class MockDocument:
            def __init__(self):
                self.id = "test-id"
                self.filename = "test.md"
                self.content = "# Test Document"
                self.status = "pending"
                self.created_at = datetime.utcnow()
                self.processed_at = None
                self.error_message = None
        
        mock_doc = MockDocument()
        doc_response = DocumentResponse.from_orm(mock_doc)
        
        assert doc_response.id == "test-id"
        assert doc_response.filename == "test.md"
        assert doc_response.status == "pending"

    def test_feature_response_from_orm(self):
        """Test FeatureResponse creation from ORM object"""
        class MockFeature:
            def __init__(self):
                self.id = "feature-123"
                self.title = "User Authentication"
                self.user_stories = "As a user, I want to log in"
                self.acceptance_criteria = "User can enter credentials"
                self.document_id = "doc-123"
                self.created_at = datetime.utcnow()
        
        mock_feature = MockFeature()
        feature_response = FeatureResponse.from_orm(mock_feature)
        
        assert feature_response.id == "feature-123"
        assert feature_response.title == "User Authentication"
        assert feature_response.document_id == "doc-123"
