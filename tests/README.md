# Doztra Auth Service Tests

This directory contains tests for the Doztra Auth Service, including the document processing and LLM interaction features.

## Test Structure

- `api/`: API endpoint tests
  - `test_documents.py`: Tests for document management endpoints
  - `test_document_queries.py`: Tests for document-based query endpoints
  - `test_chat.py`: Tests for chat functionality
  - `test_research_projects.py`: Tests for research project endpoints
- `unit/`: Unit tests for individual components
  - `test_openai_service.py`: Tests for the OpenAI service document processing functions
- `conftest.py`: Test fixtures and configuration
- `utils/`: Utility functions for testing

## Running Tests

### Prerequisites

Make sure you have all the required dependencies installed:

```bash
pip install -r requirements-dev.txt
```

### Running All Tests

To run all tests:

```bash
pytest
```

### Running Specific Test Files

To run tests from a specific file:

```bash
pytest tests/api/test_documents.py
```

### Running Tests with Coverage

To run tests with coverage reporting:

```bash
pytest --cov=app
```

To generate an HTML coverage report:

```bash
pytest --cov=app --cov-report=html
```

The report will be available in the `htmlcov` directory.

## Test Environment

The tests use an in-memory SQLite database to avoid affecting your production database. The database is created fresh for each test and destroyed afterward.

## Mocking External Services

External services like the OpenAI API are mocked in the tests to avoid making actual API calls. This makes the tests faster and more reliable.

### Mocking Async Functions

Many of the OpenAI API calls are asynchronous. When mocking these functions, use `AsyncMock` with `side_effect` rather than `return_value` to ensure the mock can be properly awaited:

```python
from unittest.mock import AsyncMock, MagicMock, patch

# Correct way to mock an async function
with patch('app.services.openai_service.client.chat.completions.create') as mock_openai:
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Test response"
    mock_openai.side_effect = AsyncMock(return_value=mock_response)
    
    # Now you can await the mocked function
    result = await some_async_function()
```

This approach ensures that the mock can be properly awaited in the test code.

## OpenAI Service Tests

The `test_openai_service.py` file contains tests for the OpenAI service, which handles document processing, embedding generation, and LLM interactions. These tests cover:

1. **Document Text Extraction**: Testing extraction from various file formats (text, PDF, images)
2. **Document Chunking**: Testing the chunking algorithm for large documents
3. **Embedding Generation**: Testing the generation of vector embeddings for document chunks
4. **Document Processing Pipeline**: Testing the full document processing workflow
5. **Document Querying**: Testing semantic search and LLM-based question answering
6. **Document Analysis**: Testing document summarization and analysis

### Running OpenAI Service Tests

To run just the OpenAI service tests:

```bash
pytest tests/unit/test_openai_service.py -v
```

### Required Dependencies

The OpenAI service tests require several dependencies that are listed in `requirements.txt`, including:

- `openai`: The OpenAI Python client
- `PyPDF2`: For PDF processing
- `python-docx`: For Word document processing
- `pandas`: For data processing
- `pytest-asyncio`: For testing async functions

## Adding New Tests

When adding new features, please add corresponding tests:

1. For API endpoints, add tests in the `api/` directory
2. For service functions, add unit tests in the `unit/` directory
3. Use the existing fixtures in `conftest.py` when possible
4. Mock external services to avoid making actual API calls

## Troubleshooting

If you encounter issues with the tests:

1. Make sure all dependencies are installed
2. Check that the test database can be created
3. Verify that the mocks are correctly set up
4. Check for any changes in the API that might require updating the tests
