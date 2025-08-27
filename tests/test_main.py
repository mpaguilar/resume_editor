import logging
from unittest.mock import patch

from fastapi.testclient import TestClient

from resume_editor.app.main import create_app, initialize_database, main

log = logging.getLogger(__name__)


def test_health_check():
    """Test that the health check endpoint returns 200 OK."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


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


@patch("resume_editor.app.main.create_app")
@patch("resume_editor.app.main.initialize_database")
def test_main(mock_initialize_database, mock_create_app):
    """Test that the main function calls create_app and initialize_database."""
    main()
    mock_create_app.assert_called_once()
    mock_initialize_database.assert_called_once()


def test_root_redirect():
    """Test that the root endpoint redirects to /dashboard."""
    app = create_app()
    # Using a base_url allows the TestClient to follow the redirect
    client = TestClient(app, base_url="http://testserver")
    # The client will follow the redirect, so the final status code is 200
    response = client.get("/")
    assert response.status_code == 200

    # The redirect response is stored in the history
    assert len(response.history) == 1
    redirect_response = response.history[0]
    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == "/dashboard"


def test_dashboard_route():
    """Test that the dashboard endpoint returns 200 OK."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_create_resume_form_route():
    """Test that the create resume form endpoint returns 200 OK."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/dashboard/create-resume-form")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


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
