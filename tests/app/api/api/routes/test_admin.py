import logging
from unittest.mock import MagicMock, patch

from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from resume_editor.app.core.auth import get_current_admin_user, get_current_user
from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app
from resume_editor.app.models.role import Role
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)

app = create_app()
client = TestClient(app)


def setup_dependency_overrides(mock_db: MagicMock, mock_user: User | None):
    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db
    app.dependency_overrides[get_current_admin_user] = lambda: mock_user


@patch("resume_editor.app.api.routes.admin.create_new_user")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
@patch("resume_editor.app.api.routes.admin.get_db")
def test_admin_create_user_success(
    mock_get_db, mock_get_current_admin_user, mock_create_new_user
):
    """Test successful user creation by an admin."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(mock_db, mock_admin_user)

    created_user = MagicMock(spec=User)
    created_user.id = 2
    created_user.username = "newuser"
    created_user.email = "new@test.com"
    created_user.is_active = True
    created_user.roles = []
    created_user.attributes = None

    mock_create_new_user.return_value = created_user

    response = client.post(
        "/api/admin/users/",
        json={"username": "newuser", "email": "new@test.com", "password": "password"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "newuser"
    assert data["id"] == 2
    app.dependency_overrides.clear()


def test_admin_get_users_forbidden():
    """Test that a non-admin user cannot list users."""
    mock_non_admin_user = MagicMock(spec=User)
    mock_role = Role(name="user")
    mock_non_admin_user.roles = [mock_role]
    app.dependency_overrides[get_current_user] = lambda: mock_non_admin_user

    response = client.get("/api/admin/users/")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    app.dependency_overrides.clear()


def test_admin_get_users_unauthorized():
    """Test that an unauthenticated user cannot list users."""
    response = client.get("/api/admin/users/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
@patch("resume_editor.app.api.routes.admin.get_db")
def test_admin_get_users_success(mock_get_db, mock_get_current_admin_user):
    """Test successful listing of all users by an admin."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(mock_db, mock_admin_user)

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
    mock_db.query.return_value.all.return_value = [user1, user2]

    response = client.get("/api/admin/users/")

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["username"] == "testuser1"
    assert response_data[1]["username"] == "testuser2"

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
def test_admin_get_user_success(mock_get_current_admin_user):
    """Test successful retrieval of a single user by ID by an admin."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(mock_db, mock_admin_user)

    user = MagicMock(spec=User)
    user.id = 2
    user.username = "testuser"
    user.email = "test@test.com"
    user.is_active = True
    user.roles = []
    user.attributes = None

    mock_db.query.return_value.filter.return_value.first.return_value = user

    response = client.get("/api/admin/users/2")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["username"] == "testuser"
    assert response_data["id"] == 2

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.admin.get_user_by_id")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
def test_admin_get_user_not_found(mock_get_current_admin_user, mock_get_user_by_id):
    """Test retrieving a non-existent user by an admin."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(mock_db, mock_admin_user)

    mock_get_user_by_id.return_value = None

    response = client.get("/api/admin/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
def test_admin_delete_user_success(mock_get_current_admin_user):
    """Test successful deletion of a user by an admin."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(mock_db, mock_admin_user)

    user_to_delete = MagicMock(spec=User)
    mock_db.query.return_value.filter.return_value.first.return_value = user_to_delete

    response = client.delete("/api/admin/users/2")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_db.delete.assert_called_with(user_to_delete)
    mock_db.commit.assert_called_once()

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.admin.get_user_by_id")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
def test_admin_delete_user_not_found(mock_get_current_admin_user, mock_get_user_by_id):
    """Test deleting a non-existent user by an admin."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(mock_db, mock_admin_user)

    mock_get_user_by_id.return_value = None

    response = client.delete("/api/admin/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.admin.get_user_by_id")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
@patch("resume_editor.app.api.routes.admin.get_db")
def test_admin_assign_role_to_user_success(
    mock_get_db, mock_get_current_admin_user, mock_get_user_by_id
):
    mock_db = MagicMock()
    mock_admin = MagicMock(spec=User)
    setup_dependency_overrides(mock_db, mock_admin)

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

    mock_get_user_by_id.return_value = mock_user
    mock_db.query.return_value.filter.return_value.first.return_value = mock_role

    response = client.post("/api/admin/users/2/roles/admin")

    assert response.status_code == status.HTTP_200_OK
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_with(mock_user)
    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.admin.get_user_by_id")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
def test_admin_assign_role_user_not_found(
    mock_get_current_admin_user, mock_get_user_by_id
):
    mock_db = MagicMock()
    mock_admin = MagicMock(spec=User)
    setup_dependency_overrides(mock_db, mock_admin)
    mock_get_user_by_id.return_value = None

    response = client.post("/api/admin/users/2/roles/admin")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"
    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.admin.get_user_by_id")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
@patch("resume_editor.app.api.routes.admin.get_db")
def test_admin_assign_role_role_not_found(
    mock_get_db, mock_get_current_admin_user, mock_get_user_by_id
):
    mock_db = MagicMock()
    mock_admin = MagicMock(spec=User)
    setup_dependency_overrides(mock_db, mock_admin)
    mock_user = MagicMock(spec=User)
    mock_get_user_by_id.return_value = mock_user
    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.post("/api/admin/users/2/roles/admin")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Role not found"
    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.admin.get_user_by_id")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
@patch("resume_editor.app.api.routes.admin.get_db")
def test_admin_assign_role_already_assigned(
    mock_get_db, mock_get_current_admin_user, mock_get_user_by_id
):
    mock_db = MagicMock()
    mock_admin = MagicMock(spec=User)
    setup_dependency_overrides(mock_db, mock_admin)
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

    mock_get_user_by_id.return_value = mock_user
    mock_db.query.return_value.filter.return_value.first.return_value = mock_role

    response = client.post("/api/admin/users/2/roles/admin")

    assert response.status_code == status.HTTP_200_OK
    mock_db.commit.assert_not_called()
    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.admin.get_user_by_id")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
@patch("resume_editor.app.api.routes.admin.get_db")
def test_admin_remove_role_from_user_success(
    mock_get_db, mock_get_current_admin_user, mock_get_user_by_id
):
    mock_db = MagicMock()
    mock_admin = MagicMock(spec=User)
    setup_dependency_overrides(mock_db, mock_admin)
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

    mock_get_user_by_id.return_value = mock_user
    mock_db.query.return_value.filter.return_value.first.return_value = mock_role

    response = client.delete("/api/admin/users/2/roles/admin")

    assert response.status_code == status.HTTP_200_OK
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_with(mock_user)
    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.admin.get_user_by_id")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
def test_admin_remove_role_from_user_user_not_found(
    mock_get_current_admin_user, mock_get_user_by_id
):
    mock_db = MagicMock()
    mock_admin = MagicMock(spec=User)
    setup_dependency_overrides(mock_db, mock_admin)
    mock_get_user_by_id.return_value = None

    response = client.delete("/api/admin/users/2/roles/admin")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"
    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.admin.get_user_by_id")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
@patch("resume_editor.app.api.routes.admin.get_db")
def test_admin_remove_role_from_user_role_not_found(
    mock_get_db, mock_get_current_admin_user, mock_get_user_by_id
):
    mock_db = MagicMock()
    mock_admin = MagicMock(spec=User)
    setup_dependency_overrides(mock_db, mock_admin)
    mock_user = MagicMock(spec=User)
    mock_get_user_by_id.return_value = mock_user
    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.delete("/api/admin/users/2/roles/admin")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Role not found"
    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.admin.get_user_by_id")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
@patch("resume_editor.app.api.routes.admin.get_db")
def test_admin_remove_role_from_user_not_assigned(
    mock_get_db, mock_get_current_admin_user, mock_get_user_by_id
):
    mock_db = MagicMock()
    mock_admin = MagicMock(spec=User)
    setup_dependency_overrides(mock_db, mock_admin)
    mock_role = MagicMock(spec=Role)
    mock_user = MagicMock(spec=User)
    mock_user.roles = []

    mock_get_user_by_id.return_value = mock_user
    mock_db.query.return_value.filter.return_value.first.return_value = mock_role

    response = client.delete("/api/admin/users/2/roles/admin")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "User does not have this role"
    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.admin.impersonate_user_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
def test_admin_impersonate_user_success(
    mock_get_current_admin_user,
    mock_impersonate_user_admin,
):
    """Test successful user impersonation by an admin."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(mock_db, mock_admin_user)

    mock_impersonate_user_admin.return_value = "fake-impersonation-token"

    response = client.post("/api/admin/users/2/impersonate")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "access_token": "fake-impersonation-token",
        "token_type": "bearer",
    }
    mock_impersonate_user_admin.assert_called_once_with(db=mock_db, user_id=2)

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.admin.impersonate_user_admin")
@patch("resume_editor.app.api.routes.admin.get_current_admin_user")
def test_admin_impersonate_user_not_found(
    mock_get_current_admin_user, mock_impersonate_user_admin
):
    """Test impersonation attempt on a non-existent user."""
    mock_db = MagicMock()
    mock_admin_user = MagicMock(spec=User)
    setup_dependency_overrides(mock_db, mock_admin_user)

    mock_impersonate_user_admin.return_value = None

    response = client.post("/api/admin/users/999/impersonate")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"
    mock_impersonate_user_admin.assert_called_once_with(db=mock_db, user_id=999)

    app.dependency_overrides.clear()
