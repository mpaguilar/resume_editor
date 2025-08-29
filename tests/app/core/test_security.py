import logging
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import InvalidToken
from jose import jwt
from sqlalchemy.orm import Session

from resume_editor.app.core import security as security_module
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)

# Use a real key for Fernet tests
TEST_FERNET_KEY = "dGVzdF9rZXlfbXVzdF9iZV8zMl9ieXRlc19sb25nQUI="


@pytest.fixture
def mock_settings():
    """Mock settings for security functions that depend on them."""
    with patch("resume_editor.app.core.security.get_settings") as mock_get_settings:
        _mock_settings = MagicMock()
        _mock_settings.secret_key = "test-secret-key"
        _mock_settings.algorithm = "HS256"
        _mock_settings.access_token_expire_minutes = 30
        _mock_settings.encryption_key = TEST_FERNET_KEY
        mock_get_settings.return_value = _mock_settings
        yield mock_get_settings


def test_password_hashing_and_verification():
    """Test that password hashing and verification work correctly."""
    password = "secret_password"
    hashed_password = security_module.get_password_hash(password)
    assert hashed_password != password
    assert isinstance(hashed_password, str)
    assert security_module.verify_password(password, hashed_password) is True
    assert security_module.verify_password("wrong_password", hashed_password) is False


def test_authenticate_user():
    """Test user authentication with correct and incorrect credentials."""
    mock_db = MagicMock(spec=Session)
    password = "my_correct_password"
    mock_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=security_module.get_password_hash(password),
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    # Test success
    authenticated_user = security_module.authenticate_user(
        mock_db,
        "testuser",
        password,
    )
    assert authenticated_user == mock_user

    # Test wrong password
    authenticated_user_wrong_pass = security_module.authenticate_user(
        mock_db,
        "testuser",
        "wrong_password",
    )
    assert authenticated_user_wrong_pass is None

    # Test user not found
    mock_db.query.return_value.filter.return_value.first.return_value = None
    authenticated_user_not_found = security_module.authenticate_user(
        mock_db,
        "nonexistent_user",
        "any_password",
    )
    assert authenticated_user_not_found is None


def test_create_and_validate_access_token(mock_settings):
    """Test JWT access token creation and content validation."""
    data = {"sub": "testuser"}
    manager = security_module.SecurityManager()
    token = manager.create_access_token(data)
    assert isinstance(token, str)

    settings = mock_settings.return_value
    decoded_payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )
    assert decoded_payload["sub"] == "testuser"
    assert "exp" in decoded_payload
    expires_at = datetime.fromtimestamp(decoded_payload["exp"], tz=UTC)
    now = datetime.now(UTC)
    expected_expires_at = now + timedelta(
        minutes=settings.access_token_expire_minutes,
    )
    # Allow a few seconds of tolerance for execution time
    assert abs((expires_at - expected_expires_at).total_seconds()) < 5


def test_create_access_token_with_custom_expiry(mock_settings):
    """Test JWT access token creation with a custom expires_delta."""
    data = {"sub": "testuser"}
    expires_delta = timedelta(minutes=15)
    manager = security_module.SecurityManager()
    token = manager.create_access_token(data, expires_delta=expires_delta)

    settings = mock_settings.return_value
    decoded_payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )
    assert decoded_payload["sub"] == "testuser"
    expires_at = datetime.fromtimestamp(decoded_payload["exp"], tz=UTC)
    now = datetime.now(UTC)
    expected_expires_at = now + expires_delta
    # Allow a few seconds of tolerance for execution time
    assert abs((expires_at - expected_expires_at).total_seconds()) < 5


def test_encrypt_and_decrypt_data(mock_settings):
    """Test that data can be encrypted and then decrypted successfully."""
    plain_text = "my secret api key"
    encrypted = security_module.encrypt_data(plain_text)
    decrypted = security_module.decrypt_data(encrypted)

    assert encrypted != plain_text
    assert decrypted == plain_text
    assert isinstance(encrypted, str)


def test_decrypt_invalid_data_raises_error(mock_settings):
    """Test decryption of invalid data raises InvalidToken."""
    with pytest.raises(InvalidToken):
        security_module.decrypt_data("this-is-not-a-valid-fernet-token")


def test_security_manager_init(mock_settings):
    """Test SecurityManager initialization."""
    manager = security_module.SecurityManager()
    settings = mock_settings.return_value
    assert manager.settings is not None
    assert manager.access_token_expire_minutes == settings.access_token_expire_minutes
    assert manager.secret_key == settings.secret_key
    assert manager.algorithm == settings.algorithm
