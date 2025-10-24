"""
Content Items API Routes
Handles content management for the knowledge base with advanced processing
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import json
import os
import tempfile
import aiofiles

from app.db.session import get_db
from app.services.auth import get_current_user
from app.models.user import User
from app.models.content_items import ContentItem, ContentChunk
from pydantic import BaseModel

# Import all processing services
from app.services.audio_transcription import audio_service
from app.services.web_scraping import web_scraping_service
from app.services.document_processing import document_processor
from app.services.vector_search import vector_service
from app.services.youtube_processing import youtube_processor

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
            source_url=request.url,
            processing_status="pending",
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
            content_item.processing_status = "completed"
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
            status=content_item.processing_status,
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
            items_query = items_query.filter(ContentItem.processing_status == status_filter)
        
        total = items_query.count()
        items = items_query.offset(skip).limit(limit).all()
        
        item_responses = [
            ContentResponse(
                id=str(item.id),
                content_id=item.content_id,
                user_id=str(item.user_id),
                title=item.title,
                content_type=item.content_type,
                status=item.processing_status,
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
            status=item.processing_status,
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
            processing_status="pending",
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

# Advanced Processing Endpoints

@router.post("/items/{content_id}/process")
async def process_content_item(
    content_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process content item with advanced extraction"""
    try:
        item = db.query(ContentItem).filter(
            ContentItem.content_id == content_id,
            ContentItem.user_id == current_user.id
        ).first()
        
        if not item:
            raise HTTPException(status_code=404, detail="Content item not found")
        
        # Add background processing task
        background_tasks.add_task(
            process_content_background,
            content_id,
            str(current_user.id),
            item.content_type
        )
        
        # Update status to processing
        item.processing_status = "processing"
        item.processing_progress = 0.1
        item.updated_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Processing started", "content_id": content_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")

@router.post("/items/process-url")
async def process_url_content(
    request: CreateContentRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process URL content with web scraping"""
    if not request.url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    try:
        # Generate unique content ID
        content_id = f"content_{uuid.uuid4().hex[:12]}"
        
        # Determine if it's a YouTube URL
        content_type = "url"
        if "youtube.com" in request.url or "youtu.be" in request.url:
            content_type = "youtube"
        
        # Create content item
        content_item = ContentItem(
            content_id=content_id,
            user_id=current_user.id,
            title=request.title,
            content_type=content_type,
            source_url=request.url,
            processing_status="processing",
            processing_progress=0.1,
            content_metadata=request.content_metadata or {},
            extraction_settings=request.extraction_settings or {},
            language="en",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(content_item)
        db.commit()
        db.refresh(content_item)
        
        # Start background processing
        background_tasks.add_task(
            process_url_background,
            content_id,
            request.url,
            str(current_user.id),
            content_type
        )
        
        return {
            "message": "URL processing started",
            "content_id": content_id,
            "status": "processing"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process URL: {str(e)}")

@router.post("/items/transcribe-audio")
async def transcribe_audio_content(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Transcribe audio file using AssemblyAI"""
    try:
        # Validate audio file
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Generate unique content ID
        content_id = f"content_{uuid.uuid4().hex[:12]}"
        
        # Create content item
        content_item = ContentItem(
            content_id=content_id,
            user_id=current_user.id,
            title=title or f"Audio Transcription - {file.filename}",
            content_type="audio",
            file_path=f"uploads/{content_id}/{file.filename}",
            file_size_bytes=file.size,
            processing_status="processing",
            processing_progress=0.1,
            content_metadata={
                "original_filename": file.filename,
                "mime_type": file.content_type,
                "transcription_service": "assemblyai"
            },
            language="en",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(content_item)
        db.commit()
        db.refresh(content_item)
        
        # Save uploaded file temporarily
        temp_file_path = f"/tmp/{content_id}_{file.filename}"
        async with aiofiles.open(temp_file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Start background transcription
        background_tasks.add_task(
            transcribe_audio_background,
            content_id,
            temp_file_path,
            str(current_user.id)
        )
        
        return {
            "message": "Audio transcription started",
            "content_id": content_id,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to start transcription: {str(e)}")

@router.get("/items/{content_id}/search")
async def search_content_vectors(
    content_id: str,
    query: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search within specific content using vector similarity"""
    try:
        # Verify content exists and belongs to user
        item = db.query(ContentItem).filter(
            ContentItem.content_id == content_id,
            ContentItem.user_id == current_user.id
        ).first()
        
        if not item:
            raise HTTPException(status_code=404, detail="Content item not found")
        
        # Search vectors
        results = await vector_service.search_similar(
            query=query,
            user_id=str(current_user.id),
            limit=limit,
            content_type=item.content_type
        )
        
        # Filter results for this specific content
        filtered_results = [
            result for result in results 
            if result.get("content_id") == content_id
        ]
        
        return {
            "content_id": content_id,
            "query": query,
            "results": filtered_results,
            "total_matches": len(filtered_results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# ---------------------------------------------------------------------------
# Helper utilities for content chunking and persistence
# ---------------------------------------------------------------------------
def _split_into_chunks(text: str, max_chars: int = 1800):
    """Split long text into reasonably sized chunks while preserving sentence boundaries.
    Fallbacks to hard splits if punctuation-aware splitting isn't sufficient.
    """
    if not text:
        return []

    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        # Try to break at the last period/newline within window
        window = text[start:end]
        split_at = max(window.rfind(". "), window.rfind("\n"), window.rfind("! "), window.rfind("? "))
        if split_at == -1 or (end == len(text)):
            chunk = window
            next_start = end
        else:
            chunk = window[: split_at + 1]
            next_start = start + split_at + 1
        chunks.append(chunk.strip())
        start = next_start
    return [c for c in chunks if c]


def _save_chunks_for_item(db: Session, item: ContentItem, processed_content: str):
    """Persist processed content into ContentChunk rows even if vector DB is unavailable."""
    if not processed_content:
        return

    # Remove any existing chunks to avoid duplication on re-processing
    existing = db.query(ContentChunk).filter(ContentChunk.content_item_id == item.id).all()
    if existing:
        for ch in existing:
            db.delete(ch)
        db.flush()

    pieces = _split_into_chunks(processed_content)
    for idx, piece in enumerate(pieces):
        chunk = ContentChunk(
            chunk_id=f"chunk_{item.content_id}_{idx}",
            content_item_id=item.id,
            text=piece,
            chunk_index=idx,
            word_count=len(piece.split()),
            chunk_metadata={
                "source_url": item.source_url,
                "content_type": item.content_type,
                "title": item.title,
            },
        )
        db.add(chunk)
    db.commit()

@router.get("/search")
async def search_all_content(
    query: str,
    content_types: Optional[List[str]] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Search across all user content using vector similarity"""
    try:
        # Perform hybrid search
        results = await vector_service.hybrid_search(
            query=query,
            user_id=str(current_user.id),
            content_types=content_types,
            limit=limit
        )
        
        return {
            "query": query,
            "results": results,
            "total_matches": len(results),
            "content_types_searched": content_types or "all"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Background Processing Functions

async def process_content_background(content_id: str, user_id: str, content_type: str):
    """Background task for processing content"""
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        item = db.query(ContentItem).filter(
            ContentItem.content_id == content_id
        ).first()
        
        if not item:
            return
        
        # Update progress
        item.processing_progress = 0.3
        item.updated_at = datetime.utcnow()
        db.commit()
        
        processed_content = ""
        
        # Process based on content type
        if content_type == "file" and item.file_path:
            # Process document
            result = await document_processor.process_document(item.file_path)
            if result.get("success"):
                processed_content = result.get("content", "")
                item.word_count = result.get("word_count", 0)
                item.content_metadata.update(result.get("metadata", {}))
        
        # Update progress
        item.processing_progress = 0.7
        db.commit()
        
        # Persist chunks regardless of vector availability
        if processed_content:
            _save_chunks_for_item(db, item, processed_content)
            # Best-effort vector addition (optional)
            try:
                await vector_service.add_content(
                    content_id=content_id,
                    user_id=user_id,
                    content_type=content_type,
                    title=item.title,
                    content=processed_content,
                    metadata=item.content_metadata
                )
            except Exception:
                # Vector DB is optional; continue gracefully
                pass
        
        # Mark as completed
        item.processing_status = "completed"
        item.processing_progress = 1.0
        item.processed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        # Mark as failed
        item.processing_status = "failed"
        item.content_metadata["error"] = str(e)
        db.commit()
    finally:
        db.close()

# ---------------------------------------------------------------------------
# Retrieval endpoints for content chunks and quick user context
# ---------------------------------------------------------------------------

@router.get("/items/{content_id}/chunks")
async def get_item_chunks(
    content_id: str,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve stored chunks for a specific content item."""
    item = db.query(ContentItem).filter(
        ContentItem.content_id == content_id,
        ContentItem.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")

    chunks = (
        db.query(ContentChunk)
        .filter(ContentChunk.content_item_id == item.id)
        .order_by(ContentChunk.chunk_index.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "content_id": content_id,
        "title": item.title,
        "content_type": item.content_type,
        "chunks": [
            {
                "chunk_id": str(ch.id),
                "index": ch.chunk_index,
                "text": ch.text,
                "word_count": ch.word_count,
            }
            for ch in chunks
        ],
        "total_chunks": db.query(ContentChunk).filter(ContentChunk.content_item_id == item.id).count(),
    }


@router.get("/context")
async def get_user_context(
    limit: int = 8,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return the latest chunk snippets across the user's completed content items.
    Useful for building chat context when vector search is unavailable.
    """
    # Join chunks with content items, filter by user and completed status
    q = (
        db.query(ContentChunk, ContentItem)
        .join(ContentItem, ContentChunk.content_item_id == ContentItem.id)
        .filter(ContentItem.user_id == current_user.id)
        .filter(ContentItem.processing_status == "completed")
        .order_by(ContentChunk.created_at.desc())
        .limit(limit)
    )

    rows = q.all()
    results = []
    for ch, it in rows:
        snippet = ch.text if len(ch.text) <= 700 else ch.text[:700] + "..."
        results.append(
            {
                "content_id": it.content_id,
                "title": it.title,
                "content_type": it.content_type,
                "chunk_index": ch.chunk_index,
                "text": snippet,
            }
        )

    return {"items": results, "total": len(results)}

async def process_url_background(content_id: str, url: str, user_id: str, content_type: str):
    """Background task for processing URLs"""
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        item = db.query(ContentItem).filter(
            ContentItem.content_id == content_id
        ).first()
        
        if not item:
            return
        
        processed_content = ""
        
        if content_type == "youtube":
            # Process YouTube video
            result = await youtube_processor.process_youtube_video(url)
            if not result.get("error"):
                processed_content = result.get("extracted_content", "")
                item.word_count = result.get("word_count", 0)
                item.content_metadata.update({
                    "video_metadata": result.get("metadata", {}),
                    "transcript_data": result.get("transcript", {})
                })
        else:
            # Process regular URL
            result = await web_scraping_service.scrape_url(url)
            content_data = web_scraping_service.extract_content_data(result)
            processed_content = content_data.get("content", "")
            item.word_count = content_data.get("text_length", 0) // 5  # Rough word estimate
            item.content_metadata.update(content_data.get("metadata", {}))
        
        # Update progress
        item.processing_progress = 0.7
        db.commit()
        
        # Persist chunks regardless of vector availability
        if processed_content:
            _save_chunks_for_item(db, item, processed_content)
            # Best-effort vector addition (optional)
            try:
                await vector_service.add_content(
                    content_id=content_id,
                    user_id=user_id,
                    content_type=content_type,
                    title=item.title,
                    content=processed_content,
                    metadata=item.content_metadata
                )
            except Exception:
                pass
        
        # Mark as completed
        item.processing_status = "completed"
        item.processing_progress = 1.0
        item.processed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        # Mark as failed
        item.processing_status = "failed"
        item.content_metadata["error"] = str(e)
        db.commit()
    finally:
        db.close()

async def transcribe_audio_background(content_id: str, file_path: str, user_id: str):
    """Background task for audio transcription"""
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        item = db.query(ContentItem).filter(
            ContentItem.content_id == content_id
        ).first()
        
        if not item:
            return
        
        # Update progress
        item.processing_progress = 0.3
        db.commit()
        
        # Transcribe audio
        result = await audio_service.transcribe_from_file(file_path)
        transcript_data = audio_service.extract_transcript_data(result)
        
        processed_content = transcript_data.get("text", "")
        item.word_count = len(processed_content.split())
        item.content_metadata.update({
            "transcription_data": transcript_data,
            "confidence": transcript_data.get("confidence", 0),
            "speakers": transcript_data.get("speakers", []),
            "sentiment": transcript_data.get("sentiment", [])
        })
        
        # Update progress
        item.processing_progress = 0.7
        db.commit()
        
        # Persist chunks regardless of vector availability
        if processed_content:
            _save_chunks_for_item(db, item, processed_content)
            # Best-effort vector addition (optional)
            try:
                await vector_service.add_content(
                    content_id=content_id,
                    user_id=user_id,
                    content_type="audio",
                    title=item.title,
                    content=processed_content,
                    metadata=item.content_metadata
                )
            except Exception:
                pass
        
        # Mark as completed
        item.processing_status = "completed"
        item.processing_progress = 1.0
        item.processed_at = datetime.utcnow()
        db.commit()
        
        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)
        
    except Exception as e:
        # Mark as failed
        item.processing_status = "failed"
        item.content_metadata["error"] = str(e)
        db.commit()
        
        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)
    finally:
        db.close()
