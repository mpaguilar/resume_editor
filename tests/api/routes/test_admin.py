from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from resume_editor.app.main import create_app
from resume_editor.app.models.role import Role
from resume_editor.app.models.user import User

# Need to import a dependency to override it in tests
from resume_editor.app.core.auth import get_current_user
from resume_editor.app.database.database import get_db


@patch("resume_editor.app.api.routes.admin.create_new_user")
def test_admin_create_user_success(mock_create_new_user):
    """Test successful user creation by an admin."""
    app = create_app()
    client = TestClient(app)

    # Mock DB
    mock_db = Mock()

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Mock admin user
    mock_admin_role = Role(name="admin")
    mock_admin_user = User(
        username="admin",
        email="admin@test.com",
        hashed_password="hashedpassword",
    )
    mock_admin_user.id = 1
    mock_admin_user.roles = [mock_admin_role]
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user

    # Mock return value from create_new_user
    new_user_data = {"username": "newuser", "email": "new@test.com"}
    created_user = User(**new_user_data, hashed_password="newpassword")
    created_user.id = 2
    mock_create_new_user.return_value = created_user

    # Make request
    response = client.post(
        "/api/admin/users/",
        json={"username": "newuser", "email": "new@test.com", "password": "password"},
    )

    # Assertions
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["username"] == "newuser"
    assert response_data["email"] == "new@test.com"
    assert response_data["id"] == 2

    # Clear overrides
    app.dependency_overrides.clear()


def test_admin_get_users_forbidden():
    """Test that a non-admin user cannot list users."""
    app = create_app()
    client = TestClient(app)

    # Mock non-admin user
    mock_user_role = Role(name="user")
    mock_user = User(
        username="user",
        email="user@test.com",
        hashed_password="hashedpassword",
    )
    mock_user.id = 2
    mock_user.roles = [mock_user_role]
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = client.get("/api/admin/users/")

    assert response.status_code == 403

    app.dependency_overrides.clear()


def test_admin_get_users_unauthorized():
    """Test that an unauthenticated user cannot list users."""
    app = create_app()
    client = TestClient(app)

    # No user override, so get_current_user will fail with 401
    response = client.get("/api/admin/users/")

    assert response.status_code == 401

    app.dependency_overrides.clear()


def test_admin_get_users_success():
    """Test successful listing of all users by an admin."""
    app = create_app()
    client = TestClient(app)

    mock_db = Mock()
    user1 = User(username="testuser1", email="test1@test.com", hashed_password="hp1")
    user1.id = 2
    user2 = User(username="testuser2", email="test2@test.com", hashed_password="hp2")
    user2.id = 3
    users_list = [user1, user2]
    mock_db.query.return_value.all.return_value = users_list

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    mock_admin_role = Role(name="admin")
    mock_admin_user = User(
        username="admin",
        email="admin@test.com",
        hashed_password="hashedpassword",
    )
    mock_admin_user.id = 1
    mock_admin_user.roles = [mock_admin_role]
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user

    response = client.get("/api/admin/users/")

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["username"] == "testuser1"
    assert response_data[1]["username"] == "testuser2"

    app.dependency_overrides.clear()


def test_admin_get_user_success():
    """Test successful retrieval of a single user by ID by an admin."""
    app = create_app()
    client = TestClient(app)

    mock_db = Mock()
    user = User(username="testuser", email="test@test.com", hashed_password="hp")
    user.id = 2
    mock_db.query.return_value.filter.return_value.first.return_value = user

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    mock_admin_role = Role(name="admin")
    mock_admin_user = User(
        username="admin",
        email="admin@test.com",
        hashed_password="hashedpassword",
    )
    mock_admin_user.id = 1
    mock_admin_user.roles = [mock_admin_role]
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user

    response = client.get("/api/admin/users/2")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["username"] == "testuser"
    assert response_data["id"] == 2

    app.dependency_overrides.clear()


def test_admin_get_user_not_found():
    """Test retrieving a non-existent user by ID."""
    app = create_app()
    client = TestClient(app)

    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    mock_admin_role = Role(name="admin")
    mock_admin_user = User(
        username="admin",
        email="admin@test.com",
        hashed_password="hashedpassword",
    )
    mock_admin_user.id = 1
    mock_admin_user.roles = [mock_admin_role]
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user

    response = client.get("/api/admin/users/999")

    assert response.status_code == 404

    app.dependency_overrides.clear()


def test_admin_delete_user_success():
    """Test successful deletion of a user by an admin."""
    app = create_app()
    client = TestClient(app)

    mock_db = Mock()
    user_to_delete = User(
        username="todelete", email="delete@test.com", hashed_password="hp"
    )
    user_to_delete.id = 2
    mock_db.query.return_value.filter.return_value.first.return_value = user_to_delete

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    mock_admin_role = Role(name="admin")
    mock_admin_user = User(
        username="admin",
        email="admin@test.com",
        hashed_password="hashedpassword",
    )
    mock_admin_user.id = 1
    mock_admin_user.roles = [mock_admin_role]
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user

    response = client.delete("/api/admin/users/2")

    assert response.status_code == 204
    mock_db.delete.assert_called_once_with(user_to_delete)
    mock_db.commit.assert_called_once()
    app.dependency_overrides.clear()


def test_admin_delete_user_not_found():
    """Test deleting a user that does not exist."""
    app = create_app()
    client = TestClient(app)

    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    mock_admin_role = Role(name="admin")
    mock_admin_user = User(
        username="admin",
        email="admin@test.com",
        hashed_password="hashedpassword",
    )
    mock_admin_user.id = 1
    mock_admin_user.roles = [mock_admin_role]
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user

    response = client.delete("/api/admin/users/999")

    assert response.status_code == 404

    app.dependency_overrides.clear()
