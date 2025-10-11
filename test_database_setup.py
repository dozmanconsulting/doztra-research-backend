#!/usr/bin/env python3
"""
Test script to verify database setup for document storage.
"""
import os
import sys
import logging
from sqlalchemy import inspect, text

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_setup():
    """Test database setup for document storage."""
    try:
        # Import database session
        from app.db.session import SessionLocal, engine
        
        # Create a session
        db = SessionLocal()
        
        try:
            # Check if database is accessible
            result = db.execute(text("SELECT 1")).scalar()
            logger.info(f"Database connection successful: {result}")
            
            # Get inspector
            inspector = inspect(engine)
            
            # Check if document tables exist
            tables = inspector.get_table_names()
            logger.info(f"Found tables: {tables}")
            
            # Check for document tables
            required_tables = ["documents", "document_chunks"]
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                logger.error(f"Missing required tables: {missing_tables}")
                logger.error("Run 'python -m alembic upgrade head' to create missing tables")
                return False
            
            # Check document table columns
            doc_columns = [col["name"] for col in inspector.get_columns("documents")]
            logger.info(f"Document table columns: {doc_columns}")
            
            required_columns = ["id", "user_id", "file_path", "processing_status"]
            missing_columns = [col for col in required_columns if col not in doc_columns]
            
            if missing_columns:
                logger.error(f"Missing required columns in documents table: {missing_columns}")
                return False
            
            # Check document_chunks table columns
            chunk_columns = [col["name"] for col in inspector.get_columns("document_chunks")]
            logger.info(f"Document chunks table columns: {chunk_columns}")
            
            required_chunk_columns = ["id", "document_id", "text", "embedding"]
            missing_chunk_columns = [col for col in required_chunk_columns if col not in chunk_columns]
            
            if missing_chunk_columns:
                logger.error(f"Missing required columns in document_chunks table: {missing_chunk_columns}")
                return False
            
            # Check foreign keys
            doc_fks = inspector.get_foreign_keys("documents")
            chunk_fks = inspector.get_foreign_keys("document_chunks")
            
            logger.info(f"Document foreign keys: {doc_fks}")
            logger.info(f"Document chunks foreign keys: {chunk_fks}")
            
            # All checks passed
            logger.info("All database checks passed!")
            return True
            
        except Exception as e:
            logger.error(f"Database query error: {str(e)}")
            return False
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error testing database setup: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Testing database setup...")
    success = test_database_setup()
    
    if success:
        logger.info("✅ Database setup test PASSED")
        sys.exit(0)
    else:
        logger.error("❌ Database setup test FAILED")
        sys.exit(1)
