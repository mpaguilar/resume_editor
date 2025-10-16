from unittest.mock import MagicMock, patch

import pytest
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.testclient import TestClient
from jose import JWTError
from sqlalchemy.orm import Session

from resume_editor.app.core.auth import (
    get_current_admin_user,
    get_current_admin_user_from_cookie,
    get_current_user,
    get_current_user_from_cookie,
    get_optional_current_user_from_cookie,
    verify_admin_privileges,
)
from resume_editor.app.models.role import Role
from resume_editor.app.models.user import User, UserData

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
        data=UserData(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
        )
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
        data=UserData(
            username="admin",
            email="admin@test.com",
            hashed_password="password",
        )
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
    user = User(
        data=UserData(username="user", email="user@test.com", hashed_password="password")
    )
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
        data=UserData(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
        )
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

    # Test browser request
    mock_request.headers = {"Accept": "text/html"}
    mock_request.url_for.return_value = "http://testserver/login"
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_from_cookie(request=mock_request, db=mock_db)
    assert exc_info.value.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert exc_info.value.headers["Location"] == "http://testserver/login"

    # Test API request
    mock_request.headers = {"Accept": "application/json"}
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_from_cookie(request=mock_request, db=mock_db)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"

    assert mock_request.cookies.get.call_count == 2


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

    # Test browser request
    mock_request.headers = {"Accept": "text/html"}
    mock_request.url_for.return_value = "http://testserver/login"
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_from_cookie(request=mock_request, db=mock_db)
    assert exc_info.value.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert exc_info.value.headers["Location"] == "http://testserver/login"

    # Test API request
    mock_request.headers = {"Accept": "application/json"}
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

    # Test browser request
    mock_request.headers = {"Accept": "text/html"}
    mock_request.url_for.return_value = "http://testserver/login"
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_from_cookie(request=mock_request, db=mock_db)
    assert exc_info.value.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert exc_info.value.headers["Location"] == "http://testserver/login"

    # Test API request
    mock_request.headers = {"Accept": "application/json"}
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

    # Test browser request
    mock_request.headers = {"Accept": "text/html"}
    mock_request.url_for.return_value = "http://testserver/login"
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_from_cookie(request=mock_request, db=mock_db)
    assert exc_info.value.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert exc_info.value.headers["Location"] == "http://testserver/login"

    # Test API request
    mock_request.headers = {"Accept": "application/json"}
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_from_cookie(request=mock_request, db=mock_db)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"


@patch("resume_editor.app.core.auth.get_settings")
@patch("resume_editor.app.core.auth.jwt.decode")
def test_get_current_user_from_cookie_force_change_redirect(
    mock_jwt_decode,
    mock_get_settings,
    mock_request,
):
    """Test user is redirected if force_password_change is true."""
    mock_get_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
    )
    mock_db = MagicMock(spec=Session)
    user_with_force = User(
        data=UserData(
            username="forceuser",
            email="force@example.com",
            hashed_password="hashed",
            attributes={"force_password_change": True},
            id_=2,
        )
    )
    mock_db.query.return_value.filter.return_value.first.return_value = user_with_force
    mock_jwt_decode.return_value = {"sub": "forceuser"}
    mock_request.cookies.get.return_value = "valid-token"
    mock_request.url.path = "/dashboard"
    # Ensure hx-request is not in headers for this test
    mock_request.headers = {}

    mock_request.url_for.return_value = "http://testserver/api/users/change-password"
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_from_cookie(request=mock_request, db=mock_db)

    assert exc_info.value.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert (
        exc_info.value.headers["Location"] == "http://testserver/api/users/change-password"
    )


@patch("resume_editor.app.core.auth.get_settings")
@patch("resume_editor.app.core.auth.jwt.decode")
def test_get_current_user_from_cookie_force_change_htmx_redirect(
    mock_jwt_decode,
    mock_get_settings,
    mock_request,
):
    """Test user is redirected via HTMX if force_password_change is true."""
    mock_get_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
    )
    mock_db = MagicMock(spec=Session)
    user_with_force = User(
        data=UserData(
            username="forceuser",
            email="force@example.com",
            hashed_password="hashed",
            attributes={"force_password_change": True},
            id_=2,
        )
    )
    mock_db.query.return_value.filter.return_value.first.return_value = user_with_force
    mock_jwt_decode.return_value = {"sub": "forceuser"}
    mock_request.cookies.get.return_value = "valid-token"
    mock_request.url.path = "/dashboard"
    mock_request.headers = {"hx-request": "true"}

    mock_request.url_for.return_value = "http://testserver/api/users/change-password"
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_from_cookie(request=mock_request, db=mock_db)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert (
        exc_info.value.headers["HX-Redirect"]
        == "http://testserver/api/users/change-password"
    )


@pytest.mark.parametrize(
    "path",
    ["/api/users/change-password", "/logout", "/static/style.css"],
)
@patch("resume_editor.app.core.auth.get_settings")
@patch("resume_editor.app.core.auth.jwt.decode")
def test_get_current_user_from_cookie_force_change_no_redirect_on_allowed_paths(
    mock_jwt_decode,
    mock_get_settings,
    mock_request,
    path,
):
    """Test user is not redirected on allowed paths when force_password_change is true."""
    mock_get_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
    )
    mock_db = MagicMock(spec=Session)
    user_with_force = User(
        data=UserData(
            username="forceuser",
            email="force@example.com",
            hashed_password="hashed",
            attributes={"force_password_change": True},
            id_=2,
        )
    )
    mock_db.query.return_value.filter.return_value.first.return_value = user_with_force
    mock_jwt_decode.return_value = {"sub": "forceuser"}
    mock_request.cookies.get.return_value = "valid-token"
    mock_request.url.path = path

    user = get_current_user_from_cookie(request=mock_request, db=mock_db)
    assert user == user_with_force


@patch("resume_editor.app.core.auth.get_settings")
@patch("resume_editor.app.core.auth.jwt.decode")
def test_get_current_user_from_cookie_no_force_change(
    mock_jwt_decode,
    mock_get_settings,
    mock_request,
):
    """Test user is not redirected if force_password_change is false."""
    mock_get_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
    )
    mock_db = MagicMock(spec=Session)
    user_no_force = User(
        data=UserData(
            username="noforceuser",
            email="noforce@example.com",
            hashed_password="hashed",
            attributes={"force_password_change": False},
            id_=3,
        )
    )
    mock_db.query.return_value.filter.return_value.first.return_value = user_no_force
    mock_jwt_decode.return_value = {"sub": "noforceuser"}
    mock_request.cookies.get.return_value = "valid-token"
    mock_request.url.path = "/dashboard"

    user = get_current_user_from_cookie(request=mock_request, db=mock_db)
    assert user == user_no_force


# --- Tests for get_optional_current_user_from_cookie ---


@patch("resume_editor.app.core.auth.get_current_user_from_cookie")
def test_get_optional_current_user_from_cookie_success(
    mock_get_current_user_from_cookie,
    mock_request,
):
    """Test successful optional user retrieval."""
    mock_db = MagicMock(spec=Session)
    expected_user = User(
        data=UserData(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
        )
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
    side_effect=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    ),
)
def test_get_optional_current_user_from_cookie_returns_none_on_auth_error(
    mock_get_current_user_from_cookie,
    mock_request,
):
    """Test optional user retrieval returns None on a standard auth error."""
    mock_db = MagicMock(spec=Session)

    user = get_optional_current_user_from_cookie(request=mock_request, db=mock_db)

    assert user is None
    mock_get_current_user_from_cookie.assert_called_once_with(
        request=mock_request,
        db=mock_db,
    )


@patch("resume_editor.app.core.auth.get_current_user_from_cookie")
def test_get_optional_current_user_from_cookie_reraises_other_exceptions(
    mock_get_current_user_from_cookie,
    mock_request,
):
    """Test that exceptions other than auth errors are re-raised."""
    mock_db = MagicMock(spec=Session)
    redirect_exception = HTTPException(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        detail="Password change required",
    )
    mock_get_current_user_from_cookie.side_effect = redirect_exception

    with pytest.raises(HTTPException) as exc_info:
        get_optional_current_user_from_cookie(request=mock_request, db=mock_db)

    assert exc_info.value == redirect_exception


def test_get_current_admin_user_with_no_roles():
    """Test that a user with no roles is denied access."""
    user = User(
        data=UserData(username="user", email="user@test.com", hashed_password="password")
    )
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
        data=UserData(
            username="admin",
            email="admin@test.com",
            hashed_password="password",
        )
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
    user = User(
        data=UserData(username="user", email="user@test.com", hashed_password="password")
    )
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


# --- Tests for verify_admin_privileges ---


def test_verify_admin_privileges_with_admin_role():
    """Test that a user with the 'admin' role is verified."""
    admin_user = User(
        data=UserData(
            username="admin",
            email="admin@test.com",
            hashed_password="password",
        )
    )
    admin_user.roles = [Role(name="admin")]
    assert verify_admin_privileges(admin_user) == admin_user


def test_verify_admin_privileges_without_admin_role():
    """Test that a user without the 'admin' role raises an HTTPException."""
    user = User(
        data=UserData(username="user", email="user@test.com", hashed_password="password")
    )
    user.roles = [Role(name="user")]
    with pytest.raises(HTTPException) as exc_info:
        verify_admin_privileges(user)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "The user does not have admin privileges"


def test_verify_admin_privileges_with_no_roles():
    """Test that a user with no roles raises an HTTPException."""
    user = User(
        data=UserData(username="user", email="user@test.com", hashed_password="password")
    )
    user.roles = []
    with pytest.raises(HTTPException) as exc_info:
        verify_admin_privileges(user)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "The user does not have admin privileges"
