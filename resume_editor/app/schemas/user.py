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

    Args:
        username (str): Unique username chosen by the user for login.
        email (EmailStr): Unique email address associated with the user.
        password (str): Plain text password provided by the user during registration.

    Attributes:
        password (str): Plain text password provided by the user during registration.

    """

    password: str


class UserLogin(BaseModel):
    """User login schema.

    This schema is used to authenticate users by validating their credentials.

    Args:
        username (str): Username provided by the user during login.
        password (str): Plain text password provided by the user during login.

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

    Args:
        id (int): Unique identifier assigned to the user in the database.
        username (str): Unique username chosen by the user for login.
        email (EmailStr): Unique email address associated with the user.
        is_active (bool): Indicates whether the user account is active and can log in.

    Attributes:
        id (int): Unique identifier assigned to the user in the database.
        is_active (bool): Indicates whether the user account is active and can log in.

    Notes:
        1. The schema includes user identification and status information.
        2. The password field is omitted to maintain security.
        3. Data is retrieved from the user database during user lookup.
        4. The model uses ConfigDict(from_attributes=True) to support ORM attribute mapping.

    """

    id: int
    is_active: bool

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

    Attributes:
        llm_endpoint (str | None): Custom LLM endpoint URL.
        api_key (str | None): Plaintext API key for the LLM service.
    """

    llm_endpoint: str | None = None
    api_key: str | None = None


class UserSettingsResponse(BaseModel):
    """Schema for returning user settings.

    The API key is not returned for security.

    Attributes:
        llm_endpoint (str | None): Custom LLM endpoint URL.
        api_key_is_set (bool): Whether an API key has been set.
    """

    llm_endpoint: str | None = None
    api_key_is_set: bool = False

    model_config = ConfigDict(from_attributes=True)
