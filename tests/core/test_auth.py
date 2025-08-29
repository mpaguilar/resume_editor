from unittest.mock import MagicMock, patch

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from jose import JWTError
from sqlalchemy.orm import Session

from resume_editor.app.core.auth import get_current_admin_user, get_current_user
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
    admin_user = User(username="admin", email="admin@test.com", hashed_password="password")
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
