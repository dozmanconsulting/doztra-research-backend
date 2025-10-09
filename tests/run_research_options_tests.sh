#!/bin/bash

# Set environment variables for testing
export TESTING=1
export TEST_DATABASE_URL="sqlite:///./test.db"
export SECRET_KEY="test_secret_key_for_research_options_testing"
export ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES=30

# Initialize test database
echo "Initializing test database..."
python -c "from app.db.init_db import init_test_db; init_test_db()"

# Run unit tests for research options
echo "Running unit tests for research options..."
python -m pytest tests/unit/test_research_options.py -v

# Run integration tests for research options
echo "Running integration tests for research options..."
python -m pytest tests/integration/test_research_options_integration.py -v

echo "All tests completed!"
