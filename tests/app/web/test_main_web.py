import html
import logging
import re
import runpy
from unittest.mock import ANY, MagicMock, patch

from bs4 import BeautifulSoup
from fastapi import HTTPException
from fastapi.testclient import TestClient

from resume_editor.app.api.routes.route_logic import user_crud
from resume_editor.app.api.routes.route_logic.resume_parsing import (
    parse_resume_content,
)
from resume_editor.app.core.auth import get_current_user, get_current_user_from_cookie
from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app, initialize_database
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

    # By default, no user is logged in
    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "http://testserver/login"

    app.dependency_overrides.clear()


@patch("resume_editor.app.main.user_crud.user_count")
def test_setup_middleware_redirects_when_no_users(mock_user_count):
    """
    GIVEN no users exist in the database
    WHEN a request is made to a protected page (e.g., /dashboard)
    THEN the user is redirected to the /setup page.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user_count.return_value = 0

    # dashboard is a non-excluded path
    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/setup"
    mock_user_count.assert_called_once()

    # Check that an excluded path is not redirected
    mock_user_count.reset_mock()
    response = client.get("/login", follow_redirects=False)
    assert response.status_code == 200
    assert mock_user_count.call_count == 0

    app.dependency_overrides.clear()


def test_health_check():
    """
    GIVEN the application is running
    WHEN the /health endpoint is requested
    THEN a 200 OK response with {"status": "ok"} is returned.
    """
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    app.dependency_overrides.clear()


def test_get_login_page():
    """
    GIVEN a request to the login page
    WHEN the /login endpoint is requested with GET
    THEN a 200 OK response with the login form is returned.
    """
    app = create_app()
    client = TestClient(app)
    response = client.get("/login")
    assert response.status_code == 200
    soup = BeautifulSoup(response.content, "html.parser")
    assert soup.find("form", action="/login") is not None
    app.dependency_overrides.clear()


@patch("resume_editor.app.main.authenticate_user")
def test_login_for_access_token_success(mock_authenticate_user):
    """
    GIVEN a user provides correct credentials
    WHEN they submit the login form
    THEN they are redirected to the dashboard and a cookie is set.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_db = MagicMock()

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    mock_user = User(
        id=1, username="testuser", email="test@test.com", hashed_password="hashed"
    )
    mock_authenticate_user.return_value = mock_user

    response = client.post(
        "/login",
        data={"username": "testuser", "password": "password"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
    assert "access_token" in response.cookies
    mock_authenticate_user.assert_called_with(
        db=mock_db, username="testuser", password="password"
    )
    app.dependency_overrides.clear()


@patch("resume_editor.app.main.authenticate_user")
def test_login_for_access_token_failure(mock_authenticate_user):
    """
    GIVEN a user provides incorrect credentials
    WHEN they submit the login form
    THEN the login page is re-rendered with an error message.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_db = MagicMock()

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    mock_authenticate_user.return_value = None

    response = client.post(
        "/login", data={"username": "testuser", "password": "wrongpassword"}
    )

    assert response.status_code == 401
    assert "Invalid username or password" in response.text
    app.dependency_overrides.clear()


def test_logout():
    """
    GIVEN an authenticated user
    WHEN they navigate to /logout
    THEN they are redirected to the login page and the cookie is cleared.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    # Set a dummy cookie to test deletion
    client.cookies.set("access_token", "fake_token")

    response = client.get("/logout", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "http://testserver/login"
    # The cookie should be expired
    assert "Max-Age=0" in response.headers["set-cookie"]
    app.dependency_overrides.clear()


@patch("resume_editor.app.main.verify_password")
@patch("resume_editor.app.main.get_password_hash")
def test_change_password_form_success(mock_hash, mock_verify):
    """
    GIVEN a user submits a valid password change form
    WHEN they POST to /change-password
    THEN the password is updated and a success message is returned.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = User(
        id=1,
        username="testuser",
        email="test@test.com",
        hashed_password="old_hashed_password",
    )
    mock_db = MagicMock()

    app.dependency_overrides[get_current_user_from_cookie] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_verify.return_value = True
    mock_hash.return_value = "new_hashed_password"

    form_data = {
        "current_password": "old_password",
        "new_password": "new_password",
        "confirm_new_password": "new_password",
    }
    response = client.post("/change-password", data=form_data)

    assert response.status_code == 200
    assert "Success!" in response.text
    assert "Your password has been changed" in response.text

    mock_verify.assert_called_once_with("old_password", "old_hashed_password")
    mock_hash.assert_called_once_with("new_password")
    assert mock_user.hashed_password == "new_hashed_password"
    mock_db.commit.assert_called_once()

    app.dependency_overrides.clear()


def test_change_password_form_mismatch():
    """
    GIVEN a user submits a password change form with mismatching new passwords
    WHEN they POST to /change-password
    THEN an error message about mismatching passwords is returned.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = User(
        id=1, username="testuser", email="test@test.com", hashed_password="hashed"
    )
    app.dependency_overrides[get_current_user_from_cookie] = lambda: mock_user

    form_data = {
        "current_password": "old_password",
        "new_password": "new_password_1",
        "confirm_new_password": "new_password_2",
    }
    response = client.post("/change-password", data=form_data)

    assert response.status_code == 200
    assert "New passwords do not match" in response.text

    app.dependency_overrides.clear()


@patch("resume_editor.app.main.verify_password")
def test_change_password_form_incorrect_current_password(mock_verify):
    """
    GIVEN a user submits a password change form with an incorrect current password
    WHEN they POST to /change-password
    THEN an error message about incorrect password is returned.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = User(
        id=1, username="testuser", email="test@test.com", hashed_password="hashed"
    )
    app.dependency_overrides[get_current_user_from_cookie] = lambda: mock_user

    mock_verify.return_value = False

    form_data = {
        "current_password": "wrong_old_password",
        "new_password": "new_password",
        "confirm_new_password": "new_password",
    }
    response = client.post("/change-password", data=form_data)

    assert response.status_code == 200
    assert "Incorrect current password" in response.text
    mock_verify.assert_called_once_with("wrong_old_password", "hashed")

    app.dependency_overrides.clear()


@patch("resume_editor.app.main.log.debug")
def test_initialize_database_logs_message(mock_log_debug):
    """
    GIVEN a call to initialize_database
    WHEN the function is executed
    THEN it logs that initialization is handled by Alembic.
    """
    initialize_database()
    mock_log_debug.assert_called_with(
        "Database initialization is now handled by Alembic. Skipping create_all."
    )


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
    assert soup.find(id="resume-detail") is None
    admin_link = soup.find("a", href="/admin/users/")
    assert admin_link is None

    new_resume_link = soup.find("a", href="/resumes/create")
    assert new_resume_link is not None
    assert "+ New Resume" in new_resume_link.text

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
    assert soup.find(id="resume-detail") is None
    admin_link = soup.find("a", href="/admin/users/")
    assert admin_link is not None
    assert admin_link.text.strip() == "Admin"

    new_resume_link = soup.find("a", href="/resumes/create")
    assert new_resume_link is not None
    assert "+ New Resume" in new_resume_link.text

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_user_resumes")
def test_list_resumes_htmx_request(mock_get_user_resumes):
    """
    GIVEN an htmx request to /api/resumes
    WHEN resumes exist for the user
    THEN an HTML partial is returned with resume items containing edit links.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = User(
        id=1, username="testuser", email="test@test.com", hashed_password="hashed"
    )

    def get_mock_user():
        return mock_user

    mock_resume = DatabaseResume(user_id=1, name="Test Resume", content="...")
    mock_resume.id = 1
    mock_resumes = [mock_resume]
    mock_get_user_resumes.return_value = mock_resumes

    mock_db = MagicMock()

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    app.dependency_overrides[get_db] = get_mock_db

    response = client.get("/api/resumes", headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    soup = BeautifulSoup(response.content, "html.parser")

    resume_item = soup.find("div", class_="resume-item")
    assert resume_item is not None
    assert "Test Resume" in resume_item.text

    edit_link = resume_item.find("a", {"href": "/resumes/1/edit"})
    assert edit_link is not None
    assert edit_link.get("hx-get") is None

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


def test_resume_editor_page_loads_correctly():
    """
    GIVEN an authenticated user and a resume
    WHEN they navigate to the dedicated editor page for that resume
    THEN the page loads with the correct resume content and links.
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
        content="# My Resume Content",
    )
    mock_resume.id = 1

    def get_mock_user():
        return mock_user

    mock_db = MagicMock()
    # This mock will be used by get_resume_by_id_and_user
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    app.dependency_overrides[get_db] = get_mock_db

    response = client.get("/resumes/1/edit")
    assert response.status_code == 200

    soup = BeautifulSoup(response.content, "html.parser")
    header = soup.find("h1")
    assert "Editing: My Test Resume" in header.text

    content_pre = soup.find("pre")
    assert "# My Resume Content" in content_pre.text

    refine_link = soup.find("a", href="/resumes/1/refine")
    assert refine_link is not None
    assert "Refine with AI" in refine_link.text

    dashboard_link = soup.find("a", href="/dashboard")
    assert dashboard_link is not None

    app.dependency_overrides.clear()


def test_resume_editor_page_not_found():
    """
    GIVEN an authenticated user
    WHEN they navigate to an editor page for a non-existent resume
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

    response = client.get("/resumes/999/edit")
    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"

    app.dependency_overrides.clear()


def test_get_create_resume_page():
    """
    GIVEN an authenticated user
    WHEN they navigate to the create resume page
    THEN the page with the creation form is returned.
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

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user

    response = client.get("/resumes/create")
    assert response.status_code == 200

    soup = BeautifulSoup(response.content, "html.parser")
    form = soup.find("form", {"action": "/resumes/create", "method": "post"})
    assert form is not None
    assert soup.find("input", {"name": "name"}) is not None
    assert soup.find("textarea", {"name": "content"}) is not None

    app.dependency_overrides.clear()


@patch("resume_editor.app.main.validate_resume_content")
@patch("resume_editor.app.main.create_resume_db")
def test_handle_create_resume_success(mock_create_resume_db, mock_validate_content):
    """
    GIVEN an authenticated user submitting a valid new resume
    WHEN the form is posted
    THEN a new resume is created and the user is redirected to the editor page.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = User(id=1, username="testuser", email="test@test.com", hashed_password="hashed")
    mock_resume = DatabaseResume(user_id=1, name="New Resume", content="Content")
    mock_resume.id = 123

    def get_mock_user():
        return mock_user

    mock_db = MagicMock()
    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_create_resume_db.return_value = mock_resume

    response = client.post(
        "/resumes/create",
        data={"name": "New Resume", "content": "Content"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/resumes/123/edit"
    mock_validate_content.assert_called_once_with("Content")
    mock_create_resume_db.assert_called_once_with(
        db=mock_db, user_id=1, name="New Resume", content="Content"
    )

    app.dependency_overrides.clear()


@patch("resume_editor.app.main.validate_resume_content")
@patch("resume_editor.app.main.create_resume_db")
def test_handle_create_resume_validation_error(
    mock_create_resume_db, mock_validate_content
):
    """
    GIVEN an authenticated user submitting an invalid resume
    WHEN the form is posted
    THEN the form is re-rendered with an error message.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = User(id=1, username="testuser", email="test@test.com", hashed_password="hashed")

    def get_mock_user():
        return mock_user

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user

    mock_validate_content.side_effect = HTTPException(status_code=422, detail="Invalid Markdown")

    response = client.post(
        "/resumes/create",
        data={"name": "Invalid Resume", "content": "Bad Content"},
        follow_redirects=False,
    )

    assert response.status_code == 422
    mock_create_resume_db.assert_not_called()
    assert "Invalid Markdown" in response.text
    assert 'value="Invalid Resume"' in response.text
    assert "Bad Content" in response.text

    app.dependency_overrides.clear()


def test_get_refine_resume_page_loads_correctly():
    """
    GIVEN an authenticated user and a resume
    WHEN they navigate to the refine page for that resume
    THEN the page loads with a form to start refinement.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = User(
        id=1, username="testuser", email="test@test.com", hashed_password="hashed"
    )
    mock_resume = DatabaseResume(user_id=1, name="My Test Resume", content="Content")
    mock_resume.id = 1

    def get_mock_user():
        return mock_user

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    app.dependency_overrides[get_db] = get_mock_db

    response = client.get("/resumes/1/refine")
    assert response.status_code == 200

    soup = BeautifulSoup(response.content, "html.parser")
    header = soup.find("h1")
    assert "Refine Resume: My Test Resume" in header.text

    form = soup.find("form")
    assert form is not None
    assert form["hx-post"] == "/resumes/1/refine/start"
    assert soup.find("textarea", {"name": "job_description"}) is not None

    app.dependency_overrides.clear()


def test_get_refine_resume_page_not_found():
    """
    GIVEN an authenticated user
    WHEN they navigate to the refine page for a non-existent resume
    THEN a 404 error is returned.
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
    # This will make get_resume_by_id_and_user return None
    mock_db.query.return_value.filter.return_value.first.return_value = None

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    app.dependency_overrides[get_db] = get_mock_db

    response = client.get("/resumes/999/refine")
    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"

    app.dependency_overrides.clear()




