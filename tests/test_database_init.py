"""
Tests for database initialization
"""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from app.core.database_init import (
    create_tables, drop_tables, reset_database, 
    check_database, init_database
)
from app.models.database import Base


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseInit:
    """Test database initialization functions"""

    async def test_create_tables(self, test_engine):
        """Test creating database tables"""
        # Tables should already be created by the test_engine fixture
        # This test verifies the function works correctly
        await create_tables()
        
        # Verify tables exist by querying them
        async with test_engine.begin() as conn:
            # Check if documents table exists
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
            )
            assert result.fetchone() is not None
            
            # Check if features table exists
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='features'")
            )
            assert result.fetchone() is not None
            
            # Check if scenarios table exists
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='scenarios'")
            )
            assert result.fetchone() is not None

    async def test_drop_tables(self, test_engine):
        """Test dropping database tables"""
        # First create tables
        await create_tables()
        
        # Verify tables exist
        async with test_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
            )
            assert result.fetchone() is not None
        
        # Drop tables
        await drop_tables()
        
        # Verify tables are gone
        async with test_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
            )
            assert result.fetchone() is None

    async def test_reset_database(self, test_engine):
        """Test resetting database (drop and recreate)"""
        # First create some tables
        await create_tables()
        
        # Verify tables exist
        async with test_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
            )
            assert result.fetchone() is not None
        
        # Reset database
        await reset_database()
        
        # Verify tables exist again
        async with test_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
            )
            assert result.fetchone() is not None

    async def test_check_database_success(self, test_engine):
        """Test successful database check"""
        # Create tables first
        await create_tables()
        
        # Check database
        result = await check_database()
        
        assert result is True

    async def test_check_database_failure(self):
        """Test database check with invalid connection"""
        # Create engine with invalid URL
        invalid_engine = create_async_engine("sqlite+aiosqlite:///nonexistent/path.db")
        
        # This should fail
        result = await check_database()
        
        # The function should handle the error gracefully
        assert result is False
        
        await invalid_engine.dispose()

    async def test_init_database(self, test_engine):
        """Test complete database initialization"""
        # This should work without errors
        await init_database()
        
        # Verify tables exist
        async with test_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
            )
            assert result.fetchone() is not None

    async def test_table_structure(self, test_engine):
        """Test that tables have correct structure"""
        await create_tables()
        
        async with test_engine.begin() as conn:
            # Check documents table structure
            result = await conn.execute(
                text("PRAGMA table_info(documents)")
            )
            columns = result.fetchall()
            column_names = [col[1] for col in columns]
            
            expected_columns = ['id', 'filename', 'content', 'status', 'created_at', 'updated_at']
            for col in expected_columns:
                assert col in column_names
            
            # Check features table structure
            result = await conn.execute(
                text("PRAGMA table_info(features)")
            )
            columns = result.fetchall()
            column_names = [col[1] for col in columns]
            
            expected_columns = ['id', 'document_id', 'title', 'user_stories', 'acceptance_criteria', 'created_at']
            for col in expected_columns:
                assert col in column_names
            
            # Check scenarios table structure
            result = await conn.execute(
                text("PRAGMA table_info(scenarios)")
            )
            columns = result.fetchall()
            column_names = [col[1] for col in columns]
            
            expected_columns = ['id', 'feature_id', 'content', 'test_type', 'created_at']
            for col in expected_columns:
                assert col in column_names

    async def test_foreign_key_constraints(self, test_engine):
        """Test that foreign key constraints are properly set up"""
        await create_tables()
        
        async with test_engine.begin() as conn:
            # Check that foreign keys are enabled
            result = await conn.execute(text("PRAGMA foreign_keys"))
            fk_enabled = result.fetchone()[0]
            assert fk_enabled == 1  # Foreign keys should be enabled

    async def test_multiple_create_tables_calls(self, test_engine):
        """Test that multiple create_tables calls don't cause errors"""
        # First call
        await create_tables()
        
        # Second call should not cause errors
        await create_tables()
        
        # Verify tables still exist
        async with test_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
            )
            assert result.fetchone() is not None
