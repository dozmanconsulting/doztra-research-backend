"""
API routes for generating research content.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Body, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid

from app.utils.uuid_helper import convert_uuid_to_str

from app.db.session import get_db
from app.services.auth import get_current_user
from app.models.user import User
from app.models.research_project import ResearchProject
from app.models.generated_content import GeneratedContent
from app.services.openai_service import generate_research_content
from app.schemas.generated_content import (
    GeneratedContentResponse,
    GeneratedContentList,
    GeneratedContentCreate,
    GeneratedContentUpdate
)

router = APIRouter()


class ContentRequest(BaseModel):
    """Request model for generating section content."""
    project_id: str
    section_title: str
    project_title: Optional[str] = None
    project_type: Optional[str] = None
    context: Optional[str] = None


class ContentResponse(BaseModel):
    """Response model for generated section content."""
    content: str


@router.post("/generate-section", response_model=ContentResponse)
async def generate_section_content(
    request: ContentRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate detailed content for a specific section of a research project.
    """
    # Verify the project exists and belongs to the user
    project = db.query(ResearchProject).filter(
        ResearchProject.id == request.project_id,
        ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or you don't have access to it")
    
    # Use provided project info
    project_title = request.project_title or project.title
    project_type = request.project_type or project.type
    
    # Extract metadata from project_metadata JSON column
    import logging
    logger = logging.getLogger(__name__)
    
    project_metadata = {}
    if project.project_metadata:
        # Extract specific fields from project_metadata with proper fallbacks
        project_metadata = {
            'academic_level': project.project_metadata.get('academic_level', ''),
            'target_audience': project.project_metadata.get('target_audience', ''),
            'research_methodology': project.project_metadata.get('research_methodology', ''),
            'country': project.project_metadata.get('country', ''),
            'keywords': project.project_metadata.get('keywords', []),
            'discipline': project.project_metadata.get('discipline', ''),
            # Include any other metadata fields that might be useful
        }
    
    # Log the metadata being used for content generation
    logger.info(f"Generating content for section '{request.section_title}' with metadata: {project_metadata}")
    
    # Add any additional metadata from project_metadata field if there are other fields
    if project.project_metadata:
        project_metadata.update(project.project_metadata)
    
    # Check if content already exists for this section
    existing_content = db.query(GeneratedContent).filter(
        GeneratedContent.project_id == project.id,
        GeneratedContent.section_title == request.section_title
    ).order_by(GeneratedContent.version.desc()).first()
    
    # Generate content using OpenAI with enhanced metadata
    try:
        content = await generate_research_content(
            section_title=request.section_title,
            project_title=project_title,
            project_type=project_type,
            context=request.context,
            metadata=project_metadata  # Pass all available metadata
        )
        
        # Store the generated content in the database
        generation_metadata = {
            "generated_at": datetime.utcnow().isoformat(),
            "model": "gpt-4-turbo",  # Get this from settings
            "context_provided": bool(request.context),
            "project_metadata": project_metadata
        }
        
        # Create new version or first version
        new_version = 1
        if existing_content:
            new_version = existing_content.version + 1
        
        generated_content = GeneratedContent(
            project_id=project.id,
            section_title=request.section_title,
            content=content,
            version=new_version,
            content_metadata=generation_metadata
        )
        
        db.add(generated_content)
        db.commit()
        db.refresh(generated_content)
        
        return ContentResponse(content=content)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate content: {str(e)}")


@router.get("/projects/{project_id}/content", response_model=GeneratedContentList)
async def get_project_content(
    project_id: str = Path(..., description="The ID of the research project"),
    skip: int = Query(0, description="Number of items to skip"),
    limit: int = Query(100, description="Maximum number of items to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all generated content for a specific research project.
    """
    # Verify the project exists and belongs to the user
    project = db.query(ResearchProject).filter(
        ResearchProject.id == project_id,
        ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or you don't have access to it")
    
    # Get all content for this project
    total = db.query(GeneratedContent).filter(GeneratedContent.project_id == project_id).count()
    content_items = db.query(GeneratedContent).filter(
        GeneratedContent.project_id == project_id
    ).order_by(GeneratedContent.section_title, GeneratedContent.version.desc()).offset(skip).limit(limit).all()
    
    return GeneratedContentList(
        items=convert_uuid_to_str(content_items),
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/projects/{project_id}/content/{section_title}", response_model=GeneratedContentResponse)
async def get_section_content(
    project_id: str = Path(..., description="The ID of the research project"),
    section_title: str = Path(..., description="The title of the section"),
    version: Optional[int] = Query(None, description="Specific version to retrieve (latest if not specified)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get generated content for a specific section of a research project.
    """
    # Verify the project exists and belongs to the user
    project = db.query(ResearchProject).filter(
        ResearchProject.id == project_id,
        ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or you don't have access to it")
    
    # Query for content
    query = db.query(GeneratedContent).filter(
        GeneratedContent.project_id == project_id,
        GeneratedContent.section_title == section_title
    )
    
    if version:
        # Get specific version
        content = query.filter(GeneratedContent.version == version).first()
    else:
        # Get latest version
        content = query.order_by(GeneratedContent.version.desc()).first()
    
    if not content:
        raise HTTPException(status_code=404, detail=f"No content found for section '{section_title}'")
    
    return convert_uuid_to_str(content)


@router.put("/projects/{project_id}/content/{content_id}", response_model=GeneratedContentResponse)
async def update_content(
    project_id: str = Path(..., description="The ID of the research project"),
    content_id: str = Path(..., description="The ID of the content to update"),
    content_update: GeneratedContentUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update generated content by ID.
    """
    # Verify the project exists and belongs to the user
    project = db.query(ResearchProject).filter(
        ResearchProject.id == project_id,
        ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or you don't have access to it")
    
    # Get the content
    content = db.query(GeneratedContent).filter(
        GeneratedContent.id == content_id,
        GeneratedContent.project_id == project_id
    ).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Update fields
    if content_update.content is not None:
        content.content = content_update.content
    
    if content_update.content_metadata is not None:
        # Merge existing metadata with new metadata
        if content.content_metadata:
            content.content_metadata.update(content_update.content_metadata)
        else:
            content.content_metadata = content_update.content_metadata
    
    if content_update.version is not None:
        content.version = content_update.version
    
    # Save changes
    content.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(content)
    
    return convert_uuid_to_str(content)


@router.put("/projects/{project_id}/content/section/{section_title}", response_model=GeneratedContentResponse)
async def update_section_content(
    project_id: str = Path(..., description="The ID of the research project"),
    section_title: str = Path(..., description="The title of the section to update"),
    content_update: GeneratedContentUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update generated content by section title. This endpoint is used to save changes to a section's content.
    """
    # Verify the project exists and belongs to the user
    project = db.query(ResearchProject).filter(
        ResearchProject.id == project_id,
        ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or you don't have access to it")
    
    # Get the latest version of content for this section
    content = db.query(GeneratedContent).filter(
        GeneratedContent.project_id == project_id,
        GeneratedContent.section_title == section_title
    ).order_by(GeneratedContent.version.desc()).first()
    
    if not content:
        raise HTTPException(status_code=404, detail=f"No content found for section '{section_title}'")
    
    # Update fields
    if content_update.content is not None:
        # Create a new version if content is different
        if content.content != content_update.content:
            # Create a new version
            new_version = content.version + 1
            
            # Create new content entry with updated content
            new_content = GeneratedContent(
                project_id=project.id,
                section_title=section_title,
                content=content_update.content,
                version=new_version,
                content_metadata=content.content_metadata or {}
            )
            
            # Add edit metadata
            if new_content.content_metadata is None:
                new_content.content_metadata = {}
                
            new_content.content_metadata.update({
                "edited_at": datetime.utcnow().isoformat(),
                "edited_by": current_user.email,
                "previous_version": content.version
            })
            
            db.add(new_content)
            db.commit()
            db.refresh(new_content)
            
            return convert_uuid_to_str(new_content)
    
    # If no changes to content or only metadata changes, update existing record
    if content_update.content_metadata is not None:
        # Merge existing metadata with new metadata
        if content.content_metadata:
            content.content_metadata.update(content_update.content_metadata)
        else:
            content.content_metadata = content_update.content_metadata
    
    # Save changes
    content.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(content)
    
    return convert_uuid_to_str(content)
