#!/bin/bash
# Script to install working dependencies for Doztra Auth Service

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}   Doztra Auth Service Dependencies   ${NC}"
echo -e "${BLUE}======================================${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo "Please install Python 3.8 or higher."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created.${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate || { echo -e "${RED}Failed to activate virtual environment.${NC}"; exit 1; }

# Install dependencies
echo -e "${BLUE}Installing working dependencies...${NC}"
pip install --upgrade pip || { echo -e "${RED}Failed to upgrade pip.${NC}"; exit 1; }
pip install -r requirements-working.txt || { echo -e "${RED}Failed to install dependencies.${NC}"; exit 1; }

# Install spaCy model
echo -e "${BLUE}Installing spaCy model...${NC}"
python -m spacy download en_core_web_sm || { echo -e "${RED}Failed to install spaCy model.${NC}"; exit 1; }

echo -e "${GREEN}Dependencies installed successfully.${NC}"
echo -e "${BLUE}To start the application:${NC}"
echo -e "  1. Activate the virtual environment: ${YELLOW}source venv/bin/activate${NC}"
echo -e "  2. Run the application: ${YELLOW}python run.py --reload${NC}"
echo -e "${BLUE}Or use the start script:${NC}"
echo -e "  ${YELLOW}./start.sh${NC}"
