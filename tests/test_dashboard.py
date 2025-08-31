from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from resume_editor.app.core.auth import (
    get_current_user,
    get_optional_current_user_from_cookie,
)
from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app
from resume_editor.app.models.user import User


@pytest.fixture
def api_authenticated_client():
    """Fixture for an authenticated test client for API calls."""
    app = create_app()

    # Mock the current user and database session
    mock_user = Mock(spec=User)
    mock_user.id = 1
    mock_user.roles = []

    mock_db = Mock()

    def get_mock_current_user():
        return mock_user

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db
    app.dependency_overrides[get_current_user] = get_mock_current_user

    with TestClient(app) as c:
        yield c, mock_db

    app.dependency_overrides.clear()


@pytest.fixture
def web_authenticated_client():
    """Fixture for an authenticated test client for web routes (cookie-based)."""
    app = create_app()
    mock_user = Mock(spec=User)
    mock_user.id = 1
    mock_user.roles = []

    def get_mock_user():
        return mock_user

    app.dependency_overrides[get_optional_current_user_from_cookie] = get_mock_user

    with TestClient(app) as c:
        yield c, None  # Yield None for db mock as it's not needed for these routes

    app.dependency_overrides.clear()


def test_dashboard_route(web_authenticated_client):
    """Test that the dashboard route returns the dashboard page."""
    client, _ = web_authenticated_client
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Resume Editor Dashboard" in response.text


def test_root_redirects_to_dashboard(web_authenticated_client):
    """Test that the root route redirects to the dashboard for an authenticated user."""
    client, _ = web_authenticated_client
    response = client.get("/")
    assert response.status_code == 200  # Follows redirect
    assert "Resume Editor Dashboard" in response.text


def test_list_resumes_html_response(api_authenticated_client):
    """Test that the list resumes endpoint returns HTML when requested by HTMX."""
    client, mock_db = api_authenticated_client

    # Mock the query result
    mock_resume = Mock()
    mock_resume.id = 1
    mock_resume.name = "Test Resume"
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_resume]

    # Make request with HTMX header
    response = client.get("/api/resumes", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "Test Resume" in response.text
    assert 'class="resume-item' in response.text


def test_get_resume_html_response(api_authenticated_client):
    """Test that the get resume endpoint returns HTML when requested by HTMX."""
    client, mock_db = api_authenticated_client

    # Mock the query result
    mock_resume = Mock()
    mock_resume.id = 1
    mock_resume.name = "Test Resume"
    mock_resume.content = "# Test Resume Content"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    # Make request with HTMX header
    response = client.get("/api/resumes/1", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "Test Resume" in response.text
    assert "# Test Resume Content" in response.text
    assert "readonly" in response.text


def test_create_resume_form(web_authenticated_client):
    """Test that the create resume form endpoint returns the form."""
    client, _ = web_authenticated_client
    response = client.get("/dashboard/create-resume-form")
    assert response.status_code == 200
    assert "Create New Resume" in response.text
    assert "<textarea" in response.text
