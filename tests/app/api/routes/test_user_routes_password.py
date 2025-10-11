from unittest.mock import Mock, patch

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_logic import user as user_logic
from resume_editor.app.core.auth import get_current_user_from_cookie


# Fixtures
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
