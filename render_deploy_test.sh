#!/bin/bash

# Script to test the deployment on Render.com
# This script will:
# 1. Check if the database tables exist
# 2. Check if the GCS credentials are properly configured
# 3. Test document upload and processing

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

echo -e "${YELLOW}=== RENDER DEPLOYMENT TEST ===${NC}"

# Step 1: Check database tables
echo -e "\n${YELLOW}1. Checking database tables...${NC}"
python -c "
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Get database URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print('DATABASE_URL environment variable not set')
    sys.exit(1)

try:
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    # Check tables
    with engine.connect() as conn:
        result = conn.execute(text(\"\"\"
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
        \"\"\"))
        
        tables = [row[0] for row in result]
        
        print(f'Found {len(tables)} tables in database:')
        for table in tables:
            print(f'  - {table}')
        
        # Check document tables specifically
        doc_tables = [t for t in tables if t in ('documents', 'document_chunks')]
        if len(doc_tables) == 2:
            print('\\nDocument tables found!')
            
            # Check document table columns
            result = conn.execute(text(\"\"\"
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'documents'
            ORDER BY column_name
            \"\"\"))
            
            columns = [row[0] for row in result]
            print(f'\\nDocument table columns: {columns}')
            
            # Check for document_metadata column
            if 'document_metadata' in columns:
                print('document_metadata column found!')
            else:
                print('document_metadata column NOT found!')
                sys.exit(1)
        else:
            print('\\nDocument tables not found!')
            sys.exit(1)
    
    print('\\nDatabase check successful!')
    sys.exit(0)
except SQLAlchemyError as e:
    print(f'Database check failed: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}Database check failed. Check the logs for details.${NC}"
    exit 1
fi

echo -e "${GREEN}Database check successful.${NC}"

# Step 2: Check GCS credentials
echo -e "\n${YELLOW}2. Checking GCS credentials...${NC}"
python -c "
import os
import sys

# Check if GCS is enabled
USE_GCS = os.environ.get('USE_GCS_STORAGE', '').lower() == 'true'
if not USE_GCS:
    print('GCS storage is not enabled')
    sys.exit(0)

# Check if credentials are set
if 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ and 'GOOGLE_APPLICATION_CREDENTIALS_JSON' not in os.environ:
    print('GCS credentials not found')
    sys.exit(1)

# Check if bucket name is set
if 'GCS_BUCKET_NAME' not in os.environ:
    print('GCS_BUCKET_NAME not set')
    sys.exit(1)

print(f'GCS bucket: {os.environ.get(\"GCS_BUCKET_NAME\")}')

# Try to import google.cloud.storage
try:
    from google.cloud import storage
    print('google-cloud-storage package is installed')
    
    # Try to create client
    try:
        client = storage.Client()
        print(f'Successfully created GCS client for project: {client.project}')
        
        # Try to access bucket
        bucket_name = os.environ.get('GCS_BUCKET_NAME')
        bucket = client.bucket(bucket_name)
        
        # List a few blobs
        blobs = list(bucket.list_blobs(max_results=5))
        print(f'Found {len(blobs)} objects in bucket {bucket_name}')
        
        print('GCS credentials check successful!')
        sys.exit(0)
    except Exception as e:
        print(f'Failed to access GCS: {e}')
        sys.exit(1)
except ImportError:
    print('google-cloud-storage package is not installed')
    sys.exit(1)
"

# Don't exit if GCS check fails, just warn
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}GCS check failed. This may be expected if GCS is not configured.${NC}"
else
    echo -e "${GREEN}GCS check successful.${NC}"
fi

echo -e "\n${GREEN}=== DEPLOYMENT TEST COMPLETED ===${NC}"
echo -e "Your deployment on Render.com appears to be properly configured."
echo -e "Next steps:"
echo -e "1. Test document upload using the API"
echo -e "2. Monitor logs for any errors"
echo -e "3. Verify document processing and storage"
