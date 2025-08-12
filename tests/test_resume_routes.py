from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_list_resumes_json_response(mock_get_db, mock_get_current_user):
    """Test that the list resumes endpoint returns JSON by default."""
    app = create_app()
    client = TestClient(app)

    # Mock the current user
    mock_user = Mock()
    mock_user.id = 1
    mock_get_current_user.return_value = mock_user

    # Create a mock database session
    mock_db = Mock()

    # Mock the query result
    mock_resume = Mock()
    mock_resume.id = 1
    mock_resume.name = "Test Resume"
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_resume]

    # Define a function to return the mock database session
    def get_mock_db():
        yield mock_db

    # Apply the dependency override
    app.dependency_overrides[get_db] = get_mock_db

    # Make regular request (no HTMX header)
    response = client.get("/api/resumes")
    assert response.status_code == 200
    json_response = response.json()
    assert isinstance(json_response, list)
    assert len(json_response) == 1
    assert json_response[0]["id"] == 1
    assert json_response[0]["name"] == "Test Resume"

    # Clean up the dependency override
    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_get_resume_json_response(mock_get_db, mock_get_current_user):
    """Test that the get resume endpoint returns JSON by default."""
    app = create_app()
    client = TestClient(app)

    # Mock the current user
    mock_user = Mock()
    mock_user.id = 1
    mock_get_current_user.return_value = mock_user

    # Create a mock database session
    mock_db = Mock()

    # Mock the query result
    mock_resume = Mock()
    mock_resume.id = 1
    mock_resume.name = "Test Resume"
    mock_resume.content = "# Test Resume Content"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    # Define a function to return the mock database session
    def get_mock_db():
        yield mock_db

    # Apply the dependency override
    app.dependency_overrides[get_db] = get_mock_db

    # Make regular request (no HTMX header)
    response = client.get("/api/resumes/1")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["id"] == 1
    assert json_response["name"] == "Test Resume"
    assert json_response["content"] == "# Test Resume Content"

    # Clean up the dependency override
    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_create_resume_html_response_with_htmx(mock_get_db, mock_get_current_user):
    """Test that the create resume endpoint returns HTML when requested by HTMX."""
    app = create_app()
    client = TestClient(app)

    # Mock the current user
    mock_user = Mock()
    mock_user.id = 1
    mock_get_current_user.return_value = mock_user

    # Create a mock database session
    mock_db = Mock()

    # Mock the created resume
    mock_resume = Mock()
    mock_resume.id = 1
    mock_resume.name = "New Resume"
    mock_resume.content = "# New Resume Content"

    # Mock the query result for the list refresh
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_resume]

    # Mock the add/commit/refresh operations
    def mock_add(resume):
        resume.id = 1
        return None

    def mock_commit():
        return None

    def mock_refresh(resume):
        return None

    mock_db.add.side_effect = mock_add
    mock_db.commit.side_effect = mock_commit
    mock_db.refresh.side_effect = mock_refresh

    # Define a function to return the mock database session
    def get_mock_db():
        yield mock_db

    # Apply the dependency override
    app.dependency_overrides[get_db] = get_mock_db

    # Make request with HTMX header
    resume_data = {"name": "New Resume", "content": "# New Resume Content"}
    response = client.post(
        "/api/resumes", json=resume_data, headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "New Resume" in response.text
    assert 'class="resume-item' in response.text

    # Clean up the dependency override
    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_update_resume_json_response(mock_get_db, mock_get_current_user):
    """Test that the update resume endpoint returns JSON by default."""
    app = create_app()
    client = TestClient(app)

    # Mock the current user
    mock_user = Mock()
    mock_user.id = 1
    mock_get_current_user.return_value = mock_user

    # Create a mock database session
    mock_db = Mock()

    # Mock the query result
    mock_resume = Mock()
    mock_resume.id = 1
    mock_resume.name = "Updated Resume"
    mock_resume.content = "# Updated Resume Content"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    # Mock the commit/refresh operations
    def mock_commit():
        return None

    def mock_refresh(resume):
        return None

    mock_db.commit.side_effect = mock_commit
    mock_db.refresh.side_effect = mock_refresh

    # Define a function to return the mock database session
    def get_mock_db():
        yield mock_db

    # Apply the dependency override
    app.dependency_overrides[get_db] = get_mock_db

    # Make regular request (no HTMX header)
    update_data = {"name": "Updated Resume", "content": "# Updated Resume Content"}
    response = client.put("/api/resumes/1", json=update_data)
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["id"] == 1
    assert json_response["name"] == "Updated Resume"

    # Clean up the dependency override
    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_update_resume_html_response_with_htmx(mock_get_db, mock_get_current_user):
    """Test that the update resume endpoint returns HTML when requested by HTMX."""
    app = create_app()
    client = TestClient(app)

    # Mock the current user
    mock_user = Mock()
    mock_user.id = 1
    mock_get_current_user.return_value = mock_user

    # Create a mock database session
    mock_db = Mock()

    # Mock the query result
    mock_resume = Mock()
    mock_resume.id = 1
    mock_resume.name = "Updated Resume"
    mock_resume.content = "# Updated Resume Content"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    # Mock the query result for the list refresh
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_resume]

    # Mock the commit/refresh operations
    def mock_commit():
        return None

    def mock_refresh(resume):
        return None

    mock_db.commit.side_effect = mock_commit
    mock_db.refresh.side_effect = mock_refresh

    # Define a function to return the mock database session
    def get_mock_db():
        yield mock_db

    # Apply the dependency override
    app.dependency_overrides[get_db] = get_mock_db

    # Make request with HTMX header
    update_data = {"name": "Updated Resume", "content": "# Updated Resume Content"}
    response = client.put(
        "/api/resumes/1", json=update_data, headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "Updated Resume" in response.text
    assert 'class="resume-item' in response.text

    # Clean up the dependency override
    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_delete_resume_json_response(mock_get_db, mock_get_current_user):
    """Test that the delete resume endpoint returns JSON by default."""
    app = create_app()
    client = TestClient(app)

    # Mock the current user
    mock_user = Mock()
    mock_user.id = 1
    mock_get_current_user.return_value = mock_user

    # Create a mock database session
    mock_db = Mock()

    # Mock the query result
    mock_resume = Mock()
    mock_resume.id = 1
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    # Mock the delete/commit operations
    def mock_delete(resume):
        return None

    def mock_commit():
        return None

    mock_db.delete.side_effect = mock_delete
    mock_db.commit.side_effect = mock_commit

    # Define a function to return the mock database session
    def get_mock_db():
        yield mock_db

    # Apply the dependency override
    app.dependency_overrides[get_db] = get_mock_db

    # Make regular request (no HTMX header)
    response = client.delete("/api/resumes/1")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["message"] == "Resume deleted successfully"

    # Clean up the dependency override
    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_delete_resume_html_response_with_htmx(mock_get_db, mock_get_current_user):
    """Test that the delete resume endpoint returns HTML when requested by HTMX."""
    app = create_app()
    client = TestClient(app)

    # Mock the current user
    mock_user = Mock()
    mock_user.id = 1
    mock_get_current_user.return_value = mock_user

    # Create a mock database session
    mock_db = Mock()

    # Mock the query result
    mock_resume = Mock()
    mock_resume.id = 1
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    # Mock the query result for the list refresh (after deletion)
    mock_db.query.return_value.filter.return_value.all.return_value = []

    # Mock the delete/commit operations
    def mock_delete(resume):
        return None

    def mock_commit():
        return None

    mock_db.delete.side_effect = mock_delete
    mock_db.commit.side_effect = mock_commit

    # Define a function to return the mock database session
    def get_mock_db():
        yield mock_db

    # Apply the dependency override
    app.dependency_overrides[get_db] = get_mock_db

    # Make request with HTMX header
    response = client.delete("/api/resumes/1", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "No resumes found" in response.text

    # Clean up the dependency override
    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_update_resume_not_found(mock_get_db, mock_get_current_user):
    """Test that updating a non-existent resume returns 404."""
    app = create_app()
    client = TestClient(app)

    # Mock the current user
    mock_user = Mock()
    mock_user.id = 1
    mock_get_current_user.return_value = mock_user

    # Create a mock database session
    mock_db = Mock()

    # Mock the query result to return None (resume not found)
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Define a function to return the mock database session
    def get_mock_db():
        yield mock_db

    # Apply the dependency override
    app.dependency_overrides[get_db] = get_mock_db

    # Make request to update non-existent resume
    update_data = {"name": "Updated Resume", "content": "# Updated Resume Content"}
    response = client.put("/api/resumes/999", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"

    # Clean up the dependency override
    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_delete_resume_not_found(mock_get_db, mock_get_current_user):
    """Test that deleting a non-existent resume returns 404."""
    app = create_app()
    client = TestClient(app)

    # Mock the current user
    mock_user = Mock()
    mock_user.id = 1
    mock_get_current_user.return_value = mock_user

    # Create a mock database session
    mock_db = Mock()

    # Mock the query result to return None (resume not found)
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Define a function to return the mock database session
    def get_mock_db():
        yield mock_db

    # Apply the dependency override
    app.dependency_overrides[get_db] = get_mock_db

    # Make request to delete non-existent resume
    response = client.delete("/api/resumes/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"

    # Clean up the dependency override
    app.dependency_overrides.clear()
