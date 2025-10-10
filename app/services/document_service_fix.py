"""
Fix for document query service to properly handle non-existent documents.
This module contains functions to check document existence before processing queries.
"""

import os
from pathlib import Path
import logging
from typing import List, Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

async def check_document_exists(document_id: str, user_id: str) -> Dict[str, Any]:
    """
    Check if a document exists and is accessible to the user.
    
    Args:
        document_id: ID of the document to check
        user_id: ID of the user requesting access
        
    Returns:
        Dict[str, Any]: Status information about the document
    """
    try:
        # Check if document exists in the database
        from app.db.session import get_db
        from app.models.documents import Document
        from sqlalchemy.orm import Session
        
        db = next(get_db())
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == user_id
        ).first()
        
        if not document:
            return {
                "exists": False,
                "status": "not_found",
                "message": f"Document with ID {document_id} not found"
            }
        
        # Check if document is processed
        chunks_dir = Path("./document_chunks")
        chunks_file = chunks_dir / f"{document_id}_chunks.json"
        
        if not chunks_file.exists():
            return {
                "exists": True,
                "status": "processing",
                "message": f"Document with ID {document_id} is still being processed"
            }
        
        return {
            "exists": True,
            "status": "ready",
            "message": "Document is ready for querying"
        }
        
    except Exception as e:
        logger.error(f"Error checking document existence: {str(e)}")
        return {
            "exists": False,
            "status": "error",
            "message": f"Error checking document: {str(e)}"
        }

async def validate_documents(document_ids: List[str], user_id: str) -> Dict[str, Any]:
    """
    Validate a list of document IDs to ensure they exist and are accessible.
    
    Args:
        document_ids: List of document IDs to validate
        user_id: ID of the user requesting access
        
    Returns:
        Dict[str, Any]: Validation results including lists of valid, missing, and processing documents
    """
    if not document_ids:
        return {
            "valid": True,
            "valid_documents": [],
            "missing_documents": [],
            "processing_documents": []
        }
    
    valid_documents = []
    missing_documents = []
    processing_documents = []
    
    for doc_id in document_ids:
        status = await check_document_exists(doc_id, user_id)
        
        if status["exists"] and status["status"] == "ready":
            valid_documents.append(doc_id)
        elif status["exists"] and status["status"] == "processing":
            processing_documents.append(doc_id)
        else:
            missing_documents.append(doc_id)
    
    return {
        "valid": len(missing_documents) == 0 and len(processing_documents) == 0,
        "valid_documents": valid_documents,
        "missing_documents": missing_documents,
        "processing_documents": processing_documents
    }
