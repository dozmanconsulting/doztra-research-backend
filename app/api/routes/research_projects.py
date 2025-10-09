from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
import uuid

from app.db.session import get_db
from app.services.auth import get_current_active_user as get_current_user
from app.models.user import User
from app.models.research_project import ResearchProject, ProjectStatus
from app.utils.uuid_helper import convert_uuid_to_str
from app.schemas.research_project import (
    ResearchProject as ResearchProjectSchema,
    ResearchProjectCreate,
    ResearchProjectUpdate,
    ResearchProjectList,
    ResearchProjectDelete
)

router = APIRouter()


@router.get("/", response_model=ResearchProjectList)
def list_research_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status: active, archived, completed"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all research projects for the current user.
    """
    query = db.query(ResearchProject).filter(ResearchProject.user_id == current_user.id)
    
    # Apply status filter if provided
    if status:
        try:
            status_enum = ProjectStatus(status)
            query = query.filter(ResearchProject.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status value: {status}")
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    projects = query.order_by(ResearchProject.updated_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "items": convert_uuid_to_str(projects),
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/", response_model=ResearchProjectSchema)
def create_research_project(
    project: ResearchProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new research project.
    """
    db_project = ResearchProject(
        user_id=current_user.id,
        title=project.title,
        description=project.description,
        type=project.type,
        project_metadata=project.metadata
    )
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return convert_uuid_to_str(db_project)


@router.get("/{project_id}", response_model=ResearchProjectSchema)
def get_research_project(
    project_id: str = Path(..., description="The ID of the research project"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific research project by ID.
    """
    project = db.query(ResearchProject).filter(
        ResearchProject.id == project_id,
        ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Research project not found")
    
    return convert_uuid_to_str(project)


@router.put("/{project_id}", response_model=ResearchProjectSchema)
def update_research_project(
    project_update: ResearchProjectUpdate,
    project_id: str = Path(..., description="The ID of the research project"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a research project.
    """
    project = db.query(ResearchProject).filter(
        ResearchProject.id == project_id,
        ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Research project not found")
    
    # Update fields if provided
    if project_update.title is not None:
        project.title = project_update.title
    
    if project_update.description is not None:
        project.description = project_update.description
    
    if project_update.type is not None:
        project.type = project_update.type
    
    if project_update.status is not None:
        project.status = project_update.status
    
    if project_update.metadata is not None:
        project.project_metadata = project_update.metadata
    
    db.commit()
    db.refresh(project)
    
    return convert_uuid_to_str(project)


@router.delete("/{project_id}", response_model=ResearchProjectDelete)
def delete_research_project(
    project_id: str = Path(..., description="The ID of the research project"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a research project.
    """
    project = db.query(ResearchProject).filter(
        ResearchProject.id == project_id,
        ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Research project not found")
    
    db.delete(project)
    db.commit()
    
    return {
        "success": True,
        "message": "Research project deleted successfully",
        "id": project_id
    }
