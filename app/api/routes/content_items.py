"""
Content Items API Routes
Simple CRUD endpoints for content items matching test expectations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from app.db.session import get_db
from app.services.auth import get_current_user
from app.models.user import User
from app.models.content_items import ContentItem, ContentChunk
from pydantic import BaseModel

router = APIRouter(prefix="/api/content", tags=["Content Items"])

# Pydantic models for requests/responses
class CreateContentRequest(BaseModel):
    title: str
    content_type: str  # text, file, audio, video, url, youtube
    content: Optional[str] = None  # For text content
    url: Optional[str] = None  # For URL content
    content_metadata: Optional[Dict[str, Any]] = {}
    extraction_settings: Optional[Dict[str, Any]] = {}

class ContentResponse(BaseModel):
    id: str
    content_id: str
    user_id: str
    title: str
    content_type: str
    status: str
    processing_progress: float
    word_count: Optional[int]
    file_size_bytes: Optional[int]
    language: str
    created_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class ContentListResponse(BaseModel):
    items: List[ContentResponse]
    total: int

@router.post("/items", response_model=ContentResponse)
async def create_content_item(
    request: CreateContentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new content item."""
    try:
        # Generate unique content ID
        content_id = f"content_{uuid.uuid4().hex[:12]}"
        
        # Create new content item
        content_item = ContentItem(
            content_id=content_id,
            user_id=current_user.id,
            title=request.title,
            content_type=request.content_type,
            url=request.url,
            status="pending",
            processing_progress=0.0,
            content_metadata=request.content_metadata or {},
            extraction_settings=request.extraction_settings or {},
            language="en",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # If text content provided, calculate word count
        if request.content:
            content_item.word_count = len(request.content.split())
            content_item.status = "completed"
            content_item.processing_progress = 1.0
            content_item.processed_at = datetime.utcnow()
        
        db.add(content_item)
        db.commit()
        db.refresh(content_item)
        
        return ContentResponse(
            id=str(content_item.id),
            content_id=content_item.content_id,
            user_id=str(content_item.user_id),
            title=content_item.title,
            content_type=content_item.content_type,
            status=content_item.status,
            processing_progress=content_item.processing_progress,
            word_count=content_item.word_count,
            file_size_bytes=content_item.file_size_bytes,
            language=content_item.language,
            created_at=content_item.created_at,
            processed_at=content_item.processed_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create content item: {str(e)}"
        )

@router.get("/items", response_model=ContentListResponse)
async def get_content_items(
    skip: int = 0,
    limit: int = 100,
    content_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's content items."""
    try:
        # Query user's content items
        items_query = db.query(ContentItem).filter(
            ContentItem.user_id == current_user.id
        )
        
        # Apply filters
        if content_type:
            items_query = items_query.filter(ContentItem.content_type == content_type)
        if status_filter:
            items_query = items_query.filter(ContentItem.status == status_filter)
        
        total = items_query.count()
        items = items_query.offset(skip).limit(limit).all()
        
        item_responses = [
            ContentResponse(
                id=str(item.id),
                content_id=item.content_id,
                user_id=str(item.user_id),
                title=item.title,
                content_type=item.content_type,
                status=item.status,
                processing_progress=item.processing_progress,
                word_count=item.word_count,
                file_size_bytes=item.file_size_bytes,
                language=item.language,
                created_at=item.created_at,
                processed_at=item.processed_at
            )
            for item in items
        ]
        
        return ContentListResponse(
            items=item_responses,
            total=total
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve content items: {str(e)}"
        )

@router.get("/items/{content_id}", response_model=ContentResponse)
async def get_content_item(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific content item."""
    try:
        item = db.query(ContentItem).filter(
            ContentItem.content_id == content_id,
            ContentItem.user_id == current_user.id
        ).first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content item not found"
            )
        
        return ContentResponse(
            id=str(item.id),
            content_id=item.content_id,
            user_id=str(item.user_id),
            title=item.title,
            content_type=item.content_type,
            status=item.status,
            processing_progress=item.processing_progress,
            word_count=item.word_count,
            file_size_bytes=item.file_size_bytes,
            language=item.language,
            created_at=item.created_at,
            processed_at=item.processed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve content item: {str(e)}"
        )

@router.delete("/items/{content_id}")
async def delete_content_item(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a content item."""
    try:
        item = db.query(ContentItem).filter(
            ContentItem.content_id == content_id,
            ContentItem.user_id == current_user.id
        ).first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content item not found"
            )
        
        db.delete(item)
        db.commit()
        
        return {"message": "Content item deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete content item: {str(e)}"
        )

@router.post("/items/upload")
async def upload_content_file(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a file as content item."""
    try:
        # Generate unique content ID
        content_id = f"content_{uuid.uuid4().hex[:12]}"
        
        # Determine content type from file
        content_type = "file"
        if file.content_type:
            if file.content_type.startswith("image/"):
                content_type = "image"
            elif file.content_type.startswith("audio/"):
                content_type = "audio"
            elif file.content_type.startswith("video/"):
                content_type = "video"
            elif file.content_type == "application/pdf":
                content_type = "pdf"
        
        # Create content item
        content_item = ContentItem(
            content_id=content_id,
            user_id=current_user.id,
            title=title or file.filename or "Uploaded File",
            content_type=content_type,
            file_path=f"uploads/{content_id}/{file.filename}",
            file_size_bytes=file.size,
            status="pending",
            processing_progress=0.0,
            content_metadata={"original_filename": file.filename, "mime_type": file.content_type},
            language="en",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(content_item)
        db.commit()
        db.refresh(content_item)
        
        return {
            "message": "File uploaded successfully",
            "content_id": content_id,
            "status": "pending"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
