import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Optional

import bcrypt
from cryptography.fernet import Fernet
from jose import jwt
from sqlalchemy.orm import Session

from resume_editor.app.core.config import get_settings

if TYPE_CHECKING:
    from resume_editor.app.models.user import User

log = logging.getLogger(__name__)

# Get settings instance
settings = get_settings()

# Initialize Fernet with encryption key
fernet = Fernet(settings.encryption_key.encode())

# Constants for JWT
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


class SecurityManager:
    """Manages user authentication and authorization using password hashing and JWT tokens.

    Attributes:
        settings (Settings): Configuration settings for the security system.
        access_token_expire_minutes (int): Duration in minutes for access token expiration.
        secret_key (str): Secret key used for signing JWT tokens.
        algorithm (str): Algorithm used for JWT encoding.

    """

    def __init__(self):
        """Initialize the SecurityManager with configuration settings.

        Notes:
            1. Retrieve the application settings using get_settings().
            2. Assign the access token expiration time from settings.
            3. Set the secret key for JWT signing from settings.
            4. Set the JWT algorithm from settings.

        """
        self.settings = get_settings()
        self.access_token_expire_minutes = self.settings.access_token_expire_minutes
        self.secret_key = self.settings.secret_key
        self.algorithm = self.settings.algorithm


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password (str): The plain text password to verify.
        hashed_password (str): The hashed password to compare against.

    Returns:
        bool: True if the password matches, False otherwise.

    Notes:
        1. Use bcrypt to verify the password.
        2. No database or network access in this function.

    """
    _msg = "Verifying password"
    log.debug(_msg)
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Hash a plain password.

    Args:
        password (str): The plain text password to hash.

    Returns:
        str: The hashed password.

    Notes:
        1. Use bcrypt to hash the password.
        2. No database or network access in this function.

    """
    _msg = "Hashing password"
    log.debug(_msg)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def authenticate_user(db: Session, username: str, password: str) -> Optional["User"]:
    """Authenticate a user by username and password.

    Args:
        db (Session): Database session used to query for user records.
        username (str): Username to authenticate.
        password (str): Password to verify.

    Returns:
        Optional[User]: The authenticated user if successful, None otherwise.

    Notes:
        1. Query the database for a user with the given username.
        2. If user exists and password is correct, return the user.
        3. Otherwise, return None.

    """
    _msg = f"Authenticating user: {username}"
    log.debug(_msg)

    from resume_editor.app.models.user import User

    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token.

    Args:
        data (dict): Data to encode in the token (e.g., user ID, role).
        expires_delta (Optional[timedelta]): Custom expiration time for the token. If None, uses default.

    Returns:
        str: The encoded JWT token as a string.

    Notes:
        1. Copy the data to avoid modifying the original.
        2. Set expiration time based on expires_delta or default.
        3. Encode the data with the secret key and algorithm.
        4. No database or network access in this function.

    """
    _msg = "Creating access token"
    log.debug(_msg)

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_minutes,
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def encrypt_data(data: str) -> str:
    """Encrypts data using Fernet symmetric encryption.

    Args:
        data (str): The plaintext data to encrypt.

    Returns:
        str: The encrypted data, encoded as a string.
    """
    _msg = "Encrypting data"
    log.debug(_msg)
    return fernet.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> str:
    """Decrypts data using Fernet symmetric encryption.

    Args:
        encrypted_data (str): The encrypted data to decrypt.

    Returns:
        str: The decrypted plaintext data.
    """
    _msg = "Decrypting data"
    log.debug(_msg)
    return fernet.decrypt(encrypted_data.encode()).decode()
