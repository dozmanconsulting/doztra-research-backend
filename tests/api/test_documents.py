"""
Tests for the Document API endpoints.
"""

import pytest
import os
import tempfile
import json
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.user import User
from tests.utils.auth import get_test_token


@pytest.fixture
def test_document_id():
    """Generate a test document ID."""
    return f"doc-{uuid.uuid4()}"


@pytest.fixture
def test_pdf_file():
    """Create a temporary PDF file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        # Write some dummy content to make it look like a PDF
        temp_file.write(b"%PDF-1.5\nTest PDF content\n%%EOF")
        temp_file_path = temp_file.name
    
    yield temp_file_path
    
    # Clean up the temporary file
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)


@pytest.fixture
def test_text_file():
    """Create a temporary text file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
        temp_file.write(b"This is a test document.\nIt contains multiple lines.\nFor testing purposes.")
        temp_file_path = temp_file.name
    
    yield temp_file_path
    
    # Clean up the temporary file
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)


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


def test_upload_document(client: TestClient, test_user: User, test_text_file: str, user_headers):
    """Test uploading a document."""
    
    # Mock the background processing task
    with patch('app.api.routes.documents.process_document_background'):
        with open(test_text_file, "rb") as file:
            response = client.post(
                "/api/documents/upload",
                headers=user_headers,
                files={"file": ("test.txt", file, "text/plain")},
                data={"metadata": json.dumps({"source": "test"})}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert data["file_name"] == "test.txt"
        assert data["file_type"] == "text/plain"
        assert data["status"] == "uploaded"


def test_get_document(client: TestClient, test_user: User, mock_document_chunks, user_headers):
    """Test getting document metadata."""
    document_id = mock_document_chunks
    
    # Create user directory and document directory
    user_dir = Path("./uploads") / test_user.id
    user_dir.mkdir(exist_ok=True, parents=True)
    
    doc_dir = user_dir / document_id
    doc_dir.mkdir(exist_ok=True)
    
    # Create a dummy file
    test_file = doc_dir / "test.txt"
    with open(test_file, "w") as f:
        f.write("Test content")
    
    try:
        response = client.get(
            f"/api/documents/{document_id}",
            headers=user_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == document_id
        assert data["file_name"] == "test.txt"
        assert data["status"] == "ready"  # Should be ready because chunks exist
    
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()
        if doc_dir.exists():
            doc_dir.rmdir()
        if user_dir.exists():
            user_dir.rmdir()


def test_list_documents(client: TestClient, test_user: User, mock_document_chunks, user_headers):
    """Test listing user documents."""
    document_id = mock_document_chunks
    
    # Create user directory and document directory
    user_dir = Path("./uploads") / test_user.id
    user_dir.mkdir(exist_ok=True, parents=True)
    
    doc_dir = user_dir / document_id
    doc_dir.mkdir(exist_ok=True)
    
    # Create a dummy file
    test_file = doc_dir / "test.txt"
    with open(test_file, "w") as f:
        f.write("Test content")
    
    try:
        response = client.get(
            "/api/documents",
            headers=user_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert len(data["documents"]) >= 1
        assert any(doc["document_id"] == document_id for doc in data["documents"])
    
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()
        if doc_dir.exists():
            doc_dir.rmdir()
        if user_dir.exists():
            user_dir.rmdir()


def test_delete_document(client: TestClient, test_user: User, mock_document_chunks, user_headers):
    """Test deleting a document."""
    document_id = mock_document_chunks
    
    # Create user directory and document directory
    user_dir = Path("./uploads") / test_user.id
    user_dir.mkdir(exist_ok=True, parents=True)
    
    doc_dir = user_dir / document_id
    doc_dir.mkdir(exist_ok=True)
    
    # Create a dummy file
    test_file = doc_dir / "test.txt"
    with open(test_file, "w") as f:
        f.write("Test content")
    
    try:
        response = client.delete(
            f"/api/documents/{document_id}",
            headers=user_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Document deleted successfully"
        
        # Verify document is deleted
        response = client.get(
            f"/api/documents/{document_id}",
            headers=user_headers
        )
        assert response.status_code == 404
    
    finally:
        # Clean up if test fails
        if test_file.exists():
            test_file.unlink()
        if doc_dir.exists():
            doc_dir.rmdir()
        if user_dir.exists():
            user_dir.rmdir()


def test_get_document_content(client: TestClient, test_user: User, mock_document_chunks, user_headers):
    """Test getting document content."""
    document_id = mock_document_chunks
    
    response = client.get(
        f"/api/documents/{document_id}/content",
        headers=user_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == document_id
    assert "content" in data
    assert "chunk_count" in data
    assert data["chunk_count"] == 2


def test_analyze_document(client: TestClient, test_user: User, mock_document_chunks, user_headers):
    """Test document analysis."""
    document_id = mock_document_chunks
    
    # Mock the analyze_document function
    with patch('app.services.openai_service.analyze_document', return_value={
        "document_id": document_id,
        "analysis_type": "summary",
        "analysis": "This is a test summary.",
        "chunk_count": 2,
        "timestamp": "2025-10-07T12:00:00Z"
    }):
        response = client.post(
            f"/api/documents/{document_id}/analyze",
            headers=user_headers,
            params={"analysis_type": "summary"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == document_id
        assert data["analysis_type"] == "summary"
        assert data["analysis"] == "This is a test summary."
