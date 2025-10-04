import logging
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, validates

from resume_editor.app.models import Base

log = logging.getLogger(__name__)


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
)


class User(Base):
    """
    User model for authentication and session management.

    Attributes:
        id (int): Unique identifier for the user.
        username (str): Unique username for the user.
        email (str): Unique email address for the user.
        hashed_password (str): Hashed password for the user.
        is_active (bool): Whether the user account is active.
        last_login_at (datetime): Timestamp of the last successful login.
        force_password_change (bool): If true, user must change password on next login.
        attributes (dict): Flexible key-value store for user-specific attributes.
        roles (list[Role]): Roles assigned to the user for authorization.
        resumes (list[Resume]): Resumes associated with the user.
        settings (UserSettings): User-specific settings.

    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    force_password_change = Column(Boolean, default=False, nullable=False)
    attributes = Column(JSONB().with_variant(JSON, "sqlite"), nullable=True)

    # Relationship to Role
    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
    )

    # Relationship to Resume
    resumes = relationship(
        "Resume",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Relationship to UserSettings
    settings = relationship(
        "UserSettings",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )

    def __init__(
        self,
        username: str,
        email: str,
        hashed_password: str,
        is_active: bool = True,
        attributes: dict[str, Any] | None = None,
        id: int | None = None,
    ):
        """
        Initialize a User instance.

        Args:
            username (str): Unique username for the user. Must be a non-empty string.
            email (str): Unique email address for the user. Must be a non-empty string.
            hashed_password (str): Hashed password for the user. Must be a non-empty string.
            is_active (bool): Whether the user account is active. Must be a boolean.
            attributes (dict | None): Flexible key-value attributes for the user.
            id (int | None): The unique identifier of the user, for testing purposes.

        Returns:
            None

        Notes:
            1. Validate that username is a non-empty string.
            2. Validate that email is a non-empty string.
            3. Validate that hashed_password is a non-empty string.
            4. Validate that is_active is a boolean.
            5. Validate that attributes is a dict or None.
            6. Assign all values to instance attributes.
            7. Log the initialization of the user with their username.
            8. This operation does not involve network, disk, or database access.

        """
        _msg = f"Initializing User with username: {username}"
        log.debug(_msg)

        if id is not None:
            self.id = id
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.is_active = is_active
        self.attributes = attributes

    @validates("username")
    def validate_username(self, key, username):
        """
        Validate the username field.

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
        """
        Validate the email field.

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
        """
        Validate the hashed_password field.

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
        """
        Validate the is_active field.

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

    @validates("attributes")
    def validate_attributes(self, key, attributes):
        """
        Validate the attributes field.

        Args:
            key (str): The field name being validated (should be 'attributes').
            attributes (dict | None): The attributes value to validate. Must be a dictionary or None.

        Returns:
            dict | None: The validated attributes.

        Notes:
            1. If attributes is not None, ensure it is a dictionary.
            2. This operation does not involve network, disk, or database access.

        """
        if attributes is not None and not isinstance(attributes, dict):
            raise ValueError("Attributes must be a dictionary")
        return attributes
