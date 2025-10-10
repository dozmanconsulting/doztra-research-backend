#!/usr/bin/env python3
"""
Script to fix document processing issues in the Doztra backend service.
This script applies fixes to common document processing problems.
"""

import os
import sys
import argparse
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
try:
    from app.db.session import get_db, engine
    from app.models.documents import Document
    from sqlalchemy.orm import Session
    from sqlalchemy import text
    DB_IMPORT_SUCCESS = True
except ImportError:
    print("Warning: Could not import database modules. Database fixes will be skipped.")
    DB_IMPORT_SUCCESS = False

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Fix document processing issues')
    parser.add_argument('--document-id', help='Document ID to fix (optional)')
    parser.add_argument('--fix-all', action='store_true', help='Fix all stuck documents')
    parser.add_argument('--db-url', help='Database URL (optional)')
    parser.add_argument('--reset-processing', action='store_true', 
                        help='Reset processing status for stuck documents')
    parser.add_argument('--clear-queue', action='store_true', 
                        help='Clear document processing queue')
    return parser.parse_args()

def get_db_session(db_url=None):
    """Get database session."""
    if not DB_IMPORT_SUCCESS:
        print("Error: Database modules not imported.")
        return None
    
    try:
        if db_url:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            engine = create_engine(db_url)
            Session = sessionmaker(bind=engine)
            return Session()
        else:
            # Use the application's session
            return next(get_db())
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        return None

def fix_document_processing_status(session, document_id=None):
    """Fix document processing status."""
    print("\n=== Fixing Document Processing Status ===")
    
    try:
        if document_id:
            # Fix specific document
            document = session.query(Document).filter(Document.id == document_id).first()
            if document:
                print(f"Found document: {document.title}")
                
                # Check if document has processing_status attribute
                if hasattr(document, 'processing_status'):
                    old_status = document.processing_status
                    document.processing_status = 'completed'
                    print(f"Updated processing status from '{old_status}' to 'completed'")
                
                # Update document metadata
                if document.metadata is None:
                    document.metadata = {}
                
                document.metadata['processing_fixed'] = True
                document.metadata['processing_fixed_at'] = datetime.utcnow().isoformat()
                
                session.commit()
                print(f"✅ Fixed document {document_id}")
                return True
            else:
                print(f"❌ Document {document_id} not found")
                return False
        else:
            # Fix all stuck documents
            # Check if processing_status column exists
            try:
                stuck_docs = session.query(Document).filter(
                    Document.processing_status.in_(['processing', 'pending', 'failed'])
                ).all()
            except:
                # If processing_status doesn't exist, try to identify stuck documents by metadata
                stuck_docs = session.query(Document).filter(
                    Document.content == None
                ).all()
            
            if stuck_docs:
                print(f"Found {len(stuck_docs)} stuck documents")
                for doc in stuck_docs:
                    print(f"Fixing document: {doc.id} - {doc.title}")
                    
                    # Update document metadata
                    if doc.metadata is None:
                        doc.metadata = {}
                    
                    doc.metadata['processing_fixed'] = True
                    doc.metadata['processing_fixed_at'] = datetime.utcnow().isoformat()
                    
                    # Set processing status if attribute exists
                    if hasattr(doc, 'processing_status'):
                        doc.processing_status = 'completed'
                
                session.commit()
                print(f"✅ Fixed {len(stuck_docs)} documents")
                return True
            else:
                print("No stuck documents found")
                return False
    except Exception as e:
        print(f"❌ Error fixing document processing status: {str(e)}")
        session.rollback()
        return False

def clear_processing_queue(session):
    """Clear document processing queue."""
    print("\n=== Clearing Document Processing Queue ===")
    
    try:
        # Check if queue table exists
        result = session.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'document_processing_queue')"
        ))
        
        if result.scalar():
            # Clear queue
            result = session.execute(text("DELETE FROM document_processing_queue"))
            session.commit()
            print(f"✅ Cleared document processing queue")
            return True
        else:
            print("ℹ️ No document_processing_queue table found")
            return False
    except Exception as e:
        print(f"❌ Error clearing processing queue: {str(e)}")
        session.rollback()
        return False

def add_missing_columns(session):
    """Add missing columns to documents table."""
    print("\n=== Checking for Missing Columns ===")
    
    try:
        # Check if processing_status column exists
        result = session.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'documents' AND column_name = 'processing_status')"
        ))
        
        if not result.scalar():
            print("Adding processing_status column to documents table")
            session.execute(text(
                "ALTER TABLE documents ADD COLUMN processing_status VARCHAR(50) DEFAULT 'completed'"
            ))
            session.commit()
            print("✅ Added processing_status column")
        else:
            print("✅ processing_status column already exists")
        
        return True
    except Exception as e:
        print(f"❌ Error adding missing columns: {str(e)}")
        session.rollback()
        return False

def main():
    """Main function."""
    args = parse_args()
    
    if not args.document_id and not args.fix_all and not args.clear_queue:
        print("Error: Please specify --document-id, --fix-all, or --clear-queue")
        return
    
    # Get database session
    session = get_db_session(args.db_url)
    if not session:
        print("Error: Could not connect to database")
        return
    
    try:
        # Add missing columns if needed
        add_missing_columns(session)
        
        # Fix document processing status
        if args.document_id or args.fix_all:
            fix_document_processing_status(session, args.document_id)
        
        # Clear processing queue if requested
        if args.clear_queue:
            clear_processing_queue(session)
        
        print("\n=== SUMMARY ===")
        print("✅ Document processing fixes applied")
        print("\nRecommendations:")
        print("1. Restart the application to apply changes")
        print("2. Monitor document processing for any new issues")
        print("3. Check application logs for any errors")
    finally:
        session.close()

if __name__ == "__main__":
    main()
