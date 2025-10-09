"""
API routes for content feedback.
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Body, Query, Path
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.auth import get_current_user
from app.models.user import User
from app.models.generated_content import GeneratedContent
from app.models.content_feedback import ContentFeedback
from app.schemas.content_feedback import (
    ContentFeedbackResponse,
    ContentFeedbackList,
    ContentFeedbackCreate,
    ContentFeedbackUpdate
)

router = APIRouter()


@router.post("/content/{content_id}/feedback", response_model=ContentFeedbackResponse)
async def create_feedback(
    content_id: str = Path(..., description="The ID of the content to provide feedback for"),
    feedback: ContentFeedbackCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create feedback for generated content.
    """
    # Verify the content exists
    content = db.query(GeneratedContent).filter(GeneratedContent.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Verify the user has access to the project
    project = db.query(content.project).filter(
        content.project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=403, detail="You don't have access to this content")
    
    # Check if user has already provided feedback
    existing_feedback = db.query(ContentFeedback).filter(
        ContentFeedback.content_id == content_id,
        ContentFeedback.user_id == current_user.id
    ).first()
    
    if existing_feedback:
        raise HTTPException(status_code=400, detail="You have already provided feedback for this content")
    
    # Create new feedback
    new_feedback = ContentFeedback(
        content_id=content_id,
        user_id=current_user.id,
        rating=feedback.rating,
        comments=feedback.comments,
        feedback_metadata=feedback.feedback_metadata
    )
    
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    
    return new_feedback


@router.get("/content/{content_id}/feedback", response_model=ContentFeedbackList)
async def get_content_feedback(
    content_id: str = Path(..., description="The ID of the content"),
    skip: int = Query(0, description="Number of items to skip"),
    limit: int = Query(100, description="Maximum number of items to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all feedback for a specific content.
    """
    # Verify the content exists
    content = db.query(GeneratedContent).filter(GeneratedContent.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Verify the user has access to the project
    project = db.query(content.project).filter(
        content.project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=403, detail="You don't have access to this content")
    
    # Get all feedback for this content
    total = db.query(ContentFeedback).filter(ContentFeedback.content_id == content_id).count()
    feedback_items = db.query(ContentFeedback).filter(
        ContentFeedback.content_id == content_id
    ).order_by(ContentFeedback.created_at.desc()).offset(skip).limit(limit).all()
    
    return ContentFeedbackList(
        items=feedback_items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.put("/content/feedback/{feedback_id}", response_model=ContentFeedbackResponse)
async def update_feedback(
    feedback_id: str = Path(..., description="The ID of the feedback to update"),
    feedback_update: ContentFeedbackUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update feedback for generated content.
    """
    # Verify the feedback exists and belongs to the user
    feedback = db.query(ContentFeedback).filter(
        ContentFeedback.id == feedback_id,
        ContentFeedback.user_id == current_user.id
    ).first()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found or you don't have access to it")
    
    # Update fields
    if feedback_update.rating is not None:
        feedback.rating = feedback_update.rating
    
    if feedback_update.comments is not None:
        feedback.comments = feedback_update.comments
    
    if feedback_update.feedback_metadata is not None:
        # Merge existing metadata with new metadata
        if feedback.feedback_metadata:
            feedback.feedback_metadata.update(feedback_update.feedback_metadata)
        else:
            feedback.feedback_metadata = feedback_update.feedback_metadata
    
    # Save changes
    feedback.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(feedback)
    
    return feedback


@router.delete("/content/feedback/{feedback_id}", status_code=204)
async def delete_feedback(
    feedback_id: str = Path(..., description="The ID of the feedback to delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete feedback for generated content.
    """
    # Verify the feedback exists and belongs to the user
    feedback = db.query(ContentFeedback).filter(
        ContentFeedback.id == feedback_id,
        ContentFeedback.user_id == current_user.id
    ).first()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found or you don't have access to it")
    
    # Delete feedback
    db.delete(feedback)
    db.commit()
    
    return None
