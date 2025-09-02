import html
import logging
import re
from unittest.mock import patch

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from resume_editor.app.api.routes.route_logic.resume_parsing import parse_resume_content
from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.main import create_app
from resume_editor.app.models.role import Role
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)


def test_dashboard_not_authenticated():
    """Test that unauthenticated access to /dashboard redirects to the login page."""
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "http://testserver/login"

    app.dependency_overrides.clear()


def test_dashboard_as_non_admin():
    """Test that a non-admin user does not see the Admin link on the dashboard."""
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = User(
        username="testuser",
        email="test@test.com",
        hashed_password="hashed",
    )
    mock_user.roles = []  # Not an admin

    def get_mock_optional_user():
        return mock_user

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_optional_user

    response = client.get("/dashboard")
    assert response.status_code == 200

    soup = BeautifulSoup(response.content, "html.parser")
    admin_link = soup.find("a", href="/admin/users/")
    assert admin_link is None

    app.dependency_overrides.clear()


def test_dashboard_as_admin():
    """Test that an admin user sees the Admin link on the dashboard."""
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_admin = User(
        username="admin",
        email="admin@test.com",
        hashed_password="hashed",
    )
    mock_admin.roles = [Role(name="admin")]

    def get_mock_admin_user():
        return mock_admin

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_admin_user

    response = client.get("/dashboard")
    assert response.status_code == 200

    soup = BeautifulSoup(response.content, "html.parser")
    admin_link = soup.find("a", href="/admin/users/")
    assert admin_link is not None
    assert admin_link.text.strip() == "Admin"

    app.dependency_overrides.clear()


def test_create_resume_form_default_content_is_valid():
    """
    GIVEN a request for the create resume form
    WHEN the form is rendered
    THEN the default resume content in the placeholder should be valid and parsable.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()
    log.debug("Starting test_create_resume_form_default_content_is_valid")

    # The create-resume-form is not protected by auth, but the middleware
    # will redirect if no users exist. So we patch user_count.
    with patch("resume_editor.app.main.user_crud.user_count", return_value=1):
        response = client.get("/dashboard/create-resume-form")

    assert response.status_code == 200
    html_content = response.text

    # Extract placeholder content from the textarea using regex
    match = re.search(r'<textarea.*?placeholder="(.*?)".*?>', html_content, re.DOTALL)
    assert match, "Textarea with placeholder not found in the response"
    placeholder_encoded = match.group(1)

    # Decode HTML entities (e.g., &#10; -> \n)
    placeholder_decoded = html.unescape(placeholder_encoded)

    assert placeholder_decoded.strip(), "Placeholder content is empty"

    # Validate that the placeholder content is parsable
    try:
        parsed_content = parse_resume_content(markdown_content=placeholder_decoded)
        assert parsed_content is not None
        # Check for key sections to ensure parsing was meaningful
        assert "personal" in parsed_content
        assert "education" in parsed_content
        assert "certifications" in parsed_content
        assert "experience" in parsed_content
    except Exception as e:
        assert False, f"Default resume content failed to parse: {e}"

    log.debug("Finished test_create_resume_form_default_content_is_valid")
    app.dependency_overrides.clear()
