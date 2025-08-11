import logging

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship, validates

from resume_editor.app.models import Base

log = logging.getLogger(__name__)


class User(Base):
    """User model for authentication and session management.

    Attributes:
        id (int): Unique identifier for the user.
        username (str): Unique username for the user.
        email (str): Unique email address for the user.
        hashed_password (str): Hashed password for the user.
        is_active (bool): Whether the user account is active.

    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationship to Resume
    resumes = relationship(
        "Resume", back_populates="user", cascade="all, delete-orphan",
    )

    def __init__(
        self,
        username: str,
        email: str,
        hashed_password: str,
        is_active: bool = True,
    ):
        """Initialize a User instance.

        Args:
            username (str): Unique username for the user. Must be a non-empty string.
            email (str): Unique email address for the user. Must be a non-empty string.
            hashed_password (str): Hashed password for the user. Must be a non-empty string.
            is_active (bool): Whether the user account is active. Must be a boolean.

        Returns:
            None

        Notes:
            1. Validate that username is a non-empty string.
            2. Validate that email is a non-empty string.
            3. Validate that hashed_password is a non-empty string.
            4. Validate that is_active is a boolean.
            5. Assign all values to instance attributes.
            6. Log the initialization of the user with their username.
            7. This operation does not involve network, disk, or database access.

        """
        _msg = f"Initializing User with username: {username}"
        log.debug(_msg)

        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.is_active = is_active

    @validates("username")
    def validate_username(self, key, username):
        """Validate the username field.

        Args:
            key (str): The field name being validated (should be 'username').
            username (str): The username value to validate. Must be a non-empty string.

        Returns:
            str: The validated username (stripped of leading/trailing whitespace).

        Notes:
            1. Ensure username is a string.
            2. Ensure username is not empty after stripping whitespace.
            3. This operation does not involve network, disk, or database access.

        """
        if not isinstance(username, str):
            raise ValueError("Username must be a string")
        if not username.strip():
            raise ValueError("Username cannot be empty")
        return username.strip()

    @validates("email")
    def validate_email(self, key, email):
        """Validate the email field.

        Args:
            key (str): The field name being validated (should be 'email').
            email (str): The email value to validate. Must be a non-empty string.

        Returns:
            str: The validated email (stripped of leading/trailing whitespace).

        Notes:
            1. Ensure email is a string.
            2. Ensure email is not empty after stripping whitespace.
            3. This operation does not involve network, disk, or database access.

        """
        if not isinstance(email, str):
            raise ValueError("Email must be a string")
        if not email.strip():
            raise ValueError("Email cannot be empty")
        return email.strip()

    @validates("hashed_password")
    def validate_hashed_password(self, key, hashed_password):
        """Validate the hashed_password field.

        Args:
            key (str): The field name being validated (should be 'hashed_password').
            hashed_password (str): The hashed password value to validate. Must be a non-empty string.

        Returns:
            str: The validated hashed password (stripped of leading/trailing whitespace).

        Notes:
            1. Ensure hashed_password is a string.
            2. Ensure hashed_password is not empty after stripping whitespace.
            3. This operation does not involve network, disk, or database access.

        """
        if not isinstance(hashed_password, str):
            raise ValueError("Hashed password must be a string")
        if not hashed_password.strip():
            raise ValueError("Hashed password cannot be empty")
        return hashed_password.strip()

    @validates("is_active")
    def validate_is_active(self, key, is_active):
        """Validate the is_active field.

        Args:
            key (str): The field name being validated (should be 'is_active').
            is_active (bool): The is_active value to validate. Must be a boolean.

        Returns:
            bool: The validated is_active value.

        Notes:
            1. Ensure is_active is a boolean.
            2. This operation does not involve network, disk, or database access.

        """
        if not isinstance(is_active, bool):
            raise ValueError("is_active must be a boolean")
        return is_active
