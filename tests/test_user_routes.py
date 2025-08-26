import logging
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.user import (
    create_new_user,
    get_user_by_email,
    get_user_by_username,
)
from resume_editor.app.models.user import User
from resume_editor.app.schemas.user import UserCreate

log = logging.getLogger(__name__)


class TestUserRoutes:
    """Test cases for user API routes."""

    @pytest.fixture(autouse=True)
    def mock_app_imports(self):
        """Mock imports to prevent database connection during app import."""
        with (
            patch("resume_editor.app.database.database.get_engine"),
            patch("resume_editor.app.database.database.get_session_local"),
        ):
            yield

    @pytest.fixture
    def client(self):
        """Create a test client."""
        with patch("resume_editor.app.database.database.get_engine"):
            from resume_editor.app.main import create_app

            app = create_app()
            return TestClient(app)

    @patch("resume_editor.app.api.routes.user.create_new_user")
    @patch("resume_editor.app.api.routes.user.get_user_by_email")
    @patch("resume_editor.app.api.routes.user.get_user_by_username")
    @patch("resume_editor.app.api.routes.user.get_db")
    def test_register_user(
        self,
        mock_get_db,
        mock_get_user_by_username,
        mock_get_user_by_email,
        mock_create_new_user,
        client,
    ):
        """Test user registration."""
        # Setup mocks
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock the helper functions to return None (user doesn't exist)
        mock_get_user_by_username.return_value = None
        mock_get_user_by_email.return_value = None

        # Mock the create_new_user function to return a user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_create_new_user.return_value = mock_user

        # Make request
        response = client.post(
            "/api/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpassword",
            },
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["id"] == 1
        assert data["is_active"] is True

    @patch("resume_editor.app.api.routes.user.get_user_by_username")
    @patch("resume_editor.app.api.routes.user.get_db")
    def test_register_user_duplicate_username(
        self,
        mock_get_db,
        mock_get_user_by_username,
        client,
    ):
        """Test user registration with duplicate username."""
        # Setup mocks
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock the helper function to return an existing user
        mock_user = MagicMock()
        mock_get_user_by_username.return_value = mock_user

        # Make request
        response = client.post(
            "/api/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpassword",
            },
        )

        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "Username already registered" in data["detail"]

    @patch("resume_editor.app.api.routes.user.get_user_by_email")
    @patch("resume_editor.app.api.routes.user.get_user_by_username")
    @patch("resume_editor.app.api.routes.user.get_db")
    def test_register_user_duplicate_email(
        self,
        mock_get_db,
        mock_get_user_by_username,
        mock_get_user_by_email,
        client,
    ):
        """Test user registration with duplicate email."""
        # Setup mocks
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock the helper functions to return None (user doesn't exist)
        mock_get_user_by_username.return_value = None
        mock_get_user_by_email.return_value = MagicMock(spec=User)

        # Make request
        response = client.post(
            "/api/users/register",
            json={
                "username": "anotheruser",
                "email": "test@example.com",
                "password": "testpassword",
            },
        )

        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "Email already registered" in data["detail"]

    @patch("resume_editor.app.api.routes.user.authenticate_user")
    @patch("resume_editor.app.api.routes.user.create_access_token")
    @patch("resume_editor.app.api.routes.user.get_db")
    def test_login_user(
        self,
        mock_get_db,
        mock_create_access_token,
        mock_authenticate_user,
        client,
    ):
        """Test user login."""
        # Setup mocks
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value.__enter__.return_value = mock_db

        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_authenticate_user.return_value = mock_user

        mock_create_access_token.return_value = "test_token"

        # Make request
        response = client.post(
            "/api/users/login",
            data={"username": "testuser", "password": "testpassword"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "test_token"
        assert data["token_type"] == "bearer"

    @patch("resume_editor.app.api.routes.user.authenticate_user")
    @patch("resume_editor.app.api.routes.user.get_db")
    def test_login_user_invalid_credentials(
        self,
        mock_get_db,
        mock_authenticate_user,
        client,
    ):
        """Test user login with invalid credentials."""
        # Setup mocks
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_authenticate_user.return_value = None

        # Make request
        response = client.post(
            "/api/users/login",
            data={"username": "testuser", "password": "wrongpassword"},
        )

        # Assertions
        assert response.status_code == 401
        data = response.json()
        assert "Incorrect username or password" in data["detail"]


class TestUserHelpers:
    """Test cases for user helper functions."""

    def test_get_user_by_username(self):
        """Test retrieving a user by username."""
        mock_db = MagicMock(spec=Session)
        mock_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        user = get_user_by_username(mock_db, "testuser")
        assert user is not None
        assert user.username == "testuser"
        mock_db.query.assert_called_once_with(User)

    def test_get_user_by_email(self):
        """Test retrieving a user by email."""
        mock_db = MagicMock(spec=Session)
        mock_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        user = get_user_by_email(mock_db, "test@example.com")
        assert user is not None
        assert user.email == "test@example.com"
        mock_db.query.assert_called_once_with(User)

    @patch("resume_editor.app.api.routes.user.get_password_hash")
    def test_create_new_user(self, mock_get_password_hash):
        """Test creating a new user."""
        mock_db = MagicMock(spec=Session)
        mock_get_password_hash.return_value = "hashed_password"
        user_data = UserCreate(
            username="newuser",
            email="new@example.com",
            password="password",
        )

        new_user = create_new_user(mock_db, user_data)

        mock_get_password_hash.assert_called_once_with("password")
        mock_db.add.assert_called_once()
        added_user = mock_db.add.call_args[0][0]
        assert isinstance(added_user, User)
        assert added_user.username == "newuser"
        assert added_user.email == "new@example.com"
        assert added_user.hashed_password == "hashed_password"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(added_user)
        assert new_user == added_user
