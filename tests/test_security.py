import logging
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from resume_editor.app.models.user import User

log = logging.getLogger(__name__)


class TestSecurity:
    """Test cases for security functions."""

    @pytest.fixture(autouse=True)
    def setup_test(self):
        """Setup test by importing functions after mocking dependencies."""
        # Mock the settings import first
        with patch("resume_editor.app.core.security.get_settings") as mock_get_settings:
            # Create a mock settings object
            mock_settings = MagicMock()
            mock_settings.secret_key = "test-secret-key"
            mock_settings.algorithm = "HS256"
            mock_settings.access_token_expire_minutes = 30
            mock_get_settings.return_value = mock_settings

            # Mock database imports
            with (
                patch("resume_editor.app.database.database.create_engine"),
                patch("resume_editor.app.database.database.sessionmaker"),
                patch("sqlalchemy.orm.declarative_base"),
            ):
                # Now import functions after mocking
                global \
                    verify_password, \
                    get_password_hash, \
                    authenticate_user, \
                    create_access_token, \
                    settings, \
                    SecurityManager
                from resume_editor.app.core.security import (
                    SecurityManager,
                    authenticate_user,
                    create_access_token,
                    get_password_hash,
                    settings,
                    verify_password,
                )

                yield

    def test_get_password_hash(self):
        """Test password hashing."""
        password = "testpassword"
        hashed = get_password_hash(password)

        assert hashed is not None
        assert hashed != password
        assert isinstance(hashed, str)

    def test_verify_password(self):
        """Test password verification."""
        password = "testpassword"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    @patch("resume_editor.app.core.security.bcrypt")
    def test_verify_password_context_called(self, mock_bcrypt):
        """Test that bcrypt.checkpw is called."""
        mock_bcrypt.checkpw.return_value = True

        result = verify_password("plain", "hashed")

        mock_bcrypt.checkpw.assert_called_once_with(
            b"plain",
            b"hashed",
        )
        assert result is True

    @patch("resume_editor.app.core.security.bcrypt")
    def test_get_password_hash_context_called(self, mock_bcrypt):
        """Test that bcrypt.hashpw is called."""
        mock_bcrypt.gensalt.return_value = b"salt"
        mock_bcrypt.hashpw.return_value = b"hashed_password"

        result = get_password_hash("plain_password")

        mock_bcrypt.gensalt.assert_called_once()
        mock_bcrypt.hashpw.assert_called_once_with(
            b"plain_password",
            b"salt",
        )
        assert result == "hashed_password"

    @patch("resume_editor.app.core.security.jwt")
    def test_create_access_token(self, mock_jwt):
        """Test creating access token."""
        mock_jwt.encode.return_value = "encoded_token"
        data = {"sub": "testuser"}

        token = create_access_token(data)

        assert token == "encoded_token"
        # Check that jwt.encode was called with the modified data (including exp)
        mock_jwt.encode.assert_called_once()
        called_args, called_kwargs = mock_jwt.encode.call_args
        assert called_args[0]["sub"] == "testuser"
        assert "exp" in called_args[0]
        assert called_args[1] == settings.secret_key
        assert called_kwargs["algorithm"] == settings.algorithm

    @patch("resume_editor.app.core.security.jwt")
    def test_create_access_token_with_expires(self, mock_jwt):
        """Test creating access token with custom expiration."""
        mock_jwt.encode.return_value = "encoded_token"
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=60)

        token = create_access_token(data, expires_delta)

        assert token == "encoded_token"
        mock_jwt.encode.assert_called_once()
        called_args, called_kwargs = mock_jwt.encode.call_args
        assert called_args[0]["sub"] == "testuser"
        assert "exp" in called_args[0]
        assert called_args[1] == settings.secret_key
        assert called_kwargs["algorithm"] == settings.algorithm

    def test_security_manager_init(self):
        """Test SecurityManager initialization."""
        manager = SecurityManager()
        assert manager.settings is not None
        assert manager.access_token_expire_minutes == 30
        assert manager.secret_key == "test-secret-key"
        assert manager.algorithm == "HS256"

    @patch("resume_editor.app.core.security.verify_password")
    def test_authenticate_user_success(self, mock_verify_password):
        """Test successful user authentication."""
        mock_db = MagicMock(spec=Session)

        mock_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        mock_verify_password.return_value = True

        result = authenticate_user(mock_db, "testuser", "testpassword")

        assert result == mock_user
        mock_verify_password.assert_called_once_with("testpassword", "hashed_password")

    def test_authenticate_user_not_found(self):
        """Test authentication for a user that is not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = authenticate_user(mock_db, "nonexistent", "password")

        assert result is None

    @patch("resume_editor.app.core.security.verify_password")
    def test_authenticate_user_incorrect_password(self, mock_verify_password):
        """Test authentication with an incorrect password."""
        mock_db = MagicMock(spec=Session)
        mock_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_verify_password.return_value = False

        result = authenticate_user(mock_db, "testuser", "wrongpassword")

        assert result is None
        mock_verify_password.assert_called_once_with("wrongpassword", "hashed_password")
