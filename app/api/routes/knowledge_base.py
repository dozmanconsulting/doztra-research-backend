"""
Multi-Modal Knowledge Base API Routes
Handles content ingestion, processing, and querying for the unified knowledge base system.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
import json
from datetime import datetime

from app.db.session import get_db
from app.services.auth import get_current_user
from app.models.user import User
from app.schemas.knowledge_base import (
    ContentIngestRequest,
    ContentIngestResponse,
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
    ContentItem,
    SearchResult,
    ProcessingStatus
)
from app.services.knowledge_base import (
    KnowledgeBaseService,
    ContentProcessor,
    VectorStore,
    ConversationMemory
)

router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge Base"])

# Initialize services
kb_service = KnowledgeBaseService()
content_processor = ContentProcessor()
vector_store = VectorStore()
conversation_memory = ConversationMemory()


@router.post("/ingest/text", response_model=ContentIngestResponse)
async def ingest_text_content(
    request: ContentIngestRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ingest text content directly into the knowledge base.
    """
    try:
        content_id = str(uuid.uuid4())
        
        # Create content item record
        content_item = await kb_service.create_content_item(
            db=db,
            user_id=current_user.id,
            content_id=content_id,
            content_type="text",
            title=request.title,
            content=request.content,
            metadata=request.metadata or {}
        )
        
        # Queue background processing
        background_tasks.add_task(
            content_processor.process_text_content,
            content_id=content_id,
            content=request.content,
            metadata=request.metadata or {}
        )
        
        return ContentIngestResponse(
            content_id=content_id,
            status="processing",
            message="Text content queued for processing"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest text content: {str(e)}")


@router.post("/ingest/file", response_model=ContentIngestResponse)
async def ingest_file_content(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    metadata: Optional[str] = Form("{}"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process file content (PDF, DOCX, TXT, audio, video).
    """
    try:
        content_id = str(uuid.uuid4())
        
        # Parse metadata
        try:
            metadata_dict = json.loads(metadata) if metadata else {}
        except json.JSONDecodeError:
            metadata_dict = {}
        
        # Determine content type from file
        content_type = content_processor.determine_content_type(file.filename, file.content_type)
        
        # Save file temporarily
        file_path = await kb_service.save_uploaded_file(file, content_id)
        
        # Create content item record
        content_item = await kb_service.create_content_item(
            db=db,
            user_id=current_user.id,
            content_id=content_id,
            content_type=content_type,
            title=title or file.filename,
            file_path=file_path,
            metadata=metadata_dict
        )
        
        # Queue background processing based on content type
        if content_type in ["audio", "video"]:
            background_tasks.add_task(
                content_processor.process_media_content,
                content_id=content_id,
                file_path=file_path,
                content_type=content_type,
                metadata=metadata_dict
            )
        else:
            background_tasks.add_task(
                content_processor.process_document_content,
                content_id=content_id,
                file_path=file_path,
                metadata=metadata_dict
            )
        
        return ContentIngestResponse(
            content_id=content_id,
            status="processing",
            message=f"File {file.filename} queued for processing"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest file: {str(e)}")


@router.post("/ingest/url", response_model=ContentIngestResponse)
async def ingest_url_content(
    url: str = Form(...),
    title: Optional[str] = Form(None),
    metadata: Optional[str] = Form("{}"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Scrape and process content from a URL.
    """
    try:
        content_id = str(uuid.uuid4())
        
        # Parse metadata
        try:
            metadata_dict = json.loads(metadata) if metadata else {}
        except json.JSONDecodeError:
            metadata_dict = {}
        
        # Add URL to metadata
        metadata_dict["source_url"] = url
        
        # Create content item record
        content_item = await kb_service.create_content_item(
            db=db,
            user_id=current_user.id,
            content_id=content_id,
            content_type="url",
            title=title or url,
            metadata=metadata_dict
        )
        
        # Queue background web scraping
        background_tasks.add_task(
            content_processor.process_url_content,
            content_id=content_id,
            url=url,
            metadata=metadata_dict
        )
        
        return ContentIngestResponse(
            content_id=content_id,
            status="processing",
            message=f"URL {url} queued for scraping and processing"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest URL: {str(e)}")


@router.post("/ingest/youtube", response_model=ContentIngestResponse)
async def ingest_youtube_content(
    video_url: str = Form(...),
    title: Optional[str] = Form(None),
    metadata: Optional[str] = Form("{}"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process YouTube video content (extract audio, transcribe, process).
    """
    try:
        content_id = str(uuid.uuid4())
        
        # Parse metadata
        try:
            metadata_dict = json.loads(metadata) if metadata else {}
        except json.JSONDecodeError:
            metadata_dict = {}
        
        # Add YouTube URL to metadata
        metadata_dict["youtube_url"] = video_url
        
        # Create content item record
        content_item = await kb_service.create_content_item(
            db=db,
            user_id=current_user.id,
            content_id=content_id,
            content_type="youtube",
            title=title or f"YouTube Video: {video_url}",
            metadata=metadata_dict
        )
        
        # Queue background YouTube processing
        background_tasks.add_task(
            content_processor.process_youtube_content,
            content_id=content_id,
            video_url=video_url,
            metadata=metadata_dict
        )
        
        return ContentIngestResponse(
            content_id=content_id,
            status="processing",
            message=f"YouTube video {video_url} queued for processing"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest YouTube content: {str(e)}")


@router.post("/query", response_model=KnowledgeQueryResponse)
async def query_knowledge_base(
    request: KnowledgeQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Query the knowledge base using RAG (Retrieval-Augmented Generation).
    """
    try:
        # Get conversation context if session_id provided
        conversation_context = None
        if request.session_id:
            conversation_context = await conversation_memory.get_relevant_memory(
                session_id=request.session_id,
                query=request.query
            )
        
        # Perform vector search
        search_results = await vector_store.similarity_search(
            query=request.query,
            user_id=current_user.id,
            top_k=request.top_k or 10,
            content_types=request.content_types,
            date_range=request.date_range
        )
        
        # Generate response using RAG
        response = await kb_service.generate_rag_response(
            query=request.query,
            search_results=search_results,
            conversation_context=conversation_context,
            user_preferences=current_user.preferences if hasattr(current_user, 'preferences') else None
        )
        
        # Store conversation if session_id provided
        if request.session_id:
            await conversation_memory.add_message(
                session_id=request.session_id,
                message={
                    "role": "user",
                    "content": request.query,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            await conversation_memory.add_message(
                session_id=request.session_id,
                message={
                    "role": "assistant",
                    "content": response["answer"],
                    "sources": [result.dict() for result in search_results],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        return KnowledgeQueryResponse(
            answer=response["answer"],
            sources=search_results,
            query=request.query,
            session_id=request.session_id,
            processing_time=response.get("processing_time", 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query knowledge base: {str(e)}")


@router.get("/content/{content_id}", response_model=ContentItem)
async def get_content_item(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific content item.
    """
    try:
        content_item = await kb_service.get_content_item(
            db=db,
            content_id=content_id,
            user_id=current_user.id
        )
        
        if not content_item:
            raise HTTPException(status_code=404, detail="Content item not found")
        
        return content_item
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get content item: {str(e)}")


@router.delete("/content/{content_id}")
async def delete_content_item(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a content item and its associated vectors.
    """
    try:
        success = await kb_service.delete_content_item(
            db=db,
            content_id=content_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Content item not found")
        
        return {"message": "Content item deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete content item: {str(e)}")


@router.get("/content", response_model=List[ContentItem])
async def list_content_items(
    skip: int = 0,
    limit: int = 50,
    content_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List user's content items with optional filtering.
    """
    try:
        content_items = await kb_service.list_content_items(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            content_type=content_type,
            status=status
        )
        
        return content_items
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list content items: {str(e)}")


@router.get("/search", response_model=List[SearchResult])
async def search_content(
    query: str,
    content_types: Optional[List[str]] = None,
    top_k: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search content using vector similarity (without RAG generation).
    """
    try:
        search_results = await vector_store.similarity_search(
            query=query,
            user_id=current_user.id,
            top_k=top_k,
            content_types=content_types
        )
        
        return search_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search content: {str(e)}")


@router.get("/content/{content_id}/status", response_model=ProcessingStatus)
async def get_processing_status(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the processing status of a content item.
    """
    try:
        status = await kb_service.get_processing_status(
            db=db,
            content_id=content_id,
            user_id=current_user.id
        )
        
        if not status:
            raise HTTPException(status_code=404, detail="Content item not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get processing status: {str(e)}")


@router.post("/reprocess/{content_id}")
async def reprocess_content(
    content_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reprocess a content item (useful for failed processing or updates).
    """
    try:
        content_item = await kb_service.get_content_item(
            db=db,
            content_id=content_id,
            user_id=current_user.id
        )
        
        if not content_item:
            raise HTTPException(status_code=404, detail="Content item not found")
        
        # Queue reprocessing based on content type
        if content_item.content_type in ["audio", "video"]:
            background_tasks.add_task(
                content_processor.process_media_content,
                content_id=content_id,
                file_path=content_item.file_path,
                content_type=content_item.content_type,
                metadata=content_item.metadata
            )
        elif content_item.content_type == "url":
            background_tasks.add_task(
                content_processor.process_url_content,
                content_id=content_id,
                url=content_item.metadata.get("source_url"),
                metadata=content_item.metadata
            )
        elif content_item.content_type == "youtube":
            background_tasks.add_task(
                content_processor.process_youtube_content,
                content_id=content_id,
                video_url=content_item.metadata.get("youtube_url"),
                metadata=content_item.metadata
            )
        else:
            background_tasks.add_task(
                content_processor.process_document_content,
                content_id=content_id,
                file_path=content_item.file_path,
                metadata=content_item.metadata
            )
        
        return {"message": "Content queued for reprocessing"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reprocess content: {str(e)}")
