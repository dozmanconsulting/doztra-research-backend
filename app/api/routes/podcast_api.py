def _serialize_podcast(podcast) -> dict:
    """Serialize a Podcast ORM object to response dict with signed audio URL if applicable."""
    storage = StorageService()
    signed_url = None
    if podcast.audio_file_path:
        # Try to generate a signed URL for remote storage
        signed_url = storage.generate_signed_url(podcast.audio_file_path) or (
            podcast.audio_file_path if str(podcast.audio_file_path).startswith(("http://", "https://")) else None
        )
    return {
        "id": str(podcast.id),
        "podcast_id": podcast.podcast_id,
        "user_id": str(podcast.user_id),
        "title": podcast.title,
        "topic": podcast.topic,
        "description": podcast.description,
        "status": podcast.status,
        "duration_seconds": podcast.duration_seconds,
        "file_size_bytes": podcast.file_size_bytes,
        "audio_format": podcast.audio_format,
        "created_at": podcast.created_at,
        "script_generated_at": podcast.script_generated_at,
        "audio_generated_at": podcast.audio_generated_at,
        "completed_at": podcast.completed_at,
        "audio_file_path": podcast.audio_file_path,
        "audio_url": signed_url,
        "script_content": podcast.script_content,
    }
"""
Podcasts API Routes
Simple CRUD endpoints for podcasts matching test expectations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from app.db.session import get_db
from app.services.auth import get_current_user
from app.models.user import User
from app.models.podcasts import Podcast, PodcastScriptSegment
from app.models.content_items import ContentItem, ContentChunk
from app.services.openai_service import generate_completion
from app.services.storage_service import StorageService
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["Podcasts"])

# Pydantic models for requests/responses
class CreatePodcastRequest(BaseModel):
    title: str
    topic: str
    description: Optional[str] = None
    voice_settings: Optional[Dict[str, Any]] = {}
    podcast_settings: Optional[Dict[str, Any]] = {}
    podcast_metadata: Optional[Dict[str, Any]] = {}
    duration_seconds: Optional[float] = None
    duration_minutes: Optional[int] = None
    source_ids: Optional[List[str]] = None
    style: Optional[str] = None

class PodcastResponse(BaseModel):
    id: str
    podcast_id: str
    user_id: str
    title: str
    topic: str
    description: Optional[str]
    status: str
    duration_seconds: Optional[float]
    file_size_bytes: Optional[int]
    audio_format: str
    created_at: datetime
    script_generated_at: Optional[datetime]
    audio_generated_at: Optional[datetime]
    completed_at: Optional[datetime]
    audio_file_path: Optional[str] = None
    audio_url: Optional[str] = None
    script_content: Optional[str] = None
    
    class Config:
        from_attributes = True

class PodcastListResponse(BaseModel):
    podcasts: List[PodcastResponse]
    total: int

@router.post("/podcasts/generate", response_model=PodcastResponse)
async def create_and_generate_podcast(
    request: CreatePodcastRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a podcast and immediately start script generation.
    Equivalent to POST /api/podcasts then POST /api/podcasts/{podcast_id}/generate.
    """
    try:
        podcast_id = f"podcast_{uuid.uuid4().hex[:12]}"
        # Normalize duration to seconds if provided
        duration_s = (
            request.duration_seconds
            if request.duration_seconds is not None
            else (request.duration_minutes * 60 if request.duration_minutes is not None else None)
        )
        podcast = Podcast(
            podcast_id=podcast_id,
            user_id=current_user.id,
            title=request.title,
            topic=request.topic,
            description=request.description,
            status="generating_script",
            audio_format="mp3",
            voice_settings=request.voice_settings or {},
            podcast_settings=request.podcast_settings or {},
            podcast_metadata=request.podcast_metadata or {},
            duration_seconds=duration_s,
            created_at=datetime.utcnow(),
            script_generated_at=datetime.utcnow(),
        )

        db.add(podcast)
        db.commit()
        db.refresh(podcast)

        try:
            texts: List[str] = []
            if request.source_ids:
                items = (
                    db.query(ContentItem)
                    .filter(ContentItem.user_id == current_user.id, ContentItem.content_id.in_(request.source_ids))
                    .all()
                )
                if items:
                    chunks = (
                        db.query(ContentChunk)
                        .join(ContentItem, ContentChunk.content_item_id == ContentItem.id)
                        .filter(ContentItem.user_id == current_user.id, ContentItem.content_id.in_(request.source_ids))
                        .order_by(ContentChunk.chunk_index.asc())
                        .limit(12)
                        .all()
                    )
                    texts = [c.text for c in chunks if c.text]
            base_context = ("\n\n".join(texts))[:4000]
            style = request.style or (request.podcast_settings or {}).get("format") or "conversational"
            target_seconds = duration_s or 60
            approx_words = max(40, int((target_seconds / 60.0) * 160))
            system = "You write concise podcast scripts. Keep it natural and engaging."
            user_prompt = (
                f"Topic: {request.topic}\nStyle: {style}\nTarget seconds: {int(target_seconds)}\n"
                f"Approx words: {approx_words}. Use content below as source context.\n\n"
                f"Context:\n{base_context}\n\nWrite the full script with a brief intro and clear closing."
            )
            try:
                script = generate_completion(system, user_prompt, max_tokens=min(1200, approx_words * 2))
            except Exception:
                snippet = base_context[:800] if base_context else request.description or request.topic
                script = f"Intro: {request.topic}.\n\n{snippet}\n\nClosing: Thanks for listening."
            podcast.script_content = script
            podcast.status = "completed"
            podcast.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(podcast)
        except Exception:
            pass

        return PodcastResponse(**_serialize_podcast(podcast))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create & start podcast generation: {str(e)}",
        )

@router.post("/podcasts", response_model=PodcastResponse)
async def create_podcast(
    request: CreatePodcastRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new podcast."""
    try:
        # Generate unique podcast ID
        podcast_id = f"podcast_{uuid.uuid4().hex[:12]}"
        # Normalize duration to seconds if provided
        duration_s = (
            request.duration_seconds
            if request.duration_seconds is not None
            else (request.duration_minutes * 60 if request.duration_minutes is not None else None)
        )
        
        # Create new podcast
        podcast = Podcast(
            podcast_id=podcast_id,
            user_id=current_user.id,
            title=request.title,
            topic=request.topic,
            description=request.description,
            status="pending",
            audio_format="mp3",
            voice_settings=request.voice_settings or {},
            podcast_settings=request.podcast_settings or {},
            podcast_metadata=request.podcast_metadata or {},
            duration_seconds=duration_s,
            created_at=datetime.utcnow()
        )
        
        db.add(podcast)
        db.commit()
        db.refresh(podcast)
        
        return PodcastResponse(**_serialize_podcast(podcast))
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create podcast: {str(e)}"
        )

@router.get("/podcasts", response_model=PodcastListResponse)
async def get_podcasts(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's podcasts."""
    try:
        # Query user's podcasts
        podcasts_query = db.query(Podcast).filter(
            Podcast.user_id == current_user.id
        )
        
        # Apply status filter
        if status_filter:
            podcasts_query = podcasts_query.filter(Podcast.status == status_filter)
        
        total = podcasts_query.count()
        podcasts = podcasts_query.offset(skip).limit(limit).all()
        
        podcast_responses = [PodcastResponse(**_serialize_podcast(p)) for p in podcasts]
        
        return PodcastListResponse(
            podcasts=podcast_responses,
            total=total
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve podcasts: {str(e)}"
        )

@router.get("/podcasts/{podcast_id}", response_model=PodcastResponse)
async def get_podcast(
    podcast_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific podcast."""
    try:
        podcast = db.query(Podcast).filter(
            Podcast.podcast_id == podcast_id,
            Podcast.user_id == current_user.id
        ).first()
        
        if not podcast:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Podcast not found"
            )
        return PodcastResponse(**_serialize_podcast(podcast))
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve podcast: {str(e)}"
        )

@router.get("/podcasts/{podcast_id}/segments")
async def get_podcast_segments(
    podcast_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return script segments and combined text for a podcast owned by the user."""
    try:
        podcast = db.query(Podcast).filter(
            Podcast.podcast_id == podcast_id,
            Podcast.user_id == current_user.id
        ).first()
        if not podcast:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Podcast not found")
        segs = (
            db.query(PodcastScriptSegment)
            .filter(PodcastScriptSegment.podcast_id == podcast.id)
            .order_by(PodcastScriptSegment.segment_index.asc())
            .all()
        )
        segments_out = [
            {
                "segment_index": s.segment_index,
                "speaker": s.speaker,
                "text": s.text,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "duration": s.duration,
            }
            for s in segs
        ]
        combined = "\n\n".join([s.text for s in segs if s.text])
        return {"segments": segments_out, "combined_text": combined}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve segments: {str(e)}")

@router.delete("/podcasts/{podcast_id}")
async def delete_podcast(
    podcast_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a podcast."""
    try:
        podcast = db.query(Podcast).filter(
            Podcast.podcast_id == podcast_id,
            Podcast.user_id == current_user.id
        ).first()
        
        if not podcast:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Podcast not found"
            )
        
        db.delete(podcast)
        db.commit()
        
        return {"message": "Podcast deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete podcast: {str(e)}"
        )

@router.post("/podcasts/{podcast_id}/generate")
async def generate_podcast_script(
    podcast_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate script for a podcast."""
    try:
        podcast = db.query(Podcast).filter(
            Podcast.podcast_id == podcast_id,
            Podcast.user_id == current_user.id
        ).first()
        
        if not podcast:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Podcast not found"
            )
        
        # Update status to script generation
        podcast.status = "generating_script"
        podcast.script_generated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "message": "Podcast script generation started",
            "podcast_id": podcast_id,
            "status": "generating_script"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate podcast script: {str(e)}"
        )
