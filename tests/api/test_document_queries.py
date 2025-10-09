"""
Tests for the document-based query API endpoints.
"""

import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.user import User
from app.models.chat import Conversation
from app.services.chat import create_conversation
from tests.utils.auth import get_test_token


@pytest.fixture
def test_document_id():
    """Generate a test document ID."""
    return f"doc-{uuid.uuid4()}"


@pytest.fixture
def mock_document_chunks(test_document_id):
    """Create mock document chunks for testing."""
    chunks_dir = Path("./document_chunks")
    chunks_dir.mkdir(exist_ok=True)
    
    chunks_file = chunks_dir / f"{test_document_id}_chunks.json"
    
    # Create mock chunks
    chunks = [
        {
            "id": f"{test_document_id}_chunk_0",
            "metadata": {
                "document_id": test_document_id,
                "chunk_index": 0,
                "file_type": "text/plain"
            },
            "text": "This is the first chunk of test content.",
            "embedding_size": 1536
        },
        {
            "id": f"{test_document_id}_chunk_1",
            "metadata": {
                "document_id": test_document_id,
                "chunk_index": 1,
                "file_type": "text/plain"
            },
            "text": "This is the second chunk of test content.",
            "embedding_size": 1536
        }
    ]
    
    # Write chunks to file
    with open(chunks_file, "w") as f:
        json.dump(chunks, f)
    
    yield test_document_id
    
    # Clean up
    if chunks_file.exists():
        chunks_file.unlink()


@pytest.fixture
def test_conversation(db: Session, test_user: User):
    """Create a test conversation."""
    conversation = create_conversation(db, test_user.id, "Test Conversation")
    return conversation


def test_query_with_documents(client: TestClient, test_user: User, mock_document_chunks, user_headers):
    """Test querying with document context."""
    document_id = mock_document_chunks
    
    # Mock the query_with_documents function
    with patch('app.services.openai_service.query_with_documents', return_value={
        "answer": "This is a test response based on the document.",
        "sources": [
            {
                "document_id": document_id,
                "chunk_id": f"{document_id}_chunk_0",
                "score": 0.95,
                "metadata": {"document_id": document_id, "chunk_index": 0}
            }
        ],
        "query": "Test query",
        "model": "gpt-4"
    }):
        response = client.post(
            "/api/chat/query",
            headers=user_headers,
            json={
                "message": "Test query",
                "document_ids": [document_id],
                "options": {"model": "gpt-4"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "This is a test response based on the document."
        assert len(data["sources"]) == 1
        assert data["sources"][0]["document_id"] == document_id


def test_search_documents(client: TestClient, test_user: User, mock_document_chunks, user_headers):
    """Test searching documents."""
    document_id = mock_document_chunks
    
    # Mock the search_document_chunks function
    with patch('app.services.openai_service.search_document_chunks', return_value=[
        {
            "chunk_id": f"{document_id}_chunk_0",
            "document_id": document_id,
            "text": "This is the first chunk of test content.",
            "metadata": {"document_id": document_id, "chunk_index": 0},
            "score": 0.95
        },
        {
            "chunk_id": f"{document_id}_chunk_1",
            "document_id": document_id,
            "text": "This is the second chunk of test content.",
            "metadata": {"document_id": document_id, "chunk_index": 1},
            "score": 0.85
        }
    ]):
        response = client.post(
            "/api/chat/search",
            headers=user_headers,
            json={
                "query": "test content",
                "document_ids": [document_id],
                "top_k": 2
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2
        assert data["results"][0]["document_id"] == document_id
        assert data["results"][0]["score"] == 0.95


def test_add_document_context(client: TestClient, test_user: User, test_conversation: Conversation, mock_document_chunks, user_headers):
    """Test adding document context to a conversation."""
    document_id = mock_document_chunks
    
    response = client.post(
        f"/api/chat/conversation/{test_conversation.id}/context",
        headers=user_headers,
        json=[document_id]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == test_conversation.id
    assert document_id in data["document_ids"]
    
    # Verify context was added by checking conversation metadata
    response = client.get(
        f"/api/chat/conversations/{test_conversation.id}",
        headers=user_headers
    )
    
    assert response.status_code == 200
    conversation_data = response.json()
    assert "metadata" in conversation_data
    assert "document_context" in conversation_data["metadata"]
    assert document_id in conversation_data["metadata"]["document_context"]


def test_remove_document_context(client: TestClient, test_user: User, test_conversation: Conversation, mock_document_chunks, user_headers):
    """Test removing document context from a conversation."""
    document_id = mock_document_chunks
    
    # First add document context
    client.post(
        f"/api/chat/conversation/{test_conversation.id}/context",
        headers=user_headers,
        json=[document_id]
    )
    
    # Then remove it
    response = client.delete(
        f"/api/chat/conversation/{test_conversation.id}/context/{document_id}",
        headers=user_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == test_conversation.id
    assert data["document_id"] == document_id
    
    # Verify context was removed
    response = client.get(
        f"/api/chat/conversations/{test_conversation.id}",
        headers=user_headers
    )
    
    assert response.status_code == 200
    conversation_data = response.json()
    assert "metadata" in conversation_data
    
    # Either document_context is empty or doesn't contain the document_id
    if "document_context" in conversation_data["metadata"]:
        assert document_id not in conversation_data["metadata"]["document_context"]
