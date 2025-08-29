from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_logic.admin_crud import (
    create_user_admin,
    delete_user_admin,
    get_user_by_id_admin,
    get_users_admin,
)
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
