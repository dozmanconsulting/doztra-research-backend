#!/bin/bash

# Script to set up the database on Render.com
# This script will:
# 1. Run the create_tables.py script to create all tables
# 2. Run the migrate_existing_documents.py script to migrate existing documents

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

echo -e "${YELLOW}=== DATABASE SETUP FOR RENDER.COM ===${NC}"

# Step 1: Run create_tables.py
echo -e "\n${YELLOW}1. Creating database tables...${NC}"
python create_tables.py

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create database tables. Check the logs for details.${NC}"
    exit 1
fi

echo -e "${GREEN}Database tables created successfully.${NC}"

# Step 2: Run alembic migrations
echo -e "\n${YELLOW}2. Running alembic migrations...${NC}"
python -m alembic upgrade head

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to run alembic migrations. Check the logs for details.${NC}"
    echo -e "${YELLOW}Continuing with document migration...${NC}"
else
    echo -e "${GREEN}Alembic migrations completed successfully.${NC}"
fi

# Step 3: Migrate existing documents
echo -e "\n${YELLOW}3. Migrating existing documents...${NC}"
python migrate_existing_documents.py

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to migrate documents. Check the logs for details.${NC}"
    exit 1
fi

echo -e "${GREEN}Document migration completed successfully.${NC}"

# Step 4: Verify database setup
echo -e "\n${YELLOW}4. Verifying database setup...${NC}"
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
            
            # Check document count
            result = conn.execute(text('SELECT COUNT(*) FROM documents'))
            doc_count = result.scalar()
            print(f'Document count: {doc_count}')
            
            # Check chunk count
            result = conn.execute(text('SELECT COUNT(*) FROM document_chunks'))
            chunk_count = result.scalar()
            print(f'Document chunk count: {chunk_count}')
        else:
            print('\\nDocument tables not found!')
            sys.exit(1)
    
    print('\\nDatabase verification successful!')
    sys.exit(0)
except SQLAlchemyError as e:
    print(f'Database verification failed: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}Database verification failed. Check the logs for details.${NC}"
    exit 1
fi

echo -e "\n${GREEN}=== DATABASE SETUP COMPLETED SUCCESSFULLY ===${NC}"
echo -e "Your database is now ready to use with the improved document storage system."
echo -e "You can now start your application with:"
echo -e "${BLUE}uvicorn app.main:app --host 0.0.0.0 --port \$PORT${NC}"
