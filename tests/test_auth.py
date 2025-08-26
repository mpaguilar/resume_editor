import logging
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from jose import JWTError
from sqlalchemy.orm import Session

from resume_editor.app.core.auth import get_current_user
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)


class TestGetCurrentUser:
    """Test cases for the get_current_user dependency."""

    @patch("resume_editor.app.core.auth.get_settings")
    @patch("resume_editor.app.core.auth.jwt.decode")
    def test_get_current_user_success(self, mock_jwt_decode, mock_get_settings):
        """Test successful authentication and user retrieval."""
        mock_get_settings.return_value = MagicMock(
            secret_key="test-secret",
            algorithm="HS256",
        )
        mock_db = MagicMock(spec=Session)
        expected_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
        )
        mock_db.query.return_value.filter.return_value.first.return_value = (
            expected_user
        )
        mock_jwt_decode.return_value = {"sub": "testuser"}
        token = "valid-token"

        user = get_current_user(db=mock_db, token=token)

        assert user == expected_user
        mock_db.query.assert_called_once_with(User)
        mock_jwt_decode.assert_called_once()

    @patch("resume_editor.app.core.auth.get_settings")
    def test_get_current_user_no_token(self, mock_get_settings):
        """Test authentication with no token provided."""
        mock_get_settings.return_value = MagicMock(
            secret_key="test-secret",
            algorithm="HS256",
        )
        mock_db = MagicMock(spec=Session)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(db=mock_db, token=None)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Could not validate credentials"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    @patch("resume_editor.app.core.auth.get_settings")
    @patch("resume_editor.app.core.auth.jwt.decode", side_effect=JWTError)
    def test_get_current_user_invalid_token(self, mock_jwt_decode, mock_get_settings):
        """Test authentication with an invalid (malformed) token."""
        mock_get_settings.return_value = MagicMock(
            secret_key="test-secret",
            algorithm="HS256",
        )
        mock_db = MagicMock(spec=Session)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(db=mock_db, token="invalid-token")

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Could not validate credentials"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    @patch("resume_editor.app.core.auth.get_settings")
    @patch("resume_editor.app.core.auth.jwt.decode")
    def test_get_current_user_no_username(self, mock_jwt_decode, mock_get_settings):
        """Test authentication with a token that has no username (sub)."""
        mock_get_settings.return_value = MagicMock(
            secret_key="test-secret",
            algorithm="HS256",
        )
        mock_db = MagicMock(spec=Session)
        mock_jwt_decode.return_value = {"id": 1}  # No 'sub' key

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(db=mock_db, token="token-no-sub")

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Could not validate credentials"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    @patch("resume_editor.app.core.auth.get_settings")
    @patch("resume_editor.app.core.auth.jwt.decode")
    def test_get_current_user_user_not_found(self, mock_jwt_decode, mock_get_settings):
        """Test authentication where user from token is not in the database."""
        mock_get_settings.return_value = MagicMock(
            secret_key="test-secret",
            algorithm="HS256",
        )
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_jwt_decode.return_value = {"sub": "nonexistent"}

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(db=mock_db, token="token-for-nonexistent-user")

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Could not validate credentials"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}
