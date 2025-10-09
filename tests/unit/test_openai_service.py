"""
Unit tests for the OpenAI service document processing functions.
"""

import pytest
import os
import tempfile
import json
from pathlib import Path
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from app.services import openai_service


@pytest.fixture
def test_document_id():
    """Generate a test document ID."""
    return "doc-test-123"


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
def test_image_file():
    """Create a temporary image file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        # Write some dummy content to make it look like a JPG
        temp_file.write(b"\xff\xd8\xff\xe0Test image content")
        temp_file_path = temp_file.name
    
    yield temp_file_path
    
    # Clean up the temporary file
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)


@pytest.mark.asyncio
async def test_extract_text_from_document_txt(test_text_file):
    """Test extracting text from a text file."""
    result = await openai_service.extract_text_from_document(test_text_file, "text/plain")
    assert "This is a test document." in result
    assert "For testing purposes." in result


@pytest.mark.asyncio
async def test_extract_text_from_document_pdf(test_pdf_file):
    """Test extracting text from a PDF file."""
    # Mock PyPDF2.PdfReader to avoid actual PDF parsing
    with patch('PyPDF2.PdfReader') as mock_pdf_reader:
        # Setup the mock
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Mocked PDF content"
        mock_pdf_reader.return_value.pages = [mock_page]
        
        result = await openai_service.extract_text_from_document(test_pdf_file, "application/pdf")
        assert "Mocked PDF content" in result


@pytest.mark.asyncio
async def test_extract_text_from_image(test_image_file):
    """Test extracting text from an image."""
    # Mock OpenAI API call
    with patch('app.services.openai_service.client.chat.completions.create') as mock_openai:
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Description: A test image\nExtracted Text: Sample text from image"
        mock_openai.side_effect = AsyncMock(return_value=mock_response)
        
        result = await openai_service.extract_text_from_image(test_image_file)
        assert "Description: A test image" in result
        assert "Extracted Text: Sample text from image" in result


@pytest.mark.asyncio
async def test_chunk_document():
    """Test document chunking."""
    # Create a long text with multiple paragraphs
    long_text = "\n\n".join([f"Paragraph {i} with enough content to make it substantial for testing purposes. This is a longer paragraph to ensure we have enough text to test the chunking functionality properly." for i in range(20)])
    
    # Add metadata
    metadata = {"document_id": "test-doc", "source": "test"}
    
    # Temporarily patch MAX_CHUNK_SIZE to force chunking
    with patch('app.services.openai_service.MAX_CHUNK_SIZE', 500):
        # Chunk the document
        chunks = await openai_service.chunk_document(long_text, metadata)
    
    # Verify chunks
    assert len(chunks) > 1
    assert all("text" in chunk for chunk in chunks)
    assert all("metadata" in chunk for chunk in chunks)
    assert all(chunk["metadata"]["document_id"] == "test-doc" for chunk in chunks)
    assert all(chunk["metadata"]["source"] == "test" for chunk in chunks)
    assert all(chunk["metadata"]["chunk_index"] >= 0 for chunk in chunks)


@pytest.mark.asyncio
async def test_generate_embeddings():
    """Test generating embeddings."""
    # Mock OpenAI API call
    with patch('app.services.openai_service.client.embeddings.create') as mock_openai:
        # Setup mock response
        mock_data1 = MagicMock()
        mock_data1.embedding = [0.1] * 1536
        mock_data2 = MagicMock()
        mock_data2.embedding = [0.2] * 1536
        
        mock_response = MagicMock()
        mock_response.data = [mock_data1, mock_data2]
        mock_openai.side_effect = AsyncMock(return_value=mock_response)
        
        # Test with two text chunks
        texts = ["This is the first chunk", "This is the second chunk"]
        embeddings = await openai_service.generate_embeddings(texts)
        
        # Verify results
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1536
        assert len(embeddings[1]) == 1536
        assert embeddings[0][0] == 0.1
        assert embeddings[1][0] == 0.2


@pytest.mark.asyncio
async def test_process_document(test_text_file, test_document_id):
    """Test the complete document processing pipeline."""
    # Create mocks for all the functions called by process_document
    with patch('app.services.openai_service.extract_text_from_document', return_value="Test document content") as mock_extract:
        with patch('app.services.openai_service.chunk_document') as mock_chunk:
            # Setup chunk mock to return two chunks
            mock_chunk.return_value = [
                {"text": "Chunk 1", "metadata": {"chunk_index": 0}},
                {"text": "Chunk 2", "metadata": {"chunk_index": 1}}
            ]
            
            with patch('app.services.openai_service.generate_embeddings') as mock_embeddings:
                # Setup embeddings mock
                mock_embeddings.return_value = [[0.1] * 1536, [0.2] * 1536]
                
                with patch('app.services.openai_service.store_document_chunks', return_value=True) as mock_store:
                    # Call the function
                    result = await openai_service.process_document(
                        file_path=test_text_file,
                        file_type="text/plain",
                        document_id=test_document_id,
                        user_id="test-user",
                        metadata={"source": "test"}
                    )
                    
                    # Verify the result
                    assert result["document_id"] == test_document_id
                    assert result["chunk_count"] == 2
                    assert result["status"] == "processed"
                    
                    # Verify the function calls
                    mock_extract.assert_called_once_with(test_text_file, "text/plain")
                    mock_chunk.assert_called_once()
                    mock_embeddings.assert_called_once_with(["Chunk 1", "Chunk 2"])
                    mock_store.assert_called_once()


@pytest.mark.asyncio
async def test_query_with_documents(test_document_id):
    """Test querying with document context."""
    # Mock the Path.exists method to return True for our test document
    with patch('pathlib.Path.exists') as mock_exists:
        mock_exists.return_value = True  # Make it look like the document chunks file exists
        
        # Mock search_document_chunks to return relevant chunks
        with patch('app.services.openai_service.search_document_chunks') as mock_search:
            mock_search.return_value = [
                {
                    "chunk_id": f"{test_document_id}_chunk_0",
                    "document_id": test_document_id,
                    "text": "This is relevant content for the query.",
                    "metadata": {"document_id": test_document_id, "chunk_index": 0},
                    "score": 0.95
                }
            ]
            
            # Mock OpenAI API call
            with patch('app.services.openai_service.client.chat.completions.create') as mock_openai:
                mock_response = MagicMock()
                mock_response.choices[0].message.content = "This is a response based on the document."
                mock_openai.side_effect = AsyncMock(return_value=mock_response)
                
                # Call the function
                result = await openai_service.query_with_documents(
                    query="Test query",
                    user_id="test-user",
                    document_ids=[test_document_id]
                )
                
                # Verify the result
                assert result["answer"] == "This is a response based on the document."
                assert len(result["sources"]) == 1
                assert result["sources"][0]["document_id"] == test_document_id
                assert result["query"] == "Test query"


@pytest.mark.asyncio
async def test_search_document_chunks(test_document_id):
    """Test searching document chunks."""
    # Mock generate_embeddings to return a query embedding
    with patch('app.services.openai_service.generate_embeddings') as mock_embeddings:
        mock_embeddings.side_effect = AsyncMock(return_value=[[0.1] * 1536])
        
        # Create a mock chunks directory and file
        chunks_dir = Path("./document_chunks")
        chunks_dir.mkdir(exist_ok=True)
        
        chunks_file = chunks_dir / f"{test_document_id}_chunks.json"
        
        # Create mock chunks
        chunks = [
            {
                "id": f"{test_document_id}_chunk_0",
                "metadata": {
                    "document_id": test_document_id,
                    "chunk_index": 0
                },
                "text": "This is relevant content.",
                "embedding_size": 1536
            }
        ]
        
        # Write chunks to file
        with open(chunks_file, "w") as f:
            json.dump(chunks, f)
        
        try:
            # Call the function
            results = await openai_service.search_document_chunks(
                query="Test query",
                user_id="test-user",
                document_ids=[test_document_id]
            )
            
            # Verify the results
            assert len(results) == 1
            assert results[0]["document_id"] == test_document_id
            assert "score" in results[0]
            assert results[0]["text"] == "This is relevant content."
        
        finally:
            # Clean up
            if chunks_file.exists():
                chunks_file.unlink()


@pytest.mark.asyncio
async def test_analyze_document(test_document_id):
    """Test document analysis."""
    # Mock the Path.exists method to return True for our test document
    with patch('pathlib.Path.exists') as mock_exists:
        mock_exists.return_value = True  # Make it look like the document chunks file exists
        
        # Mock get_document_chunks to return chunks
        with patch('app.services.openai_service.get_document_chunks') as mock_get_chunks:
            chunks_data = [
                {
                    "id": f"{test_document_id}_chunk_0",
                    "text": "This is the first chunk of content.",
                    "metadata": {"document_id": test_document_id, "chunk_index": 0}
                },
                {
                    "id": f"{test_document_id}_chunk_1",
                    "text": "This is the second chunk of content.",
                    "metadata": {"document_id": test_document_id, "chunk_index": 1}
                }
            ]
            mock_get_chunks.side_effect = AsyncMock(return_value=chunks_data)
            
            # Mock OpenAI API call
            with patch('app.services.openai_service.client.chat.completions.create') as mock_openai:
                mock_response = MagicMock()
                mock_response.choices[0].message.content = "This is a summary of the document."
                mock_openai.side_effect = AsyncMock(return_value=mock_response)
                
                # Call the function
                result = await openai_service.analyze_document(
                    document_id=test_document_id,
                    user_id="test-user",
                    analysis_type="summary"
                )
                
                # Verify the result
                assert result["document_id"] == test_document_id
                assert result["analysis_type"] == "summary"
                assert result["analysis"] == "This is a summary of the document."
                assert result["chunk_count"] == 2
