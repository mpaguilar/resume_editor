from unittest.mock import MagicMock, patch

import pytest
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.testclient import TestClient
from jose import JWTError
from sqlalchemy.orm import Session

from resume_editor.app.core.auth import (
    _verify_admin_privileges,
    get_current_admin_user,
    get_current_admin_user_from_cookie,
    get_current_user,
    get_current_user_from_cookie,
    get_optional_current_user_from_cookie,
)
from resume_editor.app.models.role import Role
from resume_editor.app.models.user import User

# --- Tests for get_current_user ---


@patch("resume_editor.app.core.auth.get_settings")
@patch("resume_editor.app.core.auth.jwt.decode")
def test_get_current_user_success(mock_jwt_decode, mock_get_settings):
    """Test successful authentication and user retrieval."""
    mock_get_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
    )
    mock_db = MagicMock(spec=Session)
    expected_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
    )
    mock_db.query.return_value.filter.return_value.first.return_value = expected_user
    mock_jwt_decode.return_value = {"sub": "testuser"}
    token = "valid-token"

    user = get_current_user(token=token, db=mock_db)

    assert user == expected_user
    mock_db.query.assert_called_once_with(User)
    mock_jwt_decode.assert_called_once()


@patch("resume_editor.app.core.auth.get_settings")
@patch("resume_editor.app.core.auth.jwt.decode", side_effect=JWTError)
def test_get_current_user_invalid_token(mock_jwt_decode, mock_get_settings):
    """Test authentication with an invalid (malformed) token."""
    mock_get_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
    )
    mock_db = MagicMock(spec=Session)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="invalid-token", db=mock_db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


@patch("resume_editor.app.core.auth.get_settings")
@patch("resume_editor.app.core.auth.jwt.decode")
def test_get_current_user_no_username(mock_jwt_decode, mock_get_settings):
    """Test authentication with a token that has no username (sub)."""
    mock_get_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
    )
    mock_db = MagicMock(spec=Session)
    mock_jwt_decode.return_value = {"id": 1}  # No 'sub' key

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="token-no-sub", db=mock_db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


@patch("resume_editor.app.core.auth.get_settings")
@patch("resume_editor.app.core.auth.jwt.decode")
def test_get_current_user_user_not_found(mock_jwt_decode, mock_get_settings):
    """Test authentication where user from token is not in the database."""
    mock_get_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
    )
    mock_db = MagicMock(spec=Session)
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_jwt_decode.return_value = {"sub": "nonexistent"}

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="token-for-nonexistent-user", db=mock_db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


# --- Tests for get_current_admin_user ---

# Setup for get_current_admin_user tests
app = FastAPI()


@app.get("/admin-only")
async def admin_only_route(
    current_user: User = Depends(get_current_admin_user),
):
    """A test route protected by the get_current_admin_user dependency."""
    return {"message": "Welcome admin"}


client = TestClient(app)


def test_get_current_admin_user_with_admin_role():
    """Test that a user with the 'admin' role is granted access."""
    admin_user = User(
        username="admin",
        email="admin@test.com",
        hashed_password="password",
    )
    admin_role = Role(name="admin")
    admin_user.roles = [admin_role]

    def override_get_current_user():
        return admin_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    response = client.get("/admin-only")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome admin"}

    app.dependency_overrides.clear()


def test_get_current_admin_user_without_admin_role():
    """Test that a user without the 'admin' role is denied access."""
    user = User(username="user", email="user@test.com", hashed_password="password")
    user_role = Role(name="user")
    user.roles = [user_role]

    def override_get_current_user():
        return user

    app.dependency_overrides[get_current_user] = override_get_current_user

    response = client.get("/admin-only")
    assert response.status_code == 403
    assert response.json() == {"detail": "The user does not have admin privileges"}

    app.dependency_overrides.clear()


@pytest.fixture
def mock_request():
    """Provides a mock FastAPI Request object."""
    return MagicMock(spec=Request)


# --- Tests for get_current_user_from_cookie ---


@patch("resume_editor.app.core.auth.get_settings")
@patch("resume_editor.app.core.auth.jwt.decode")
def test_get_current_user_from_cookie_success(
    mock_jwt_decode,
    mock_get_settings,
    mock_request,
):
    """Test successful user retrieval from a cookie."""
    mock_get_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
    )
    mock_db = MagicMock(spec=Session)
    expected_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
    )
    mock_db.query.return_value.filter.return_value.first.return_value = expected_user
    mock_jwt_decode.return_value = {"sub": "testuser"}
    mock_request.cookies.get.return_value = "valid-token"

    user = get_current_user_from_cookie(request=mock_request, db=mock_db)

    assert user == expected_user
    mock_request.cookies.get.assert_called_once_with("access_token")
    mock_db.query.assert_called_once_with(User)
    mock_jwt_decode.assert_called_once()


def test_get_current_user_from_cookie_no_token(mock_request):
    """Test get_current_user_from_cookie when no token is present."""
    mock_db = MagicMock(spec=Session)
    mock_request.cookies.get.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_current_user_from_cookie(request=mock_request, db=mock_db)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"
    mock_request.cookies.get.assert_called_once_with("access_token")


@patch("resume_editor.app.core.auth.get_settings")
@patch("resume_editor.app.core.auth.jwt.decode", side_effect=JWTError)
def test_get_current_user_from_cookie_jwt_error(
    mock_jwt_decode,
    mock_get_settings,
    mock_request,
):
    """Test get_current_user_from_cookie with a malformed JWT."""
    mock_get_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
    )
    mock_db = MagicMock(spec=Session)
    mock_request.cookies.get.return_value = "invalid-token"

    with pytest.raises(HTTPException) as exc_info:
        get_current_user_from_cookie(request=mock_request, db=mock_db)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"


@patch("resume_editor.app.core.auth.get_settings")
@patch("resume_editor.app.core.auth.jwt.decode")
def test_get_current_user_from_cookie_no_username(
    mock_jwt_decode,
    mock_get_settings,
    mock_request,
):
    """Test get_current_user_from_cookie with a token that has no username."""
    mock_get_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
    )
    mock_db = MagicMock(spec=Session)
    mock_jwt_decode.return_value = {"id": 1}  # No 'sub' key
    mock_request.cookies.get.return_value = "token-no-sub"

    with pytest.raises(HTTPException) as exc_info:
        get_current_user_from_cookie(request=mock_request, db=mock_db)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"


@patch("resume_editor.app.core.auth.get_settings")
@patch("resume_editor.app.core.auth.jwt.decode")
def test_get_current_user_from_cookie_user_not_found(
    mock_jwt_decode,
    mock_get_settings,
    mock_request,
):
    """Test get_current_user_from_cookie where user from token is not in DB."""
    mock_get_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
    )
    mock_db = MagicMock(spec=Session)
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_jwt_decode.return_value = {"sub": "nonexistent"}
    mock_request.cookies.get.return_value = "token-for-nonexistent-user"

    with pytest.raises(HTTPException) as exc_info:
        get_current_user_from_cookie(request=mock_request, db=mock_db)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"


# --- Tests for get_optional_current_user_from_cookie ---


@patch("resume_editor.app.core.auth.get_current_user_from_cookie")
def test_get_optional_current_user_from_cookie_success(
    mock_get_current_user_from_cookie,
    mock_request,
):
    """Test successful optional user retrieval."""
    mock_db = MagicMock(spec=Session)
    expected_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
    )
    mock_get_current_user_from_cookie.return_value = expected_user

    user = get_optional_current_user_from_cookie(request=mock_request, db=mock_db)

    assert user == expected_user
    mock_get_current_user_from_cookie.assert_called_once_with(
        request=mock_request,
        db=mock_db,
    )


@patch(
    "resume_editor.app.core.auth.get_current_user_from_cookie",
    side_effect=HTTPException(status_code=401),
)
def test_get_optional_current_user_from_cookie_failure(
    mock_get_current_user_from_cookie,
    mock_request,
):
    """Test optional user retrieval when underlying function fails."""
    mock_db = MagicMock(spec=Session)

    user = get_optional_current_user_from_cookie(request=mock_request, db=mock_db)

    assert user is None
    mock_get_current_user_from_cookie.assert_called_once_with(
        request=mock_request,
        db=mock_db,
    )


def test_get_current_admin_user_with_no_roles():
    """Test that a user with no roles is denied access."""
    user = User(username="user", email="user@test.com", hashed_password="password")
    user.roles = []

    def override_get_current_user():
        return user

    app.dependency_overrides[get_current_user] = override_get_current_user

    response = client.get("/admin-only")
    assert response.status_code == 403
    assert response.json() == {"detail": "The user does not have admin privileges"}

    app.dependency_overrides.clear()


# --- Tests for get_current_admin_user_from_cookie ---


@app.get("/admin-only-cookie")
async def admin_only_cookie_route(
    current_user: User = Depends(get_current_admin_user_from_cookie),
):
    """A test route protected by get_current_admin_user_from_cookie."""
    return {"message": "Welcome admin from cookie"}


def test_get_current_admin_user_from_cookie_with_admin_role():
    """Test that an admin user from a cookie is granted access."""
    admin_user = User(
        username="admin",
        email="admin@test.com",
        hashed_password="password",
    )
    admin_role = Role(name="admin")
    admin_user.roles = [admin_role]

    def override_get_current_user_from_cookie():
        return admin_user

    app.dependency_overrides[get_current_user_from_cookie] = (
        override_get_current_user_from_cookie
    )

    response = client.get("/admin-only-cookie")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome admin from cookie"}

    app.dependency_overrides.clear()


def test_get_current_admin_user_from_cookie_without_admin_role():
    """Test that a non-admin user from a cookie is denied access."""
    user = User(username="user", email="user@test.com", hashed_password="password")
    user_role = Role(name="user")
    user.roles = [user_role]

    def override_get_current_user_from_cookie():
        return user

    app.dependency_overrides[get_current_user_from_cookie] = (
        override_get_current_user_from_cookie
    )

    response = client.get("/admin-only-cookie")
    assert response.status_code == 403
    assert response.json() == {"detail": "The user does not have admin privileges"}

    app.dependency_overrides.clear()


# --- Tests for _verify_admin_privileges ---


def test_verify_admin_privileges_with_admin_role():
    """Test that a user with the 'admin' role is verified."""
    admin_user = User(
        username="admin",
        email="admin@test.com",
        hashed_password="password",
    )
    admin_user.roles = [Role(name="admin")]
    assert _verify_admin_privileges(admin_user) == admin_user


def test_verify_admin_privileges_without_admin_role():
    """Test that a user without the 'admin' role raises an HTTPException."""
    user = User(username="user", email="user@test.com", hashed_password="password")
    user.roles = [Role(name="user")]
    with pytest.raises(HTTPException) as exc_info:
        _verify_admin_privileges(user)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "The user does not have admin privileges"


def test_verify_admin_privileges_with_no_roles():
    """Test that a user with no roles raises an HTTPException."""
    user = User(username="user", email="user@test.com", hashed_password="password")
    user.roles = []
    with pytest.raises(HTTPException) as exc_info:
        _verify_admin_privileges(user)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "The user does not have admin privileges"
