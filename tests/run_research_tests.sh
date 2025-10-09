#!/bin/bash

# Script to run the research project API tests

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Set environment variables for testing
export ENVIRONMENT="test"
export DATABASE_URL="sqlite:///./test.db"

# Run the tests
echo "Running research project API tests..."
pytest tests/api/test_research_projects.py -v

# Print completion message
echo "Tests completed!"
