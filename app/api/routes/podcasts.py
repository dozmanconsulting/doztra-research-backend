"""
Podcast Generation API Routes
Handles podcast creation, script generation, and audio synthesis using Kokoro 82M.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Form
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
import json
from datetime import datetime

from app.db.session import get_db
from app.services.auth import get_current_user
from app.models.user import User
from app.schemas.podcasts import (
    PodcastGenerationRequest,
    PodcastGenerationResponse,
    PodcastItem,
    PodcastScript,
    PodcastSettings,
    PodcastListResponse
)
from app.services.podcasts import PodcastService
from app.services.knowledge_base import KnowledgeBaseService

router = APIRouter(prefix="/api/v1/podcasts", tags=["Podcasts"])

# Initialize services
podcast_service = PodcastService()
kb_service = KnowledgeBaseService()


@router.post("/generate", response_model=PodcastGenerationResponse)
async def generate_podcast(
    request: PodcastGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a podcast from knowledge base content.
    """
    try:
        podcast_id = str(uuid.uuid4())
        
        # Create podcast record
        podcast = await podcast_service.create_podcast(
            db=db,
            podcast_id=podcast_id,
            user_id=current_user.id,
            title=request.title,
            topic=request.topic,
            settings=request.settings.dict() if request.settings else {},
            content_ids=request.content_ids or []
        )
        
        # Queue background podcast generation
        background_tasks.add_task(
            podcast_service.generate_podcast_async,
            podcast_id=podcast_id,
            topic=request.topic,
            content_ids=request.content_ids or [],
            knowledge_query=request.knowledge_query,
            settings=request.settings,
            user_id=current_user.id
        )
        
        return PodcastGenerationResponse(
            podcast_id=podcast_id,
            status="processing",
            message="Podcast generation started",
            estimated_duration=request.settings.duration_minutes if request.settings else 10
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate podcast: {str(e)}")


@router.get("/", response_model=PodcastListResponse)
async def list_podcasts(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List user's podcasts.
    """
    try:
        podcasts = await podcast_service.list_podcasts(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            status=status
        )
        
        total_count = await podcast_service.count_podcasts(
            db=db,
            user_id=current_user.id,
            status=status
        )
        
        return PodcastListResponse(
            podcasts=podcasts,
            total_count=total_count,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list podcasts: {str(e)}")


@router.get("/{podcast_id}", response_model=PodcastItem)
async def get_podcast(
    podcast_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific podcast with its details.
    """
    try:
        podcast = await podcast_service.get_podcast(
            db=db,
            podcast_id=podcast_id,
            user_id=current_user.id
        )
        
        if not podcast:
            raise HTTPException(status_code=404, detail="Podcast not found")
        
        return podcast
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get podcast: {str(e)}")


@router.get("/{podcast_id}/download")
async def download_podcast(
    podcast_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download the podcast audio file.
    """
    try:
        podcast = await podcast_service.get_podcast(
            db=db,
            podcast_id=podcast_id,
            user_id=current_user.id
        )
        
        if not podcast:
            raise HTTPException(status_code=404, detail="Podcast not found")
        
        if not podcast.audio_file_path or podcast.status != "completed":
            raise HTTPException(status_code=400, detail="Podcast audio not available")
        
        # Return file for download
        return FileResponse(
            path=podcast.audio_file_path,
            media_type="audio/mpeg",
            filename=f"{podcast.title.replace(' ', '_')}.mp3"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download podcast: {str(e)}")


@router.get("/{podcast_id}/stream")
async def stream_podcast(
    podcast_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stream the podcast audio file.
    """
    try:
        podcast = await podcast_service.get_podcast(
            db=db,
            podcast_id=podcast_id,
            user_id=current_user.id
        )
        
        if not podcast:
            raise HTTPException(status_code=404, detail="Podcast not found")
        
        if not podcast.audio_file_path or podcast.status != "completed":
            raise HTTPException(status_code=400, detail="Podcast audio not available")
        
        # Stream audio file
        def generate_audio():
            with open(podcast.audio_file_path, "rb") as audio_file:
                while True:
                    chunk = audio_file.read(8192)
                    if not chunk:
                        break
                    yield chunk
        
        return StreamingResponse(
            generate_audio(),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename={podcast.title.replace(' ', '_')}.mp3"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stream podcast: {str(e)}")


@router.get("/{podcast_id}/script", response_model=PodcastScript)
async def get_podcast_script(
    podcast_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the podcast script/transcript.
    """
    try:
        script = await podcast_service.get_podcast_script(
            db=db,
            podcast_id=podcast_id,
            user_id=current_user.id
        )
        
        if not script:
            raise HTTPException(status_code=404, detail="Podcast script not found")
        
        return script
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get podcast script: {str(e)}")


@router.put("/{podcast_id}/script")
async def update_podcast_script(
    podcast_id: str,
    script_content: str = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the podcast script and regenerate audio.
    """
    try:
        podcast = await podcast_service.get_podcast(
            db=db,
            podcast_id=podcast_id,
            user_id=current_user.id
        )
        
        if not podcast:
            raise HTTPException(status_code=404, detail="Podcast not found")
        
        # Update script
        await podcast_service.update_podcast_script(
            db=db,
            podcast_id=podcast_id,
            script_content=script_content
        )
        
        # Queue audio regeneration
        background_tasks.add_task(
            podcast_service.regenerate_podcast_audio,
            podcast_id=podcast_id,
            script_content=script_content
        )
        
        return {"message": "Script updated, audio regeneration queued"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update podcast script: {str(e)}")


@router.delete("/{podcast_id}")
async def delete_podcast(
    podcast_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a podcast and its associated files.
    """
    try:
        success = await podcast_service.delete_podcast(
            db=db,
            podcast_id=podcast_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Podcast not found")
        
        return {"message": "Podcast deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete podcast: {str(e)}")


@router.post("/{podcast_id}/regenerate")
async def regenerate_podcast(
    podcast_id: str,
    settings: Optional[PodcastSettings] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Regenerate a podcast with new settings or updated content.
    """
    try:
        podcast = await podcast_service.get_podcast(
            db=db,
            podcast_id=podcast_id,
            user_id=current_user.id
        )
        
        if not podcast:
            raise HTTPException(status_code=404, detail="Podcast not found")
        
        # Update settings if provided
        if settings:
            await podcast_service.update_podcast_settings(
                db=db,
                podcast_id=podcast_id,
                settings=settings.dict()
            )
        
        # Queue regeneration
        background_tasks.add_task(
            podcast_service.regenerate_podcast_full,
            podcast_id=podcast_id,
            user_id=current_user.id
        )
        
        return {"message": "Podcast regeneration queued"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate podcast: {str(e)}")


@router.get("/{podcast_id}/status")
async def get_podcast_status(
    podcast_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current status of podcast generation.
    """
    try:
        status = await podcast_service.get_podcast_status(
            db=db,
            podcast_id=podcast_id,
            user_id=current_user.id
        )
        
        if not status:
            raise HTTPException(status_code=404, detail="Podcast not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get podcast status: {str(e)}")


@router.post("/preview-script")
async def preview_podcast_script(
    topic: str = Form(...),
    knowledge_query: str = Form(...),
    content_ids: Optional[List[str]] = Form(None),
    settings: Optional[str] = Form("{}"),  # JSON string
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a preview of the podcast script without creating the full podcast.
    """
    try:
        # Parse settings
        try:
            settings_dict = json.loads(settings) if settings else {}
        except json.JSONDecodeError:
            settings_dict = {}
        
        # Generate script preview
        script_preview = await podcast_service.generate_script_preview(
            topic=topic,
            knowledge_query=knowledge_query,
            content_ids=content_ids or [],
            user_id=current_user.id,
            settings=settings_dict
        )
        
        return {
            "script_preview": script_preview,
            "estimated_duration": script_preview.get("estimated_duration", 0),
            "word_count": script_preview.get("word_count", 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate script preview: {str(e)}")


@router.post("/{podcast_id}/share")
async def share_podcast(
    podcast_id: str,
    public: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a shareable link for the podcast.
    """
    try:
        podcast = await podcast_service.get_podcast(
            db=db,
            podcast_id=podcast_id,
            user_id=current_user.id
        )
        
        if not podcast:
            raise HTTPException(status_code=404, detail="Podcast not found")
        
        if podcast.status != "completed":
            raise HTTPException(status_code=400, detail="Podcast not ready for sharing")
        
        # Generate share link
        share_link = await podcast_service.create_share_link(
            db=db,
            podcast_id=podcast_id,
            public=public
        )
        
        return {
            "share_url": share_link,
            "public": public,
            "expires_at": None if public else datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to share podcast: {str(e)}")


@router.get("/shared/{share_token}")
async def get_shared_podcast(share_token: str):
    """
    Access a shared podcast via its share token.
    """
    try:
        podcast = await podcast_service.get_shared_podcast(share_token)
        
        if not podcast:
            raise HTTPException(status_code=404, detail="Shared podcast not found or expired")
        
        return podcast
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get shared podcast: {str(e)}")


@router.get("/shared/{share_token}/stream")
async def stream_shared_podcast(share_token: str):
    """
    Stream a shared podcast audio file.
    """
    try:
        podcast = await podcast_service.get_shared_podcast(share_token)
        
        if not podcast:
            raise HTTPException(status_code=404, detail="Shared podcast not found or expired")
        
        if not podcast.audio_file_path:
            raise HTTPException(status_code=400, detail="Podcast audio not available")
        
        # Stream audio file
        def generate_audio():
            with open(podcast.audio_file_path, "rb") as audio_file:
                while True:
                    chunk = audio_file.read(8192)
                    if not chunk:
                        break
                    yield chunk
        
        return StreamingResponse(
            generate_audio(),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename={podcast.title.replace(' ', '_')}.mp3"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stream shared podcast: {str(e)}")
