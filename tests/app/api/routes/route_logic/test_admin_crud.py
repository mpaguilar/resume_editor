from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_logic.admin_crud import (
    assign_role_to_user_admin,
    create_initial_admin,
    create_user_admin,
    delete_user_admin,
    get_role_by_name_admin,
    get_user_by_id_admin,
    get_user_by_username_admin,
    get_users_admin,
    remove_role_from_user_admin,
    update_user_admin,
)
from resume_editor.app.models.role import Role
from resume_editor.app.models.user import User, UserData
from resume_editor.app.schemas.user import AdminUserCreate, AdminUserUpdateRequest


@pytest.mark.parametrize(
    "email_update, force_password_change, existing_attributes",
    [
        (None, None, None),
        (None, True, None),
        (None, False, {"force_password_change": True}),
        ("new@test.com", None, None),
        ("new@test.com", True, {"other_key": "value"}),
    ],
)
@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.route_logic.admin_crud.flag_modified")
def test_update_user_admin(
    mock_flag_modified: MagicMock,
    mock_get_user_by_id_admin: MagicMock,
    email_update: str | None,
    force_password_change: bool | None,
    existing_attributes: dict | None,
):
    """Test updating a user with various combinations of data."""
    mock_db = MagicMock(spec=Session)
    original_email = "test@test.com"

    # User object passed to the function
    user_to_update = User(
        data=UserData(
            username="test",
            email=original_email,
            hashed_password="pw",
            id_=1,
        )
    )
    user_to_update.attributes = (
        existing_attributes.copy() if existing_attributes is not None else None
    )

    # Mock the re-fetched user object to reflect expected state
    refetched_user = User(
        data=UserData(username="test", email=original_email, hashed_password="pw", id_=1)
    )

    expected_attributes = (
        existing_attributes.copy() if existing_attributes is not None else {}
    )
    if force_password_change is not None:
        expected_attributes["force_password_change"] = force_password_change

    refetched_user.attributes = expected_attributes if expected_attributes else None
    refetched_user.email = email_update if email_update else original_email
    mock_get_user_by_id_admin.return_value = refetched_user

    update_data = AdminUserUpdateRequest(
        email=email_update,
        force_password_change=force_password_change,
    )

    updated_user = update_user_admin(
        db=mock_db,
        user=user_to_update,
        update_data=update_data,
    )

    # Check that the original object's attributes were modified correctly
    if email_update:
        assert user_to_update.email == email_update
    else:
        assert user_to_update.email == original_email

    if force_password_change is not None:
        assert (
            user_to_update.attributes["force_password_change"] is force_password_change
        )
        if existing_attributes and "other_key" in existing_attributes:
            assert "other_key" in user_to_update.attributes
        mock_flag_modified.assert_called_once_with(user_to_update, "attributes")
    else:
        mock_flag_modified.assert_not_called()

    # Check function calls
    mock_db.commit.assert_called_once()
    mock_get_user_by_id_admin.assert_called_once_with(db=mock_db, user_id=1)

    # Check that the re-fetched user is returned
    assert updated_user == refetched_user
    assert updated_user is not user_to_update


@pytest.mark.parametrize("user_exists", [True, False])
@patch("resume_editor.app.api.routes.route_logic.admin_crud.selectinload")
def test_get_user_by_id_admin(mock_selectinload, user_exists: bool):
    """Test retrieving a user by ID as an admin."""
    mock_db = MagicMock(spec=Session)
    expected_user = (
        User(
            data=UserData(
                username="testuser",
                email="test@example.com",
                hashed_password="hashed_password",
            )
        )
        if user_exists
        else None
    )

    (
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value
    ) = expected_user

    found_user = get_user_by_id_admin(mock_db, 1)

    assert found_user == expected_user
    mock_db.query.assert_called_once_with(User)
    mock_selectinload.assert_called_once_with(User.resumes)
    mock_db.query.return_value.options.assert_called_once_with(
        mock_selectinload.return_value,
    )
    (
        mock_db.query.return_value.options.return_value.filter.return_value.first.assert_called_once()
    )


@pytest.mark.parametrize("user_exists", [True, False])
def test_get_user_by_username_admin(user_exists: bool):
    """Test retrieving a user by username as an admin."""
    mock_db = MagicMock(spec=Session)
    expected_user = (
        User(
            data=UserData(
                username="testuser",
                email="test@example.com",
                hashed_password="hashed_password",
            )
        )
        if user_exists
        else None
    )
    mock_db.query.return_value.filter.return_value.first.return_value = expected_user

    found_user = get_user_by_username_admin(mock_db, "testuser")

    assert found_user == expected_user
    mock_db.query.assert_called_once_with(User)
    mock_db.query.return_value.filter.return_value.first.assert_called_once()


@patch("resume_editor.app.api.routes.route_logic.admin_crud.selectinload")
def test_get_users_admin(mock_selectinload):
    """Test retrieving all users as an admin."""
    mock_db = MagicMock(spec=Session)
    users = [
        User(
            data=UserData(
                username="test1", email="test1@example.com", hashed_password="pw1"
            )
        ),
        User(
            data=UserData(
                username="test2", email="test2@example.com", hashed_password="pw2"
            )
        ),
    ]
    mock_db.query.return_value.options.return_value.all.return_value = users

    found_users = get_users_admin(mock_db)

    assert found_users == users
    mock_db.query.assert_called_once_with(User)
    mock_selectinload.assert_called_once_with(User.resumes)
    mock_db.query.return_value.options.assert_called_once_with(
        mock_selectinload.return_value,
    )
    mock_db.query.return_value.options.return_value.all.assert_called_once()


def test_delete_user_admin():
    """Test deleting a user as an admin."""
    mock_db = MagicMock(spec=Session)
    user = User(
        data=UserData(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
        )
    )

    delete_user_admin(mock_db, user)

    mock_db.delete.assert_called_once_with(user)
    mock_db.commit.assert_called_once()


@pytest.mark.parametrize("role_exists", [True, False])
def test_get_role_by_name_admin(role_exists: bool):
    """Test get_role_by_name_admin for found and not found cases."""
    mock_db = MagicMock(spec=Session)
    expected_role = Role(name="admin") if role_exists else None
    mock_db.query.return_value.filter.return_value.first.return_value = expected_role

    role = get_role_by_name_admin(db=mock_db, name="admin")

    assert role == expected_role
    mock_db.query.assert_called_once_with(Role)


@pytest.mark.parametrize("role_already_assigned", [True, False])
@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_user_by_id_admin")
def test_assign_role_to_user_admin(
    mock_get_user_by_id_admin: MagicMock,
    role_already_assigned: bool,
):
    """Test assign_role_to_user_admin for new and existing role cases."""
    mock_db = MagicMock(spec=Session)
    mock_role = Role(name="admin")
    initial_user = User(
        data=UserData(
            username="testuser",
            email="test@test.com",
            hashed_password="hashed",
            id_=1,
        )
    )
    initial_user.roles = [mock_role] if role_already_assigned else []
    mock_get_user_by_id_admin.return_value = initial_user

    updated_user = assign_role_to_user_admin(
        db=mock_db,
        user=initial_user,
        role=mock_role,
    )

    if not role_already_assigned:
        mock_db.commit.assert_called_once()
        mock_get_user_by_id_admin.assert_called_once_with(db=mock_db, user_id=1)
        assert updated_user == initial_user
    else:
        assert updated_user == initial_user
        mock_db.commit.assert_not_called()
        mock_get_user_by_id_admin.assert_not_called()


@pytest.mark.parametrize("role_is_assigned", [True, False])
@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_user_by_id_admin")
def test_remove_role_from_user_admin(
    mock_get_user_by_id_admin: MagicMock,
    role_is_assigned: bool,
):
    """Test remove_role_from_user_admin for existing and non-existing role cases."""
    mock_db = MagicMock(spec=Session)
    mock_role = Role(name="admin")
    initial_user = User(
        data=UserData(
            username="testuser",
            email="test@test.com",
            hashed_password="hashed",
            id_=1,
        )
    )
    initial_user.roles = [mock_role] if role_is_assigned else []
    mock_get_user_by_id_admin.return_value = initial_user

    updated_user = remove_role_from_user_admin(
        db=mock_db,
        user=initial_user,
        role=mock_role,
    )

    if role_is_assigned:
        mock_db.commit.assert_called_once()
        mock_get_user_by_id_admin.assert_called_once_with(db=mock_db, user_id=1)
        assert updated_user == initial_user
    else:
        assert updated_user == initial_user
        mock_db.commit.assert_not_called()
        mock_get_user_by_id_admin.assert_not_called()


@pytest.mark.parametrize(
    "is_active, attributes",
    [
        (True, None),
        (False, {"key": "value"}),
        (True, {"force_password_change": True}),
    ],
)
@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_password_hash")
def test_create_user_admin(
    mock_get_password_hash: MagicMock,
    mock_get_user_by_id_admin: MagicMock,
    is_active: bool,
    attributes: dict | None,
):
    """Test creating a user as an admin with various options."""
    mock_db = MagicMock(spec=Session)
    user_data = AdminUserCreate(
        username="testuser",
        email="test@example.com",
        password="password",
        is_active=is_active,
        attributes=attributes,
    )
    mock_get_password_hash.return_value = "hashed_password"
    # Mock the user instance that is added to the db
    user_init_data = UserData(
        username=user_data.username,
        email=user_data.email,
        hashed_password="hashed_password",
        is_active=is_active,
        attributes=attributes,
        id_=1,
    )
    mock_user_instance = User(data=user_init_data)
    # Mock the re-fetched user
    mock_get_user_by_id_admin.return_value = mock_user_instance

    with patch(
        "resume_editor.app.api.routes.route_logic.admin_crud.User",
        return_value=mock_user_instance,
    ) as mock_user_class:
        created_user = create_user_admin(mock_db, user_data)

        mock_get_password_hash.assert_called_once_with("password")
        mock_user_class.assert_called_once()
        call_args = mock_user_class.call_args.kwargs
        assert "data" in call_args
        user_data_arg = call_args["data"]
        assert isinstance(user_data_arg, UserData)
        assert user_data_arg.username == user_data.username
        assert user_data_arg.email == user_data.email
        assert user_data_arg.hashed_password == "hashed_password"
        assert user_data_arg.is_active is is_active
        assert user_data_arg.attributes == attributes
        mock_db.add.assert_called_once_with(mock_user_instance)
        mock_db.commit.assert_called_once()
        mock_get_user_by_id_admin.assert_called_once_with(db=mock_db, user_id=1)
        assert created_user == mock_user_instance


@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_role_by_name_admin")
@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_password_hash")
def test_create_initial_admin_success(
    mock_get_password_hash: MagicMock,
    mock_get_role_by_name_admin: MagicMock,
    mock_get_user_by_id_admin: MagicMock,
):
    """
    Test successful creation of the initial admin user.
    """
    mock_db = MagicMock(spec=Session)
    mock_role = Role(name="admin", id=1)
    username = "admin"
    password = "password"

    # User object that's "created" and passed to add()
    created_db_user = User(
        data=UserData(
            username=username,
            email=f"{username}@placeholder.email",
            hashed_password="hashed_password",
            id_=1,
        )
    )

    # Fully formed user object that is returned by get_user_by_id_admin
    mock_returned_user = User(
        data=UserData(
            id_=1,
            username=username,
            email=f"{username}@placeholder.email",
            hashed_password="hashed_password",
        )
    )
    mock_returned_user.roles.append(mock_role)

    mock_get_password_hash.return_value = "hashed_password"
    mock_get_role_by_name_admin.return_value = mock_role
    mock_get_user_by_id_admin.return_value = mock_returned_user

    with patch(
        "resume_editor.app.api.routes.route_logic.admin_crud.User",
        return_value=created_db_user,
    ) as mock_user_class:
        result = create_initial_admin(
            db=mock_db, username=username, password=password
        )

        mock_get_password_hash.assert_called_once_with(password)
        mock_user_class.assert_called_once()
        call_args = mock_user_class.call_args.kwargs
        assert "data" in call_args
        user_data_arg = call_args["data"]
        assert isinstance(user_data_arg, UserData)
        assert user_data_arg.username == username
        assert user_data_arg.email == f"{username}@placeholder.email"
        assert user_data_arg.hashed_password == "hashed_password"
        assert user_data_arg.is_active is True
        assert user_data_arg.attributes == {}

        mock_get_role_by_name_admin.assert_called_once_with(db=mock_db, name="admin")
        mock_db.add.assert_called_once_with(created_db_user)
        mock_db.commit.assert_called_once()
        mock_get_user_by_id_admin.assert_called_once_with(
            db=mock_db, user_id=created_db_user.id
        )

        assert result is mock_returned_user
        assert result.username == username
        assert "admin" in [role.name for role in result.roles]


@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_role_by_name_admin")
@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_password_hash")
def test_create_initial_admin_role_not_found(
    mock_get_password_hash: MagicMock, mock_get_role_by_name_admin: MagicMock
):
    """
    Test create_initial_admin when the 'admin' role is not found.
    """
    mock_db = MagicMock(spec=Session)
    username = "admin"
    password = "password"

    mock_get_password_hash.return_value = "hashed_password"
    mock_get_role_by_name_admin.return_value = None

    with pytest.raises(
        RuntimeError, match="Admin role not found. Database may not be seeded correctly."
    ):
        create_initial_admin(db=mock_db, username=username, password=password)

    mock_get_password_hash.assert_called_once_with(password)
    mock_get_role_by_name_admin.assert_called_once_with(db=mock_db, name="admin")
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_user_by_id_admin")
def test_update_user_admin_refetch_fails(mock_get_user_by_id_admin: MagicMock):
    """Test update_user_admin raises RuntimeError if re-fetch fails."""
    mock_db = MagicMock(spec=Session)
    user_to_update = User(
        data=UserData(
            username="test", email="test@test.com", hashed_password="pw", id_=1
        )
    )
    mock_get_user_by_id_admin.return_value = None
    update_data = AdminUserUpdateRequest()

    with pytest.raises(
        RuntimeError, match="User with ID 1 not found after update commit."
    ):
        update_user_admin(
            db=mock_db,
            user=user_to_update,
            update_data=update_data,
        )

    mock_db.commit.assert_called_once()
    mock_get_user_by_id_admin.assert_called_once_with(db=mock_db, user_id=1)


@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_user_by_id_admin")
def test_assign_role_to_user_admin_refetch_fails(
    mock_get_user_by_id_admin: MagicMock,
):
    """Test assign_role_to_user_admin raises RuntimeError if re-fetch fails."""
    mock_db = MagicMock(spec=Session)
    mock_role = Role(name="admin")
    initial_user = User(
        data=UserData(
            username="testuser", email="test@test.com", hashed_password="hashed", id_=1
        )
    )
    initial_user.roles = []  # Role not assigned
    mock_get_user_by_id_admin.return_value = None

    with pytest.raises(
        RuntimeError, match="User with ID 1 not found after role assignment commit."
    ):
        assign_role_to_user_admin(db=mock_db, user=initial_user, role=mock_role)

    mock_db.commit.assert_called_once()
    mock_get_user_by_id_admin.assert_called_once_with(db=mock_db, user_id=1)


@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_user_by_id_admin")
def test_remove_role_from_user_admin_refetch_fails(
    mock_get_user_by_id_admin: MagicMock,
):
    """Test remove_role_from_user_admin raises RuntimeError if re-fetch fails."""
    mock_db = MagicMock(spec=Session)
    mock_role = Role(name="admin")
    initial_user = User(
        data=UserData(
            username="testuser", email="test@test.com", hashed_password="hashed", id_=1
        )
    )
    initial_user.roles = [mock_role]  # Role is assigned
    mock_get_user_by_id_admin.return_value = None

    with pytest.raises(
        RuntimeError, match="User with ID 1 not found after role removal commit."
    ):
        remove_role_from_user_admin(db=mock_db, user=initial_user, role=mock_role)

    mock_db.commit.assert_called_once()
    mock_get_user_by_id_admin.assert_called_once_with(db=mock_db, user_id=1)


@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_password_hash")
def test_create_user_admin_refetch_fails(
    mock_get_password_hash: MagicMock,
    mock_get_user_by_id_admin: MagicMock,
):
    """Test create_user_admin raises RuntimeError if re-fetch fails."""
    mock_db = MagicMock(spec=Session)
    user_data = AdminUserCreate(
        username="testuser",
        email="test@example.com",
        password="password",
    )
    mock_get_password_hash.return_value = "hashed_password"
    mock_user_instance = User(
        data=UserData(
            username=user_data.username,
            email=user_data.email,
            hashed_password="hashed_password",
            id_=1,
        )
    )
    mock_get_user_by_id_admin.return_value = None

    with patch(
        "resume_editor.app.api.routes.route_logic.admin_crud.User",
        return_value=mock_user_instance,
    ):
        with pytest.raises(
            RuntimeError, match="Failed to re-fetch created user after commit"
        ):
            create_user_admin(mock_db, user_data)

        mock_db.add.assert_called_once_with(mock_user_instance)
        mock_db.commit.assert_called_once()
        mock_get_user_by_id_admin.assert_called_once_with(db=mock_db, user_id=1)


@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_role_by_name_admin")
@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_password_hash")
def test_create_initial_admin_refetch_fails(
    mock_get_password_hash: MagicMock,
    mock_get_role_by_name_admin: MagicMock,
    mock_get_user_by_id_admin: MagicMock,
):
    """Test create_initial_admin raises RuntimeError if re-fetch fails."""
    mock_db = MagicMock(spec=Session)
    mock_role = Role(name="admin", id=1)
    username = "admin"
    password = "password"

    created_db_user = User(
        data=UserData(
            username=username,
            email=f"{username}@placeholder.email",
            hashed_password="hashed_password",
            id_=1,
        )
    )

    mock_get_password_hash.return_value = "hashed_password"
    mock_get_role_by_name_admin.return_value = mock_role
    mock_get_user_by_id_admin.return_value = None

    with patch(
        "resume_editor.app.api.routes.route_logic.admin_crud.User",
        return_value=created_db_user,
    ):
        with pytest.raises(
            RuntimeError, match="Failed to re-fetch created initial admin user"
        ):
            create_initial_admin(db=mock_db, username=username, password=password)

    mock_db.add.assert_called_once_with(created_db_user)
    mock_db.commit.assert_called_once()
    mock_get_user_by_id_admin.assert_called_once_with(db=mock_db, user_id=1)


@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_user_by_id_admin")
def test_update_user_admin_refetch_fails(mock_get_user_by_id_admin: MagicMock):
    """Test update_user_admin raises RuntimeError if re-fetch fails."""
    mock_db = MagicMock(spec=Session)
    user_to_update = User(
        data=UserData(
            username="test", email="test@test.com", hashed_password="pw", id_=1
        )
    )
    mock_get_user_by_id_admin.return_value = None
    update_data = AdminUserUpdateRequest()

    with pytest.raises(
        RuntimeError, match="User with ID 1 not found after update commit."
    ):
        update_user_admin(
            db=mock_db,
            user=user_to_update,
            update_data=update_data,
        )

    mock_db.commit.assert_called_once()
    mock_get_user_by_id_admin.assert_called_once_with(db=mock_db, user_id=1)


@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_user_by_id_admin")
def test_assign_role_to_user_admin_refetch_fails(
    mock_get_user_by_id_admin: MagicMock,
):
    """Test assign_role_to_user_admin raises RuntimeError if re-fetch fails."""
    mock_db = MagicMock(spec=Session)
    mock_role = Role(name="admin")
    initial_user = User(
        data=UserData(
            username="testuser", email="test@test.com", hashed_password="hashed", id_=1
        )
    )
    initial_user.roles = []  # Role not assigned
    mock_get_user_by_id_admin.return_value = None

    with pytest.raises(
        RuntimeError, match="User with ID 1 not found after role assignment commit."
    ):
        assign_role_to_user_admin(db=mock_db, user=initial_user, role=mock_role)

    mock_db.commit.assert_called_once()
    mock_get_user_by_id_admin.assert_called_once_with(db=mock_db, user_id=1)


@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_user_by_id_admin")
def test_remove_role_from_user_admin_refetch_fails(
    mock_get_user_by_id_admin: MagicMock,
):
    """Test remove_role_from_user_admin raises RuntimeError if re-fetch fails."""
    mock_db = MagicMock(spec=Session)
    mock_role = Role(name="admin")
    initial_user = User(
        data=UserData(
            username="testuser", email="test@test.com", hashed_password="hashed", id_=1
        )
    )
    initial_user.roles = [mock_role]  # Role is assigned
    mock_get_user_by_id_admin.return_value = None

    with pytest.raises(
        RuntimeError, match="User with ID 1 not found after role removal commit."
    ):
        remove_role_from_user_admin(db=mock_db, user=initial_user, role=mock_role)

    mock_db.commit.assert_called_once()
    mock_get_user_by_id_admin.assert_called_once_with(db=mock_db, user_id=1)


@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_password_hash")
def test_create_user_admin_refetch_fails(
    mock_get_password_hash: MagicMock,
    mock_get_user_by_id_admin: MagicMock,
):
    """Test create_user_admin raises RuntimeError if re-fetch fails."""
    mock_db = MagicMock(spec=Session)
    user_data = AdminUserCreate(
        username="testuser",
        email="test@example.com",
        password="password",
    )
    mock_get_password_hash.return_value = "hashed_password"
    mock_user_instance = User(
        data=UserData(
            username=user_data.username,
            email=user_data.email,
            hashed_password="hashed_password",
            id_=1,
        )
    )
    mock_get_user_by_id_admin.return_value = None

    with patch(
        "resume_editor.app.api.routes.route_logic.admin_crud.User",
        return_value=mock_user_instance,
    ):
        with pytest.raises(
            RuntimeError, match="Failed to re-fetch created user after commit"
        ):
            create_user_admin(mock_db, user_data)

        mock_db.add.assert_called_once_with(mock_user_instance)
        mock_db.commit.assert_called_once()
        mock_get_user_by_id_admin.assert_called_once_with(db=mock_db, user_id=1)


@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_user_by_id_admin")
@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_role_by_name_admin")
@patch("resume_editor.app.api.routes.route_logic.admin_crud.get_password_hash")
def test_create_initial_admin_refetch_fails(
    mock_get_password_hash: MagicMock,
    mock_get_role_by_name_admin: MagicMock,
    mock_get_user_by_id_admin: MagicMock,
):
    """Test create_initial_admin raises RuntimeError if re-fetch fails."""
    mock_db = MagicMock(spec=Session)
    mock_role = Role(name="admin", id=1)
    username = "admin"
    password = "password"

    created_db_user = User(
        data=UserData(
            username=username,
            email=f"{username}@placeholder.email",
            hashed_password="hashed_password",
            id_=1,
        )
    )

    mock_get_password_hash.return_value = "hashed_password"
    mock_get_role_by_name_admin.return_value = mock_role
    mock_get_user_by_id_admin.return_value = None

    with patch(
        "resume_editor.app.api.routes.route_logic.admin_crud.User",
        return_value=created_db_user,
    ):
        with pytest.raises(
            RuntimeError, match="Failed to re-fetch created initial admin user"
        ):
            create_initial_admin(db=mock_db, username=username, password=password)

    mock_db.add.assert_called_once_with(created_db_user)
    mock_db.commit.assert_called_once()
    mock_get_user_by_id_admin.assert_called_once_with(db=mock_db, user_id=1)
