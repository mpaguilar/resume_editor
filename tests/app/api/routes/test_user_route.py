from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_logic import user as user_logic
from resume_editor.app.api.routes.user import (
    create_new_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    get_users,
)
from resume_editor.app.core.auth import get_current_user, get_current_user_from_cookie
from resume_editor.app.core.config import get_settings
from resume_editor.app.core.security import get_password_hash
from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app
from resume_editor.app.models.role import Role
from resume_editor.app.models.user import User as DBUser
from resume_editor.app.models.user_settings import UserSettings
from resume_editor.app.schemas.user import UserCreate, UserResponse


# Fixtures
@pytest.fixture
def test_user():
    """Fixture for a test user."""
    user = DBUser(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        attributes={},
    )
    user.id = 1
    return user


@pytest.fixture
def client_with_db():
    """Fixture for a test client with a mocked database."""
    get_settings.cache_clear()
    app = create_app()
    mock_db = Mock()

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db
    with TestClient(app) as c:
        yield c, mock_db
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(client_with_db, test_user):
    """Fixture for a test client with an authenticated user."""
    client, mock_db = client_with_db
    app = client.app

    def get_mock_current_user():
        return test_user

    app.dependency_overrides[get_current_user] = get_mock_current_user

    yield client, mock_db


@pytest.fixture
def authenticated_cookie_client(client_with_db, test_user):
    """Fixture for a test client with an authenticated user from a cookie."""
    client, mock_db = client_with_db
    app = client.app

    def get_mock_current_user_from_cookie():
        return test_user

    app.dependency_overrides[get_current_user_from_cookie] = (
        get_mock_current_user_from_cookie
    )

    yield client, mock_db
    app.dependency_overrides.clear()


# Tests for /register
@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch("resume_editor.app.api.routes.user.get_user_by_username", return_value=None)
@patch("resume_editor.app.api.routes.user.get_user_by_email", return_value=None)
@patch("resume_editor.app.api.routes.user.create_new_user")
def test_register_user_success(
    mock_create_user,
    mock_get_by_email,
    mock_get_by_username,
    mock_get_session_local,
    mock_user_count,
    client_with_db,
    test_user,
):
    """Test successful user registration."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, _ = client_with_db
    mock_create_user.return_value = test_user
    response = client.post(
        "/api/users/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["roles"] == []
    assert data["attributes"] == {}
    mock_get_by_username.assert_called_once()
    mock_get_by_email.assert_called_once()
    mock_create_user.assert_called_once()
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch("resume_editor.app.api.routes.user.get_user_by_username")
def test_register_user_duplicate_username(
    mock_get_by_username,
    mock_get_session_local,
    mock_user_count,
    client_with_db,
    test_user,
):
    """Test registration with a duplicate username fails."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, _ = client_with_db
    mock_get_by_username.return_value = test_user
    response = client.post(
        "/api/users/register",
        json={
            "username": "testuser",
            "email": "new@example.com",
            "password": "password",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch("resume_editor.app.api.routes.user.get_user_by_username", return_value=None)
@patch("resume_editor.app.api.routes.user.get_user_by_email")
def test_register_user_duplicate_email(
    mock_get_by_email,
    mock_get_by_username,
    mock_get_session_local,
    mock_user_count,
    client_with_db,
    test_user,
):
    """Test registration with a duplicate email fails."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, _ = client_with_db
    mock_get_by_email.return_value = test_user
    response = client.post(
        "/api/users/register",
        json={
            "username": "newuser",
            "email": "test@example.com",
            "password": "password",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"
    mock_user_count.assert_called_once()


# Tests for /login
@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch("resume_editor.app.api.routes.user.datetime")
def test_login_success(
    mock_datetime, mock_get_session_local, mock_user_count, client_with_db, test_user
):
    """Test successful user login and `last_login_at` update."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, mock_db = client_with_db

    test_settings = get_settings()
    client.app.dependency_overrides[get_settings] = lambda: test_settings

    test_user.last_login_at = None
    test_now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_datetime.now.return_value = test_now

    query_result_mock = Mock()
    query_result_mock.filter.return_value.first.return_value = test_user
    mock_db.query.return_value = query_result_mock
    response = client.post(
        "/api/users/login",
        data={"username": "testuser", "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Verify last_login_at was updated
    assert test_user.last_login_at == test_now
    mock_db.commit.assert_called_once()
    mock_datetime.now.assert_called_with(timezone.utc)

    # Verify the token
    from jose import jwt

    decoded_token = jwt.decode(
        data["access_token"],
        test_settings.secret_key,
        algorithms=[test_settings.algorithm],
    )
    assert decoded_token["sub"] == test_user.username
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_login_failure_user_not_found(
    mock_get_session_local, mock_user_count, client_with_db
):
    """Test that login fails when the user is not found."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, mock_db = client_with_db
    mock_db.query.return_value.filter.return_value.first.return_value = None
    response = client.post(
        "/api/users/login",
        data={"username": "wronguser", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_login_failure_wrong_password(
    mock_get_session_local, mock_user_count, client_with_db, test_user
):
    """Test that login fails with an incorrect password."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, mock_db = client_with_db
    query_result_mock = Mock()
    query_result_mock.filter.return_value.first.return_value = test_user
    mock_db.query.return_value = query_result_mock
    response = client.post(
        "/api/users/login",
        data={"username": "testuser", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
    mock_user_count.assert_called_once()


# Tests for /settings
@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch("resume_editor.app.api.routes.user.settings_crud.get_user_settings")
def test_get_user_settings(
    mock_get_settings,
    mock_get_session_local,
    mock_user_count,
    authenticated_client,
    test_user,
):
    """Test successfully fetching user settings."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, _ = authenticated_client
    mock_settings = UserSettings(
        user_id=test_user.id,
        llm_endpoint="http://llm.test",
        encrypted_api_key="key",
    )
    mock_get_settings.return_value = mock_settings
    response = client.get("/api/users/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["llm_endpoint"] == "http://llm.test"
    assert data["api_key_is_set"] is True
    mock_get_settings.assert_called_once()
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch("resume_editor.app.api.routes.user.settings_crud.get_user_settings")
def test_get_user_settings_none(
    mock_get_settings, mock_get_session_local, mock_user_count, authenticated_client
):
    """Test fetching settings when none are set."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, _ = authenticated_client
    mock_get_settings.return_value = None
    response = client.get("/api/users/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["llm_endpoint"] is None
    assert data["api_key_is_set"] is False
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch("resume_editor.app.api.routes.user.settings_crud.update_user_settings")
def test_update_user_settings(
    mock_update_settings,
    mock_get_session_local,
    mock_user_count,
    authenticated_client,
    test_user,
):
    """Test successfully updating user settings."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, _ = authenticated_client
    mock_settings = UserSettings(
        user_id=test_user.id,
        llm_endpoint="http://new.llm",
        encrypted_api_key="newkey",
    )
    mock_update_settings.return_value = mock_settings

    response = client.put(
        "/api/users/settings",
        json={"llm_endpoint": "http://new.llm", "api_key": "newkey"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["llm_endpoint"] == "http://new.llm"
    assert data["api_key_is_set"] is True
    mock_update_settings.assert_called_once()
    mock_user_count.assert_called_once()


# Tests for auth flow
@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_access_protected_route_with_token(
    mock_get_session_local, mock_user_count, client_with_db, test_user
):
    """Test accessing a protected route with a valid JWT token."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, mock_db = client_with_db

    test_settings = get_settings()
    client.app.dependency_overrides[get_settings] = lambda: test_settings

    # Mock the database call for login and for get_current_user
    # We set up a mock that will be returned every time `query` is called.
    query_result_mock = Mock()
    query_result_mock.filter.return_value.first.return_value = test_user
    mock_db.query.return_value = query_result_mock

    # 1. Login to get a token
    login_response = client.post(
        "/api/users/login",
        data={"username": "testuser", "password": "testpassword"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    assert token

    # 2. Access a protected route with the token
    with (
        patch(
            "resume_editor.app.api.routes.user.settings_crud.get_user_settings",
        ) as mock_get_user_settings,
        patch("resume_editor.app.core.auth.get_settings") as mock_auth_get_settings,
    ):
        mock_get_user_settings.return_value = (
            None  # We don't care about the return value
        )
        mock_auth_get_settings.return_value = test_settings

        headers = {"Authorization": f"Bearer {token}"}
        settings_response = client.get("/api/users/settings", headers=headers)
        assert settings_response.status_code == 200
        # The user from the token should be passed to the route logic
        mock_get_user_settings.assert_called_once()
        (
            _db,
            user_id,
        ) = mock_get_user_settings.call_args.args
        assert user_id == test_user.id
        assert mock_user_count.call_count == 2


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_access_protected_route_no_token(
    mock_get_session_local, mock_user_count, client_with_db
):
    """Test accessing a protected route without a token fails."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, _ = client_with_db
    response = client.get("/api/users/settings")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_access_protected_route_invalid_token(
    mock_get_session_local, mock_user_count, client_with_db
):
    """Test accessing a protected route with a malformed/invalid token."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, _ = client_with_db
    headers = {"Authorization": "Bearer invalidtoken"}
    response = client.get("/api/users/settings", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"
    mock_user_count.assert_called_once()


# Tests for helper functions
def test_get_user_by_username_helper(test_user):
    """Test retrieving a user by username helper."""
    mock_db = Mock(spec=Session)
    query_mock = mock_db.query.return_value.filter.return_value
    query_mock.first.return_value = test_user
    user = get_user_by_username(mock_db, "testuser")
    assert user is not None
    assert user.username == "testuser"
    mock_db.query.assert_called_with(DBUser)


def test_get_user_by_email_helper(test_user):
    """Test retrieving a user by email helper."""
    mock_db = Mock(spec=Session)
    query_mock = mock_db.query.return_value.filter.return_value
    query_mock.first.return_value = test_user
    user = get_user_by_email(mock_db, "test@example.com")
    assert user is not None
    assert user.email == "test@example.com"
    mock_db.query.assert_called_with(DBUser)


@patch("resume_editor.app.api.routes.user.get_password_hash")
def test_create_new_user_helper(mock_get_password_hash):
    """Test creating a new user helper."""
    mock_db = Mock(spec=Session)
    mock_get_password_hash.return_value = "hashed_password"
    user_data = UserCreate(
        username="newuser",
        email="new@example.com",
        password="password",
    )

    new_user = create_new_user(mock_db, user_data)

    mock_get_password_hash.assert_called_once_with("password")
    mock_db.add.assert_called_once()
    added_user = mock_db.add.call_args[0][0]
    assert isinstance(added_user, DBUser)
    assert added_user.username == "newuser"
    assert added_user.email == "new@example.com"
    assert added_user.hashed_password == "hashed_password"
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(added_user)
    assert new_user == added_user


def test_get_users_helper(test_user):
    """Test retrieving all users helper."""
    mock_db = Mock(spec=Session)
    mock_db.query.return_value.all.return_value = [test_user]
    users = get_users(mock_db)
    assert users is not None
    assert len(users) == 1
    assert users[0].username == "testuser"
    mock_db.query.assert_called_with(DBUser)
    mock_db.query.return_value.all.assert_called_once()


def test_get_user_by_id_helper(test_user):
    """Test retrieving a user by ID helper."""
    mock_db = Mock(spec=Session)
    mock_db.query.return_value.filter.return_value.first.return_value = test_user
    user = get_user_by_id(mock_db, 1)
    assert user is not None
    assert user.id == 1
    assert user.username == "testuser"
    mock_db.query.assert_called_with(DBUser)
    mock_db.query.return_value.filter.return_value.first.assert_called_once()


def test_delete_user_helper(test_user):
    """Test deleting a user helper."""
    mock_db = Mock(spec=Session)
    delete_user(mock_db, test_user)
    mock_db.delete.assert_called_once_with(test_user)
    mock_db.commit.assert_called_once()


# Tests for schemas
def test_user_response_schema_with_data():
    """Test the UserResponse schema correctly serializes a User model with roles and attributes."""
    # 1. Create a mock role
    mock_role = Role()
    mock_role.id = 1
    mock_role.name = "admin"

    # 2. Create a mock user model instance with data
    mock_user = DBUser(
        username="test_user_with_data",
        email="data@example.com",
        hashed_password="hashed_password",
        attributes={"is_cool": True, "level": 99},
    )
    mock_user.id = 99
    mock_user.is_active = True
    mock_user.roles = [mock_role]

    # 3. Create UserResponse from the model instance
    user_response = UserResponse.model_validate(mock_user)

    # 4. Assert the data is correct
    assert user_response.id == 99
    assert user_response.username == "test_user_with_data"
    assert user_response.email == "data@example.com"
    assert user_response.is_active is True
    assert user_response.attributes == {"is_cool": True, "level": 99}
    assert len(user_response.roles) == 1
    assert user_response.roles[0].id == 1
    assert user_response.roles[0].name == "admin"


# Tests for /change-password
@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch(
    "resume_editor.app.api.routes.route_logic.user.verify_password",
    return_value=True,
)
@patch(
    "resume_editor.app.api.routes.route_logic.user.get_password_hash",
    return_value="new_hashed_password",
)
def test_change_password_success_and_unsets_flag(
    mock_get_hash,
    mock_verify,
    mock_get_session_local,
    mock_user_count,
    authenticated_cookie_client,
    test_user,
):
    """
    Test successful password change, unsets force_password_change flag, and redirects.
    """
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, mock_db = authenticated_cookie_client
    test_user.attributes = {"force_password_change": True}
    original_hashed_password = test_user.hashed_password
    response = client.post(
        "/api/users/change-password",
        data={
            "current_password": "old_password",
            "new_password": "new_password",
            "confirm_new_password": "new_password",
        },
        follow_redirects=False,
    )
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == "/dashboard"
    mock_verify.assert_not_called()
    mock_get_hash.assert_called_once_with("new_password")
    assert test_user.hashed_password == "new_hashed_password"
    assert test_user.attributes["force_password_change"] is False
    mock_db.commit.assert_called_once()
    mock_user_count.assert_called_once()
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch(
    "resume_editor.app.api.routes.route_logic.user.verify_password",
    return_value=True,
)
@patch(
    "resume_editor.app.api.routes.route_logic.user.get_password_hash",
    return_value="new_hashed_password",
)
def test_change_password_success_htmx(
    mock_get_hash,
    mock_verify,
    mock_get_session_local,
    mock_user_count,
    authenticated_cookie_client,
    test_user,
):
    """
    Test successful password change with HTMX redirect.
    """
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, mock_db = authenticated_cookie_client
    test_user.attributes = {"force_password_change": True}
    response = client.post(
        "/api/users/change-password",
        data={
            "current_password": "old_password",
            "new_password": "new_password",
            "confirm_new_password": "new_password",
        },
        headers={"HX-Request": "true"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["hx-redirect"] == "/dashboard"
    assert test_user.attributes["force_password_change"] is False
    mock_db.commit.assert_called_once()
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch(
    "resume_editor.app.api.routes.route_logic.user.verify_password",
    return_value=True,
)
@patch(
    "resume_editor.app.api.routes.route_logic.user.get_password_hash",
    return_value="new_hashed_password",
)
def test_change_password_with_none_attributes(
    mock_get_hash,
    mock_verify,
    mock_get_session_local,
    mock_user_count,
    authenticated_cookie_client,
    test_user,
):
    """
    Test successful password change when user attributes are initially None.
    """
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, mock_db = authenticated_cookie_client
    test_user.attributes = None  # Set attributes to None
    original_hashed_password = test_user.hashed_password

    client.post(
        "/api/users/change-password",
        data={
            "current_password": "old_password",
            "new_password": "new_password",
            "confirm_new_password": "new_password",
        },
        follow_redirects=False,
    )

    mock_verify.assert_called_once_with("old_password", original_hashed_password)
    mock_get_hash.assert_called_once_with("new_password")
    assert test_user.hashed_password == "new_hashed_password"
    assert test_user.attributes is not None
    assert test_user.attributes["force_password_change"] is False
    mock_db.commit.assert_called_once()
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch(
    "resume_editor.app.api.routes.route_logic.user.get_password_hash",
    return_value="new_hashed_password",
)
def test_change_password_forced_without_current_password(
    mock_get_hash,
    mock_get_session_local,
    mock_user_count,
    authenticated_cookie_client,
    test_user,
):
    """
    Test successful forced password change without providing current password.
    """
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, mock_db = authenticated_cookie_client
    test_user.attributes = {"force_password_change": True}

    response = client.post(
        "/api/users/change-password",
        data={"new_password": "new_password", "confirm_new_password": "new_password"},
        follow_redirects=False,
    )

    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == "/dashboard"
    mock_get_hash.assert_called_once_with("new_password")
    assert test_user.hashed_password == "new_hashed_password"
    assert test_user.attributes["force_password_change"] is False
    mock_db.commit.assert_called_once()
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch(
    "resume_editor.app.api.routes.route_logic.user.get_password_hash",
    return_value="new_hashed_password",
)
@patch("resume_editor.app.api.routes.route_logic.user.verify_password")
def test_change_password_forced_with_incorrect_current_password_succeeds(
    mock_verify,
    mock_get_hash,
    mock_get_session_local,
    mock_user_count,
    authenticated_cookie_client,
    test_user,
):
    """
    Test forced password change with incorrect current password succeeds.

    The current password check should be bypassed during a forced change.
    """
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, mock_db = authenticated_cookie_client
    test_user.attributes = {"force_password_change": True}
    test_user.hashed_password = "hashed_old_password"

    response = client.post(
        "/api/users/change-password",
        data={
            "current_password": "wrong_password",
            "new_password": "new_password",
            "confirm_new_password": "new_password",
        },
        follow_redirects=False,
    )

    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == "/dashboard"

    mock_verify.assert_not_called()
    mock_get_hash.assert_called_once_with("new_password")
    assert test_user.hashed_password == "new_hashed_password"
    assert test_user.attributes["force_password_change"] is False
    mock_db.commit.assert_called_once()


@patch(
    "resume_editor.app.api.routes.route_logic.user.verify_password",
    return_value=True,
)
@patch(
    "resume_editor.app.api.routes.route_logic.user.get_password_hash",
    return_value="new_hashed_password",
)
def test_change_password_logic_when_attributes_is_none(
    mock_get_hash,
    mock_verify,
    test_user,
):
    """Test change_password logic directly when attributes are None."""
    mock_db = Mock(spec=Session)
    test_user.attributes = None
    original_hashed_password = test_user.hashed_password

    user_logic.change_password(
        db=mock_db,
        user=test_user,
        current_password="old_password",
        new_password="new_password",
    )

    mock_verify.assert_called_once_with("old_password", original_hashed_password)
    mock_get_hash.assert_called_once_with("new_password")
    assert test_user.hashed_password == "new_hashed_password"
    assert test_user.attributes is not None
    assert test_user.attributes["force_password_change"] is False
    mock_db.commit.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch(
    "resume_editor.app.api.routes.route_logic.user.verify_password",
    return_value=False,
)
def test_change_password_incorrect_current_password(
    mock_verify,
    mock_get_session_local,
    mock_user_count,
    authenticated_cookie_client,
    test_user,
):
    """Test password change with incorrect current password."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, mock_db = authenticated_cookie_client
    test_user.hashed_password = "hashed_old_password"
    response = client.post(
        "/api/users/change-password",
        data={
            "current_password": "wrong_password",
            "new_password": "new_password",
            "confirm_new_password": "new_password",
        },
        headers={"Accept": "application/json"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Incorrect current password"
    mock_verify.assert_called_once_with("wrong_password", "hashed_old_password")
    mock_db.commit.assert_not_called()
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_change_password_unauthenticated_api(
    mock_get_session_local, mock_user_count, client_with_db
):
    """Test unauthenticated POST to change password with API header returns 401."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, _ = client_with_db
    response = client.post(
        "/api/users/change-password",
        data={
            "current_password": "old_password",
            "new_password": "new_password",
            "confirm_new_password": "new_password",
        },
        headers={"Accept": "application/json"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Could not validate credentials"
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_change_password_unauthenticated_browser(
    mock_get_session_local, mock_user_count, client_with_db
):
    """Test unauthenticated POST to change password with browser header redirects."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, _ = client_with_db
    response = client.post(
        "/api/users/change-password",
        data={
            "current_password": "old_password",
            "new_password": "new_password",
            "confirm_new_password": "new_password",
        },
        headers={"Accept": "text/html"},
        follow_redirects=False,
    )
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"] == "http://testserver/login"
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_change_password_confirmation_mismatch(
    mock_get_session_local, mock_user_count, authenticated_cookie_client
):
    """Test password change when new password and confirmation don't match."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, _ = authenticated_cookie_client
    response = client.post(
        "/api/users/change-password",
        data={
            "current_password": "old_password",
            "new_password": "new_password",
            "confirm_new_password": "different_password",
        },
        headers={"Accept": "text/html"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "New passwords do not match." in response.text
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_change_password_confirmation_mismatch_json(
    mock_get_session_local, mock_user_count, authenticated_cookie_client
):
    """Test password change with confirmation mismatch returns JSON."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, _ = authenticated_cookie_client
    response = client.post(
        "/api/users/change-password",
        data={
            "current_password": "old_password",
            "new_password": "new_password",
            "confirm_new_password": "different_password",
        },
        headers={"Accept": "application/json"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "New passwords do not match."
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_get_change_password_page(
    mock_get_session_local, mock_user_count, authenticated_cookie_client
):
    """Test the GET /change-password page renders correctly."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, _ = authenticated_cookie_client
    response = client.get("/api/users/change-password")
    assert response.status_code == status.HTTP_200_OK
    assert "Change Your Password" in response.text
    assert "/api/users/change-password" in response.text
    assert "current_password" in response.text
    assert "new_password" in response.text
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch(
    "resume_editor.app.api.routes.route_logic.user.verify_password",
    return_value=True,
)
@patch(
    "resume_editor.app.api.routes.route_logic.user.get_password_hash",
    return_value="new_hashed_password",
)
def test_change_password_success_partial_htmx(
    mock_get_hash,
    mock_verify,
    mock_get_session_local,
    mock_user_count,
    authenticated_cookie_client,
    test_user,
):
    """Test successful password change with a partial HTMX request returns HTML snippet."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, mock_db = authenticated_cookie_client
    test_user.attributes = {}  # Not a forced change

    response = client.post(
        "/api/users/change-password",
        data={
            "current_password": "old_password",
            "new_password": "new_password",
            "confirm_new_password": "new_password",
        },
        headers={"HX-Target": "password-notification"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "Your password has been changed" in response.text
    mock_get_hash.assert_called_once_with("new_password")
    mock_db.commit.assert_called_once()
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_change_password_mismatch_partial_htmx(
    mock_get_session_local, mock_user_count, authenticated_cookie_client
):
    """Test password mismatch with a partial HTMX request returns error snippet."""
    mock_session = Mock(spec=Session)
    mock_get_session_local.return_value = lambda: mock_session
    client, _ = authenticated_cookie_client
    response = client.post(
        "/api/users/change-password",
        data={
            "current_password": "old_password",
            "new_password": "new_password",
            "confirm_new_password": "different_password",
        },
        headers={"HX-Target": "password-notification"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "New passwords do not match." in response.text
    assert "Error!" in response.text
    mock_user_count.assert_called_once()
