from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from resume_editor.app.main import create_app
from resume_editor.app.models.role import Role
from resume_editor.app.models.user import User


def setup_admin_user_mock() -> User:
    """Helper to create a mock admin user."""
    admin_user = User(
        id=1,
        username="admin",
        email="admin@test.com",
        hashed_password="hashed",
    )
    admin_user.roles = [Role(name="admin")]
    return admin_user


def test_get_admin_create_user_form_unauthenticated():
    """Test that unauthenticated users are redirected from create user form."""
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/admin/users/create-form", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/login"


def test_get_admin_create_user_form_non_admin():
    """Test that non-admin users cannot access the create user form."""
    app = create_app()
    # non-admin user has no roles
    non_admin_user = User(
        id=2,
        username="testuser",
        email="test@test.com",
        hashed_password="pw",
    )

    from resume_editor.app.core.auth import get_optional_current_user_from_cookie

    def override_get_optional_current_user_from_cookie():
        return non_admin_user

    app.dependency_overrides[get_optional_current_user_from_cookie] = (
        override_get_optional_current_user_from_cookie
    )

    with TestClient(app) as client:
        response = client.get("/admin/users/create-form", follow_redirects=False)
        assert response.status_code == 403
        assert response.json() == {"detail": "The user does not have admin privileges"}

    app.dependency_overrides.clear()


def test_get_admin_create_user_form_authenticated():
    """Test that admin users can access the create user form."""
    app = create_app()
    admin_user = setup_admin_user_mock()

    def override_get_optional_current_user_from_cookie():
        return admin_user

    from resume_editor.app.core.auth import get_optional_current_user_from_cookie

    app.dependency_overrides[get_optional_current_user_from_cookie] = (
        override_get_optional_current_user_from_cookie
    )

    with TestClient(app) as client:
        response = client.get("/admin/users/create-form")
        assert response.status_code == 200
        assert "Create New User" in response.text

    app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("resume_editor.app.web.admin_forms.admin_crud.create_user_admin")
async def test_handle_admin_create_user_form(mock_create_user_admin: MagicMock):
    """Test submitting the create user form."""
    app = create_app()
    admin_user = setup_admin_user_mock()

    def override_get_optional_current_user_from_cookie():
        return admin_user

    from resume_editor.app.core.auth import get_optional_current_user_from_cookie

    app.dependency_overrides[get_optional_current_user_from_cookie] = (
        override_get_optional_current_user_from_cookie
    )

    new_user = User(
        id=2, username="newuser", email="new@test.com", hashed_password="pw",
    )
    mock_create_user_admin.return_value = new_user

    with TestClient(app) as client:
        form_data = {
            "username": "newuser",
            "email": "new@test.com",
            "password": "password",
            "force_password_change": "true",
        }
        with patch(
            "resume_editor.app.web.admin_forms.admin_crud.get_users_admin",
            return_value=[admin_user, new_user],
        ):
            response = client.post("/admin/users/create", data=form_data)
        assert response.status_code == 200
        assert "newuser" in response.text
        mock_create_user_admin.assert_called_once()
        # Verify call arguments
        call_args = mock_create_user_admin.call_args[1]
        assert call_args["user_data"].username == "newuser"
        assert call_args["user_data"].attributes == {"force_password_change": True}

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_handle_admin_create_user_form_unauthenticated():
    """Test that unauthenticated users are redirected from handle create user form."""
    app = create_app()
    with TestClient(app) as client:
        response = client.post("/admin/users/create", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/login"


@patch("resume_editor.app.web.admin_forms.admin_crud.get_user_by_id_admin")
def test_get_admin_edit_user_form(mock_get_user: MagicMock):
    """Test getting the edit user form."""
    app = create_app()
    admin_user = setup_admin_user_mock()
    target_user = User(
        id=2,
        username="testuser",
        email="test@test.com",
        hashed_password="pw",
    )
    mock_get_user.return_value = target_user

    def override_get_optional_current_user_from_cookie():
        return admin_user

    from resume_editor.app.core.auth import get_optional_current_user_from_cookie

    app.dependency_overrides[get_optional_current_user_from_cookie] = (
        override_get_optional_current_user_from_cookie
    )

    with TestClient(app) as client:
        response = client.get("/admin/users/2/edit-form")
        assert response.status_code == 200
        assert "Edit User: testuser" in response.text
        assert 'value="test@test.com"' in response.text

    app.dependency_overrides.clear()


def test_get_admin_edit_user_form_unauthenticated():
    """Test that unauthenticated users are redirected from edit user form."""
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/admin/users/1/edit-form", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/login"


@pytest.mark.asyncio
@patch("resume_editor.app.web.admin_forms.admin_crud.update_user_admin")
@patch("resume_editor.app.web.admin_forms.admin_crud.get_user_by_id_admin")
async def test_handle_admin_edit_user_form(
    mock_get_user: MagicMock,
    mock_update_user: MagicMock,
):
    """Test submitting the edit user form."""
    app = create_app()
    admin_user = setup_admin_user_mock()
    target_user = User(
        id=2,
        username="testuser",
        email="test@test.com",
        hashed_password="pw",
    )
    mock_get_user.return_value = target_user

    def override_get_optional_current_user_from_cookie():
        return admin_user

    from resume_editor.app.core.auth import get_optional_current_user_from_cookie

    app.dependency_overrides[get_optional_current_user_from_cookie] = (
        override_get_optional_current_user_from_cookie
    )

    # This will be the "updated" user object returned by the update_user_admin mock
    updated_target_user = User(
        id=2,
        username="testuser",
        email="updated@test.com",
        hashed_password="pw",
    )
    mock_update_user.return_value = updated_target_user

    with TestClient(app) as client:
        form_data = {
            "email": "updated@test.com",
            "force_password_change": "true",
        }
        with patch(
            "resume_editor.app.web.admin_forms.admin_crud.get_users_admin",
            return_value=[admin_user, updated_target_user],
        ):
            response = client.post("/admin/users/2/edit", data=form_data)
        assert response.status_code == 200
        assert "updated@test.com" in response.text
        mock_update_user.assert_called_once()
        call_args = mock_update_user.call_args[1]
        assert call_args["update_data"].email == "updated@test.com"
        assert call_args["update_data"].force_password_change is True

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_handle_admin_edit_user_form_unauthenticated():
    """Test that unauthenticated users are redirected from handle edit user form."""
    app = create_app()
    with TestClient(app) as client:
        response = client.post("/admin/users/1/edit", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/login"


@patch("resume_editor.app.web.admin_forms.admin_crud.get_user_by_id_admin")
def test_get_admin_edit_user_form_user_not_found(mock_get_user: MagicMock):
    """Test getting the edit user form for a user that does not exist."""
    app = create_app()
    admin_user = setup_admin_user_mock()
    mock_get_user.return_value = None

    def override_get_optional_current_user_from_cookie():
        return admin_user

    from resume_editor.app.core.auth import get_optional_current_user_from_cookie

    app.dependency_overrides[get_optional_current_user_from_cookie] = (
        override_get_optional_current_user_from_cookie
    )

    with TestClient(app) as client:
        response = client.get("/admin/users/999/edit-form")
        assert response.status_code == 404
        assert response.json() == {"detail": "User not found"}

    app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("resume_editor.app.web.admin_forms.admin_crud.update_user_admin")
@patch("resume_editor.app.web.admin_forms.admin_crud.get_user_by_id_admin")
async def test_handle_admin_edit_user_form_user_not_found(
    mock_get_user: MagicMock,
    mock_update_user: MagicMock,
):
    """Test submitting the edit user form for a user that does not exist."""
    app = create_app()
    admin_user = setup_admin_user_mock()
    mock_get_user.return_value = None

    def override_get_optional_current_user_from_cookie():
        return admin_user

    from resume_editor.app.core.auth import get_optional_current_user_from_cookie

    app.dependency_overrides[get_optional_current_user_from_cookie] = (
        override_get_optional_current_user_from_cookie
    )

    with TestClient(app) as client:
        form_data = {
            "email": "updated@test.com",
            "force_password_change": "true",
        }
        response = client.post("/admin/users/999/edit", data=form_data)
        assert response.status_code == 404
        assert response.json() == {"detail": "User not found"}
        mock_update_user.assert_not_called()

    app.dependency_overrides.clear()
