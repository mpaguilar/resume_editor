import html
import logging
import re
from unittest.mock import MagicMock, patch

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from resume_editor.app.api.routes.route_logic.resume_parsing import parse_resume_content
from resume_editor.app.core.auth import get_current_user, get_current_user_from_cookie
from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.role import Role
from resume_editor.app.models.user import User
from resume_editor.app.models.user_settings import UserSettings
from resume_editor.app.schemas.user import UserSettingsUpdateRequest

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


def test_get_edit_resume_form():
    """
    GIVEN an authenticated user with a resume
    WHEN they request the edit form for that resume
    THEN the form is returned with the resume's data pre-filled.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = User(
        id=1,
        username="testuser",
        email="test@test.com",
        hashed_password="hashed",
    )
    mock_resume = DatabaseResume(
        user_id=1,
        name="My Test Resume",
        content="# Personal\n\nName: Test User",
    )
    mock_resume.id = 1

    def get_mock_user():
        return mock_user

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    app.dependency_overrides[get_db] = get_mock_db

    with patch("resume_editor.app.main.user_crud.user_count", return_value=1):
        response = client.get("/dashboard/edit-resume-form/1")
    assert response.status_code == 200

    soup = BeautifulSoup(response.content, "html.parser")
    name_input = soup.find("input", {"name": "name"})
    content_textarea = soup.find("textarea", {"name": "content"})

    assert name_input["value"] == "My Test Resume"
    assert content_textarea.text == "# Personal\n\nName: Test User"

    form = soup.find("form")
    assert form["hx-put"] == "/api/resumes/1"
    assert form["hx-target"] == "#resume-content"

    app.dependency_overrides.clear()


def test_get_edit_resume_form_not_found():
    """
    GIVEN an authenticated user
    WHEN they request the edit form for a non-existent resume
    THEN a 404 error is returned.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = User(
        id=1,
        username="testuser",
        email="test@test.com",
        hashed_password="hashed",
    )

    def get_mock_user():
        return mock_user

    mock_db = MagicMock()
    # This will make get_resume_by_id_and_user return None
    mock_db.query.return_value.filter.return_value.first.return_value = None

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    app.dependency_overrides[get_db] = get_mock_db

    with patch("resume_editor.app.main.user_crud.user_count", return_value=1):
        response = client.get("/dashboard/edit-resume-form/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.validate_resume_content")
@patch("resume_editor.app.api.routes.resume.update_resume_db")
def test_update_resume_htmx(mock_update_resume_db, mock_validate_content):
    """
    GIVEN an authenticated user and a resume
    WHEN the user submits the edit form via HTMX
    THEN the resume is updated and the resume detail view is returned.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = User(
        id=1,
        username="testuser",
        email="test@test.com",
        hashed_password="hashed",
    )
    original_resume = DatabaseResume(
        user_id=1,
        name="Original Name",
        content="Original Content",
    )
    original_resume.id = 1
    updated_resume = DatabaseResume(
        user_id=1,
        name="Updated Name",
        content="Updated Content",
    )
    updated_resume.id = 1

    mock_update_resume_db.return_value = updated_resume

    def get_mock_user():
        return mock_user

    mock_db = MagicMock()

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    app.dependency_overrides[get_db] = get_mock_db

    with patch(
        "resume_editor.app.api.routes.resume.get_resume_by_id_and_user"
    ) as mock_get_resume_by_id:
        mock_get_resume_by_id.return_value = original_resume
        response = client.put(
            "/api/resumes/1",
            data={"name": "Updated Name", "content": "Updated Content"},
            headers={"HX-Request": "true"},
        )

    assert response.status_code == 200
    mock_validate_content.assert_called_once_with("Updated Content")
    mock_update_resume_db.assert_called_once_with(
        db=mock_db,
        resume=original_resume,
        name="Updated Name",
        content="Updated Content",
    )

    # Check that the response is the updated detail view
    soup = BeautifulSoup(response.content, "html.parser")
    h2 = soup.find("h2")
    assert h2
    assert "Updated Name" in h2.text

    textarea = soup.find("textarea")
    assert textarea
    assert "Updated Content" in textarea.text

    # Check for OOB content (list view)
    oob_div = soup.find("div", {"id": "resume-list", "hx-swap-oob": "innerHTML"})
    assert oob_div is None

    app.dependency_overrides.clear()


def test_settings_page_displays_model_name():
    """
    GIVEN an authenticated user
    WHEN they visit the settings page
    THEN the LLM model name field is displayed and populated correctly.
    """
    app = create_app()
    client = TestClient(app)
    mock_user = User(id=1, username="testuser", email="test@test.com", hashed_password="hashed")

    def get_mock_user():
        return mock_user

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user

    # Scenario 1: User has settings with a model name
    mock_settings_with_name = UserSettings(user_id=1, llm_model_name="test-model")
    mock_db_with_name = MagicMock()
    mock_db_with_name.query.return_value.filter.return_value.first.return_value = (
        mock_settings_with_name
    )

    def get_mock_db_with_name():
        yield mock_db_with_name

    app.dependency_overrides[get_db] = get_mock_db_with_name

    response = client.get("/settings")
    assert response.status_code == 200
    soup = BeautifulSoup(response.content, "html.parser")
    model_name_input = soup.find("input", {"name": "llm_model_name"})
    assert model_name_input is not None
    assert model_name_input["value"] == "test-model"

    # Scenario 2: User has settings but no model name
    mock_settings_no_name = UserSettings(user_id=1, llm_model_name=None)
    mock_db_no_name = MagicMock()
    mock_db_no_name.query.return_value.filter.return_value.first.return_value = (
        mock_settings_no_name
    )

    def get_mock_db_no_name():
        yield mock_db_no_name

    app.dependency_overrides[get_db] = get_mock_db_no_name

    response = client.get("/settings")
    assert response.status_code == 200
    soup = BeautifulSoup(response.content, "html.parser")
    model_name_input = soup.find("input", {"name": "llm_model_name"})
    assert model_name_input is not None
    assert model_name_input.get("value") == ""

    # Scenario 3: User has no settings object
    mock_db_no_settings = MagicMock()
    mock_db_no_settings.query.return_value.filter.return_value.first.return_value = None

    def get_mock_db_no_settings():
        yield mock_db_no_settings

    app.dependency_overrides[get_db] = get_mock_db_no_settings

    response = client.get("/settings")
    assert response.status_code == 200
    soup = BeautifulSoup(response.content, "html.parser")
    model_name_input = soup.find("input", {"name": "llm_model_name"})
    assert model_name_input is not None
    assert model_name_input.get("value") == ""

    app.dependency_overrides.clear()


@patch("resume_editor.app.main.update_user_settings")
def test_update_settings_form_submission(mock_update_user_settings):
    """
    GIVEN an authenticated user
    WHEN they submit the settings form with the new model name field
    THEN the update_user_settings crud function is called with the correct data.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = User(
        id=1, username="testuser", email="test@test.com", hashed_password="hashed"
    )

    def get_mock_user():
        return mock_user

    mock_db = MagicMock()

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    app.dependency_overrides[get_db] = get_mock_db

    form_data = {
        "llm_endpoint": "http://new-endpoint.com",
        "llm_model_name": "new-model",
        "api_key": "new_key",
    }

    response = client.post("/settings", data=form_data)

    assert response.status_code == 200
    mock_update_user_settings.assert_called_once()

    # Check the arguments passed to the mocked function
    args, kwargs = mock_update_user_settings.call_args
    assert kwargs["db"] == mock_db
    assert kwargs["user_id"] == mock_user.id

    settings_data = kwargs["settings_data"]
    assert isinstance(settings_data, UserSettingsUpdateRequest)
    assert settings_data.llm_endpoint == "http://new-endpoint.com"
    assert settings_data.llm_model_name == "new-model"
    assert settings_data.api_key == "new_key"

    assert "Your settings have been updated" in response.text

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.validate_resume_content")
@patch("resume_editor.app.api.routes.resume.create_resume_db")
def test_create_resume_htmx(mock_create_resume_db, mock_validate_content):
    """
    GIVEN an authenticated user
    WHEN they submit the create resume form via HTMX
    THEN a new resume is created and the detail view is returned.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = User(
        id=1,
        username="testuser",
        email="test@test.com",
        hashed_password="hashed",
    )
    new_resume = DatabaseResume(
        user_id=1, name="New Resume", content="# Personal\n\nName: New Name"
    )
    new_resume.id = 2
    mock_create_resume_db.return_value = new_resume

    def get_mock_user():
        return mock_user

    mock_db = MagicMock()

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    app.dependency_overrides[get_db] = get_mock_db

    response = client.post(
        "/api/resumes",
        data={"name": "New Resume", "content": "# Personal\n\nName: New Name"},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    mock_validate_content.assert_called_once_with("# Personal\n\nName: New Name")
    mock_create_resume_db.assert_called_once_with(
        db=mock_db,
        user_id=1,
        name="New Resume",
        content="# Personal\n\nName: New Name",
    )

    soup = BeautifulSoup(response.content, "html.parser")

    # Check for main content (detail view)
    h2 = soup.find("h2")
    assert h2
    assert "New Resume" in h2.text

    # Check that there is no OOB content
    oob_div = soup.find("div", {"id": "resume-list", "hx-swap-oob": "innerHTML"})
    assert oob_div is None

    app.dependency_overrides.clear()
