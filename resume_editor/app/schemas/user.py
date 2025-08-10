import logging

from pydantic import BaseModel, ConfigDict, EmailStr

log = logging.getLogger(__name__)


class UserBase(BaseModel):
    """Base user schema with common fields.

    This schema serves as the foundation for user-related data transfer,
    containing the essential information required for user identification.

    Attributes:
        username (str): Unique username chosen by the user for login.
        email (EmailStr): Unique email address associated with the user.

    """

    username: str
    email: EmailStr


class UserCreate(UserBase):
    """User creation schema with password.

    This schema is used when a new user is registering, including the password
    in plain text form for initial storage and hashing.

    Attributes:
        password (str): Plain text password provided by the user during registration.

    """

    password: str


class UserLogin(BaseModel):
    """User login schema.

    This schema is used to authenticate users by validating their credentials.

    Attributes:
        username (str): Username provided by the user during login.
        password (str): Plain text password provided by the user during login.

    """

    username: str
    password: str


class UserResponse(UserBase):
    """User response schema without password.

    This schema is used to return user data after authentication or retrieval,
    excluding sensitive fields like passwords.

    Attributes:
        id (int): Unique identifier assigned to the user in the database.
        is_active (bool): Indicates whether the user account is active and can log in.

    """

    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Token response schema.

    This schema represents the JWT access token returned by the authentication system
    after successful login.

    Attributes:
        access_token (str): The JWT access token used for subsequent authenticated requests.
        token_type (str): The type of token, which is always "bearer".

    """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data schema.

    This schema holds the information extracted from the JWT token payload,
    primarily used to identify the authenticated user.

    Attributes:
        username (str | None): The username stored in the token payload, or None if no user is authenticated.

    """

    username: str | None = None
