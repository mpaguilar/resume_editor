import logging
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from jose import jwt

from resume_editor.app.core.auth import get_current_admin_user, get_current_user
from resume_editor.app.core.config import Settings, get_settings
from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app
from resume_editor.app.models.role import Role
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)


@pytest.fixture
def app():
    """Fixture to create a new app for each test."""
    # To ensure settings are fresh for each test, we clear the cache.
    get_settings.cache_clear()
    _app = create_app()
    yield _app
    # Clear dependency overrides after test
    _app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    """Fixture to create a test client for each test."""
    with TestClient(app) as c:
        yield c


def setup_dependency_overrides(app, mock_db: MagicMock, mock_user: User | None):
    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db
    app.dependency_overrides[get_current_admin_user] = lambda: mock_user


@patch("resume_editor.app.api.routes.admin.admin_crud.create_user_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
@patch("resume_editor.app.api.routes.admin.get_db")
def test_admin_create_user_success(
    mock_get_db,
    mock_get_current_admin_user,
    mock_create_user_admin,
    client,
    app,
):
    """Test successful user creation by an admin."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin_user)

    created_user = MagicMock(spec=User)
    created_user.id = 2
    created_user.username = "newuser"
    created_user.email = "new@test.com"
    created_user.is_active = True
    created_user.roles = []
    created_user.attributes = None

    mock_create_user_admin.return_value = created_user

    response = client.post(
        "/api/admin/users/",
        json={
            "username": "newuser",
            "email": "new@test.com",
            "password": "password",
            "is_active": True,
            "attributes": None,
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "newuser"
    assert data["id"] == 2


def test_admin_get_users_forbidden(client, app):
    """Test that a non-admin user cannot list users."""

    def raise_forbidden():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have administrative privileges",
        )

    app.dependency_overrides[get_current_admin_user] = raise_forbidden

    response = client.get("/api/admin/users/")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_admin_get_users_unauthorized(client):
    """Test that an unauthenticated user cannot list users."""
    response = client.get("/api/admin/users/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@patch("resume_editor.app.api.routes.admin.admin_crud.get_users_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
@patch("resume_editor.app.api.routes.admin.get_db")
def test_admin_get_users_success(
    mock_get_db, mock_get_current_admin_user, mock_get_users_admin, client, app
):
    """Test successful listing of all users by an admin."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin_user)

    user1 = MagicMock(spec=User)
    user1.id = 2
    user1.username = "testuser1"
    user1.email = "test1@test.com"
    user1.is_active = True
    user1.roles = []
    user1.attributes = None
    user2 = MagicMock(spec=User)
    user2.id = 3
    user2.username = "testuser2"
    user2.email = "test2@test.com"
    user2.is_active = True
    user2.roles = []
    user2.attributes = None
    mock_get_users_admin.return_value = [user1, user2]

    response = client.get("/api/admin/users/")

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["username"] == "testuser1"
    assert response_data[1]["username"] == "testuser2"


@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
def test_admin_get_user_success(
    mock_get_current_admin_user, mock_get_user_by_id_admin, client, app
):
    """Test successful retrieval of a single user by ID by an admin."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin_user)

    user = MagicMock(spec=User)
    user.id = 2
    user.username = "testuser"
    user.email = "test@test.com"
    user.is_active = True
    user.roles = []
    user.attributes = None

    mock_get_user_by_id_admin.return_value = user

    response = client.get("/api/admin/users/2")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["username"] == "testuser"
    assert response_data["id"] == 2


@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
def test_admin_get_user_not_found(
    mock_get_current_admin_user, mock_get_user_by_id_admin, client, app
):
    """Test retrieving a non-existent user by an admin."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin_user)

    mock_get_user_by_id_admin.return_value = None

    response = client.get("/api/admin/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@patch("resume_editor.app.api.routes.admin.admin_crud.delete_user_admin")
@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
def test_admin_delete_user_success(
    mock_get_current_admin_user,
    mock_get_user_by_id_admin,
    mock_delete_user_admin,
    client,
    app,
):
    """Test successful deletion of a user by an admin."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin_user)

    user_to_delete = MagicMock(spec=User)
    mock_get_user_by_id_admin.return_value = user_to_delete

    response = client.delete("/api/admin/users/2")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_delete_user_admin.assert_called_with(mock_db, user=user_to_delete)


@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
def test_admin_delete_user_not_found(
    mock_get_current_admin_user, mock_get_user_by_id_admin, client, app
):
    """Test deleting a non-existent user by an admin."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin_user)

    mock_get_user_by_id_admin.return_value = None

    response = client.delete("/api/admin/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@patch("resume_editor.app.api.routes.admin.admin_crud.assign_role_to_user_admin")
@patch("resume_editor.app.api.routes.admin.admin_crud.get_role_by_name_admin")
@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
@patch("resume_editor.app.api.routes.admin.get_db")
def test_admin_assign_role_to_user_success(
    mock_get_db,
    mock_get_current_admin_user,
    mock_get_user_by_id_admin,
    mock_get_role_by_name_admin,
    mock_assign_role_to_user_admin,
    client,
    app,
):
    mock_db = MagicMock()
    mock_admin = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin)

    mock_user = MagicMock(spec=User)
    mock_user.id = 2
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    mock_user.is_active = True
    mock_user.attributes = {}
    mock_user.roles = []

    mock_role = MagicMock(spec=Role)
    mock_role.id = 1
    mock_role.name = "admin"

    mock_get_user_by_id_admin.return_value = mock_user
    mock_get_role_by_name_admin.return_value = mock_role
    mock_assign_role_to_user_admin.return_value = mock_user

    response = client.post("/api/admin/users/2/roles/admin")

    assert response.status_code == status.HTTP_200_OK
    mock_assign_role_to_user_admin.assert_called_once_with(
        db=mock_db, user=mock_user, role=mock_role
    )


@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
def test_admin_assign_role_user_not_found(
    mock_get_current_admin_user, mock_get_user_by_id_admin, client, app
):
    mock_db = MagicMock()
    mock_admin = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin)
    mock_get_user_by_id_admin.return_value = None

    response = client.post("/api/admin/users/2/roles/admin")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"


@patch("resume_editor.app.api.routes.admin.admin_crud.get_role_by_name_admin")
@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
@patch("resume_editor.app.api.routes.admin.get_db")
def test_admin_assign_role_role_not_found(
    mock_get_db,
    mock_get_current_admin_user,
    mock_get_user_by_id_admin,
    mock_get_role_by_name_admin,
    client,
    app,
):
    mock_db = MagicMock()
    mock_admin = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin)
    mock_user = MagicMock(spec=User)
    mock_get_user_by_id_admin.return_value = mock_user
    mock_get_role_by_name_admin.return_value = None

    response = client.post("/api/admin/users/2/roles/admin")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Role not found"


@patch("resume_editor.app.api.routes.admin.admin_crud.assign_role_to_user_admin")
@patch("resume_editor.app.api.routes.admin.admin_crud.get_role_by_name_admin")
@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
@patch("resume_editor.app.api.routes.admin.get_db")
def test_admin_assign_role_already_assigned(
    mock_get_db,
    mock_get_current_admin_user,
    mock_get_user_by_id_admin,
    mock_get_role_by_name_admin,
    mock_assign_role_to_user_admin,
    client,
    app,
):
    mock_db = MagicMock()
    mock_admin = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin)
    mock_role = MagicMock(spec=Role)
    mock_role.id = 1
    mock_role.name = "admin"
    mock_user = MagicMock(spec=User)
    mock_user.id = 2
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    mock_user.is_active = True
    mock_user.attributes = {}
    mock_user.roles = [mock_role]

    mock_get_user_by_id_admin.return_value = mock_user
    mock_get_role_by_name_admin.return_value = mock_role

    response = client.post("/api/admin/users/2/roles/admin")

    assert response.status_code == status.HTTP_200_OK
    # The user object should be returned directly without calling the assign function.
    response_data = response.json()
    assert response_data["username"] == "testuser"
    mock_assign_role_to_user_admin.assert_not_called()


@patch("resume_editor.app.api.routes.admin.admin_crud.remove_role_from_user_admin")
@patch("resume_editor.app.api.routes.admin.admin_crud.get_role_by_name_admin")
@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
@patch("resume_editor.app.api.routes.admin.get_db")
def test_admin_remove_role_from_user_success(
    mock_get_db,
    mock_get_current_admin_user,
    mock_get_user_by_id_admin,
    mock_get_role_by_name_admin,
    mock_remove_role_from_user_admin,
    client,
    app,
):
    mock_db = MagicMock()
    mock_admin = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin)
    mock_role = MagicMock(spec=Role)
    mock_role.id = 1
    mock_role.name = "admin"
    mock_user = MagicMock(spec=User)
    mock_user.id = 2
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    mock_user.is_active = True
    mock_user.attributes = {}
    mock_user.roles = [mock_role]

    mock_get_user_by_id_admin.return_value = mock_user
    mock_get_role_by_name_admin.return_value = mock_role
    mock_remove_role_from_user_admin.return_value = mock_user

    response = client.delete("/api/admin/users/2/roles/admin")

    assert response.status_code == status.HTTP_200_OK
    mock_remove_role_from_user_admin.assert_called_once_with(
        db=mock_db, user=mock_user, role=mock_role
    )


@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
def test_admin_remove_role_from_user_user_not_found(
    mock_get_current_admin_user, mock_get_user_by_id_admin, client, app
):
    mock_db = MagicMock()
    mock_admin = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin)
    mock_get_user_by_id_admin.return_value = None

    response = client.delete("/api/admin/users/2/roles/admin")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"


@patch("resume_editor.app.api.routes.admin.admin_crud.get_role_by_name_admin")
@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
@patch("resume_editor.app.api.routes.admin.get_db")
def test_admin_remove_role_from_user_role_not_found(
    mock_get_db,
    mock_get_current_admin_user,
    mock_get_user_by_id_admin,
    mock_get_role_by_name_admin,
    client,
    app,
):
    mock_db = MagicMock()
    mock_admin = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin)
    mock_user = MagicMock(spec=User)
    mock_get_user_by_id_admin.return_value = mock_user
    mock_get_role_by_name_admin.return_value = None

    response = client.delete("/api/admin/users/2/roles/admin")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Role not found"


@patch("resume_editor.app.api.routes.admin.admin_crud.get_role_by_name_admin")
@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
@patch("resume_editor.app.api.routes.admin.get_db")
def test_admin_remove_role_from_user_not_assigned(
    mock_get_db,
    mock_get_current_admin_user,
    mock_get_user_by_id_admin,
    mock_get_role_by_name_admin,
    client,
    app,
):
    mock_db = MagicMock()
    mock_admin = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin)
    mock_role = MagicMock(spec=Role)
    mock_user = MagicMock(spec=User)
    mock_user.roles = []

    mock_get_user_by_id_admin.return_value = mock_user
    mock_get_role_by_name_admin.return_value = mock_role

    response = client.delete("/api/admin/users/2/roles/admin")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "User does not have this role"


def test_admin_impersonate_user_unauthorized(client):
    """Test that an unauthenticated user cannot access the impersonation endpoint."""
    response = client.post("/api/admin/impersonate/someuser")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@patch("resume_editor.app.api.routes.user.settings_crud.get_user_settings")
@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_username_admin")
def test_admin_impersonate_user_success_and_use_token(
    mock_get_user_by_username_admin, mock_get_user_settings, client, app
):
    """Test successful impersonation and using the token to access a protected route."""
    mock_db = MagicMock()
    mock_admin_user = User(
        username="admin", email="admin@test.com", hashed_password="pw"
    )
    mock_admin_user.id = 1
    setup_dependency_overrides(app, mock_db, mock_admin_user)

    mock_target_user = User(
        username="target", email="target@test.com", hashed_password="pw"
    )
    mock_target_user.id = 2

    mock_get_user_by_username_admin.return_value = mock_target_user

    # Configure mock DB to return the target user when get_current_user queries for it
    mock_db.query.return_value.filter.return_value.first.return_value = mock_target_user

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


def test_admin_impersonate_user_forbidden(client, app):
    """Test that a non-admin user cannot impersonate another user."""

    def raise_forbidden():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have administrative privileges",
        )

    app.dependency_overrides[get_current_admin_user] = raise_forbidden

    response = client.post("/api/admin/impersonate/someuser")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_username_admin")
def test_admin_impersonate_user_not_found(mock_get_user_by_username_admin, client, app):
    """Test impersonation attempt on a non-existent user."""
    mock_db = MagicMock()
    mock_admin_user = User(
        username="admin", email="admin@test.com", hashed_password="pw"
    )
    setup_dependency_overrides(app, mock_db, mock_admin_user)

    mock_get_user_by_username_admin.return_value = None

    response = client.post("/api/admin/impersonate/nonexistent")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"
    mock_get_user_by_username_admin.assert_called_once_with(
        db=mock_db, username="nonexistent"
    )
