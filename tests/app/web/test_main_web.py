from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from resume_editor.app.core.auth import get_optional_current_user_from_cookie
from resume_editor.app.main import create_app
from resume_editor.app.models.role import Role
from resume_editor.app.models.user import User


def test_dashboard_not_authenticated():
    """Test that unauthenticated access to /dashboard redirects to the login page."""
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/login"

    app.dependency_overrides.clear()


def test_dashboard_as_non_admin():
    """Test that a non-admin user does not see the Admin link on the dashboard."""
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

    response = client.get("/dashboard")
    assert response.status_code == 200

    soup = BeautifulSoup(response.content, "html.parser")
    admin_link = soup.find("a", href="/admin/users")
    assert admin_link is None

    app.dependency_overrides.clear()


def test_dashboard_as_admin():
    """Test that an admin user sees the Admin link on the dashboard."""
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

    response = client.get("/dashboard")
    assert response.status_code == 200

    soup = BeautifulSoup(response.content, "html.parser")
    admin_link = soup.find("a", href="/admin/users")
    assert admin_link is not None
    assert admin_link.text.strip() == "Admin"

    app.dependency_overrides.clear()
