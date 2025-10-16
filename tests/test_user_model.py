import logging
from unittest.mock import patch

import pytest

log = logging.getLogger(__name__)


class TestUser:
    """Test cases for the User model."""

    @pytest.fixture(autouse=True)
    def mock_user_model_imports(self):
        """Mock imports to prevent database connection during User model import."""
        with (
            patch("resume_editor.app.database.database.create_engine"),
            patch("resume_editor.app.database.database.sessionmaker"),
        ):
            # Import User after mocking
            global User, UserData
            from resume_editor.app.models.user import User, UserData

            yield

    def test_user_creation(self):
        """Test creating a User instance."""
        user_data = UserData(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        user = User(data=user_data)

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_password"
        assert user.is_active is True

    def test_user_creation_defaults(self):
        """Test creating a User instance with default values."""
        user_data = UserData(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
        )
        user = User(data=user_data)

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_password"
        assert user.is_active is True

    def test_user_validation_username_empty(self):
        """Test User validation with empty username."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            user_data = UserData(
                username="",
                email="test@example.com",
                hashed_password="hashed_password",
            )
            User(data=user_data)

    def test_user_validation_email_empty(self):
        """Test User validation with empty email."""
        with pytest.raises(ValueError, match="Email cannot be empty"):
            user_data = UserData(
                username="testuser", email="", hashed_password="hashed_password"
            )
            User(data=user_data)

    def test_user_validation_password_empty(self):
        """Test User validation with empty password."""
        with pytest.raises(ValueError, match="Hashed password cannot be empty"):
            user_data = UserData(
                username="testuser", email="test@example.com", hashed_password=""
            )
            User(data=user_data)

    def test_user_validation_username_not_string(self):
        """Test User validation with non-string username."""
        with pytest.raises(ValueError, match="Username must be a string"):
            user_data = UserData(
                username=123,
                email="test@example.com",
                hashed_password="hashed_password",
            )
            User(data=user_data)

    def test_user_validation_email_not_string(self):
        """Test User validation with non-string email."""
        with pytest.raises(ValueError, match="Email must be a string"):
            user_data = UserData(
                username="testuser", email=123, hashed_password="hashed_password"
            )
            User(data=user_data)

    def test_user_validation_password_not_string(self):
        """Test User validation with non-string password."""
        with pytest.raises(ValueError, match="Hashed password must be a string"):
            user_data = UserData(
                username="testuser", email="test@example.com", hashed_password=123
            )
            User(data=user_data)

    def test_user_validation_is_active_not_boolean(self):
        """Test User validation with non-boolean is_active."""
        with pytest.raises(ValueError, match="is_active must be a boolean"):
            user_data = UserData(
                username="testuser",
                email="test@example.com",
                hashed_password="hashed_password",
                is_active="yes",
            )
            User(data=user_data)
