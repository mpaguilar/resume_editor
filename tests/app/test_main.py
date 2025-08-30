import logging
import runpy
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from resume_editor.app.core.auth import get_current_user, get_optional_current_user_from_cookie
from resume_editor.app.database.database import get_db
from resume_editor.app.main import app, create_app, initialize_database, main
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)


@pytest.fixture
def api_auth_client_and_db():
    """Fixture for an authenticated test client for API calls."""
    app = create_app()
    mock_user = User(username="testuser", email="test@test.com", hashed_password="pw")
    mock_user.id = 1
    mock_db = Mock(spec=Session)

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
def authenticated_client():
    """Fixture for an authenticated test client using cookie-based auth."""
    app = create_app()
    mock_user = User(username="testuser", email="test@test.com", hashed_password="pw")
    mock_user.id = 1

    def get_mock_user():
        return mock_user

    app.dependency_overrides[get_optional_current_user_from_cookie] = get_mock_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_health_check():
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_redirects_to_dashboard():
    app = create_app()
    client = TestClient(app, follow_redirects=False)
    response = client.get("/")
    assert response.status_code == 307  # RedirectResponse default
    assert response.headers["location"] == "/dashboard"


def test_login_page_loads():
    app = create_app()
    client = TestClient(app)
    response = client.get("/login")
    assert response.status_code == 200
    assert "Login to your account" in response.text


def test_unauthenticated_dashboard_redirects():
    app = create_app()
    client = TestClient(app, follow_redirects=False)

    # Mock the database dependency
    mock_db = Mock()

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    response = client.get("/dashboard")

    assert response.status_code == 307
    assert response.headers["location"] == "/login"

    app.dependency_overrides.clear()


def test_dashboard_with_invalid_cookie_redirects():
    app = create_app()
    client = TestClient(app, follow_redirects=False)

    mock_db = Mock()

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # The get_current_user_from_cookie will fail to decode this and raise an exception
    response = client.get("/dashboard", cookies={"access_token": "invalid-token"})

    assert response.status_code == 307
    assert response.headers["location"] == "/login"

    app.dependency_overrides.clear()


def test_authenticated_dashboard_access():
    app = create_app()
    mock_user = User(username="testuser", email="test@test.com", hashed_password="pw")

    def get_mock_user():
        return mock_user

    app.dependency_overrides[get_optional_current_user_from_cookie] = get_mock_user

    client = TestClient(app)
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "Resume Editor Dashboard" in response.text

    app.dependency_overrides.clear()


def test_create_resume_form_loads():
    app = create_app()
    client = TestClient(app)
    response = client.get("/dashboard/create-resume-form")
    assert response.status_code == 200
    assert "Create New Resume" in response.text


def test_initialize_database_logging(caplog):
    """Test that initialize_database logs the correct message.

    Args:
        caplog: Pytest fixture to capture logs.

    Returns:
        None

    Notes:
        1. Set the logging level to DEBUG.
        2. Call initialize_database.
        3. Assert that the expected message is in the logs.
    """
    _msg = "Testing initialize_database logging"
    log.debug(_msg)
    with caplog.at_level(logging.DEBUG):
        initialize_database()

    assert (
        "Database initialization is now handled by Alembic. Skipping create_all."
        in caplog.text
    )


@patch("uvicorn.run")
@patch("resume_editor.app.main.initialize_database")
def test_main(mock_initialize_database, mock_uvicorn_run):
    """Test that the main function calls initialize_database and uvicorn.run."""
    main()
    mock_initialize_database.assert_called_once()
    mock_uvicorn_run.assert_called_once_with(app, host="0.0.0.0", port=8000)


def test_edit_personal_info_form_route():
    """Test that the edit personal info form endpoint returns 200 OK."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/dashboard/resumes/1/edit/personal")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_edit_education_form_route():
    """Test that the edit education form endpoint returns 200 OK."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/dashboard/resumes/1/edit/education")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_edit_experience_form_route():
    """Test that the edit experience form endpoint returns 200 OK."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/dashboard/resumes/1/edit/experience")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_edit_projects_form_route():
    """Test that the edit projects form endpoint returns 200 OK."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/dashboard/resumes/1/edit/projects")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_edit_certifications_form_route():
    """Test that the edit certifications form endpoint returns 200 OK."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/dashboard/resumes/1/edit/certifications")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@patch("uvicorn.run")
def test_main_entrypoint(mock_uvicorn_run):
    """Test that the __main__ guard calls uvicorn.run."""
    import sys

    # To avoid unpredictable behavior with runpy and already-imported modules,
    # we remove the module from sys.modules to ensure a clean execution.
    if "resume_editor.app.main" in sys.modules:
        del sys.modules["resume_editor.app.main"]

    runpy.run_module("resume_editor.app.main", run_name="__main__")
    mock_uvicorn_run.assert_called_once()


# These tests below are for HTMX fragment-returning endpoints.
# They require an authenticated client.
def test_get_resume_html_response_not_found(api_auth_client_and_db):
    """Test get_resume with an unknown ID returns an error message."""
    client, mock_db = api_auth_client_and_db
    mock_db.query.return_value.filter.return_value.first.return_value = None
    response = client.get("/api/resumes/999", headers={"HX-Request": "true"})
    assert response.status_code == 404
    assert "Resume not found" in response.text


def test_list_resumes_html_response(api_auth_client_and_db):
    """Test that the list resumes endpoint returns HTML when requested by HTMX."""
    client, mock_db = api_auth_client_and_db

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


def test_get_resume_html_response(api_auth_client_and_db):
    """Test that the get resume endpoint returns HTML when requested by HTMX."""
    client, mock_db = api_auth_client_and_db

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
