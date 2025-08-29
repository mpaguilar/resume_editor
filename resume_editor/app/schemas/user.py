import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr

log = logging.getLogger(__name__)


class RoleResponse(BaseModel):
    """Schema for returning role data.

    This schema is used to represent a user role within API responses.

    Args:
        id (int): The unique identifier for the role.
        name (str): The name of the role (e.g., 'admin', 'user').

    Attributes:
        id (int): The unique identifier for the role.
        name (str): The name of the role (e.g., 'admin', 'user').

    Notes:
        1. The model uses ConfigDict(from_attributes=True) to support ORM attribute mapping.
    """

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


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

    Args:
        username (str): Unique username chosen by the user for login.
        email (EmailStr): Unique email address associated with the user.
        password (str): Plain text password provided by the user during registration.

    Attributes:
        password (str): Plain text password provided by the user during registration.

    Notes:
        1. The password is stored in plain text temporarily for hashing.
        2. The password is not returned in any response.
        3. The schema is used during user registration to validate input.

    """

    password: str


class AdminUserCreate(UserCreate):
    """Schema for creating a user as an administrator.

    This schema extends UserCreate to include additional fields that can be
    set by an administrator during user creation.

    Args:
        username (str): Unique username for the user.
        email (EmailStr): Unique email address for the user.
        password (str): Plain text password for the user.
        is_active (bool): Whether the user account is active. Defaults to True.
        attributes (dict[str, Any] | None): Flexible key-value attributes for the user.

    Attributes:
        is_active (bool): Whether the user account is active.
        attributes (dict[str, Any] | None): Flexible key-value attributes for the user.

    """

    is_active: bool = True
    attributes: dict[str, Any] | None = None


class UserLogin(BaseModel):
    """User login schema.

    This schema is used to authenticate users by validating their credentials.

    Args:
        username (str): Username provided by the user during login.
        password (str): Plain text password provided by the user during login.

    Attributes:
        username (str): Username provided by the user during login.
        password (str): Plain text password provided by the user during login.

    Notes:
        1. The credentials are validated against the user database.
        2. The password is not stored after authentication.
        3. This schema is used in the login endpoint to accept user input.

    """

    username: str
    password: str


class UserResponse(UserBase):
    """User response schema without password.

    This schema is used to return user data after authentication or retrieval,
    excluding sensitive fields like passwords.

    Args:
        id (int): Unique identifier assigned to the user in the database.
        username (str): Unique username chosen by the user for login.
        email (EmailStr): Unique email address associated with the user.
        is_active (bool): Indicates whether the user account is active and can log in.
        roles (list[RoleResponse]): List of roles assigned to the user.
        attributes (dict[str, Any] | None): Flexible key-value attributes for the user.

    Attributes:
        id (int): Unique identifier assigned to the user in the database.
        is_active (bool): Indicates whether the user account is active and can log in.
        roles (list[RoleResponse]): List of roles assigned to the user.
        attributes (dict[str, Any] | None): Flexible key-value attributes for the user.

    Notes:
        1. Data is retrieved from the user database during user lookup.
        2. The password field is omitted to maintain security.
        3. The model uses ConfigDict(from_attributes=True) to support ORM attribute mapping.

    """

    id: int
    is_active: bool
    roles: list[RoleResponse] = []
    attributes: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Token response schema.

    This schema represents the JWT access token returned by the authentication system
    after successful login.

    Args:
        access_token (str): The JWT access token used for subsequent authenticated requests.
        token_type (str): The type of token, which is always "bearer".

    Attributes:
        access_token (str): The JWT access token used for subsequent authenticated requests.
        token_type (str): The type of token, which is always "bearer".

    Notes:
        1. The access token is generated after successful authentication.
        2. The token type is always "bearer" as per standard JWT conventions.
        3. The token is returned to the client to authenticate future requests.

    """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data schema.

    This schema holds the information extracted from the JWT token payload,
    primarily used to identify the authenticated user.

    Args:
        username (str | None): The username stored in the token payload, or None if no user is authenticated.

    Attributes:
        username (str | None): The username stored in the token payload, or None if no user is authenticated.

    Notes:
        1. The schema extracts the username from the JWT token payload.
        2. If the token is invalid or expired, the username will be None.
        3. This data is used during request validation to identify the user.

    """

    username: str | None = None


class UserSettingsUpdateRequest(BaseModel):
    """Schema for updating user settings.

    This schema is used to update the user's LLM service configuration.

    Args:
        llm_endpoint (str | None): Custom LLM endpoint URL.
        api_key (str | None): Plaintext API key for the LLM service.

    Attributes:
        llm_endpoint (str | None): Custom LLM endpoint URL.
        api_key (str | None): Plaintext API key for the LLM service.

    Notes:
        1. The API key is not returned in the response for security.
        2. The settings are stored in the user database.
        3. Network access may occur when the LLM service is accessed using the endpoint.

    """

    llm_endpoint: str | None = None
    api_key: str | None = None


class UserSettingsResponse(BaseModel):
    """Schema for returning user settings.

    The API key is not returned for security.

    Args:
        llm_endpoint (str | None): Custom LLM endpoint URL.
        api_key_is_set (bool): Whether an API key has been set.

    Attributes:
        llm_endpoint (str | None): Custom LLM endpoint URL.
        api_key_is_set (bool): Whether an API key has been set.

    Notes:
        1. The API key is not returned in the response.
        2. The data is retrieved from the user database.
        3. The model uses ConfigDict(from_attributes=True) to support ORM attribute mapping.

    """

    llm_endpoint: str | None = None
    api_key_is_set: bool = False

    model_config = ConfigDict(from_attributes=True)
