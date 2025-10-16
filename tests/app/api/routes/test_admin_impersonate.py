from unittest.mock import MagicMock, patch

from fastapi import FastAPI, HTTPException, status
from jose import jwt

from resume_editor.app.core.auth import get_current_admin_user, get_current_user
from resume_editor.app.core.config import get_settings
from resume_editor.app.database.database import get_db
from resume_editor.app.models.user import User, UserData


def setup_dependency_overrides(app: FastAPI, mock_db: MagicMock, mock_user: User | None):
    """
    Helper to set up dependency overrides for tests.

    Args:
        app (FastAPI): The FastAPI app instance.
        mock_db (MagicMock): The mock database session.
        mock_user (User | None): The mock user.
    """

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db
    app.dependency_overrides[get_current_admin_user] = lambda: mock_user


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_admin_impersonate_user_unauthorized(
    mock_get_session_local, mock_user_count, client
):
    """Test that an unauthenticated user cannot access the impersonation endpoint."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    response = client.post("/api/admin/impersonate/someuser")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch("resume_editor.app.api.routes.user.settings_crud.get_user_settings")
@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_username_admin")
def test_admin_impersonate_user_success_and_use_token(
    mock_get_user_by_username_admin,
    mock_get_user_settings,
    mock_get_session_local,
    mock_user_count,
    client,
    app,
):
    """Test successful impersonation and using the token to access a protected route."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    mock_db = MagicMock()
    mock_admin_user = User(
        data=UserData(
            username="admin", email="admin@test.com", hashed_password="pw", id_=1
        )
    )
    setup_dependency_overrides(app, mock_db, mock_admin_user)

    mock_target_user = User(
        data=UserData(
            username="target", email="target@test.com", hashed_password="pw", id_=2
        )
    )

    mock_get_user_by_username_admin.return_value = mock_target_user

    # Configure mock DB to return the target user when get_current_user queries for it
    mock_db.query.return_value.filter.return_value.first.return_value = (
        mock_target_user
    )

    test_settings = get_settings()
    app.dependency_overrides[get_settings] = lambda: test_settings

    response = client.post(f"/api/admin/impersonate/{mock_target_user.username}")
    assert response.status_code == status.HTTP_200_OK
    token_data = response.json()
    impersonation_token = token_data["access_token"]

    # Decode the token and verify claims
    decoded_token = jwt.decode(
        impersonation_token,
        test_settings.secret_key,
        algorithms=[test_settings.algorithm],
    )
    assert decoded_token["sub"] == mock_target_user.username
    assert decoded_token["impersonator"] == mock_admin_user.username

    # Now use the token to access a protected route
    def get_mock_target_user():
        return mock_target_user

    app.dependency_overrides[get_current_user] = get_mock_target_user

    mock_get_user_settings.return_value = (
        None  # We don't care about the result, just the call
    )
    headers = {"Authorization": f"Bearer {impersonation_token}"}
    settings_response = client.get("/api/users/settings", headers=headers)

    assert settings_response.status_code == 200
    mock_get_user_settings.assert_called_once()
    # get_user_settings crud takes user_id
    (
        _db,
        user_id,
    ) = mock_get_user_settings.call_args.args
    assert user_id == mock_target_user.id
    # Once for impersonation, once for settings get
    assert mock_user_count.call_count == 2


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_admin_impersonate_user_forbidden(
    mock_get_session_local, mock_user_count, client, app
):
    """Test that a non-admin user cannot impersonate another user."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session

    def raise_forbidden():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have administrative privileges",
        )

    app.dependency_overrides[get_current_admin_user] = raise_forbidden

    response = client.post("/api/admin/impersonate/someuser")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_username_admin")
def test_admin_impersonate_user_not_found(
    mock_get_user_by_username_admin, mock_get_session_local, mock_user_count, client, app
):
    """Test impersonation attempt on a non-existent user."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    mock_db = MagicMock()
    mock_admin_user = User(
        data=UserData(
            username="admin",
            email="admin@test.com",
            hashed_password="pw",
        )
    )
    setup_dependency_overrides(app, mock_db, mock_admin_user)

    mock_get_user_by_username_admin.return_value = None

    response = client.post("/api/admin/impersonate/nonexistent")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"
    mock_get_user_by_username_admin.assert_called_once_with(
        db=mock_db,
        username="nonexistent",
    )
    mock_user_count.assert_called_once()
