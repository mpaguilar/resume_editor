from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.user import (
    create_new_user,
    get_user_by_email,
    get_user_by_username,
)
from resume_editor.app.core.auth import get_current_user
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
    )
    user.id = 1
    return user


@pytest.fixture
def client_with_db():
    """Fixture for a test client with a mocked database."""
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


# Tests for /register
@patch("resume_editor.app.api.routes.user.get_user_by_username", return_value=None)
@patch("resume_editor.app.api.routes.user.get_user_by_email", return_value=None)
@patch("resume_editor.app.api.routes.user.create_new_user")
def test_register_user_success(
    mock_create_user,
    mock_get_by_email,
    mock_get_by_username,
    client_with_db,
    test_user,
):
    """Test successful user registration."""
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
    assert data["attributes"] is None
    mock_get_by_username.assert_called_once()
    mock_get_by_email.assert_called_once()
    mock_create_user.assert_called_once()


@patch("resume_editor.app.api.routes.user.get_user_by_username")
def test_register_user_duplicate_username(
    mock_get_by_username,
    client_with_db,
    test_user,
):
    """Test registration with a duplicate username fails."""
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


@patch("resume_editor.app.api.routes.user.get_user_by_username", return_value=None)
@patch("resume_editor.app.api.routes.user.get_user_by_email")
def test_register_user_duplicate_email(
    mock_get_by_email,
    mock_get_by_username,
    client_with_db,
    test_user,
):
    """Test registration with a duplicate email fails."""
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


# Tests for /login
def test_login_success(client_with_db, test_user):
    """Test successful user login."""
    client, mock_db = client_with_db
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

    # Verify the token
    from jose import jwt

    from resume_editor.app.core.config import get_settings

    settings = get_settings()
    decoded_token = jwt.decode(
        data["access_token"],
        settings.secret_key,
        algorithms=[settings.algorithm],
    )
    assert decoded_token["sub"] == test_user.username


def test_login_failure_user_not_found(client_with_db):
    """Test that login fails when the user is not found."""
    client, mock_db = client_with_db
    mock_db.query.return_value.filter.return_value.first.return_value = None
    response = client.post(
        "/api/users/login",
        data={"username": "wronguser", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_login_failure_wrong_password(client_with_db, test_user):
    """Test that login fails with an incorrect password."""
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


# Tests for /settings
@patch("resume_editor.app.api.routes.user.settings_crud.get_user_settings")
def test_get_user_settings(mock_get_settings, authenticated_client, test_user):
    """Test successfully fetching user settings."""
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


@patch("resume_editor.app.api.routes.user.settings_crud.get_user_settings")
def test_get_user_settings_none(mock_get_settings, authenticated_client):
    """Test fetching settings when none are set."""
    client, _ = authenticated_client
    mock_get_settings.return_value = None
    response = client.get("/api/users/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["llm_endpoint"] is None
    assert data["api_key_is_set"] is False


@patch("resume_editor.app.api.routes.user.settings_crud.update_user_settings")
def test_update_user_settings(mock_update_settings, authenticated_client, test_user):
    """Test successfully updating user settings."""
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


# Tests for auth flow
def test_access_protected_route_with_token(client_with_db, test_user):
    """Test accessing a protected route with a valid JWT token."""
    client, mock_db = client_with_db
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
    with patch(
        "resume_editor.app.api.routes.user.settings_crud.get_user_settings"
    ) as mock_get_user_settings:
        mock_get_user_settings.return_value = (
            None  # We don't care about the return value
        )

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


def test_access_protected_route_no_token(client_with_db):
    """Test accessing a protected route without a token fails."""
    client, _ = client_with_db
    response = client.get("/api/users/settings")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_access_protected_route_invalid_token(client_with_db):
    """Test accessing a protected route with a malformed/invalid token."""
    client, _ = client_with_db
    headers = {"Authorization": "Bearer invalidtoken"}
    response = client.get("/api/users/settings", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


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
        username="newuser", email="new@example.com", password="password"
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
