from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from resume_editor.app.core.auth import get_current_user_from_cookie, get_db
from resume_editor.app.main import create_app
from resume_editor.app.models.user import User, UserData


@pytest.fixture
def app():
    """Fixture to create a new app for each test."""
    _app = create_app()
    yield _app
    # Clear dependency overrides after test
    _app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    """Fixture to create a test client for each test."""
    with TestClient(app) as c:
        yield c


@patch("resume_editor.app.core.auth.get_settings")
@patch("resume_editor.app.core.auth.jwt.decode")
def test_force_password_change_redirect(mock_decode, mock_settings, client, app):
    """Verify user with force_password_change flag is redirected to change password page."""
    app.dependency_overrides.clear()
    mock_db_session = MagicMock()
    mock_user = User(
        data=UserData(
            username="testuser",
            email="test@test.com",
            hashed_password="old_hashed_password",
        )
    )
    mock_user.attributes = {"force_password_change": True}

    app.dependency_overrides[get_db] = lambda: mock_db_session
    mock_decode.return_value = {"sub": "testuser"}
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        mock_user
    )

    client.cookies.set("access_token", "dummy")
    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 307
    assert (
        response.headers["Location"] == "http://testserver/api/users/change-password"
    )


def test_get_change_password_page(client, app):
    """Test that an authenticated user can access the change password page."""
    app.dependency_overrides.clear()
    mock_db_session = MagicMock()
    mock_user = User(
        data=UserData(
            username="testuser",
            email="test@test.com",
            hashed_password="some_password_hash",
            attributes={"force_password_change": True},
        )
    )
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user_from_cookie] = lambda: mock_user

    # Test forced password change view
    response_forced = client.get(
        "/api/users/change-password", headers={"Accept": "text/html"},
    )
    assert response_forced.status_code == 200
    assert "Change Your Password" in response_forced.text
    assert "Current Password" not in response_forced.text
    assert "For security, you must change your password" in response_forced.text

    # Test standard password change view
    mock_user.attributes["force_password_change"] = False
    response_standard = client.get(
        "/api/users/change-password", headers={"Accept": "text/html"},
    )
    assert response_standard.status_code == 200
    assert "Current Password" in response_standard.text
    assert "For security, you must change your password" not in response_standard.text

    # Test standard password change when attributes are None
    mock_user.attributes = None
    response_none_attr = client.get(
        "/api/users/change-password", headers={"Accept": "text/html"},
    )
    assert response_none_attr.status_code == 200
    assert "Current Password" in response_none_attr.text
    assert "For security, you must change your password" not in response_none_attr.text


def test_post_change_password_success_forced(client, app):
    """Test successful forced password change."""
    app.dependency_overrides.clear()
    mock_db_session = MagicMock()
    mock_user = User(
        data=UserData(
            username="testuser",
            email="test@test.com",
            hashed_password="old_hashed_password",
            attributes={"force_password_change": True},
        )
    )
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user_from_cookie] = lambda: mock_user

    with patch(
        "resume_editor.app.api.routes.route_logic.user.get_password_hash",
    ) as mock_hash:
        mock_hash.return_value = "new_hashed_password"
        response = client.post(
            "/api/users/change-password",
            data={
                "new_password": "new_password",
                "confirm_new_password": "new_password",
            },
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
    mock_hash.assert_called_once_with("new_password")
    assert mock_user.hashed_password == "new_hashed_password"
    assert mock_user.attributes["force_password_change"] is False
    mock_db_session.commit.assert_called_once()


def test_post_change_password_mismatch(client, app):
    """Test forced password change with mismatched passwords."""
    app.dependency_overrides.clear()
    mock_db_session = MagicMock()
    mock_user = User(
        data=UserData(
            username="testuser",
            email="test@test.com",
            hashed_password="old_hashed_password",
            attributes={"force_password_change": True},
        )
    )
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user_from_cookie] = lambda: mock_user

    response = client.post(
        "/api/users/change-password",
        data={"new_password": "new_password", "confirm_new_password": "wrong_password"},
        follow_redirects=False,
        headers={"Accept": "text/html"},
    )

    assert response.status_code == 400
    assert "New passwords do not match." in response.text
    assert mock_user.attributes["force_password_change"] is True
    mock_db_session.commit.assert_not_called()


@patch("resume_editor.app.core.auth.get_settings")
@patch("resume_editor.app.core.auth.jwt.decode")
def test_force_password_change_redirect_htmx(mock_decode, mock_settings, client, app):
    """Verify user with force_password_change flag is redirected via HTMX header."""
    app.dependency_overrides.clear()
    mock_db_session = MagicMock()
    mock_user = User(
        data=UserData(
            username="testuser",
            email="test@test.com",
            hashed_password="old_hashed_password",
        )
    )
    mock_user.attributes = {"force_password_change": True}

    app.dependency_overrides[get_db] = lambda: mock_db_session
    mock_decode.return_value = {"sub": "testuser"}
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        mock_user
    )

    client.cookies.set("access_token", "dummy")
    response = client.get("/dashboard", headers={"HX-Request": "true"})

    assert response.status_code == 401
    assert (
        response.headers["HX-Redirect"] == "http://testserver/api/users/change-password"
    )


def test_dashboard_unauthenticated(client, app):
    """Verify unauthenticated access to the dashboard redirects to the login page."""
    app.dependency_overrides.clear()
    mock_db_session = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db_session

    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "http://testserver/login"


def test_post_change_password_failure_incorrect_current_no_mock(client, app):
    """Test password change failure due to incorrect current password without mocking."""
    app.dependency_overrides.clear()
    mock_db_session = MagicMock()
    from resume_editor.app.core.security import get_password_hash

    current_password = "current_password"
    new_password = "new_password"
    hashed_current_password = get_password_hash(current_password)

    mock_user = User(
        data=UserData(
            username="testuser",
            email="test@test.com",
            hashed_password=hashed_current_password,
            attributes={"force_password_change": False},
        )
    )
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user_from_cookie] = lambda: mock_user

    response = client.post(
        "/api/users/change-password",
        data={
            "current_password": "wrong_password",
            "new_password": new_password,
            "confirm_new_password": new_password,
        },
        headers={"Accept": "text/html"},
    )

    assert response.status_code == 400
    assert "Incorrect current password" in response.text
    mock_db_session.commit.assert_not_called()


def test_post_change_password_success_htmx(client, app):
    """Test successful forced password change with HTMX request."""
    app.dependency_overrides.clear()
    mock_db_session = MagicMock()
    mock_user = User(
        data=UserData(
            username="testuser",
            email="test@test.com",
            hashed_password="old_hashed_password",
            attributes={"force_password_change": True},
        )
    )
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user_from_cookie] = lambda: mock_user

    with patch(
        "resume_editor.app.api.routes.route_logic.user.get_password_hash",
    ) as mock_hash:
        mock_hash.return_value = "new_hashed_password"
        response = client.post(
            "/api/users/change-password",
            data={
                "new_password": "new_password",
                "confirm_new_password": "new_password",
            },
            headers={"HX-Request": "true"},
        )

    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == "/dashboard"
    mock_hash.assert_called_once_with("new_password")
    assert mock_user.hashed_password == "new_hashed_password"
    assert mock_user.attributes["force_password_change"] is False
    mock_db_session.commit.assert_called_once()


def test_post_change_password_and_login_with_new_password(client, app):
    """Test successful password change and subsequent password verification."""
    app.dependency_overrides.clear()
    mock_db_session = MagicMock()
    from resume_editor.app.core.security import get_password_hash, verify_password

    old_password = "old_password"
    new_password = "new_password"
    hashed_old_password = get_password_hash(old_password)

    mock_user = User(
        data=UserData(
            username="testuser",
            email="test@test.com",
            hashed_password=hashed_old_password,
            attributes={"force_password_change": True},
        )
    )
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user_from_cookie] = lambda: mock_user

    response = client.post(
        "/api/users/change-password",
        data={"new_password": new_password, "confirm_new_password": new_password},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
    assert mock_user.attributes["force_password_change"] is False
    mock_db_session.commit.assert_called_once()

    # Verify that the password was actually changed and the new one works
    assert verify_password(new_password, mock_user.hashed_password)
    assert not verify_password(old_password, mock_user.hashed_password)


def test_post_change_password_success_not_forced(client, app):
    """Test successful non-forced password change."""
    app.dependency_overrides.clear()
    mock_db_session = MagicMock()
    from resume_editor.app.core.security import get_password_hash, verify_password

    current_password = "current_password"
    new_password = "new_password"
    hashed_current_password = get_password_hash(current_password)

    mock_user = User(
        data=UserData(
            username="testuser",
            email="test@test.com",
            hashed_password=hashed_current_password,
            attributes={"force_password_change": False},
        )
    )
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user_from_cookie] = lambda: mock_user

    response = client.post(
        "/api/users/change-password",
        data={
            "current_password": current_password,
            "new_password": new_password,
            "confirm_new_password": new_password,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
    assert verify_password(new_password, mock_user.hashed_password)
    assert not verify_password(current_password, mock_user.hashed_password)
    mock_db_session.commit.assert_called_once()


def test_post_change_password_with_none_attributes(client, app):
    """Test successful password change when user attributes are initially None."""
    app.dependency_overrides.clear()
    mock_db_session = MagicMock()
    from resume_editor.app.core.security import get_password_hash, verify_password

    current_password = "current_password"
    hashed_current_password = get_password_hash(current_password)

    mock_user = User(
        data=UserData(
            username="testuser",
            email="test@test.com",
            hashed_password=hashed_current_password,
            attributes=None,  # Attributes are None
        )
    )
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user_from_cookie] = lambda: mock_user

    response = client.post(
        "/api/users/change-password",
        data={
            "current_password": current_password,
            "new_password": "new_password",
            "confirm_new_password": "new_password",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303, response.text
    assert mock_user.attributes is not None
    assert mock_user.attributes["force_password_change"] is False
    assert verify_password("new_password", mock_user.hashed_password)
    mock_db_session.commit.assert_called_once()


def test_post_change_password_non_forced_missing_current_password(client, app):
    """Test non-forced password change fails if current password is not provided."""
    app.dependency_overrides.clear()
    mock_db_session = MagicMock()
    mock_user = User(
        data=UserData(
            username="testuser",
            email="test@test.com",
            hashed_password="some_hash",
            attributes={"force_password_change": False},
        )
    )
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user_from_cookie] = lambda: mock_user

    response = client.post(
        "/api/users/change-password",
        data={"new_password": "new_password", "confirm_new_password": "new_password"},
        follow_redirects=False,
        headers={"Accept": "text/html"},
    )

    assert response.status_code == 400
    assert "Incorrect current password" in response.text
    mock_db_session.commit.assert_not_called()


def test_post_forced_change_with_incorrect_current_password_succeeds(client, app):
    """Test a forced password change succeeds even if an incorrect old password is submitted."""
    app.dependency_overrides.clear()
    mock_db_session = MagicMock()
    from resume_editor.app.core.security import get_password_hash

    old_password = "old_password"
    hashed_old_password = get_password_hash(old_password)
    mock_user = User(
        data=UserData(
            username="testuser",
            email="test@test.com",
            hashed_password=hashed_old_password,
            attributes={"force_password_change": True},
        )
    )
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user_from_cookie] = lambda: mock_user

    response = client.post(
        "/api/users/change-password",
        data={
            "current_password": "an_incorrect_password",  # This should be ignored
            "new_password": "new_password",
            "confirm_new_password": "new_password",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert mock_db_session.commit.call_count == 1


def test_get_change_password_page_unauthenticated(client, app):
    """Verify unauthenticated GET to change password page redirects to login."""
    app.dependency_overrides.clear()
    mock_db_session = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db_session

    # Test API request
    api_response = client.get(
        "/api/users/change-password",
        follow_redirects=False,
        headers={"Accept": "application/json"},
    )
    assert api_response.status_code == 401
    assert api_response.json()["detail"] == "Could not validate credentials"

    # Test browser request
    browser_response = client.get(
        "/api/users/change-password",
        follow_redirects=False,
        headers={"Accept": "text/html"},
    )
    assert browser_response.status_code == 307
    assert browser_response.headers["location"] == "http://testserver/login"


def test_post_change_password_unauthenticated(client, app):
    """Verify unauthenticated POST to change password page redirects to login."""
    app.dependency_overrides.clear()
    mock_db_session = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db_session

    # Test API request
    api_response = client.post(
        "/api/users/change-password",
        data={"new_password": "new", "confirm_new_password": "new"},
        follow_redirects=False,
        headers={"Accept": "application/json"},
    )
    assert api_response.status_code == 401
    assert api_response.json()["detail"] == "Could not validate credentials"

    # Test browser request
    browser_response = client.post(
        "/api/users/change-password",
        data={"new_password": "new", "confirm_new_password": "new"},
        follow_redirects=False,
        headers={"Accept": "text/html"},
    )
    assert browser_response.status_code == 307
    assert browser_response.headers["location"] == "http://testserver/login"


def test_get_settings_page_unauthenticated(client, app):
    """Verify unauthenticated GET to settings page redirects to login."""
    app.dependency_overrides.clear()
    mock_db_session = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db_session

    # Test browser request
    browser_response = client.get(
        "/settings",
        follow_redirects=False,
        headers={"Accept": "text/html"},
    )
    assert browser_response.status_code == 307
    assert browser_response.headers["location"] == "http://testserver/login"

    # Test API request
    api_response = client.get(
        "/settings",
        follow_redirects=False,
        headers={"Accept": "application/json"},
    )
    assert api_response.status_code == 401
    assert api_response.json()["detail"] == "Could not validate credentials"


def test_post_settings_unauthenticated(client, app):
    """Verify unauthenticated POST to settings page redirects to login."""
    app.dependency_overrides.clear()
    mock_db_session = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db_session

    # Test browser request
    browser_response = client.post(
        "/settings",
        data={"llm_endpoint": "x", "api_key": "x"},
        follow_redirects=False,
        headers={"Accept": "text/html"},
    )
    assert browser_response.status_code == 307
    assert browser_response.headers["location"] == "http://testserver/login"

    # Test API request
    api_response = client.post(
        "/settings",
        data={"llm_endpoint": "x", "api_key": "x"},
        follow_redirects=False,
        headers={"Accept": "application/json"},
    )
    assert api_response.status_code == 401
    assert api_response.json()["detail"] == "Could not validate credentials"
