from datetime import datetime
from unittest.mock import MagicMock, patch

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from resume_editor.app.core.auth import get_optional_current_user_from_cookie
from resume_editor.app.main import create_app
from resume_editor.app.models.role import Role
from resume_editor.app.models.user import User


def test_admin_users_page_not_authenticated():
    """Test that unauthenticated access to /admin/users redirects to the login page."""
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    # The dependency will return None if not authenticated
    def get_mock_optional_user_none():
        return None

    app.dependency_overrides[get_optional_current_user_from_cookie] = (
        get_mock_optional_user_none
    )

    response = client.get("/admin/users", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/login"

    app.dependency_overrides.clear()


def test_admin_users_page_as_non_admin():
    """Test that a non-admin user receives a 403 Forbidden error."""
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = User(
        username="testuser",
        email="test@test.com",
        hashed_password="hashed",
    )
    mock_user.roles = []  # Not an admin

    def get_mock_optional_user():
        return mock_user

    app.dependency_overrides[get_optional_current_user_from_cookie] = (
        get_mock_optional_user
    )

    response = client.get("/admin/users", follow_redirects=False)
    assert response.status_code == 403
    assert "The user does not have admin privileges" in response.text

    app.dependency_overrides.clear()


@patch("resume_editor.app.web.admin.get_users_admin")
def test_admin_users_page_as_admin(mock_get_users_admin):
    """Test that an admin user can successfully access the admin users page and see user data."""
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_admin = User(
        username="admin",
        email="admin@test.com",
        hashed_password="hashed",
    )
    mock_admin.roles = [Role(name="admin")]

    def get_mock_admin_user():
        return mock_admin

    app.dependency_overrides[get_optional_current_user_from_cookie] = (
        get_mock_admin_user
    )

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
    mock_get_users_admin.assert_called_once()
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

    app.dependency_overrides.clear()
