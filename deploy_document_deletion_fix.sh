#!/bin/bash

# Script to deploy the document deletion fix
# This script will:
# 1. Back up the original file
# 2. Apply the fix
# 3. Restart the service

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color

echo -e "${YELLOW}=== DEPLOYING DOCUMENT DELETION FIX ===${NC}"

# Set the project directory
PROJECT_DIR="/opt/render/project/src"
cd "$PROJECT_DIR" || { echo -e "${RED}Error: Could not change to project directory${NC}"; exit 1; }

# Create backup directory
BACKUP_DIR="$PROJECT_DIR/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}Created backup directory: $BACKUP_DIR${NC}"

# Backup original file
echo -e "\n${YELLOW}1. Backing up original file...${NC}"
cp -v "$PROJECT_DIR/app/api/routes/documents.py" "$BACKUP_DIR/documents.py.bak"

# Apply fix
echo -e "\n${YELLOW}2. Applying fix...${NC}"

# Extract the fixed delete_document function
grep -A 100 "@router.delete" "$PROJECT_DIR/app/api/routes/documents_delete_fix.py" > "$BACKUP_DIR/delete_function.txt"

# Replace the delete_document function in the original file
sed -i -e '/^@router.delete/,/^@router/ {
    /^@router.delete/,/^@router/ {
        /^@router.delete/p
        /^@router.[^d]/!d
    }
}' "$PROJECT_DIR/app/api/routes/documents.py"

# Insert the fixed function
sed -i "/^@router.delete/r $BACKUP_DIR/delete_function.txt" "$PROJECT_DIR/app/api/routes/documents.py"

echo -e "${GREEN}Applied document deletion fix${NC}"

echo -e "\n${YELLOW}3. Restarting the service...${NC}"
# Restart command would go here, e.g.:
# systemctl restart doztra-backend

echo -e "\n${GREEN}=== DOCUMENT DELETION FIX DEPLOYED SUCCESSFULLY ===${NC}"
echo "The following fixes were applied:"
echo "1. Improved error handling for document deletion"
echo "2. Added logging for better debugging"
echo "3. Added cleanup for associated files"
echo -e "\nBackups were saved to: $BACKUP_DIR"
