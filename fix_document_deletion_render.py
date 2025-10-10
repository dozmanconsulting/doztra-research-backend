#!/usr/bin/env python3
"""
Fix for document deletion functionality in the Doztra backend service.
This script creates an improved version of the delete_document endpoint.
Adapted for the Render environment.
"""

import os
import sys
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_fixed_delete_function():
    """
    Create an improved version of the delete_document function.
    """
    fixed_code = """
@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user)
):
    \"\"\"
    Delete a document.
    
    This endpoint deletes a document and all associated files.
    \"\"\"
    try:
        # Check if document exists
        user_dir = UPLOAD_DIR / str(current_user.id)
        doc_dir = user_dir / document_id
        
        if not doc_dir.exists():
            # Check if document ID format is valid
            if not document_id.startswith("doc-"):
                raise HTTPException(status_code=400, detail="Invalid document ID format")
            
            # Document directory doesn't exist, but let's check if there are any chunks
            chunks_dir = Path("./document_chunks")
            chunks_file = chunks_dir / f"{document_id}_chunks.json"
            
            if chunks_file.exists():
                # Delete chunks file
                chunks_file.unlink()
                logger.info(f"Deleted chunks file for document {document_id}")
                return {"message": "Document chunks deleted successfully"}
            else:
                # Document truly doesn't exist
                raise HTTPException(status_code=404, detail="Document not found")
        
        # Document exists, proceed with deletion
        
        # Get list of files before deletion for logging
        files = list(doc_dir.glob("*"))
        file_names = [f.name for f in files]
        logger.info(f"Deleting document {document_id} with files: {file_names}")
        
        # Delete document directory
        try:
            shutil.rmtree(doc_dir)
            logger.info(f"Deleted document directory for {document_id}")
        except Exception as e:
            logger.error(f"Error deleting document directory: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete document directory: {str(e)}")
        
        # Delete chunks file if it exists
        chunks_dir = Path("./document_chunks")
        chunks_file = chunks_dir / f"{document_id}_chunks.json"
        if chunks_file.exists():
            try:
                chunks_file.unlink()
                logger.info(f"Deleted chunks file for document {document_id}")
            except Exception as e:
                logger.error(f"Error deleting chunks file: {str(e)}")
                # Don't fail the request if only the chunks deletion fails
        
        # Delete any other associated files
        # For example, status files
        status_dir = Path("./document_status")
        if status_dir.exists():
            status_file = status_dir / f"{document_id}_status.json"
            if status_file.exists():
                try:
                    status_file.unlink()
                    logger.info(f"Deleted status file for document {document_id}")
                except Exception as e:
                    logger.error(f"Error deleting status file: {str(e)}")
        
        return {"message": "Document deleted successfully", "document_id": document_id}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in delete_document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")
"""
    
    # Write the fixed code to a file
    with open("app/api/routes/documents_delete_fix.py", "w") as f:
        f.write(fixed_code)
    
    logger.info("Created fixed delete_document function")

def create_deployment_script():
    """
    Create a deployment script for the document deletion fix.
    """
    script = """#!/bin/bash

# Script to deploy the document deletion fix
# This script will:
# 1. Back up the original file
# 2. Apply the fix
# 3. Restart the service

# Colors for better readability
GREEN="\\033[0;32m"
RED="\\033[0;31m"
YELLOW="\\033[0;33m"
NC="\\033[0m" # No Color

echo -e "${YELLOW}=== DEPLOYING DOCUMENT DELETION FIX ===${NC}"

# Set the project directory to the current directory
PROJECT_DIR="$(pwd)"
echo -e "${GREEN}Using project directory: $PROJECT_DIR${NC}"

# Create backup directory
BACKUP_DIR="$PROJECT_DIR/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}Created backup directory: $BACKUP_DIR${NC}"

# Backup original file
echo -e "\\n${YELLOW}1. Backing up original file...${NC}"
cp -v "$PROJECT_DIR/app/api/routes/documents.py" "$BACKUP_DIR/documents.py.bak"

# Apply fix
echo -e "\\n${YELLOW}2. Applying fix...${NC}"

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

echo -e "\\n${YELLOW}3. Restarting the service...${NC}"
# Restart command would go here, e.g.:
# systemctl restart doztra-backend

echo -e "\\n${GREEN}=== DOCUMENT DELETION FIX DEPLOYED SUCCESSFULLY ===${NC}"
echo "The following fixes were applied:"
echo "1. Improved error handling for document deletion"
echo "2. Added logging for better debugging"
echo "3. Added cleanup for associated files"
echo -e "\\nBackups were saved to: $BACKUP_DIR"
"""
    
    # Write the deployment script to a file
    with open("deploy_document_deletion_fix_render.sh", "w") as f:
        f.write(script)
    
    # Make the script executable
    os.chmod("deploy_document_deletion_fix_render.sh", 0o755)
    
    logger.info("Created deployment script for document deletion fix")

def main():
    """Main function."""
    logger.info("Document deletion fix script for Render")
    
    # Check if we're running in the correct directory
    if not os.path.exists("app") or not os.path.exists("app/api"):
        logger.error("This script must be run from the project root directory.")
        sys.exit(1)
    
    # Create the fixed delete function
    create_fixed_delete_function()
    
    # Create the deployment script
    create_deployment_script()
    
    # Print recommendations
    print("\n=== DOCUMENT DELETION FIX FOR RENDER ===")
    print("The following files were created:")
    print("1. app/api/routes/documents_delete_fix.py - Fixed delete_document function")
    print("2. deploy_document_deletion_fix_render.sh - Deployment script")
    print("\nTo deploy the fix:")
    print("1. Run the deployment script: ./deploy_document_deletion_fix_render.sh")
    print("2. Test document deletion using curl or the frontend")

if __name__ == "__main__":
    main()
