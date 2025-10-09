# Research Project Management API Documentation

This document provides an overview of the Research Project Management API endpoints implemented in the Doztra Auth Service.

## Core Functionality

The Research Project Management API provides the following core functionality:

1. Create, retrieve, update, and delete research projects
2. List all research projects with filtering and pagination

## API Endpoints

### List Research Projects

```
GET /api/research/projects
```

Gets all research projects for the current user.

**Query Parameters:**
- `skip` (int, default: 0): Number of records to skip
- `limit` (int, default: 20): Maximum number of records to return
- `status` (string, optional): Filter by status: active, archived, completed

**Response:**
```json
{
  "items": [
    {
      "id": "project-uuid",
      "user_id": "user-uuid",
      "title": "Literature Review on Climate Change",
      "description": "A comprehensive review of recent literature on climate change impacts",
      "type": "literature_review",
      "status": "active",
      "created_at": "2025-10-06T13:00:00.000Z",
      "updated_at": "2025-10-06T13:30:00.000Z",
      "metadata": {
        "tags": ["climate", "research"]
      }
    },
    // More projects...
  ],
  "total": 5,
  "skip": 0,
  "limit": 20
}
```

### Create Research Project

```
POST /api/research/projects
```

Creates a new research project.

**Request Body:**
```json
{
  "title": "Literature Review on Climate Change",
  "description": "A comprehensive review of recent literature on climate change impacts",
  "type": "literature_review",
  "metadata": {
    "tags": ["climate", "research"]
  }
}
```

**Response:**
```json
{
  "id": "project-uuid",
  "user_id": "user-uuid",
  "title": "Literature Review on Climate Change",
  "description": "A comprehensive review of recent literature on climate change impacts",
  "type": "literature_review",
  "status": "active",
  "created_at": "2025-10-06T13:00:00.000Z",
  "updated_at": "2025-10-06T13:00:00.000Z",
  "metadata": {
    "tags": ["climate", "research"]
  }
}
```

### Get Research Project

```
GET /api/research/projects/{project_id}
```

Gets a specific research project by ID.

**Path Parameters:**
- `project_id` (string): ID of the research project

**Response:**
```json
{
  "id": "project-uuid",
  "user_id": "user-uuid",
  "title": "Literature Review on Climate Change",
  "description": "A comprehensive review of recent literature on climate change impacts",
  "type": "literature_review",
  "status": "active",
  "created_at": "2025-10-06T13:00:00.000Z",
  "updated_at": "2025-10-06T13:30:00.000Z",
  "metadata": {
    "tags": ["climate", "research"]
  }
}
```

### Update Research Project

```
PUT /api/research/projects/{project_id}
```

Updates a research project's details.

**Path Parameters:**
- `project_id` (string): ID of the research project

**Request Body:**
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "type": "research_paper",
  "status": "completed",
  "metadata": {
    "tags": ["climate", "research", "updated"]
  }
}
```

**Response:**
```json
{
  "id": "project-uuid",
  "user_id": "user-uuid",
  "title": "Updated Title",
  "description": "Updated description",
  "type": "research_paper",
  "status": "completed",
  "created_at": "2025-10-06T13:00:00.000Z",
  "updated_at": "2025-10-06T13:35:00.000Z",
  "metadata": {
    "tags": ["climate", "research", "updated"]
  }
}
```

### Delete Research Project

```
DELETE /api/research/projects/{project_id}
```

Deletes a research project.

**Path Parameters:**
- `project_id` (string): ID of the research project

**Response:**
```json
{
  "success": true,
  "message": "Research project deleted successfully",
  "id": "project-uuid"
}
```

## Database Model

### ResearchProject

```python
class ResearchProject(Base):
    __tablename__ = "research_projects"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String, nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.active, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    project_metadata = Column(JSON, nullable=True)  # Named project_metadata to avoid conflict with SQLAlchemy's reserved 'metadata' attribute
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="research_projects")
```

## Implementation Notes

1. The Research Project Management API is fully integrated with the authentication system
2. All endpoints require a valid JWT token
3. Users can only access their own research projects
4. The API supports filtering projects by status
5. Pagination is supported for listing projects
6. The metadata field allows for storing additional project-specific data in a flexible way
