#!/bin/bash

# Script to fix the PDF dependency issue
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

# Set the project directory
PROJECT_DIR="/Users/shed/Desktop/doztra-v1/doztra-backend-service-v1"
cd "$PROJECT_DIR" || { echo -e "${RED}Error: Could not change to project directory${NC}"; exit 1; }

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

# Create a deployment script for Render
echo -e "\n${YELLOW}Creating deployment script for Render...${NC}"
cat > deploy_pdf_fix.sh << EOL
#!/bin/bash

# Add PyPDF2 to requirements.txt if not already present
if ! grep -q "PyPDF2" requirements.txt; then
  echo "PyPDF2==3.0.1" >> requirements.txt
  echo "Added PyPDF2 to requirements.txt"
fi

# Install the dependency
pip install PyPDF2==3.0.1

# Restart the service (if needed)
# systemctl restart doztra-backend
EOL

chmod +x deploy_pdf_fix.sh
echo -e "${GREEN}Created deploy_pdf_fix.sh${NC}"

echo -e "\n${YELLOW}=== PDF DEPENDENCY FIX COMPLETE ===${NC}"
echo -e "To deploy this fix to production:"
echo -e "1. Push the updated requirements.txt to the repository"
echo -e "2. Run deploy_pdf_fix.sh on the production server"
echo -e "3. Restart the backend service"
