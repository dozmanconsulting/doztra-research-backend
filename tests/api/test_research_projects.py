import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base_class import Base
from app.db.session import get_db
from app.models.research_project import ResearchProject, ProjectStatus
from app.models.user import User
from app.core.config import settings
from app.services.auth import create_access_token

# Create a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the tables
Base.metadata.create_all(bind=engine)

# Override the get_db dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Test client
client = TestClient(app)

# Test data
test_project_data = {
    "title": "Test Research Project",
    "description": "This is a test research project",
    "type": "literature_review",
    "metadata": {"tags": ["test", "research"]}
}

updated_project_data = {
    "title": "Updated Research Project",
    "description": "This is an updated test research project",
    "type": "research_paper",
    "status": "completed",
    "metadata": {"tags": ["test", "updated"]}
}


@pytest.fixture
def db_session():
    """
    Get a test database session.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session: Session):
    """
    Create a test user.
    """
    # Check if test user already exists
    user = db_session.query(User).filter(User.email == "test@example.com").first()
    if not user:
        # Create test user
        user = User(
            email="test@example.com",
            name="Test User",
            hashed_password="$2b$12$test_hashed_password",
            is_active=True,
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def test_project(db_session: Session, test_user: User):
    """
    Create a test research project.
    """
    # Create test project
    project = ResearchProject(
        user_id=test_user.id,
        title=test_project_data["title"],
        description=test_project_data["description"],
        type=test_project_data["type"],
        project_metadata=test_project_data["metadata"]
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def auth_headers(test_user: User):
    """
    Get authentication headers for test user.
    """
    from datetime import timedelta
    access_token = create_access_token(
        data={"sub": test_user.id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"Authorization": f"Bearer {access_token}"}


def test_create_research_project(auth_headers, db_session: Session):
    """
    Test creating a new research project.
    """
    response = client.post(
        "/api/research/projects/",
        json=test_project_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == test_project_data["title"]
    assert data["description"] == test_project_data["description"]
    assert data["type"] == test_project_data["type"]
    
    # Clean up
    project = db_session.query(ResearchProject).filter(ResearchProject.id == data["id"]).first()
    if project:
        db_session.delete(project)
        db_session.commit()


def test_get_research_projects(auth_headers, test_project):
    """
    Test getting a list of research projects.
    """
    response = client.get(
        "/api/research/projects/",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1
    
    # Check if our test project is in the list
    project_ids = [project["id"] for project in data["items"]]
    assert test_project.id in project_ids


def test_get_research_project_by_id(auth_headers, test_project):
    """
    Test getting a specific research project by ID.
    """
    response = client.get(
        f"/api/research/projects/{test_project.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_project.id
    assert data["title"] == test_project.title
    assert data["description"] == test_project.description
    assert data["type"] == test_project.type


def test_update_research_project(auth_headers, test_project, db_session: Session):
    """
    Test updating a research project.
    """
    response = client.put(
        f"/api/research/projects/{test_project.id}",
        json=updated_project_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == updated_project_data["title"]
    assert data["description"] == updated_project_data["description"]
    assert data["type"] == updated_project_data["type"]
    assert data["status"] == updated_project_data["status"]
    
    # Verify in database
    db_session.refresh(test_project)
    assert test_project.title == updated_project_data["title"]
    assert test_project.description == updated_project_data["description"]
    assert test_project.type == updated_project_data["type"]
    assert test_project.status == ProjectStatus(updated_project_data["status"])


def test_delete_research_project(auth_headers, test_project, db_session: Session):
    """
    Test deleting a research project.
    """
    response = client.delete(
        f"/api/research/projects/{test_project.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["id"] == test_project.id
    
    # Verify project is deleted
    project = db_session.query(ResearchProject).filter(ResearchProject.id == test_project.id).first()
    assert project is None


def test_get_nonexistent_project(auth_headers):
    """
    Test getting a project that doesn't exist.
    """
    response = client.get(
        "/api/research/projects/nonexistent-id",
        headers=auth_headers
    )
    
    assert response.status_code == 404


def test_update_nonexistent_project(auth_headers):
    """
    Test updating a project that doesn't exist.
    """
    response = client.put(
        "/api/research/projects/nonexistent-id",
        json=updated_project_data,
        headers=auth_headers
    )
    
    assert response.status_code == 404


def test_delete_nonexistent_project(auth_headers):
    """
    Test deleting a project that doesn't exist.
    """
    response = client.delete(
        "/api/research/projects/nonexistent-id",
        headers=auth_headers
    )
    
    assert response.status_code == 404


def test_unauthorized_access(db_session: Session, test_project):
    """
    Test accessing endpoints without authentication.
    """
    # Try to get projects without auth
    response = client.get("/api/research/projects/")
    assert response.status_code == 401
    
    # Try to create project without auth
    response = client.post(
        "/api/research/projects/",
        json=test_project_data
    )
    assert response.status_code == 401
    
    # Try to get specific project without auth
    response = client.get(f"/api/research/projects/{test_project.id}")
    assert response.status_code == 401
    
    # Try to update project without auth
    response = client.put(
        f"/api/research/projects/{test_project.id}",
        json=updated_project_data
    )
    assert response.status_code == 401
    
    # Try to delete project without auth
    response = client.delete(f"/api/research/projects/{test_project.id}")
    assert response.status_code == 401


def test_filter_projects_by_status(auth_headers, db_session: Session, test_user: User):
    """
    Test filtering projects by status.
    """
    # Create projects with different statuses
    active_project = ResearchProject(
        user_id=test_user.id,
        title="Active Project",
        description="This is an active project",
        type="literature_review",
        status=ProjectStatus.active
    )
    
    completed_project = ResearchProject(
        user_id=test_user.id,
        title="Completed Project",
        description="This is a completed project",
        type="research_paper",
        status=ProjectStatus.completed
    )
    
    archived_project = ResearchProject(
        user_id=test_user.id,
        title="Archived Project",
        description="This is an archived project",
        type="dissertation",
        status=ProjectStatus.archived
    )
    
    db_session.add_all([active_project, completed_project, archived_project])
    db_session.commit()
    
    # Test filtering by active status
    response = client.get(
        "/api/research/projects/?status=active",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert all(project["status"] == "active" for project in data["items"])
    
    # Test filtering by completed status
    response = client.get(
        "/api/research/projects/?status=completed",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert all(project["status"] == "completed" for project in data["items"])
    
    # Test filtering by archived status
    response = client.get(
        "/api/research/projects/?status=archived",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert all(project["status"] == "archived" for project in data["items"])
    
    # Clean up
    db_session.delete(active_project)
    db_session.delete(completed_project)
    db_session.delete(archived_project)
    db_session.commit()


def test_pagination(auth_headers, db_session: Session, test_user: User):
    """
    Test pagination of research projects.
    """
    # Create multiple projects
    projects = []
    for i in range(25):  # Create 25 projects
        project = ResearchProject(
            user_id=test_user.id,
            title=f"Project {i}",
            description=f"Description for project {i}",
            type="literature_review"
        )
        projects.append(project)
    
    db_session.add_all(projects)
    db_session.commit()
    
    # Test first page (default limit is 20)
    response = client.get(
        "/api/research/projects/",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 20  # Should be 20 or fewer
    assert data["skip"] == 0
    assert data["limit"] == 20
    
    # Test second page
    response = client.get(
        "/api/research/projects/?skip=20",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["skip"] == 20
    
    # Test custom limit
    response = client.get(
        "/api/research/projects/?limit=10",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 10
    assert data["limit"] == 10
    
    # Clean up
    for project in projects:
        db_session.delete(project)
    db_session.commit()
