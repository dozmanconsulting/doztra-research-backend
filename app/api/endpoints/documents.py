"""
API endpoints for document management and processing.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from uuid import uuid4
import os
import shutil
from datetime import datetime
import tempfile
from pathlib import Path

from app.core.auth import get_current_user
from app.models.user import User
from app.services import openai_service
from app.core.config import settings

router = APIRouter(prefix="/documents", tags=["documents"])

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

# Create temp directory for document storage
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a document for processing.
    """
    try:
        # Validate file type
        if file.content_type not in ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. Supported types: {', '.join(ALLOWED_FILE_TYPES.keys())}"
            )
            
        # Generate document ID
        document_id = f"doc-{uuid4()}"
        
        # Create user directory if it doesn't exist
        user_dir = UPLOAD_DIR / current_user.id
        user_dir.mkdir(exist_ok=True)
        
        # Create document directory
        doc_dir = user_dir / document_id
        doc_dir.mkdir(exist_ok=True)
        
        # Save file with original name
        file_extension = ALLOWED_FILE_TYPES[file.content_type]
        original_filename = file.filename or f"document{file_extension}"
        file_path = doc_dir / original_filename
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
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
            "original_filename": original_filename,
            "content_type": file.content_type,
            "upload_date": datetime.now().isoformat(),
            "user_id": current_user.id,
            "conversation_id": conversation_id
        })
        
        # Schedule background processing
        background_tasks.add_task(
            process_document_background,
            str(file_path),
            file.content_type,
            document_id,
            current_user.id,
            meta_dict
        )
        
        # Return immediate response
        return {
            "document_id": document_id,
            "file_name": original_filename,
            "file_type": file.content_type,
            "file_size": os.path.getsize(file_path),
            "upload_date": meta_dict["upload_date"],
            "status": "uploaded",
            "message": "Document uploaded successfully and queued for processing."
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get document metadata.
    """
    try:
        # Check if document exists
        user_dir = UPLOAD_DIR / current_user.id
        doc_dir = user_dir / document_id
        
        if not doc_dir.exists():
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Get document metadata
        # In a real implementation, this would come from a database
        # For now, we'll check the processing status based on file existence
        
        # Find the original file
        files = list(doc_dir.glob("*"))
        if not files:
            raise HTTPException(status_code=404, detail="Document file not found")
            
        original_file = files[0]
        
        # Check if processing is complete
        chunks_dir = Path("./document_chunks")
        chunks_file = chunks_dir / f"{document_id}_chunks.json"
        
        status = "processing"
        if chunks_file.exists():
            status = "ready"
            
        # Return document metadata
        return {
            "document_id": document_id,
            "file_name": original_file.name,
            "file_size": os.path.getsize(original_file),
            "upload_date": datetime.fromtimestamp(os.path.getctime(original_file)).isoformat(),
            "status": status,
            "user_id": current_user.id
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.get("")
async def list_documents(
    current_user: User = Depends(get_current_user)
):
    """
    List all documents for the current user.
    """
    try:
        # Check if user directory exists
        user_dir = UPLOAD_DIR / current_user.id
        if not user_dir.exists():
            return {"documents": []}
            
        # Get all document directories
        documents = []
        for doc_dir in user_dir.iterdir():
            if doc_dir.is_dir():
                document_id = doc_dir.name
                
                # Find the original file
                files = list(doc_dir.glob("*"))
                if not files:
                    continue
                    
                original_file = files[0]
                
                # Check if processing is complete
                chunks_dir = Path("./document_chunks")
                chunks_file = chunks_dir / f"{document_id}_chunks.json"
                
                status = "processing"
                if chunks_file.exists():
                    status = "ready"
                    
                # Add document metadata
                documents.append({
                    "document_id": document_id,
                    "file_name": original_file.name,
                    "file_size": os.path.getsize(original_file),
                    "upload_date": datetime.fromtimestamp(os.path.getctime(original_file)).isoformat(),
                    "status": status
                })
                
        return {"documents": documents}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a document.
    """
    try:
        # Check if document exists
        user_dir = UPLOAD_DIR / current_user.id
        doc_dir = user_dir / document_id
        
        if not doc_dir.exists():
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Delete document directory
        shutil.rmtree(doc_dir)
        
        # Delete chunks file if it exists
        chunks_dir = Path("./document_chunks")
        chunks_file = chunks_dir / f"{document_id}_chunks.json"
        if chunks_file.exists():
            chunks_file.unlink()
            
        return {"message": "Document deleted successfully"}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.post("/{document_id}/analyze")
async def analyze_document_endpoint(
    document_id: str,
    analysis_type: str = "summary",
    current_user: User = Depends(get_current_user)
):
    """
    Analyze a document (generate summary, extract key points, etc.).
    """
    try:
        # Check if document exists and is processed
        chunks_dir = Path("./document_chunks")
        chunks_file = chunks_dir / f"{document_id}_chunks.json"
        
        if not chunks_file.exists():
            raise HTTPException(status_code=404, detail="Document not found or not yet processed")
            
        # Call analysis function
        result = await openai_service.analyze_document(
            document_id=document_id,
            user_id=current_user.id,
            analysis_type=analysis_type
        )
        
        return result
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the extracted text content of a document.
    """
    try:
        # Check if document exists and is processed
        chunks_dir = Path("./document_chunks")
        chunks_file = chunks_dir / f"{document_id}_chunks.json"
        
        if not chunks_file.exists():
            raise HTTPException(status_code=404, detail="Document not found or not yet processed")
            
        # Get document chunks
        chunks = await openai_service.get_document_chunks(document_id, current_user.id)
        
        # Combine chunks into full text
        full_text = "\n\n".join([chunk["text"] for chunk in chunks])
        
        return {
            "document_id": document_id,
            "content": full_text,
            "chunk_count": len(chunks)
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document content: {str(e)}")


# Background processing function
async def process_document_background(file_path: str, file_type: str, document_id: str, user_id: str, metadata: Dict[str, Any]):
    """
    Process document in the background.
    """
    try:
        await openai_service.process_document(
            file_path=file_path,
            file_type=file_type,
            document_id=document_id,
            user_id=user_id,
            metadata=metadata
        )
    except Exception as e:
        # Log error but don't raise (background task)
        import logging
        logging.error(f"Background processing failed for document {document_id}: {str(e)}")
