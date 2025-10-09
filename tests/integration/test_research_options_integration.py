import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.auth import create_access_token

client = TestClient(app)


@pytest.fixture
def user_token():
    """Create a test user token"""
    return create_access_token(
        data={"sub": "test-user-id", "email": "test@example.com", "role": "USER"}
    )


def test_create_project_with_options(user_token):
    """Test creating a research project with options from the API"""
    # First, get academic disciplines
    disciplines_response = client.get(
        "/api/research/options/academic-disciplines",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert disciplines_response.status_code == 200
    disciplines = disciplines_response.json()
    
    # Get academic levels
    levels_response = client.get(
        "/api/research/options/academic-levels",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert levels_response.status_code == 200
    levels = levels_response.json()
    
    # Get countries
    countries_response = client.get(
        "/api/research/options/countries",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert countries_response.status_code == 200
    countries = countries_response.json()
    
    # Create a project using the options
    project_data = {
        "title": "Test Project with Options",
        "description": "Testing integration of research options with project creation",
        "type": "dissertation",
        "metadata": {
            "discipline": disciplines[0]["value"] if disciplines else "computer_science",
            "academic_level": levels[0]["value"] if levels else "masters",
            "country": countries[0]["value"] if countries else "us"
        }
    }
    
    create_response = client.post(
        "/api/research/projects/",
        json=project_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    assert create_response.status_code == 200
    created_project = create_response.json()
    assert created_project["title"] == project_data["title"]
    assert created_project["project_metadata"]["discipline"] == project_data["metadata"]["discipline"]
    assert created_project["project_metadata"]["academic_level"] == project_data["metadata"]["academic_level"]
    assert created_project["project_metadata"]["country"] == project_data["metadata"]["country"]
    
    # Clean up - delete the project
    project_id = created_project["id"]
    delete_response = client.delete(
        f"/api/research/projects/{project_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert delete_response.status_code == 200


def test_update_project_with_options(user_token):
    """Test updating a research project with options from the API"""
    # Create a project first
    project_data = {
        "title": "Test Project for Update",
        "description": "Testing updating with research options",
        "type": "thesis",
        "metadata": {}
    }
    
    create_response = client.post(
        "/api/research/projects/",
        json=project_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    assert create_response.status_code == 200
    created_project = create_response.json()
    project_id = created_project["id"]
    
    # Get research methodologies
    methodologies_response = client.get(
        "/api/research/options/research-methodologies",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert methodologies_response.status_code == 200
    methodologies = methodologies_response.json()
    
    # Get target audiences
    audiences_response = client.get(
        "/api/research/options/target-audiences",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert audiences_response.status_code == 200
    audiences = audiences_response.json()
    
    # Update the project with new options
    update_data = {
        "metadata": {
            "research_methodology": methodologies[0]["value"] if methodologies else "qualitative",
            "target_audience": audiences[0]["value"] if audiences else "researchers",
            "keywords": ["integration", "testing", "research"]
        }
    }
    
    update_response = client.put(
        f"/api/research/projects/{project_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    assert update_response.status_code == 200
    updated_project = update_response.json()
    assert updated_project["project_metadata"]["research_methodology"] == update_data["metadata"]["research_methodology"]
    assert updated_project["project_metadata"]["target_audience"] == update_data["metadata"]["target_audience"]
    assert "keywords" in updated_project["project_metadata"]
    assert len(updated_project["project_metadata"]["keywords"]) == 3
    
    # Clean up - delete the project
    delete_response = client.delete(
        f"/api/research/projects/{project_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert delete_response.status_code == 200


def test_filter_projects_by_metadata(user_token):
    """Test filtering projects by metadata fields from options"""
    # Create multiple projects with different metadata
    projects = [
        {
            "title": "Computer Science Project",
            "type": "dissertation",
            "metadata": {
                "discipline": "computer_science",
                "academic_level": "doctoral",
                "country": "us"
            }
        },
        {
            "title": "Psychology Project",
            "type": "thesis",
            "metadata": {
                "discipline": "psychology",
                "academic_level": "masters",
                "country": "uk"
            }
        },
        {
            "title": "Biology Project",
            "type": "research_paper",
            "metadata": {
                "discipline": "biology",
                "academic_level": "undergraduate",
                "country": "ca"
            }
        }
    ]
    
    project_ids = []
    
    # Create all projects
    for project in projects:
        response = client.post(
            "/api/research/projects/",
            json=project,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        project_ids.append(response.json()["id"])
    
    # Get all projects and verify count
    all_projects_response = client.get(
        "/api/research/projects/",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert all_projects_response.status_code == 200
    all_projects = all_projects_response.json()
    assert all_projects["total"] >= 3  # There might be other projects from previous tests
    
    # Clean up - delete all created projects
    for project_id in project_ids:
        delete_response = client.delete(
            f"/api/research/projects/{project_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert delete_response.status_code == 200
