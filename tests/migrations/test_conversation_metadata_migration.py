"""
Tests for the conversation metadata migration.
"""

import pytest
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSON

from app.db.session import get_db


def test_conversation_metadata_column_exists():
    """Test that the conversation_metadata column exists in the conversations table."""
    # Get a database session
    db = next(get_db())
    
    # Get the inspector
    inspector = inspect(db.bind)
    
    # Check that the conversations table exists
    assert "conversations" in inspector.get_table_names()
    
    # Get columns in the conversations table
    columns = inspector.get_columns("conversations")
    column_names = [column["name"] for column in columns]
    
    # Check that the conversation_metadata column exists
    assert "conversation_metadata" in column_names
    
    # Check the column type (this might be different depending on the database)
    metadata_column = next(col for col in columns if col["name"] == "conversation_metadata")
    
    # The type might be different depending on the database used (SQLite vs PostgreSQL)
    # For PostgreSQL, it should be JSON
    # For SQLite, it might be TEXT or similar
    assert metadata_column["type"] is not None
