import logging
import runpy
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from resume_editor.app.core.auth import (
    get_current_user,
    get_optional_current_user_from_cookie,
)
from resume_editor.app.core.config import get_settings
from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app, initialize_database, main
from resume_editor.app.models.user import User
from resume_editor.app.models.user_settings import UserSettings
from resume_editor.app.schemas.user import UserSettingsUpdateRequest

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
def web_auth_client_and_db():
    """Fixture for an authenticated test client for web routes."""
    app = create_app()
    mock_user = User(username="testuser", email="test@test.com", hashed_password="pw")
    mock_user.id = 1
    mock_db = Mock(spec=Session)

    def get_mock_user():
        return mock_user

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db
    app.dependency_overrides[get_optional_current_user_from_cookie] = get_mock_user

    with TestClient(app) as c:
        yield c, mock_db
    app.dependency_overrides.clear()


def test_health_check():
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_root_redirects_to_dashboard_when_users_exist(
    mock_get_session_local, mock_user_count
):
    """Test root redirects to dashboard when users exist."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session

    app = create_app()
    client = TestClient(app, follow_redirects=False)
    response = client.get("/")

    assert response.status_code == 307
    assert response.headers["location"] == "/dashboard"
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=0)
@patch("resume_editor.app.main.get_session_local")
def test_root_redirects_to_setup_when_no_users(mock_get_session_local, mock_user_count):
    """Test root redirects to setup when no users exist."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session

    app = create_app()
    client = TestClient(app, follow_redirects=False)
    response = client.get("/")

    assert response.status_code == 307
    assert response.headers["location"] == "/setup"
    mock_user_count.assert_called_once()


def test_login_page_loads():
    app = create_app()
    client = TestClient(app)
    response = client.get("/login")
    assert response.status_code == 200
    assert "Login to your account" in response.text


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_unauthenticated_dashboard_redirects(mock_get_session_local, mock_user_count):
    """Test unauthenticated access to dashboard redirects to login when users exist."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session

    app = create_app()
    client = TestClient(app, follow_redirects=False)

    # Mock the database dependency for the route
    mock_db = Mock()

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    response = client.get("/dashboard")

    assert response.status_code == 307
    assert response.headers["location"] == "/login"
    mock_user_count.assert_called_once()
    app.dependency_overrides.clear()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_post_settings_unauthenticated(mock_get_session_local, mock_user_count):
    """Test POST /settings for an unauthenticated user redirects to login."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session

    app = create_app()
    client = TestClient(app, follow_redirects=False)

    # Mock the database dependency
    mock_db = Mock()

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    response = client.post(
        "/settings",
        data={"llm_endpoint": "some_endpoint", "api_key": "some_key"},
    )
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"] == "/login"
    mock_user_count.assert_called_once()
    app.dependency_overrides.clear()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_settings_page_access_unauthenticated(mock_get_session_local, mock_user_count):
    """Test unauthenticated access to settings page redirects to login."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session

    app = create_app()
    client = TestClient(app, follow_redirects=False)

    # Mock the database dependency
    mock_db = Mock()

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    response = client.get("/settings")

    assert response.status_code == 307
    assert response.headers["location"] == "/login"
    mock_user_count.assert_called_once()
    app.dependency_overrides.clear()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_dashboard_with_invalid_cookie_redirects(
    mock_get_session_local, mock_user_count
):
    """Test dashboard access with invalid cookie redirects to login when users exist."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session

    app = create_app()
    client = TestClient(app, follow_redirects=False)

    mock_db = Mock()

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Set cookie on the client instance to avoid deprecation warning
    client.cookies.set("access_token", "invalid-token")
    response = client.get("/dashboard")

    assert response.status_code == 307
    assert response.headers["location"] == "/login"
    mock_user_count.assert_called_once()
    app.dependency_overrides.clear()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch("resume_editor.app.main.get_user_settings")
def test_settings_page_authenticated_no_settings(
    mock_get_user_settings,
    mock_get_session_local,
    mock_user_count,
    web_auth_client_and_db,
):
    """Test GET /settings for an authenticated user with no existing settings."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    client, mock_db = web_auth_client_and_db
    mock_get_user_settings.return_value = None

    response = client.get("/settings")

    assert response.status_code == 200
    assert 'value=""' in response.text
    assert 'placeholder="Enter your API key"' in response.text
    mock_get_user_settings.assert_called_once_with(db=mock_db, user_id=1)
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch("resume_editor.app.main.get_user_settings")
def test_settings_page_with_endpoint_no_key(
    mock_get_user_settings,
    mock_get_session_local,
    mock_user_count,
    web_auth_client_and_db,
):
    """Test GET /settings for a user with endpoint set but no API key."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    client, mock_db = web_auth_client_and_db
    mock_settings = UserSettings(
        user_id=1,
        llm_endpoint="http://test.com",
        encrypted_api_key=None,
    )
    mock_get_user_settings.return_value = mock_settings

    response = client.get("/settings")

    assert response.status_code == 200
    assert 'value="http://test.com"' in response.text
    assert 'placeholder="Enter your API key"' in response.text
    mock_get_user_settings.assert_called_once_with(db=mock_db, user_id=1)
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch("resume_editor.app.main.get_user_settings")
def test_settings_page_authenticated_with_settings(
    mock_get_user_settings,
    mock_get_session_local,
    mock_user_count,
    web_auth_client_and_db,
):
    """Test GET /settings for a user with existing settings."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    client, mock_db = web_auth_client_and_db
    mock_settings = UserSettings(
        user_id=1,
        llm_endpoint="http://test.com",
        encrypted_api_key="encrypted_key",
    )
    mock_get_user_settings.return_value = mock_settings

    response = client.get("/settings")

    assert response.status_code == 200
    assert 'value="http://test.com"' in response.text
    assert 'placeholder="************"' in response.text
    assert "encrypted_key" not in response.text
    mock_get_user_settings.assert_called_once_with(db=mock_db, user_id=1)
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch("resume_editor.app.main.update_user_settings")
def test_post_settings_authenticated(
    mock_update_user_settings,
    mock_get_session_local,
    mock_user_count,
    web_auth_client_and_db,
):
    """Test POST /settings for an authenticated user."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    client, mock_db = web_auth_client_and_db

    # Test with new values
    response = client.post(
        "/settings",
        data={"llm_endpoint": "http://new.com", "api_key": "new_key"},
    )

    assert response.status_code == 200
    assert "Your settings have been updated." in response.text

    mock_update_user_settings.assert_called_once()
    _args, kwargs = mock_update_user_settings.call_args
    assert kwargs["db"] == mock_db
    assert kwargs["user_id"] == 1
    settings_data = kwargs["settings_data"]
    assert isinstance(settings_data, UserSettingsUpdateRequest)
    assert settings_data.llm_endpoint == "http://new.com"
    assert settings_data.api_key == "new_key"
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch("resume_editor.app.main.update_user_settings")
def test_post_settings_empty_values(
    mock_update_user_settings,
    mock_get_session_local,
    mock_user_count,
    web_auth_client_and_db,
):
    """Test POST /settings with empty values to clear settings."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    client, mock_db = web_auth_client_and_db

    response = client.post("/settings", data={"llm_endpoint": "", "api_key": ""})

    assert response.status_code == 200
    assert "Your settings have been updated." in response.text

    mock_update_user_settings.assert_called_once()
    _args, kwargs = mock_update_user_settings.call_args
    assert kwargs["user_id"] == 1
    settings_data = kwargs["settings_data"]
    assert isinstance(settings_data, UserSettingsUpdateRequest)
    assert settings_data.llm_endpoint == ""
    assert settings_data.api_key == ""
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_authenticated_dashboard_access(
    mock_get_session_local, mock_user_count, web_auth_client_and_db
):
    """Test that an authenticated user can access the dashboard."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    client, _ = web_auth_client_and_db
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "Resume Editor Dashboard" in response.text
    assert 'href="/settings"' in response.text
    assert 'href="/logout"' in response.text
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_create_resume_form_loads(mock_get_session_local, mock_user_count):
    """Test that the create resume form loads when users exist."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    app = create_app()
    client = TestClient(app)
    response = client.get("/dashboard/create-resume-form")
    assert response.status_code == 200
    assert "Create New Resume" in response.text
    mock_user_count.assert_called_once()


def test_initialize_database_logging(caplog):
    """
    Test that initialize_database logs the correct message.

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
    from fastapi import FastAPI

    main()
    mock_initialize_database.assert_called_once()
    mock_uvicorn_run.assert_called_once()
    call_args, call_kwargs = mock_uvicorn_run.call_args
    assert isinstance(call_args[0], FastAPI)
    assert call_kwargs == {"host": "0.0.0.0", "port": 8000}


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_edit_personal_info_form_route(mock_get_session_local, mock_user_count):
    """Test that the edit personal info form endpoint returns 200 OK."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    app = create_app()
    client = TestClient(app)
    response = client.get("/dashboard/resumes/1/edit/personal")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_edit_education_form_route(mock_get_session_local, mock_user_count):
    """Test that the edit education form endpoint returns 200 OK."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    app = create_app()
    client = TestClient(app)
    response = client.get("/dashboard/resumes/1/edit/education")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_edit_experience_form_route(mock_get_session_local, mock_user_count):
    """Test that the edit experience form endpoint returns 200 OK."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    app = create_app()
    client = TestClient(app)
    response = client.get("/dashboard/resumes/1/edit/experience")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_edit_projects_form_route(mock_get_session_local, mock_user_count):
    """Test that the edit projects form endpoint returns 200 OK."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    app = create_app()
    client = TestClient(app)
    response = client.get("/dashboard/resumes/1/edit/projects")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_edit_certifications_form_route(mock_get_session_local, mock_user_count):
    """Test that the edit certifications form endpoint returns 200 OK."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    app = create_app()
    client = TestClient(app)
    response = client.get("/dashboard/resumes/1/edit/certifications")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    mock_user_count.assert_called_once()


@patch("uvicorn.run")
def test_main_entrypoint(mock_uvicorn_run):
    """Test that the __main__ guard calls uvicorn.run."""
    import sys

    module_name = "resume_editor.app.main"
    # Store the original module if it exists
    original_module = sys.modules.get(module_name)

    try:
        # To avoid unpredictable behavior with runpy and already-imported modules,
        # we remove the module from sys.modules to ensure a clean execution.
        if module_name in sys.modules:
            del sys.modules[module_name]

        runpy.run_module(module_name, run_name="__main__")
        mock_uvicorn_run.assert_called_once()
    finally:
        # Clean up: remove the module loaded by runpy, if it's there
        if module_name in sys.modules:
            del sys.modules[module_name]
        # And restore the original module if it existed
        if original_module:
            sys.modules[module_name] = original_module


def test_login_success():
    """Test successful login."""
    mock_user = User(
        username="testuser",
        email="t@t.com",
        hashed_password="hashedpassword",
    )
    mock_db = Mock()
    mock_settings = Mock()
    mock_settings.secret_key = "test-secret"
    mock_settings.algorithm = "HS256"
    mock_settings.access_token_expire_minutes = 30

    def get_mock_db():
        yield mock_db

    def get_mock_settings():
        return mock_settings

    with (
        patch(
            "resume_editor.app.main.authenticate_user",
            return_value=mock_user,
        ) as mock_auth,
        patch(
            "resume_editor.app.main.create_access_token",
            return_value="fake-token",
        ) as mock_create_token,
    ):
        test_app = create_app()
        client = TestClient(test_app)
        test_app.dependency_overrides[get_db] = get_mock_db
        test_app.dependency_overrides[get_settings] = get_mock_settings

        response = client.post(
            "/login",
            data={"username": "testuser", "password": "password"},
            follow_redirects=False,
        )

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["location"] == "/dashboard"
        assert "access_token=fake-token" in response.headers["set-cookie"]
        assert "HttpOnly" in response.headers["set-cookie"]

        mock_auth.assert_called_once_with(
            db=mock_db,
            username="testuser",
            password="password",
        )
        mock_create_token.assert_called_once_with(
            data={"sub": "testuser"},
            settings=mock_settings,
        )

        test_app.dependency_overrides.clear()


def test_login_failure():
    """Test failed login."""
    mock_db = Mock()
    mock_settings = Mock()

    def get_mock_db():
        yield mock_db

    def get_mock_settings():
        return mock_settings

    with patch(
        "resume_editor.app.main.authenticate_user",
        return_value=None,
    ) as mock_auth:
        test_app = create_app()
        client = TestClient(test_app)
        test_app.dependency_overrides[get_db] = get_mock_db
        test_app.dependency_overrides[get_settings] = get_mock_settings

        response = client.post(
            "/login",
            data={"username": "testuser", "password": "wrongpassword"},
            follow_redirects=False,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid username or password" in response.text

        mock_auth.assert_called_once_with(
            db=mock_db,
            username="testuser",
            password="wrongpassword",
        )

        test_app.dependency_overrides.clear()


def test_logout():
    """Test user logout."""
    test_app = create_app()
    client = TestClient(test_app)

    response = client.get("/logout", follow_redirects=False)

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"] == "/login"
    # When a cookie is deleted, its value is empty and Max-Age is 0.
    assert 'access_token="";' in response.headers["set-cookie"].replace(" ", "")
    assert "Max-Age=0" in response.headers["set-cookie"]


# These tests below are for HTMX fragment-returning endpoints.
# They require an authenticated client.
@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_get_resume_html_response_not_found(
    mock_get_session_local, mock_user_count, api_auth_client_and_db
):
    """Test get_resume with an unknown ID returns an error message."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    client, mock_db = api_auth_client_and_db
    mock_db.query.return_value.filter.return_value.first.return_value = None
    response = client.get("/api/resumes/999", headers={"HX-Request": "true"})
    assert response.status_code == 404
    assert "Resume not found" in response.text
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_list_resumes_html_response(
    mock_get_session_local, mock_user_count, api_auth_client_and_db
):
    """Test that the list resumes endpoint returns HTML when requested by HTMX."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
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
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_get_resume_html_response(
    mock_get_session_local, mock_user_count, api_auth_client_and_db
):
    """Test that the get resume endpoint returns HTML when requested by HTMX."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
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
    mock_user_count.assert_called_once()


def test_change_password_form_success():
    """Test successful password change via form."""
    app = create_app()
    client = TestClient(app)

    mock_db = MagicMock()
    mock_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_old_password",
    )
    mock_user.id = 1

    from resume_editor.app.main import get_db, get_optional_current_user_from_cookie

    def get_mock_db():
        yield mock_db

    def get_mock_user():
        return mock_user

    app.dependency_overrides[get_db] = get_mock_db
    app.dependency_overrides[get_optional_current_user_from_cookie] = get_mock_user

    with (
        patch(
            "resume_editor.app.main.verify_password",
            return_value=True,
        ) as mock_verify,
        patch(
            "resume_editor.app.main.get_password_hash",
            return_value="hashed_new_password",
        ) as mock_hash,
    ):
        response = client.post(
            "/change-password",
            data={
                "current_password": "old_password",
                "new_password": "new_password",
                "confirm_new_password": "new_password",
            },
        )

        assert response.status_code == 200
        assert "Success!" in response.text
        assert "Your password has been changed" in response.text
        mock_verify.assert_called_once_with("old_password", "hashed_old_password")
        mock_hash.assert_called_once_with("new_password")
        assert mock_user.hashed_password == "hashed_new_password"
        mock_db.commit.assert_called_once()

    app.dependency_overrides.clear()


def test_change_password_form_unauthenticated():
    """Test password change form when unauthenticated."""
    app = create_app()
    client = TestClient(app, follow_redirects=False)

    from resume_editor.app.main import get_optional_current_user_from_cookie

    def get_mock_user_none():
        return None

    app.dependency_overrides[get_optional_current_user_from_cookie] = get_mock_user_none

    response = client.post(
        "/change-password",
        data={
            "current_password": "old_password",
            "new_password": "new_password",
            "confirm_new_password": "new_password",
        },
    )

    assert response.status_code == 307
    assert response.headers["location"] == "/login"
    app.dependency_overrides.clear()


def test_change_password_form_passwords_do_not_match():
    """Test password change form when new passwords do not match."""
    app = create_app()
    client = TestClient(app)

    mock_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_old_password",
    )
    mock_user.id = 1

    from resume_editor.app.main import get_optional_current_user_from_cookie

    def get_mock_user():
        return mock_user

    app.dependency_overrides[get_optional_current_user_from_cookie] = get_mock_user

    response = client.post(
        "/change-password",
        data={
            "current_password": "old_password",
            "new_password": "new_password",
            "confirm_new_password": "different_password",
        },
    )

    assert response.status_code == 200
    assert "Error!" in response.text
    assert "New passwords do not match" in response.text
    app.dependency_overrides.clear()


def test_change_password_form_incorrect_current_password():
    """Test password change form with incorrect current password."""
    app = create_app()
    client = TestClient(app)

    mock_db = MagicMock()
    mock_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_old_password",
    )
    mock_user.id = 1

    from resume_editor.app.main import get_db, get_optional_current_user_from_cookie

    def get_mock_db():
        yield mock_db

    def get_mock_user():
        return mock_user

    app.dependency_overrides[get_db] = get_mock_db
    app.dependency_overrides[get_optional_current_user_from_cookie] = get_mock_user

    with patch(
        "resume_editor.app.main.verify_password",
        return_value=False,
    ) as mock_verify:
        response = client.post(
            "/change-password",
            data={
                "current_password": "wrong_password",
                "new_password": "new_password",
                "confirm_new_password": "new_password",
            },
        )

        assert response.status_code == 200
        assert "Error!" in response.text
        assert "Incorrect current password" in response.text
        mock_verify.assert_called_once_with("wrong_password", "hashed_old_password")
        mock_db.commit.assert_not_called()

    app.dependency_overrides.clear()


def test_middleware_redirects_to_setup_when_no_users():
    """
    Test that the middleware redirects to /setup when no users are in the database.
    """
    app = create_app()

    with patch("resume_editor.app.main.get_session_local") as mock_get_session_local:
        mock_session = MagicMock()
        mock_get_session_local.return_value = lambda: mock_session

        with patch(
            "resume_editor.app.main.user_crud.user_count", return_value=0
        ) as mock_user_count:
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/dashboard", follow_redirects=False)

            assert response.status_code == 307
            assert response.headers["location"] == "/setup"
            mock_user_count.assert_called_once_with(db=mock_session)
            mock_session.close.assert_called_once()


def test_middleware_proceeds_when_users_exist():
    """
    Test that the middleware allows the request to proceed when users exist.
    """
    app = create_app()

    with patch("resume_editor.app.main.get_session_local") as mock_get_session_local:
        mock_session = MagicMock()
        mock_get_session_local.return_value = lambda: mock_session

        with patch(
            "resume_editor.app.main.user_crud.user_count", return_value=1
        ) as mock_user_count:
            with patch(
                "resume_editor.app.main.get_optional_current_user_from_cookie"
            ) as mock_get_user:
                mock_get_user.return_value = None  # Act as if not logged in
                client = TestClient(app, raise_server_exceptions=False)
                response = client.get(
                    "/dashboard", follow_redirects=False
                )  # /dashboard is not excluded

                # It should pass middleware, then dashboard logic will hit.
                # dashboard redirects to /login if user is not authenticated.
                assert response.status_code == 307
                assert response.headers["location"] == "/login"

                mock_user_count.assert_called_once_with(db=mock_session)
                mock_session.close.assert_called_once()


@pytest.mark.parametrize(
    "path,expected_status",
    [
        (
            "/setup",
            200,
        ),
        ("/static/style.css", 404),  # No static files mounted
        ("/docs", 200),
        ("/openapi.json", 200),
        ("/health", 200),
        ("/login", 200),
        ("/logout", 307),
        ("/change-password", 405),  # GET not allowed for this path
    ],
)
def test_middleware_excludes_paths(path, expected_status):
    """
    Test that the middleware excludes specified paths and does not check user count.
    """
    app = create_app()
    app.dependency_overrides[get_db] = lambda: MagicMock()

    with patch(
        "resume_editor.app.main.user_crud.user_count", return_value=0
    ) as mock_main_user_count, patch(
        "resume_editor.app.api.routes.pages.setup.user_count", return_value=0
    ):
        client = TestClient(app)
        response = client.get(path, follow_redirects=False)
        assert response.status_code == expected_status
        mock_main_user_count.assert_not_called()
    app.dependency_overrides.clear()


def test_middleware_db_exception_handling():
    """
    Test that the middleware properly closes the db session if user_count fails.
    """
    app = create_app()

    with patch("resume_editor.app.main.get_session_local") as mock_get_session_local:
        mock_session = MagicMock()
        mock_get_session_local.return_value = lambda: mock_session

        with patch(
            "resume_editor.app.main.user_crud.user_count",
            side_effect=Exception("DB Error"),
        ) as mock_user_count:
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/dashboard", follow_redirects=False)

            # The server should return a 500 Internal Server Error
            assert response.status_code == 500

            mock_user_count.assert_called_once_with(db=mock_session)
            # Crucially, assert that the session was closed despite the exception
            mock_session.close.assert_called_once()
