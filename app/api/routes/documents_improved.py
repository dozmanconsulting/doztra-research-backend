"""
Improved API routes for document management and processing.
This implementation uses the new document service and database models.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from uuid import uuid4
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.models.user import User
from app.db.session import get_db
from app.services.document_service import DocumentService
from app.core.config import settings

router = APIRouter()
document_service = DocumentService()

# Allowed file types
ALLOWED_FILE_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
    "text/csv": ".csv",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp"
}


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    conversation_id: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a document for processing.
    """
    try:
        # Validate file type
        if file.content_type not in ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}. Supported types: {', '.join(ALLOWED_FILE_TYPES.keys())}"
            )
            
        # Generate document ID
        document_id = f"doc-{uuid4()}"
        
        # Parse metadata if provided
        meta_dict = {}
        if metadata:
            import json
            try:
                meta_dict = json.loads(metadata)
            except:
                # If JSON parsing fails, use as-is
                meta_dict = {"raw_metadata": metadata}
                
        # Add basic metadata
        meta_dict.update({
            "original_filename": file.filename,
            "content_type": file.content_type,
            "upload_date": str(status.datetime.now().isoformat()),
            "user_id": str(current_user.id),
            "conversation_id": conversation_id,
            "title": title or file.filename
        })
        
        # Upload document
        document = await document_service.upload_document(
            db=db,
            file=file,
            user_id=str(current_user.id),
            document_id=document_id,
            background_tasks=background_tasks,
            metadata=meta_dict
        )
        
        # Return immediate response
        return {
            "document_id": document.id,
            "file_name": document.original_filename,
            "file_type": document.file_type,
            "file_size": document.file_size,
            "upload_date": document.upload_date.isoformat(),
            "status": document.processing_status,
            "message": "Document uploaded successfully and queued for processing."
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload failed: {str(e)}")


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get document metadata.
    """
    try:
        # Get document
        document = await document_service.get_document(db, document_id, str(current_user.id))
        
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
            
        # Return document metadata
        return {
            "document_id": document.id,
            "file_name": document.original_filename,
            "file_size": document.file_size,
            "upload_date": document.upload_date.isoformat(),
            "status": document.processing_status,
            "error": document.error_message if document.processing_status == "failed" else None,
            "user_id": document.user_id,
            "metadata": document.metadata
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get document: {str(e)}")


@router.get("")
async def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all documents for the current user.
    """
    try:
        # Get all documents
        documents = await document_service.list_documents(db, str(current_user.id))
        
        # Format response
        result = []
        for doc in documents:
            result.append({
                "document_id": doc.id,
                "file_name": doc.original_filename,
                "file_size": doc.file_size,
                "upload_date": doc.upload_date.isoformat(),
                "status": doc.processing_status,
                "title": doc.title or doc.original_filename
            })
            
        return {"documents": result}
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list documents: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a document.
    """
    try:
        # Delete document
        success = await document_service.delete_document(db, document_id, str(current_user.id))
        
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
            
        return {"message": "Document deleted successfully"}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete document: {str(e)}")


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the extracted text content of a document.
    """
    try:
        # Get document content
        content = await document_service.get_document_content(db, document_id, str(current_user.id))
        
        if not content:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
            
        # Check if document is still processing
        if content.get("status") == "processing":
            return {
                "document_id": document_id,
                "status": "processing",
                "message": "Document is still being processed"
            }
            
        # Check if document processing failed
        if content.get("status") == "failed":
            return {
                "document_id": document_id,
                "status": "failed",
                "error": content.get("error"),
                "message": "Document processing failed"
            }
            
        return content
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get document content: {str(e)}")
