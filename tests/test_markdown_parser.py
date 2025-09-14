"""
Tests for markdown parser service
"""

import pytest
from app.services.parser import MarkdownParser


@pytest.mark.unit
class TestMarkdownParser:
    """Test markdown parser functionality"""

    def test_parse_document_basic(self, sample_markdown_content):
        """Test parsing basic markdown document"""
        parser = MarkdownParser()
        result = parser.parse_document(sample_markdown_content)
        
        assert "user_stories" in result
        assert "acceptance_criteria" in result
        assert "features" in result
        assert "raw_content" in result
        assert result["raw_content"] == sample_markdown_content

    def test_extract_user_stories(self):
        """Test extracting user stories from markdown"""
        parser = MarkdownParser()
        
        content = """# Test Document
## User Stories
- As a user, I want to log in
- As a user, I want to reset password
- As a user, I want to log out

## Other Section
Some other content
"""
        
        stories = parser._extract_user_stories(content)
        
        assert len(stories) == 3
        assert "As a user, I want to log in" in stories
        assert "As a user, I want to reset password" in stories
        assert "As a user, I want to log out" in stories

    def test_extract_user_stories_case_insensitive(self):
        """Test extracting user stories with case insensitive matching"""
        parser = MarkdownParser()
        
        content = """# Test Document
## user stories
- As a user, I want to log in
- As a user, I want to reset password

## Other Section
Some other content
"""
        
        stories = parser._extract_user_stories(content)
        
        assert len(stories) == 2
        assert "As a user, I want to log in" in stories

    def test_extract_user_stories_no_section(self):
        """Test extracting user stories when no user stories section exists"""
        parser = MarkdownParser()
        
        content = """# Test Document
## Other Section
Some content
"""
        
        stories = parser._extract_user_stories(content)
        
        assert len(stories) == 0

    def test_extract_acceptance_criteria(self):
        """Test extracting acceptance criteria from markdown"""
        parser = MarkdownParser()
        
        content = """# Test Document
## User Stories
- As a user, I want to log in

## Acceptance Criteria
- User can enter email and password
- System validates credentials
- User is redirected to dashboard on success

## Other Section
Some other content
"""
        
        criteria = parser._extract_acceptance_criteria(content)
        
        assert len(criteria) == 3
        assert "User can enter email and password" in criteria
        assert "System validates credentials" in criteria
        assert "User is redirected to dashboard on success" in criteria

    def test_extract_acceptance_criteria_case_insensitive(self):
        """Test extracting acceptance criteria with case insensitive matching"""
        parser = MarkdownParser()
        
        content = """# Test Document
## acceptance criteria
- User can enter email and password
- System validates credentials
"""
        
        criteria = parser._extract_acceptance_criteria(content)
        
        assert len(criteria) == 2
        assert "User can enter email and password" in criteria

    def test_extract_acceptance_criteria_no_section(self):
        """Test extracting acceptance criteria when no section exists"""
        parser = MarkdownParser()
        
        content = """# Test Document
## User Stories
- As a user, I want to log in
"""
        
        criteria = parser._extract_acceptance_criteria(content)
        
        assert len(criteria) == 0

    def test_extract_features(self):
        """Test extracting features from markdown"""
        parser = MarkdownParser()
        
        content = """# Test Document
## User Stories
- As a user, I want to log in

## Feature: User Authentication
This feature handles user authentication including login, logout, and password reset.

## Feature: User Profile
This feature handles user profile management.

## Other Section
Some other content
"""
        
        features = parser._extract_features(content)
        
        assert len(features) == 2
        assert features[0]["title"] == "User Authentication"
        assert "handles user authentication" in features[0]["content"]
        assert features[1]["title"] == "User Profile"
        assert "handles user profile management" in features[1]["content"]

    def test_extract_features_case_insensitive(self):
        """Test extracting features with case insensitive matching"""
        parser = MarkdownParser()
        
        content = """# Test Document
## feature: User Authentication
This feature handles user authentication.
"""
        
        features = parser._extract_features(content)
        
        assert len(features) == 1
        assert features[0]["title"] == "User Authentication"

    def test_extract_features_no_features(self):
        """Test extracting features when no features exist"""
        parser = MarkdownParser()
        
        content = """# Test Document
## User Stories
- As a user, I want to log in

## Acceptance Criteria
- User can enter email and password
"""
        
        features = parser._extract_features(content)
        
        assert len(features) == 0

    def test_parse_document_complete(self):
        """Test parsing a complete document with all sections"""
        parser = MarkdownParser()
        
        content = """# User Story: User Login

## User Stories
- As a user, I want to log into the application
- As a user, I want to reset my password

## Acceptance Criteria
- User can enter email and password
- System validates credentials
- User is redirected to dashboard on success

## Feature: User Authentication
This feature handles user authentication including login, logout, and password reset functionality.
"""
        
        result = parser.parse_document(content)
        
        assert len(result["user_stories"]) == 2
        assert len(result["acceptance_criteria"]) == 3
        assert len(result["features"]) == 1
        assert result["features"][0]["title"] == "User Authentication"

    def test_parse_document_empty_content(self):
        """Test parsing empty content"""
        parser = MarkdownParser()
        
        with pytest.raises(ValueError, match="Failed to parse markdown"):
            parser.parse_document("")

    def test_parse_document_invalid_content(self):
        """Test parsing invalid content"""
        parser = MarkdownParser()
        
        # This should not raise an exception, just return empty results
        result = parser.parse_document("Just some random text without proper structure")
        
        assert result["user_stories"] == []
        assert result["acceptance_criteria"] == []
        assert result["features"] == []
        assert result["raw_content"] == "Just some random text without proper structure"

    def test_parse_document_multiline_stories(self):
        """Test parsing user stories with multiline content"""
        parser = MarkdownParser()
        
        content = """# Test Document
## User Stories
- As a user, I want to log into the application
  so that I can access my personal dashboard
- As a user, I want to reset my password
  when I forget it

## Acceptance Criteria
- User can enter email and password
- System validates credentials
"""
        
        result = parser.parse_document(content)
        
        assert len(result["user_stories"]) == 2
        assert "so that I can access my personal dashboard" in result["user_stories"][0]
        assert "when I forget it" in result["user_stories"][1]
