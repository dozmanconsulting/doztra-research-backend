#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== RUNNING TOKEN USAGE API TESTS ===${NC}"
echo ""

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python -m venv venv
fi

# Activate the virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.dependencies_installed" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -r requirements.txt
    touch venv/.dependencies_installed
fi

# Run the tests
echo -e "${YELLOW}Running token usage tests...${NC}"
echo ""

# Run the original token usage tests
echo -e "${YELLOW}1. Running original token usage tests...${NC}"
python -m pytest tests/test_token_usage.py -v
ORIGINAL_RESULT=$?

echo ""
echo -e "${YELLOW}2. Running usage statistics tests...${NC}"
python -m pytest tests/test_usage_statistics.py -v
USAGE_STATS_RESULT=$?

echo ""
echo -e "${YELLOW}3. Running comprehensive token usage tests...${NC}"
python -m pytest tests/test_token_usage_comprehensive.py -v
COMPREHENSIVE_RESULT=$?

# Check if all tests passed
if [ $ORIGINAL_RESULT -eq 0 ] && [ $USAGE_STATS_RESULT -eq 0 ] && [ $COMPREHENSIVE_RESULT -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=== ALL TOKEN USAGE TESTS PASSED ===${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}=== SOME TESTS FAILED ===${NC}"
    exit 1
fi
