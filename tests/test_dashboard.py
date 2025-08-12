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


def test_dashboard_route(client):
    """Test that the dashboard route returns the dashboard page."""
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Resume Editor Dashboard" in response.text


def test_root_redirects_to_dashboard(client):
    """Test that the root route redirects to the dashboard."""
    response = client.get("/")
    assert response.status_code == 200  # Follows redirect
    assert "Resume Editor Dashboard" in response.text


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_list_resumes_html_response(mock_get_db, mock_get_current_user):
    """Test that the list resumes endpoint returns HTML when requested by HTMX."""
    app = create_app()
    client = TestClient(app)

    # Mock the current user and database session
    mock_user = Mock()
    mock_user.id = 1
    mock_get_current_user.return_value = mock_user

    # Mock the query result
    mock_resume = Mock()
    mock_resume.id = 1
    mock_resume.name = "Test Resume"

    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_resume]

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Make request with HTMX header
    response = client.get("/api/resumes", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "Test Resume" in response.text
    assert 'class="resume-item' in response.text
    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_get_resume_html_response(mock_get_db, mock_get_current_user):
    """Test that the get resume endpoint returns HTML when requested by HTMX."""
    app = create_app()
    client = TestClient(app)

    # Mock the current user and database session
    mock_user = Mock()
    mock_user.id = 1
    mock_get_current_user.return_value = mock_user

    mock_db = Mock()
    mock_get_db.return_value = mock_db

    # Mock the query result
    mock_resume = Mock()
    mock_resume.id = 1
    mock_resume.name = "Test Resume"
    mock_resume.content = "# Test Resume Content"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Make request with HTMX header
    response = client.get("/api/resumes/1", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "Test Resume" in response.text
    assert "# Test Resume Content" in response.text
    assert "readonly" in response.text
    app.dependency_overrides.clear()


def test_create_resume_form(client):
    """Test that the create resume form endpoint returns the form."""
    response = client.get("/dashboard/create-resume-form")
    assert response.status_code == 200
    assert "Create New Resume" in response.text
    assert "<textarea" in response.text
