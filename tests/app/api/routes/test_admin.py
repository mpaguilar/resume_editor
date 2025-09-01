import logging
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from jose import jwt

from resume_editor.app.core.auth import get_current_admin_user, get_current_user
from resume_editor.app.core.config import get_settings
from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app
from resume_editor.app.models.role import Role
from resume_editor.app.models.user import User
from resume_editor.app.schemas.user import AdminUserUpdateRequest

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


@pytest.mark.parametrize(
    "attributes, expected_force_password_change",
    [
        (None, False),
        ({"key": "value"}, False),
        ({"force_password_change": True}, True),
        ({"force_password_change": False}, False),
    ],
)
@patch("resume_editor.app.api.routes.admin.admin_crud.create_user_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
@patch("resume_editor.app.api.routes.admin.get_db")
def test_admin_create_user_success(
    mock_get_db,
    mock_get_current_admin_user,
    mock_create_user_admin,
    attributes,
    expected_force_password_change,
    client,
    app,
):
    """Test successful user creation by an admin with different attributes."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin_user)

    created_user = MagicMock(spec=User)
    created_user.id = 2
    created_user.username = "newuser"
    created_user.email = "new@test.com"
    created_user.is_active = True
    created_user.roles = []
    created_user.attributes = attributes
    created_user.resumes = []
    created_user.last_login_at = None

    mock_create_user_admin.return_value = created_user

    response = client.post(
        "/api/admin/users/",
        json={
            "username": "newuser",
            "email": "new@test.com",
            "password": "password",
            "is_active": True,
            "attributes": attributes,
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "newuser"
    assert data["id"] == 2
    assert data["resume_count"] == 0
    assert data["force_password_change"] is expected_force_password_change
    assert data["last_login_at"] is None


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
    mock_get_db,
    mock_get_current_admin_user,
    mock_get_users_admin,
    client,
    app,
):
    """Test successful listing of all users by an admin."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin_user)

    # Case 1: has resumes, force_password_change=True
    user1 = MagicMock(spec=User)
    user1.id = 2
    user1.username = "testuser1"
    user1.email = "test1@test.com"
    user1.is_active = True
    user1.roles = []
    user1.resumes = [MagicMock(), MagicMock()]
    user1.last_login_at = datetime.now(UTC)
    user1.attributes = {"force_password_change": True}

    # Case 2: no resumes, attributes is None
    user2 = MagicMock(spec=User)
    user2.id = 3
    user2.username = "testuser2"
    user2.email = "test2@test.com"
    user2.is_active = True
    user2.roles = []
    user2.resumes = []
    user2.last_login_at = None
    user2.attributes = None

    # Case 3: attributes is an empty dict
    user3 = MagicMock(spec=User)
    user3.id = 4
    user3.username = "testuser3"
    user3.email = "test3@test.com"
    user3.is_active = True
    user3.roles = []
    user3.resumes = []
    user3.last_login_at = None
    user3.attributes = {}

    # Case 4: force_password_change is False
    user4 = MagicMock(spec=User)
    user4.id = 5
    user4.username = "testuser4"
    user4.email = "test4@test.com"
    user4.is_active = True
    user4.roles = []
    user4.resumes = [MagicMock()]
    user4.last_login_at = None
    user4.attributes = {"force_password_change": False}

    # Case 5: attributes has other keys
    user5 = MagicMock(spec=User)
    user5.id = 6
    user5.username = "testuser5"
    user5.email = "test5@test.com"
    user5.is_active = True
    user5.roles = []
    user5.resumes = []
    user5.last_login_at = None
    user5.attributes = {"another_key": "value"}

    # Case 6: Mock without spec to test hasattr branches
    user_no_spec = MagicMock(spec=True)
    user_no_spec.id = 7
    user_no_spec.username = "no_spec_user"
    user_no_spec.email = "no_spec@test.com"
    user_no_spec.is_active = True
    user_no_spec.roles = []
    user_no_spec.last_login_at = None
    # This mock does not have `resumes` or `attributes` attributes

    # Case 7: force_password_change is None
    user7 = MagicMock(spec=User)
    user7.id = 8
    user7.username = "testuser7"
    user7.email = "test7@test.com"
    user7.is_active = True
    user7.roles = []
    user7.resumes = []
    user7.last_login_at = None
    user7.attributes = {"force_password_change": None}

    mock_get_users_admin.return_value = [
        user1,
        user2,
        user3,
        user4,
        user5,
        user_no_spec,
        user7,
    ]

    response = client.get("/api/admin/users/")

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 7

    # Assertions for user1
    user1_data = next(u for u in response_data if u["id"] == 2)
    assert user1_data["username"] == "testuser1"
    assert user1_data["resume_count"] == 2
    assert user1_data["force_password_change"] is True
    assert user1_data["last_login_at"] is not None

    # Assertions for user2
    user2_data = next(u for u in response_data if u["id"] == 3)
    assert user2_data["username"] == "testuser2"
    assert user2_data["resume_count"] == 0
    assert user2_data["force_password_change"] is False
    assert user2_data["last_login_at"] is None

    # Assertions for user3
    user3_data = next(u for u in response_data if u["id"] == 4)
    assert user3_data["resume_count"] == 0
    assert user3_data["force_password_change"] is False

    # Assertions for user4
    user4_data = next(u for u in response_data if u["id"] == 5)
    assert user4_data["resume_count"] == 1
    assert user4_data["force_password_change"] is False

    # Assertions for user5
    user5_data = next(u for u in response_data if u["id"] == 6)
    assert user5_data["resume_count"] == 0
    assert user5_data["force_password_change"] is False

    # Assertions for user_no_spec
    user_no_spec_data = next(u for u in response_data if u["id"] == 7)
    assert user_no_spec_data["resume_count"] == 0
    assert user_no_spec_data["force_password_change"] is False

    # Assertions for user7
    user7_data = next(u for u in response_data if u["id"] == 8)
    assert user7_data["force_password_change"] is False


@pytest.mark.parametrize(
    "attributes, expected_force_password_change, resume_count, last_login_at",
    [
        ({"force_password_change": True}, True, 1, datetime.now(UTC)),
        (None, False, 0, None),
        ({}, False, 2, datetime.now(UTC)),
        ({"force_password_change": False}, False, 0, None),
        ({"another_key": "value"}, False, 1, datetime.now(UTC)),
        ({"force_password_change": None}, False, 0, None),
    ],
)
@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
def test_admin_get_user_success(
    mock_get_current_admin_user,
    mock_get_user_by_id_admin,
    attributes,
    expected_force_password_change,
    resume_count,
    last_login_at,
    client,
    app,
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
    user.last_login_at = last_login_at
    user.attributes = attributes
    user.resumes = [MagicMock()] * resume_count

    mock_get_user_by_id_admin.return_value = user

    response = client.get("/api/admin/users/2")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["username"] == "testuser"
    assert response_data["id"] == 2
    assert (response_data["last_login_at"] is not None) == (last_login_at is not None)
    assert response_data["force_password_change"] is expected_force_password_change
    assert response_data["resume_count"] == resume_count


@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
def test_admin_get_user_not_found(
    mock_get_current_admin_user,
    mock_get_user_by_id_admin,
    client,
    app,
):
    """Test retrieving a non-existent user by an admin."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin_user)

    mock_get_user_by_id_admin.return_value = None

    response = client.get("/api/admin/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@pytest.mark.parametrize("force_password_change", [True, False])
@patch("resume_editor.app.api.routes.admin.admin_crud.update_user_admin")
@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
@patch("resume_editor.app.api.routes.admin.get_db")
def test_admin_update_user_success(
    mock_get_db,
    mock_get_current_admin_user,
    mock_get_user_by_id_admin,
    mock_update_user_admin,
    force_password_change,
    client,
    app,
):
    """Test successful user update by an admin."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin_user)

    existing_user = MagicMock(spec=User)
    existing_user.id = 2
    existing_user.username = "testuser"
    existing_user.email = "test@test.com"
    existing_user.is_active = True
    existing_user.roles = []
    existing_user.resumes = []
    existing_user.last_login_at = None
    existing_user.attributes = {"force_password_change": not force_password_change}

    mock_get_user_by_id_admin.return_value = existing_user

    updated_user = MagicMock(spec=User)
    updated_user.id = 2
    updated_user.username = "testuser"
    updated_user.email = "test@test.com"
    updated_user.is_active = True
    updated_user.roles = []
    updated_user.resumes = []
    updated_user.last_login_at = None
    updated_user.attributes = {"force_password_change": force_password_change}
    mock_update_user_admin.return_value = updated_user

    response = client.put(
        "/api/admin/users/2",
        json={"force_password_change": force_password_change},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == 2
    assert data["force_password_change"] is force_password_change
    mock_update_user_admin.assert_called_once()
    # Can't easily check the Pydantic model directly, so check the value
    update_data_arg = mock_update_user_admin.call_args.kwargs["update_data"]
    assert isinstance(update_data_arg, AdminUserUpdateRequest)
    assert update_data_arg.force_password_change is force_password_change
    assert mock_update_user_admin.call_args.kwargs["user"] == existing_user


@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
def test_admin_update_user_not_found(
    mock_get_current_admin_user,
    mock_get_user_by_id_admin,
    client,
    app,
):
    """Test updating a non-existent user by an admin."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin_user)

    mock_get_user_by_id_admin.return_value = None

    response = client.put("/api/admin/users/999", json={"force_password_change": True})

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
    mock_get_current_admin_user,
    mock_get_user_by_id_admin,
    client,
    app,
):
    """Test deleting a non-existent user by an admin."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(app, mock_db, mock_admin_user)

    mock_get_user_by_id_admin.return_value = None

    response = client.delete("/api/admin/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_admin_delete_user_self_delete_fails(
    client,
    app,
):
    """Test that an admin cannot delete themselves via the API."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    mock_admin_user.id = 1
    setup_dependency_overrides(app, mock_db, mock_admin_user)

    with patch(
        "resume_editor.app.api.routes.admin.admin_crud.get_user_by_id_admin",
    ) as mock_get_user_by_id_admin:
        mock_get_user_by_id_admin.return_value = mock_admin_user

        response = client.delete("/api/admin/users/1")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Administrators cannot delete themselves."


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
    mock_user.resumes = []
    mock_user.last_login_at = None

    mock_role = MagicMock(spec=Role)
    mock_role.id = 1
    mock_role.name = "admin"

    mock_get_user_by_id_admin.return_value = mock_user
    mock_get_role_by_name_admin.return_value = mock_role
    # The return mock needs to have all attributes for AdminUserResponse
    updated_user = MagicMock(spec=User)
    updated_user.id = mock_user.id
    updated_user.username = mock_user.username
    updated_user.email = mock_user.email
    updated_user.is_active = mock_user.is_active
    updated_user.attributes = mock_user.attributes
    updated_user.roles = [mock_role]
    updated_user.resumes = mock_user.resumes
    updated_user.last_login_at = mock_user.last_login_at
    mock_assign_role_to_user_admin.return_value = updated_user

    response = client.post("/api/admin/users/2/roles/admin")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == 2
    assert len(data["roles"]) == 1
    assert data["roles"][0]["name"] == "admin"
    assert data["resume_count"] == 0
    mock_assign_role_to_user_admin.assert_called_once_with(
        db=mock_db,
        user=mock_user,
        role=mock_role,
    )


@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
def test_admin_assign_role_user_not_found(
    mock_get_current_admin_user,
    mock_get_user_by_id_admin,
    client,
    app,
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
    mock_user.resumes = []
    mock_user.last_login_at = None

    mock_get_user_by_id_admin.return_value = mock_user
    mock_get_role_by_name_admin.return_value = mock_role

    response = client.post("/api/admin/users/2/roles/admin")

    assert response.status_code == status.HTTP_200_OK
    # The user object should be returned directly without calling the assign function.
    response_data = response.json()
    assert response_data["username"] == "testuser"
    assert response_data["resume_count"] == 0
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
    mock_user.resumes = []
    mock_user.last_login_at = None

    mock_get_user_by_id_admin.return_value = mock_user
    mock_get_role_by_name_admin.return_value = mock_role
    # The return mock needs to have all attributes for AdminUserResponse
    updated_user = MagicMock(spec=User)
    updated_user.id = mock_user.id
    updated_user.username = mock_user.username
    updated_user.email = mock_user.email
    updated_user.is_active = mock_user.is_active
    updated_user.attributes = mock_user.attributes
    updated_user.roles = []
    updated_user.resumes = mock_user.resumes
    updated_user.last_login_at = mock_user.last_login_at
    mock_remove_role_from_user_admin.return_value = updated_user

    response = client.delete("/api/admin/users/2/roles/admin")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == 2
    assert len(data["roles"]) == 0
    assert data["resume_count"] == 0

    mock_remove_role_from_user_admin.assert_called_once_with(
        db=mock_db,
        user=mock_user,
        role=mock_role,
    )


@patch("resume_editor.app.api.routes.admin.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
def test_admin_remove_role_from_user_user_not_found(
    mock_get_current_admin_user,
    mock_get_user_by_id_admin,
    client,
    app,
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
    mock_get_user_by_username_admin,
    mock_get_user_settings,
    client,
    app,
):
    """Test successful impersonation and using the token to access a protected route."""
    mock_db = MagicMock()
    mock_admin_user = User(
        username="admin",
        email="admin@test.com",
        hashed_password="pw",
    )
    mock_admin_user.id = 1
    setup_dependency_overrides(app, mock_db, mock_admin_user)

    mock_target_user = User(
        username="target",
        email="target@test.com",
        hashed_password="pw",
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
        username="admin",
        email="admin@test.com",
        hashed_password="pw",
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
