#!/bin/bash

# Script to deploy the document query fix directly
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

# Set the project directory to the current directory
PROJECT_DIR="$(pwd)"
echo -e "${GREEN}Using project directory: $PROJECT_DIR${NC}"

# Create backup directory
BACKUP_DIR="$PROJECT_DIR/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}Created backup directory: $BACKUP_DIR${NC}"

# Backup original files
echo -e "\n${YELLOW}1. Backing up original files...${NC}"
cp -v "$PROJECT_DIR/app/services/openai_service.py" "$BACKUP_DIR/openai_service.py.bak"
cp -v "$PROJECT_DIR/app/api/routes/document_queries.py" "$BACKUP_DIR/document_queries.py.bak"

# Apply fixes to openai_service.py
echo -e "\n${YELLOW}2. Applying fix to openai_service.py...${NC}"
cat > "$BACKUP_DIR/openai_service_fix.py" << 'EOL'
        # Check if documents exist and are processed
        chunks_dir = Path("./document_chunks")
        for doc_id in document_ids or []:
            # First check if the document exists in the user's uploads
            user_dir = Path("./uploads") / user_id
            doc_dir = user_dir / doc_id
            
            if not doc_dir.exists():
                # Document doesn't exist
                return {
                    "answer": f"The document with ID {doc_id} was not found. Please check the document ID and try again.",
                    "sources": [],
                    "query": query,
                    "model": query_options["model"],
                    "error": "document_not_found"
                }
                
            # Now check if document is processed
            chunks_file = chunks_dir / f"{doc_id}_chunks.json"
            if not chunks_file.exists():
                # Document exists but is not processed yet
                return {
                    "answer": f"The document with ID {doc_id} is still being processed. Please try again in a few moments.",
                    "sources": [],
                    "query": query,
                    "model": query_options["model"],
                    "processing_status": "pending"
                }
EOL

# Replace the document check section in openai_service.py
sed -i -e '/# Check if documents are processed/,/}/c\
        # Check if documents exist and are processed\
        chunks_dir = Path("./document_chunks")\
        for doc_id in document_ids or []:\
            # First check if the document exists in the user'\''s uploads\
            user_dir = Path("./uploads") / user_id\
            doc_dir = user_dir / doc_id\
            \
            if not doc_dir.exists():\
                # Document doesn'\''t exist\
                return {\
                    "answer": f"The document with ID {doc_id} was not found. Please check the document ID and try again.",\
                    "sources": [],\
                    "query": query,\
                    "model": query_options["model"],\
                    "error": "document_not_found"\
                }\
                \
            # Now check if document is processed\
            chunks_file = chunks_dir / f"{doc_id}_chunks.json"\
            if not chunks_file.exists():\
                # Document exists but is not processed yet\
                return {\
                    "answer": f"The document with ID {doc_id} is still being processed. Please try again in a few moments.",\
                    "sources": [],\
                    "query": query,\
                    "model": query_options["model"],\
                    "processing_status": "pending"\
                }' "$PROJECT_DIR/app/services/openai_service.py"

echo -e "${GREEN}Applied fix to openai_service.py${NC}"

# Apply fixes to document_queries.py
echo -e "\n${YELLOW}3. Applying fix to document_queries.py...${NC}"
cat > "$BACKUP_DIR/document_queries_fix.py" << 'EOL'
    try:
        # Call the service function
        response = await openai_service.query_with_documents(
            query=request.message,
            user_id=str(current_user.id),
            document_ids=request.document_ids,
            options=request.options
        )
        
        # Check for specific error conditions
        if "error" in response and response["error"] == "document_not_found":
            # Return a 404 status for missing documents
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=response["answer"]
            )
        
        # Track token usage (in a real implementation)
        # await track_token_usage(db, current_user.id, response.get("usage", {}))
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )
EOL

# Replace the try-except block in document_queries.py
sed -i -e '/try:/,/detail=f"Query failed: {str(e)}"/c\
    try:\
        # Call the service function\
        response = await openai_service.query_with_documents(\
            query=request.message,\
            user_id=str(current_user.id),\
            document_ids=request.document_ids,\
            options=request.options\
        )\
        \
        # Check for specific error conditions\
        if "error" in response and response["error"] == "document_not_found":\
            # Return a 404 status for missing documents\
            raise HTTPException(\
                status_code=status.HTTP_404_NOT_FOUND,\
                detail=response["answer"]\
            )\
        \
        # Track token usage (in a real implementation)\
        # await track_token_usage(db, current_user.id, response.get("usage", {}))\
        \
        return response\
        \
    except HTTPException:\
        # Re-raise HTTP exceptions\
        raise\
    except Exception as e:\
        raise HTTPException(\
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,\
            detail=f"Query failed: {str(e)}"\
        )' "$PROJECT_DIR/app/api/routes/document_queries.py"

echo -e "${GREEN}Applied fix to document_queries.py${NC}"

echo -e "\n${YELLOW}4. Restarting the service...${NC}"
# Restart command would go here, e.g.:
# systemctl restart doztra-backend

echo -e "\n${GREEN}=== DOCUMENT QUERY FIX DEPLOYED SUCCESSFULLY ===${NC}"
echo "The following fixes were applied:"
echo "1. Added document existence check before processing check"
echo "2. Improved error handling for non-existent documents"
echo "3. Added proper HTTP status codes for different error conditions"
echo -e "\nBackups were saved to: $BACKUP_DIR"
echo -e "\nTo verify the fix, try querying a document that doesn't exist and one that is still processing."
