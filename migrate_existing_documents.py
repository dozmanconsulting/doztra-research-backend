#!/usr/bin/env python3
"""
Script to migrate existing documents to the new database structure.
This script will:
1. Scan the uploads directory for existing documents
2. Create database records for each document
3. Process documents that haven't been processed yet
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
import argparse

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import project modules
from app.db.session import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.document_service import DocumentService
from app.core.config import settings

# Initialize document service
document_service = DocumentService()

async def migrate_document(user_id, document_id, file_path, db):
    """
    Migrate a single document to the database.
    
    Args:
        user_id: User ID
        document_id: Document ID
        file_path: Path to the document file
        db: Database session
    """
    try:
        # Check if document already exists in database
        existing_doc = db.query(Document).filter(Document.id == document_id).first()
        if existing_doc:
            print(f"Document {document_id} already exists in database, skipping")
            return
        
        # Get file info
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()
        
        # Determine file type
        file_type_map = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.csv': 'text/csv',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        file_type = file_type_map.get(file_ext, 'application/octet-stream')
        
        # Check if document has been processed
        chunks_file = Path(settings.DOCUMENT_CHUNKS_DIR) / f"{document_id}_chunks.json"
        processing_status = "completed" if chunks_file.exists() else "pending"
        
        # Create document record
        document = Document(
            id=document_id,
            user_id=user_id,
            title=file_name,
            original_filename=file_name,
            file_path=str(file_path),
            file_type=file_type,
            file_size=file_size,
            upload_date=datetime.fromtimestamp(os.path.getctime(file_path)),
            processing_status=processing_status,
            metadata={
                "migrated": True,
                "migration_date": datetime.utcnow().isoformat(),
                "original_path": str(file_path)
            }
        )
        
        # Add to database
        db.add(document)
        db.commit()
        
        print(f"Migrated document {document_id} to database")
        
        # If document has been processed, migrate chunks
        if processing_status == "completed":
            await migrate_document_chunks(document_id, chunks_file, db)
        else:
            print(f"Document {document_id} needs processing")
            
    except Exception as e:
        db.rollback()
        print(f"Error migrating document {document_id}: {str(e)}")

async def migrate_document_chunks(document_id, chunks_file, db):
    """
    Migrate document chunks to the database.
    
    Args:
        document_id: Document ID
        chunks_file: Path to the chunks file
        db: Database session
    """
    try:
        # Load chunks from file
        with open(chunks_file, 'r') as f:
            chunks = json.load(f)
        
        # Add chunks to database
        for i, chunk in enumerate(chunks):
            db_chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=i,
                text=chunk["text"],
                embedding=chunk.get("embedding"),
                metadata=chunk.get("metadata", {})
            )
            db.add(db_chunk)
        
        db.commit()
        print(f"Migrated {len(chunks)} chunks for document {document_id}")
        
    except Exception as e:
        db.rollback()
        print(f"Error migrating chunks for document {document_id}: {str(e)}")

async def process_pending_documents(db):
    """
    Process documents that haven't been processed yet.
    
    Args:
        db: Database session
    """
    # Get pending documents
    pending_docs = db.query(Document).filter(Document.processing_status == "pending").all()
    
    if not pending_docs:
        print("No pending documents to process")
        return
    
    print(f"Processing {len(pending_docs)} pending documents")
    
    # Process each document
    for doc in pending_docs:
        try:
            print(f"Processing document {doc.id}")
            
            # Update status to processing
            doc.processing_status = "processing"
            db.commit()
            
            # Process document
            await document_service.process_document_background(
                document_id=doc.id,
                user_id=doc.user_id,
                file_path=doc.file_path,
                file_type=doc.file_type,
                metadata=doc.metadata or {}
            )
            
            print(f"Scheduled processing for document {doc.id}")
            
        except Exception as e:
            print(f"Error processing document {doc.id}: {str(e)}")
            
            # Update status to failed
            doc.processing_status = "failed"
            doc.error_message = str(e)
            db.commit()

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Migrate existing documents to database')
    parser.add_argument('--process', action='store_true', help='Process pending documents after migration')
    args = parser.parse_args()
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Scan uploads directory
        uploads_dir = Path(settings.UPLOAD_DIR)
        if not uploads_dir.exists():
            print(f"Uploads directory {uploads_dir} does not exist")
            return
        
        print(f"Scanning uploads directory: {uploads_dir}")
        
        # Iterate through user directories
        for user_dir in uploads_dir.iterdir():
            if not user_dir.is_dir():
                continue
            
            user_id = user_dir.name
            print(f"Processing user directory: {user_id}")
            
            # Iterate through document directories
            for doc_dir in user_dir.iterdir():
                if not doc_dir.is_dir():
                    continue
                
                document_id = doc_dir.name
                print(f"Found document directory: {document_id}")
                
                # Find document file
                files = list(doc_dir.glob("*"))
                if not files:
                    print(f"No files found in document directory {document_id}")
                    continue
                
                file_path = files[0]
                print(f"Found document file: {file_path}")
                
                # Migrate document
                await migrate_document(user_id, document_id, file_path, db)
        
        # Process pending documents if requested
        if args.process:
            await process_pending_documents(db)
        
        print("Migration completed successfully")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
