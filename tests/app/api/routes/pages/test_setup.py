import logging
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app

log = logging.getLogger(__name__)

# This is important for overriding dependencies
app = create_app()


def setup_dependency_overrides(mock_db: MagicMock):
    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db


def test_get_setup_page_no_users():
    """
    Test GET /setup when no users exist in the database.
    """
    _msg = "test_get_setup_page_no_users starting"
    log.debug(_msg)

    mock_db = MagicMock()
    mock_db.query.return_value.count.return_value = 0
    setup_dependency_overrides(mock_db=mock_db)

    client = TestClient(app)
    response = client.get("/setup")

    assert response.status_code == 200
    assert "Welcome to Resume Writer!" in response.text
    # Check that user_count was called
    mock_db.query.return_value.count.assert_called_once()

    app.dependency_overrides.clear()


def test_get_setup_page_users_exist():
    """
    Test GET /setup when users already exist in the database.
    """
    _msg = "test_get_setup_page_users_exist starting"
    log.debug(_msg)

    mock_db = MagicMock()
    mock_db.query.return_value.count.return_value = 1
    setup_dependency_overrides(mock_db=mock_db)

    client = TestClient(app)
    response = client.get("/setup", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/login"
    mock_db.query.return_value.count.assert_called_once()

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.pages.setup.create_initial_admin")
def test_handle_setup_form_success(mock_create_initial_admin: MagicMock):
    """
    Test POST /setup with valid form data and no existing users.
    """
    _msg = "test_handle_setup_form_success starting"
    log.debug(_msg)

    mock_db = MagicMock()
    mock_db.query.return_value.count.return_value = 0
    setup_dependency_overrides(mock_db=mock_db)

    client = TestClient(app)
    form_data = {
        "username": "admin",
        "password": "password123",
        "confirm_password": "password123",
    }
    response = client.post("/setup", data=form_data, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    mock_create_initial_admin.assert_called_once_with(
        db=mock_db, username="admin", password="password123"
    )
    # user_count is called at the beginning
    assert mock_db.query.return_value.count.call_count == 1

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.pages.setup.create_initial_admin")
def test_handle_setup_form_passwords_mismatch(mock_create_initial_admin: MagicMock):
    """
    Test POST /setup when passwords do not match.
    """
    _msg = "test_handle_setup_form_passwords_mismatch starting"
    log.debug(_msg)

    mock_db = MagicMock()
    mock_db.query.return_value.count.return_value = 0
    setup_dependency_overrides(mock_db=mock_db)

    client = TestClient(app)
    form_data = {
        "username": "admin",
        "password": "password123",
        "confirm_password": "password456",
    }
    response = client.post("/setup", data=form_data)

    assert response.status_code == 400
    assert "Passwords do not match" in response.text
    mock_create_initial_admin.assert_not_called()
    assert mock_db.query.return_value.count.call_count == 1

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.pages.setup.create_initial_admin")
def test_handle_setup_form_users_exist(mock_create_initial_admin: MagicMock):
    """
    Test POST /setup when users already exist (race condition).
    """
    _msg = "test_handle_setup_form_users_exist starting"
    log.debug(_msg)

    mock_db = MagicMock()
    mock_db.query.return_value.count.return_value = 1
    setup_dependency_overrides(mock_db=mock_db)

    client = TestClient(app)
    form_data = {
        "username": "admin",
        "password": "password123",
        "confirm_password": "password123",
    }
    response = client.post("/setup", data=form_data, follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/login"
    mock_create_initial_admin.assert_not_called()
    assert mock_db.query.return_value.count.call_count == 1

    app.dependency_overrides.clear()
