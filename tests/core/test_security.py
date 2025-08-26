import logging
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import InvalidToken
from sqlalchemy.orm import Session

from resume_editor.app.core import security as security_module
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)


# This fixture will mock settings for the entire module before any tests run
@pytest.fixture(scope="module", autouse=True)
def mock_security_dependencies():
    """Sets up mocks for security functions for the entire module."""
    with patch("resume_editor.app.core.config.get_settings") as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.secret_key = "test-secret-key"
        mock_settings.algorithm = "HS256"
        mock_settings.access_token_expire_minutes = 30
        mock_settings.encryption_key = "dGVzdF9rZXlfbXVzdF9iZV8zMl9ieXRlc19sb25nQUI="
        mock_get_settings.return_value = mock_settings

        # Reload the security module to pick up the mocked settings
        import importlib

        importlib.reload(security_module)
        yield


def test_get_password_hash():
    """Test password hashing."""
    password = "testpassword"
    hashed = security_module.get_password_hash(password)

    assert hashed is not None
    assert hashed != password
    assert isinstance(hashed, str)


def test_verify_password():
    """Test password verification."""
    password = "testpassword"
    hashed = security_module.get_password_hash(password)

    assert security_module.verify_password(password, hashed) is True
    assert security_module.verify_password("wrongpassword", hashed) is False


@patch("resume_editor.app.core.security.bcrypt")
def test_verify_password_context_called(mock_bcrypt):
    """Test that bcrypt.checkpw is called."""
    mock_bcrypt.checkpw.return_value = True

    result = security_module.verify_password("plain", "hashed")

    mock_bcrypt.checkpw.assert_called_once_with(
        b"plain",
        b"hashed",
    )
    assert result is True


@patch("resume_editor.app.core.security.bcrypt")
def test_get_password_hash_context_called(mock_bcrypt):
    """Test that bcrypt.hashpw is called."""
    mock_bcrypt.gensalt.return_value = b"salt"
    mock_bcrypt.hashpw.return_value = b"hashed_password"

    result = security_module.get_password_hash("plain_password")

    mock_bcrypt.gensalt.assert_called_once()
    mock_bcrypt.hashpw.assert_called_once_with(
        b"plain_password",
        b"salt",
    )
    assert result == "hashed_password"


@patch("resume_editor.app.core.security.jwt")
def test_create_access_token(mock_jwt):
    """Test creating access token."""
    mock_jwt.encode.return_value = "encoded_token"
    data = {"sub": "testuser"}

    token = security_module.create_access_token(data)

    assert token == "encoded_token"
    # Check that jwt.encode was called with the modified data (including exp)
    mock_jwt.encode.assert_called_once()
    called_args, called_kwargs = mock_jwt.encode.call_args
    assert called_args[0]["sub"] == "testuser"
    assert "exp" in called_args[0]
    assert called_args[1] == security_module.settings.secret_key
    assert called_kwargs["algorithm"] == security_module.settings.algorithm


@patch("resume_editor.app.core.security.jwt")
def test_create_access_token_with_expires(mock_jwt):
    """Test creating access token with custom expiration."""
    mock_jwt.encode.return_value = "encoded_token"
    data = {"sub": "testuser"}
    expires_delta = timedelta(minutes=60)

    token = security_module.create_access_token(data, expires_delta)

    assert token == "encoded_token"
    mock_jwt.encode.assert_called_once()
    called_args, called_kwargs = mock_jwt.encode.call_args
    assert called_args[0]["sub"] == "testuser"
    assert "exp" in called_args[0]
    assert called_args[1] == security_module.settings.secret_key
    assert called_kwargs["algorithm"] == security_module.settings.algorithm


def test_security_manager_init():
    """Test SecurityManager initialization."""
    manager = security_module.SecurityManager()
    assert manager.settings is not None
    assert manager.access_token_expire_minutes == 30
    assert manager.secret_key == "test-secret-key"
    assert manager.algorithm == "HS256"


@patch("resume_editor.app.core.security.verify_password")
def test_authenticate_user_success(mock_verify_password):
    """Test successful user authentication."""
    mock_db = MagicMock(spec=Session)

    mock_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    mock_verify_password.return_value = True

    result = security_module.authenticate_user(mock_db, "testuser", "testpassword")

    assert result == mock_user
    mock_verify_password.assert_called_once_with("testpassword", "hashed_password")


def test_authenticate_user_not_found():
    """Test authentication for a user that is not found."""
    mock_db = MagicMock(spec=Session)
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = security_module.authenticate_user(mock_db, "nonexistent", "password")

    assert result is None


@patch("resume_editor.app.core.security.verify_password")
def test_authenticate_user_incorrect_password(mock_verify_password):
    """Test authentication with an incorrect password."""
    mock_db = MagicMock(spec=Session)
    mock_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    mock_verify_password.return_value = False

    result = security_module.authenticate_user(mock_db, "testuser", "wrongpassword")

    assert result is None
    mock_verify_password.assert_called_once_with("wrongpassword", "hashed_password")


def test_encrypt_decrypt_data():
    """Test data encryption and decryption."""
    plain_text = "my secret data"
    encrypted = security_module.encrypt_data(plain_text)
    decrypted = security_module.decrypt_data(encrypted)

    assert encrypted != plain_text
    assert decrypted == plain_text


def test_decrypt_invalid_data():
    """Test decryption of invalid data raises InvalidToken."""
    with pytest.raises(InvalidToken):
        security_module.decrypt_data("invalid_encrypted_data")
