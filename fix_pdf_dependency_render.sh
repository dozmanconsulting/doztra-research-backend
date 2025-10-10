#!/bin/bash

# Script to fix the PDF dependency issue on Render
# This script will:
# 1. Add PyPDF2 to requirements.txt
# 2. Install the dependency
# 3. Restart the service

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color

echo -e "${YELLOW}=== FIXING PDF DEPENDENCY ISSUE ===${NC}"

# Set the project directory to the current directory on Render
PROJECT_DIR="$(pwd)"
echo -e "${GREEN}Using project directory: $PROJECT_DIR${NC}"

# Check if PyPDF2 is already in requirements.txt
if grep -q "PyPDF2" requirements.txt; then
  echo -e "${GREEN}PyPDF2 is already in requirements.txt${NC}"
else
  echo -e "${YELLOW}Adding PyPDF2 to requirements.txt...${NC}"
  echo "PyPDF2==3.0.1" >> requirements.txt
  echo -e "${GREEN}Added PyPDF2 to requirements.txt${NC}"
fi

# Install the dependency
echo -e "\n${YELLOW}Installing PyPDF2...${NC}"
pip install PyPDF2==3.0.1

# Check if installation was successful
if pip list | grep -q "PyPDF2"; then
  echo -e "${GREEN}PyPDF2 installed successfully${NC}"
else
  echo -e "${RED}Failed to install PyPDF2${NC}"
  exit 1
fi

echo -e "\n${YELLOW}=== PDF DEPENDENCY FIX COMPLETE ===${NC}"
echo -e "The PyPDF2 dependency has been added to requirements.txt and installed."
echo -e "You may need to restart the service for the changes to take effect."
