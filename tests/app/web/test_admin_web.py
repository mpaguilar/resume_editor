from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup
from fastapi import status
from fastapi.testclient import TestClient

from resume_editor.app.core.auth import (
    get_db,
    get_optional_current_user_from_cookie,
)
from resume_editor.app.main import create_app
from resume_editor.app.models.role import Role
from resume_editor.app.models.user import User


@pytest.fixture
def app():
    """Fixture to create a new app for each test."""
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
    """Helper to set up dependency overrides for tests."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_optional_current_user_from_cookie] = lambda: mock_user


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_admin_users_page_not_authenticated(
    mock_get_session_local, mock_user_count, client, app
):
    """Test that unauthenticated access to /admin/users redirects to the login page."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    mock_db_session = MagicMock()
    setup_dependency_overrides(app, mock_db_session, None)

    response = client.get("/admin/users", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/login"
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_admin_users_page_as_non_admin(
    mock_get_session_local, mock_user_count, client, app
):
    """Test that a non-admin user receives a 403 Forbidden error."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    mock_db_session = MagicMock()
    mock_user = User(
        username="testuser",
        email="test@test.com",
        hashed_password="hashed",
    )
    mock_user.roles = []  # Not an admin

    setup_dependency_overrides(app, mock_db_session, mock_user)

    response = client.get("/admin/users", follow_redirects=False)
    assert response.status_code == 403
    assert "The user does not have admin privileges" in response.text
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
@patch("resume_editor.app.web.admin.get_users_admin")
def test_admin_users_page_as_admin(
    mock_get_users_admin, mock_get_session_local, mock_user_count, client, app
):
    """Test that an admin user can successfully access the admin users page and see user data."""
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    mock_db_session = MagicMock()
    mock_admin = User(
        username="admin",
        email="admin@test.com",
        hashed_password="hashed",
    )
    mock_admin.roles = [Role(name="admin")]

    setup_dependency_overrides(app, mock_db_session, mock_admin)

    mock_user_1 = User(
        id=2,
        username="testuser1",
        email="user1@test.com",
        hashed_password="pwd",
    )
    mock_user_1.resumes = []
    mock_user_1.attributes = {}
    mock_user_1.last_login_at = None

    mock_user_2 = User(
        id=3,
        username="testuser2",
        email="user2@test.com",
        hashed_password="pwd",
    )
    mock_user_2.resumes = [MagicMock()]
    mock_user_2.attributes = {"force_password_change": True}
    mock_user_2.last_login_at = datetime(2025, 8, 31, 12, 0, 0)

    mock_user_3 = User(
        id=4,
        username="testuser3",
        email="user3@test.com",
        hashed_password="pwd",
    )
    mock_user_3.resumes = []
    mock_user_3.attributes = None
    mock_user_3.last_login_at = None

    mock_get_users_admin.return_value = [mock_user_1, mock_user_2, mock_user_3]

    response = client.get("/admin/users")

    assert response.status_code == 200
    mock_get_users_admin.assert_called_once_with(db=mock_db_session)
    soup = BeautifulSoup(response.content, "html.parser")
    rows = soup.find("tbody").find_all("tr")
    assert len(rows) == 3

    # Check User 1
    cols_user1 = rows[0].find_all("td")
    assert cols_user1[0].text.strip() == "testuser1"
    assert cols_user1[1].text.strip() == "user1@test.com"
    assert cols_user1[2].text.strip() == "Never"
    assert cols_user1[3].text.strip() == "0"
    assert "No" in cols_user1[4].text.strip()

    # Check User 2
    cols_user2 = rows[1].find_all("td")
    assert cols_user2[0].text.strip() == "testuser2"
    assert cols_user2[1].text.strip() == "user2@test.com"
    assert cols_user2[2].text.strip() == "2025-08-31 12:00:00"
    assert cols_user2[3].text.strip() == "1"
    assert "Yes" in cols_user2[4].text.strip()

    # Check User 3 (attributes is None)
    cols_user3 = rows[2].find_all("td")
    assert cols_user3[0].text.strip() == "testuser3"
    assert cols_user3[1].text.strip() == "user3@test.com"
    assert cols_user3[2].text.strip() == "Never"
    assert cols_user3[3].text.strip() == "0"
    assert "No" in cols_user3[4].text.strip()
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_admin_delete_user_web_success(
    mock_get_session_local, mock_user_count, client, app
):
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    mock_db_session = MagicMock()
    admin_user = User(
        id=1,
        username="admin",
        email="admin@test.com",
        hashed_password="hashed",
    )
    admin_user.roles = [Role(id=1, name="admin")]
    user_to_delete = User(
        id=2,
        username="delete_me",
        email="delete@me.com",
        hashed_password="hashed",
    )
    user_to_delete.roles = []

    setup_dependency_overrides(app, mock_db_session, admin_user)

    with (
        patch("resume_editor.app.web.admin.get_user_by_id_admin") as mock_get_user,
        patch("resume_editor.app.web.admin.delete_user_admin") as mock_delete,
        patch("resume_editor.app.web.admin.get_users_admin") as mock_get_users,
    ):
        mock_get_user.return_value = user_to_delete
        # After deletion, get_users_admin should only return the admin user
        mock_get_users.return_value = [admin_user]

        response = client.delete("/admin/users/2")

        assert response.status_code == 200
        mock_get_user.assert_called_once_with(db=mock_db_session, user_id=2)
        mock_delete.assert_called_once_with(db=mock_db_session, user=user_to_delete)
        mock_get_users.assert_called_once_with(db=mock_db_session)
        assert "delete_me" not in response.text
        assert "admin" in response.text
        mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_admin_delete_user_web_redirects_if_not_logged_in(
    mock_get_session_local, mock_user_count, client, app
):
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    mock_db_session = MagicMock()
    setup_dependency_overrides(app, mock_db_session, None)

    response = client.delete("/admin/users/1", follow_redirects=False)

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"] == "/login"
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_admin_delete_user_web_forbidden_if_not_admin(
    mock_get_session_local, mock_user_count, client, app
):
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    mock_db_session = MagicMock()
    non_admin_user = User(
        id=1,
        username="test",
        email="test@test.com",
        hashed_password="hashed",
    )
    non_admin_user.roles = []  # No admin role
    setup_dependency_overrides(app, mock_db_session, non_admin_user)

    response = client.delete("/admin/users/1", follow_redirects=False)
    assert response.status_code == 403
    assert "The user does not have admin privileges" in response.text
    mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_admin_delete_user_web_not_found(
    mock_get_session_local, mock_user_count, client, app
):
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    mock_db_session = MagicMock()
    admin_user = User(
        id=1,
        username="admin",
        email="admin@test.com",
        hashed_password="hashed",
    )
    admin_user.roles = [Role(name="admin")]
    setup_dependency_overrides(app, mock_db_session, admin_user)

    with patch("resume_editor.app.web.admin.get_user_by_id_admin") as mock_get_user:
        mock_get_user.return_value = None
        response = client.delete("/admin/users/999")
        assert response.status_code == 404
        assert "User not found" in response.text
        mock_user_count.assert_called_once()


@patch("resume_editor.app.main.user_crud.user_count", return_value=1)
@patch("resume_editor.app.main.get_session_local")
def test_admin_delete_user_web_self_delete_fails(
    mock_get_session_local, mock_user_count, client, app
):
    mock_session = MagicMock()
    mock_get_session_local.return_value = lambda: mock_session
    mock_db_session = MagicMock()
    admin_user = User(
        id=1,
        username="admin",
        email="admin@test.com",
        hashed_password="hashed",
    )
    admin_user.roles = [Role(name="admin")]
    setup_dependency_overrides(app, mock_db_session, admin_user)

    with patch("resume_editor.app.web.admin.get_user_by_id_admin") as mock_get_user:
        # Admin trying to delete themselves
        mock_get_user.return_value = admin_user
        response = client.delete("/admin/users/1")
        assert response.status_code == 400
        assert "Administrators cannot delete themselves." in response.text
        mock_user_count.assert_called_once()
