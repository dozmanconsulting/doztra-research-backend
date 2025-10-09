from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.research_project import ProjectStatus


# Base schema for shared attributes
class ResearchProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: str


# Schema for creating a new research project
class ResearchProjectCreate(ResearchProjectBase):
    metadata: Optional[Dict[str, Any]] = None  # Keep as metadata for frontend compatibility


# Schema for updating an existing research project
class ResearchProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    status: Optional[ProjectStatus] = None
    metadata: Optional[Dict[str, Any]] = None


# Schema for returning a research project
class ResearchProject(ResearchProjectBase):
    id: str
    user_id: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    project_metadata: Optional[Dict[str, Any]] = None
    
    # For backward compatibility with frontend
    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        return self.project_metadata

    class Config:
        from_attributes = True


# Schema for returning a list of research projects
class ResearchProjectList(BaseModel):
    items: List[ResearchProject]
    total: int
    skip: int
    limit: int


# Schema for delete response
class ResearchProjectDelete(BaseModel):
    success: bool
    message: str
    id: str
