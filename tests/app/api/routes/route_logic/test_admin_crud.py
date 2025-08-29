from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_logic.admin_crud import (
    assign_role_to_user_admin,
    create_user_admin,
    delete_user_admin,
    get_role_by_name_admin,
    get_user_by_id_admin,
    get_users_admin,
    impersonate_user_admin,
    remove_role_from_user_admin,
)
from resume_editor.app.models.role import Role
from resume_editor.app.models.user import User
from resume_editor.app.schemas.user import AdminUserCreate


@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_password_hash")
def test_create_user_admin_defaults(mock_get_password_hash: MagicMock):
    """Test creating a user as an admin with default values."""
    mock_db = MagicMock(spec=Session)
    user_data = AdminUserCreate(
        username="testuser", email="test@example.com", password="password"
    )
    mock_get_password_hash.return_value = "hashed_password"

    created_user = create_user_admin(mock_db, user_data)

    mock_get_password_hash.assert_called_once_with("password")
    assert isinstance(created_user, User)
    assert created_user.username == user_data.username
    assert created_user.email == user_data.email
    assert created_user.hashed_password == "hashed_password"
    assert created_user.is_active is True
    assert created_user.attributes is None
    mock_db.add.assert_called_once_with(created_user)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(created_user)


@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_password_hash")
def test_create_user_admin_with_options(mock_get_password_hash: MagicMock):
    """Test creating a user as an admin with specific is_active and attributes."""
    mock_db = MagicMock(spec=Session)
    user_data = AdminUserCreate(
        username="testuser",
        email="test@example.com",
        password="password",
        is_active=False,
        attributes={"key": "value"},
    )
    mock_get_password_hash.return_value = "hashed_password"

    created_user = create_user_admin(mock_db, user_data)

    mock_get_password_hash.assert_called_once_with("password")
    assert isinstance(created_user, User)
    assert created_user.username == user_data.username
    assert created_user.email == user_data.email
    assert created_user.hashed_password == "hashed_password"
    assert created_user.is_active is False
    assert created_user.attributes == {"key": "value"}
    mock_db.add.assert_called_once_with(created_user)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(created_user)


def test_get_user_by_id_admin():
    """Test retrieving a user by ID as an admin."""
    mock_db = MagicMock(spec=Session)
    user = User(
        username="testuser", email="test@example.com", hashed_password="hashed_password"
    )
    mock_db.query.return_value.filter.return_value.first.return_value = user

    found_user = get_user_by_id_admin(mock_db, 1)

    assert found_user == user
    mock_db.query.assert_called_once_with(User)
    mock_db.query.return_value.filter.return_value.first.assert_called_once()


def test_get_user_by_id_admin_not_found():
    """Test retrieving a non-existent user by ID as an admin."""
    mock_db = MagicMock(spec=Session)
    mock_db.query.return_value.filter.return_value.first.return_value = None

    found_user = get_user_by_id_admin(mock_db, 1)

    assert found_user is None
    mock_db.query.assert_called_once_with(User)
    mock_db.query.return_value.filter.return_value.first.assert_called_once()


def test_get_users_admin():
    """Test retrieving all users as an admin."""
    mock_db = MagicMock(spec=Session)
    users = [
        User(username="test1", email="test1@example.com", hashed_password="pw1"),
        User(username="test2", email="test2@example.com", hashed_password="pw2"),
    ]
    mock_db.query.return_value.all.return_value = users

    found_users = get_users_admin(mock_db)

    assert found_users == users
    mock_db.query.assert_called_once_with(User)
    mock_db.query.return_value.all.assert_called_once()


def test_delete_user_admin():
    """Test deleting a user as an admin."""
    mock_db = MagicMock(spec=Session)
    user = User(
        username="testuser", email="test@example.com", hashed_password="hashed_password"
    )

    delete_user_admin(mock_db, user)

    mock_db.delete.assert_called_once_with(user)
    mock_db.commit.assert_called_once()


def test_get_role_by_name_admin_found():
    """Test get_role_by_name_admin when role is found."""
    mock_db = MagicMock(spec=Session)
    mock_role = Role(name="admin")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_role

    role = get_role_by_name_admin(db=mock_db, name="admin")

    assert role is not None
    assert role.name == "admin"
    mock_db.query.assert_called_once_with(Role)


def test_get_role_by_name_admin_not_found():
    """Test get_role_by_name_admin when role is not found."""
    mock_db = MagicMock(spec=Session)
    mock_db.query.return_value.filter.return_value.first.return_value = None

    role = get_role_by_name_admin(db=mock_db, name="nonexistent")

    assert role is None
    mock_db.query.assert_called_once_with(Role)


def test_assign_role_to_user_admin_new_role():
    """Test assign_role_to_user_admin with a new role for the user."""
    mock_db = MagicMock(spec=Session)
    mock_user = User(
        username="testuser", email="test@test.com", hashed_password="hashed"
    )
    mock_user.roles = []
    mock_role = Role(name="admin")

    updated_user = assign_role_to_user_admin(db=mock_db, user=mock_user, role=mock_role)

    assert mock_role in updated_user.roles
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_user)


def test_assign_role_to_user_admin_existing_role():
    """Test assign_role_to_user_admin when user already has the role."""
    mock_db = MagicMock(spec=Session)
    mock_role = Role(name="admin")
    mock_user = User(
        username="testuser", email="test@test.com", hashed_password="hashed"
    )
    mock_user.roles = [mock_role]

    updated_user = assign_role_to_user_admin(db=mock_db, user=mock_user, role=mock_role)

    assert updated_user == mock_user
    mock_db.commit.assert_not_called()
    mock_db.refresh.assert_not_called()


@patch("resume_editor.app.api.routes.route_logic.admin_crud.SecurityManager")
@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_user_by_id_admin")
def test_impersonate_user_admin_success(
    mock_get_user_by_id_admin, mock_security_manager
):
    """Test successful user impersonation token generation."""
    mock_db = MagicMock(spec=Session)
    target_user = MagicMock(spec=User)
    target_user.username = "targetuser"
    mock_get_user_by_id_admin.return_value = target_user

    mock_sm_instance = mock_security_manager.return_value
    mock_sm_instance.create_access_token.return_value = "fake-token"

    token = impersonate_user_admin(db=mock_db, user_id=1)

    assert token == "fake-token"
    mock_get_user_by_id_admin.assert_called_once_with(db=mock_db, user_id=1)
    mock_security_manager.assert_called_once()
    mock_sm_instance.create_access_token.assert_called_once_with(
        data={"sub": "targetuser"}
    )


@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_user_by_id_admin")
def test_impersonate_user_admin_user_not_found(mock_get_user_by_id_admin):
    """Test impersonation when user is not found."""
    mock_db = MagicMock(spec=Session)
    mock_get_user_by_id_admin.return_value = None

    token = impersonate_user_admin(db=mock_db, user_id=1)

    assert token is None
    mock_get_user_by_id_admin.assert_called_once_with(db=mock_db, user_id=1)


def test_remove_role_from_user_admin_existing_role():
    """Test remove_role_from_user_admin when user has the role."""
    mock_db = MagicMock(spec=Session)
    mock_role = Role(name="admin")
    mock_user = User(
        username="testuser", email="test@test.com", hashed_password="hashed"
    )
    mock_user.roles = [mock_role]

    updated_user = remove_role_from_user_admin(
        db=mock_db, user=mock_user, role=mock_role
    )

    assert mock_role not in updated_user.roles
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_user)


def test_remove_role_from_user_admin_non_existing_role():
    """Test remove_role_from_user_admin when user does not have the role."""
    mock_db = MagicMock(spec=Session)
    mock_user = User(
        username="testuser", email="test@test.com", hashed_password="hashed"
    )
    mock_user.roles = []
    mock_role = Role(name="admin")

    updated_user = remove_role_from_user_admin(
        db=mock_db, user=mock_user, role=mock_role
    )

    assert updated_user == mock_user
    mock_db.commit.assert_not_called()
    mock_db.refresh.assert_not_called()
