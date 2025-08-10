import logging
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

log = logging.getLogger(__name__)


class TestSecurity:
    """Test cases for security functions."""

    @pytest.fixture(autouse=True)
    def setup_test(self):
        """Setup test by importing functions after mocking dependencies."""
        # Mock the settings import first
        with patch("resume_editor.app.core.config.get_settings") as mock_get_settings:
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
                    settings
                from resume_editor.app.core.security import (
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
            b"plain", b"hashed",
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
            b"plain_password", b"salt",
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
