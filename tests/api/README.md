# API Tests for Research Project Management

This directory contains tests for the Research Project Management API endpoints.

## Test Coverage

The test suite covers the following functionality:

1. **CRUD Operations**:
   - Creating a new research project
   - Getting a list of research projects
   - Getting a specific research project by ID
   - Updating a research project
   - Deleting a research project

2. **Error Handling**:
   - Attempting to access non-existent projects
   - Unauthorized access attempts

3. **Filtering and Pagination**:
   - Filtering projects by status (active, completed, archived)
   - Testing pagination with skip and limit parameters

## Running the Tests

To run the tests, use the following command from the project root:

```bash
pytest tests/api/test_research_projects.py -v
```

## Test Dependencies

The tests depend on:
- FastAPI TestClient
- SQLAlchemy
- Pytest
- Authentication utilities from the app

## Test Data

The tests use the following test data:

1. **Test User**:
   - Email: test@example.com
   - Name: Test User

2. **Test Project**:
   - Title: Test Research Project
   - Description: This is a test research project
   - Type: literature_review
   - Metadata: {"tags": ["test", "research"]}

3. **Updated Project Data**:
   - Title: Updated Research Project
   - Description: This is an updated test research project
   - Type: research_paper
   - Status: completed
   - Metadata: {"tags": ["test", "updated"]}

## Notes

- The tests use a test database session to avoid affecting the production database
- Authentication is handled using JWT tokens
- Each test cleans up after itself to maintain test isolation
