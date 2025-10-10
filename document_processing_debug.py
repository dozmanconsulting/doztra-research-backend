#!/usr/bin/env python3
"""
Script to debug document processing issues in the Doztra backend service.
This script checks the document processing pipeline and identifies potential issues.
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
try:
    from app.db.session import get_db
    from app.models.documents import Document
    from app.services.documents import get_document_by_id
    import app.services.documents as doc_service
    DB_IMPORT_SUCCESS = True
except ImportError:
    print("Warning: Could not import database modules. Database checks will be skipped.")
    DB_IMPORT_SUCCESS = False

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Debug document processing issues')
    parser.add_argument('--document-id', required=True, help='Document ID to check')
    parser.add_argument('--token', required=True, help='Access token for API requests')
    parser.add_argument('--api-url', default='https://doztra-research.onrender.com', 
                        help='API base URL')
    parser.add_argument('--db-url', help='Database URL (optional)')
    return parser.parse_args()

def check_api_document_status(api_url, document_id, token):
    """Check document status via API."""
    print("\n=== Checking Document Status via API ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check document metadata
    url = f"{api_url}/api/documents/{document_id}"
    print(f"Requesting: {url}")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("✅ Document exists in the API")
        doc_data = response.json()
        print(f"Title: {doc_data.get('title', 'N/A')}")
        print(f"Created at: {doc_data.get('created_at', 'N/A')}")
        print(f"Status: {doc_data.get('status', 'N/A')}")
        return doc_data
    else:
        print(f"❌ API Error: {response.status_code}")
        print(response.text)
        return None

def check_document_content(api_url, document_id, token):
    """Check if document content is available."""
    print("\n=== Checking Document Content ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    url = f"{api_url}/api/documents/{document_id}/content"
    print(f"Requesting: {url}")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        content = response.json()
        if content and "content" in content:
            print("✅ Document content is available")
            content_length = len(content["content"])
            print(f"Content length: {content_length} characters")
            return content
        else:
            print("❌ Document content is empty or malformed")
            return None
    else:
        print(f"❌ Content Error: {response.status_code}")
        print(response.text)
        return None

def check_document_in_db(db_url, document_id):
    """Check document status in the database."""
    if not DB_IMPORT_SUCCESS:
        print("\n=== Skipping Database Check (Import Failed) ===")
        return None
    
    print("\n=== Checking Document in Database ===")
    
    try:
        # Create database connection
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Query the document
        document = session.query(Document).filter(Document.id == document_id).first()
        
        if document:
            print("✅ Document found in database")
            print(f"Title: {document.title}")
            print(f"Created at: {document.created_at}")
            print(f"Content available: {'Yes' if document.content else 'No'}")
            print(f"Metadata available: {'Yes' if document.metadata else 'No'}")
            
            # Check processing status
            if hasattr(document, 'processing_status'):
                print(f"Processing status: {document.processing_status}")
            
            return document
        else:
            print("❌ Document not found in database")
            return None
    except Exception as e:
        print(f"❌ Database Error: {str(e)}")
        return None
    finally:
        if 'session' in locals():
            session.close()

def check_document_processing_queue(db_url, document_id):
    """Check if document is in processing queue."""
    if not DB_IMPORT_SUCCESS:
        print("\n=== Skipping Queue Check (Import Failed) ===")
        return None
    
    print("\n=== Checking Document Processing Queue ===")
    
    try:
        # Create database connection
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if there's a processing queue table
        result = session.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'document_processing_queue')"
        ))
        
        if result.scalar():
            # Check if document is in queue
            result = session.execute(text(
                "SELECT * FROM document_processing_queue "
                "WHERE document_id = :document_id"
            ), {"document_id": document_id})
            
            queue_item = result.fetchone()
            if queue_item:
                print("✅ Document found in processing queue")
                print(f"Queue position: {queue_item.position if hasattr(queue_item, 'position') else 'Unknown'}")
                print(f"Status: {queue_item.status if hasattr(queue_item, 'status') else 'Unknown'}")
                print(f"Created at: {queue_item.created_at if hasattr(queue_item, 'created_at') else 'Unknown'}")
                return queue_item
            else:
                print("❌ Document not found in processing queue")
                return None
        else:
            print("ℹ️ No document_processing_queue table found")
            return None
    except Exception as e:
        print(f"❌ Queue Error: {str(e)}")
        return None
    finally:
        if 'session' in locals():
            session.close()

def check_document_processing_logs(api_url, document_id, token):
    """Check document processing logs."""
    print("\n=== Checking Document Processing Logs ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    url = f"{api_url}/api/documents/{document_id}/logs"
    print(f"Requesting: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            logs = response.json()
            if logs and len(logs) > 0:
                print("✅ Processing logs found")
                for log in logs:
                    print(f"[{log.get('timestamp', 'N/A')}] {log.get('message', 'N/A')}")
                return logs
            else:
                print("ℹ️ No processing logs found")
                return []
        else:
            print(f"ℹ️ Logs endpoint returned: {response.status_code}")
            print(response.text)
            return None
    except requests.RequestException as e:
        print(f"ℹ️ Logs endpoint not available: {str(e)}")
        return None

def test_document_query(api_url, document_id, token):
    """Test a simple query on the document."""
    print("\n=== Testing Document Query ===")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{api_url}/api/documents/query"
    data = {
        "message": "What is this document about?",
        "document_ids": [document_id]
    }
    
    print(f"Requesting: {url}")
    print(f"Query: {data['message']}")
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if "error" in result:
            print(f"❌ Query Error: {result['error']}")
        else:
            print("✅ Query successful")
            if "content" in result:
                print(f"Response: {result['content']}")
            else:
                print(f"Response: {result}")
        return result
    else:
        print(f"❌ Query Error: {response.status_code}")
        print(response.text)
        return None

def check_document_processing_code():
    """Check document processing code for issues."""
    if not DB_IMPORT_SUCCESS:
        print("\n=== Skipping Code Check (Import Failed) ===")
        return
    
    print("\n=== Checking Document Processing Code ===")
    
    # Check if document processing functions exist
    if hasattr(doc_service, 'process_document'):
        print("✅ process_document function exists")
    else:
        print("❌ process_document function not found")
    
    if hasattr(doc_service, 'extract_document_content'):
        print("✅ extract_document_content function exists")
    else:
        print("❌ extract_document_content function not found")
    
    # Check for any known issues in the code
    print("\nChecking for known issues...")
    
    # Check for potential timeout issues
    if hasattr(doc_service, 'process_document'):
        import inspect
        process_doc_code = inspect.getsource(doc_service.process_document)
        if "timeout" in process_doc_code:
            print("ℹ️ process_document has timeout settings")
        else:
            print("⚠️ process_document may not have timeout handling")

def main():
    """Main function."""
    args = parse_args()
    
    print(f"Document ID: {args.document_id}")
    print(f"API URL: {args.api_url}")
    
    # Check document status via API
    doc_data = check_api_document_status(args.api_url, args.document_id, args.token)
    
    # Check document content
    content_data = check_document_content(args.api_url, args.document_id, args.token)
    
    # Check document in database (if DB URL provided)
    if args.db_url:
        db_doc = check_document_in_db(args.db_url, args.document_id)
        queue_item = check_document_processing_queue(args.db_url, args.document_id)
    
    # Check document processing logs
    logs = check_document_processing_logs(args.api_url, args.document_id, args.token)
    
    # Test document query
    query_result = test_document_query(args.api_url, args.document_id, args.token)
    
    # Check document processing code
    if DB_IMPORT_SUCCESS:
        check_document_processing_code()
    
    # Print summary
    print("\n=== SUMMARY ===")
    if doc_data:
        print("✅ Document exists in API")
    else:
        print("❌ Document not found in API")
    
    if content_data:
        print("✅ Document content is available")
    else:
        print("❌ Document content is not available")
    
    if query_result and "error" not in query_result:
        print("✅ Document query works")
    else:
        print("❌ Document query fails")
    
    print("\n=== RECOMMENDATIONS ===")
    if not doc_data:
        print("- Check if the document ID is correct")
        print("- Verify that the document was uploaded successfully")
    elif not content_data:
        print("- The document exists but content is not available")
        print("- Check document processing logs for errors")
        print("- Verify that the document processing service is running")
        print("- Try re-uploading the document")
    elif not query_result or "error" in query_result:
        print("- Document and content exist but querying fails")
        print("- Check if the document has been properly indexed")
        print("- Verify that the query service is running")
        print("- Check for any errors in the query service logs")

if __name__ == "__main__":
    main()
