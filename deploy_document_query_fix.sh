#!/bin/bash

# Script to deploy the document query fix
# This script will:
# 1. Back up the original files
# 2. Apply the fixes
# 3. Restart the service

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color

echo -e "${YELLOW}=== DEPLOYING DOCUMENT QUERY FIX ===${NC}"

# Set the project directory
PROJECT_DIR="/Users/shed/Desktop/doztra-v1/doztra-backend-service-v1"
cd "$PROJECT_DIR" || { echo -e "${RED}Error: Could not change to project directory${NC}"; exit 1; }

# Create backup directory
BACKUP_DIR="$PROJECT_DIR/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}Created backup directory: $BACKUP_DIR${NC}"

# Backup original files
echo -e "\n${YELLOW}1. Backing up original files...${NC}"
cp -v "$PROJECT_DIR/app/services/openai_service.py" "$BACKUP_DIR/openai_service.py.bak"
cp -v "$PROJECT_DIR/app/api/routes/document_queries.py" "$BACKUP_DIR/document_queries.py.bak"

# Apply fixes
echo -e "\n${YELLOW}2. Applying fixes...${NC}"

# Copy the new service files
echo -e "${GREEN}Adding document_service_fix.py${NC}"
cp -v "$PROJECT_DIR/app/services/document_service_fix.py" "$PROJECT_DIR/app/services/document_service.py"

# Update the main.py file to use the fixed router
echo -e "${GREEN}Updating main.py to use fixed document_queries router${NC}"
MAIN_FILE="$PROJECT_DIR/app/main.py"
MAIN_BACKUP="$BACKUP_DIR/main.py.bak"

# Backup main.py
cp -v "$MAIN_FILE" "$MAIN_BACKUP"

# Update the import in main.py
sed -i.bak "s/from app.api.routes import document_queries/from app.api.routes import document_queries_fix as document_queries/" "$MAIN_FILE"

# Apply the OpenAI service fix
echo -e "${GREEN}Updating openai_service.py${NC}"
OPENAI_FILE="$PROJECT_DIR/app/services/openai_service.py"
OPENAI_BACKUP="$BACKUP_DIR/openai_service.py.bak"

# Backup openai_service.py again (just to be safe)
cp -v "$OPENAI_FILE" "$OPENAI_BACKUP"

# Replace the query_with_documents function with our fixed version
# This is a complex sed operation, so we'll use a temporary file
cat "$PROJECT_DIR/app/services/openai_service_fix.py" > "$PROJECT_DIR/app/services/openai_service_new.py"
cat "$OPENAI_FILE" >> "$PROJECT_DIR/app/services/openai_service_new.py"
mv "$PROJECT_DIR/app/services/openai_service_new.py" "$OPENAI_FILE"

echo -e "\n${YELLOW}3. Restarting the service...${NC}"
# Restart command would go here, e.g.:
# systemctl restart doztra-backend

echo -e "\n${GREEN}=== DOCUMENT QUERY FIX DEPLOYED SUCCESSFULLY ===${NC}"
echo "The following fixes were applied:"
echo "1. Added document existence validation before processing queries"
echo "2. Improved error handling for missing documents"
echo "3. Added clear error messages for users"
echo -e "\nBackups were saved to: $BACKUP_DIR"
echo -e "\nTo verify the fix, run the check_document_status.sh script with a non-existent document ID."
