# Docstrings Reference

===
# File: `__init__.py`


===

===
# File: `main.py`

## function: `create_app() -> FastAPI`

Create and configure the FastAPI application.

Args:
    None

Returns:
    FastAPI: The configured FastAPI application instance.

Notes:
    1. Initialize the FastAPI application with the title "Resume Editor API".
    2. Create the database tables by calling Base.metadata.create_all with the database engine.
    3. Add CORS middleware to allow requests from any origin (for development only).
    4. Include the user router to handle user-related API endpoints.
    5. Define a health check endpoint at "/health" that returns a JSON object with status "ok".
    6. Log a success message indicating the application was created.

---


===

===
# File: `__init__.py`


===

===
# File: `user.py`

## function: `get_user_by_username(db: Session, username: str) -> User | None`

Retrieve a user from the database using their username.

Args:
    db: Database session dependency used to query the database.
    username: The unique username to search for in the database.

Returns:
    User | None: The User object if found, otherwise None.

Notes:
    1. Query the database for a user with the given username.
    2. Return the first match or None if no user is found.
    3. Database access: Performs a read operation on the User table.

---

## function: `get_user_by_email(db: Session, email: str) -> User | None`

Retrieve a user from the database using their email address.

Args:
    db: Database session dependency used to query the database.
    email: The unique email address to search for in the database.

Returns:
    User | None: The User object if found, otherwise None.

Notes:
    1. Query the database for a user with the given email.
    2. Return the first match or None if no user is found.
    3. Database access: Performs a read operation on the User table.

---

## function: `create_new_user(db: Session, user_data: UserCreate) -> User`

Create a new user in the database with the provided data.

Args:
    db: Database session dependency used to persist the new user.
    user_data: Data required to create a new user, including username, email, and password.

Returns:
    User: The newly created User object with all fields populated.

Notes:
    1. Hash the provided password using a secure hashing algorithm.
    2. Instantiate a new User object with the username, email, and hashed password.
    3. Add the new user object to the database session.
    4. Commit the transaction to persist the user to the database.
    5. Refresh the object to ensure it contains the latest state from the database.
    6. Database access: Performs a write operation on the User table.

---

## function: `register_user(user: UserCreate, db: Session) -> UserResponse`

Register a new user with the provided credentials.

Args:
    user: Data containing username, email, and password for the new user.
    db: Database session dependency used to interact with the user database.

Returns:
    UserResponse: The created user's data, excluding the password.

Notes:
    1. Check if the provided username already exists in the database.
    2. If the username exists, raise a 400 error.
    3. Check if the provided email already exists in the database.
    4. If the email exists, raise a 400 error.
    5. Create a new user with the provided data and store it in the database.
    6. Return the newly created user's data (without the password).
    7. Database access: Performs read and write operations on the User table.

---

## function: `login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session) -> Token`

Authenticate a user and return an access token.

Args:
    form_data: Form data containing username and password for authentication.
    db: Database session dependency used to verify user credentials.

Returns:
    Token: An access token for the authenticated user, formatted as a JWT.

Notes:
    1. Attempt to authenticate the user using the provided username and password.
    2. If authentication fails, raise a 401 error.
    3. Generate a JWT access token with a defined expiration time.
    4. Return the access token to the client.
    5. Database access: Performs a read operation on the User table to verify credentials.

---


===

===
# File: `__init__.py`


===

===
# File: `__init__.py`


===

===
# File: `config.py`

## function: `get_settings() -> Settings`

Get the global settings instance.

This function returns a singleton instance of the Settings class,
which contains all application configuration values.

Args:
    None: This function does not take any arguments.

Returns:
    Settings: The global settings instance, containing all configuration values.
        The instance is created by loading environment variables and applying defaults.

Notes:
    1. The function reads configuration from environment variables using the .env file.
    2. If environment variables are not set, default values are used.
    3. The Settings class uses Pydantic's validation and configuration features to ensure correct values.
    4. The function returns a cached instance to avoid repeated parsing of the .env file.
    5. This function does not perform any disk or network access beyond reading the .env file at startup.

---


===

===
# File: `security.py`

## function: `verify_password(plain_password: str, hashed_password: str) -> bool`

Verify a plain password against a hashed password.

Args:
    plain_password (str): The plain text password to verify.
    hashed_password (str): The hashed password to compare against.

Returns:
    bool: True if the password matches, False otherwise.

Notes:
    1. Use bcrypt to verify the password.
    2. No database or network access in this function.

---

## function: `get_password_hash(password: str) -> str`

Hash a plain password.

Args:
    password (str): The plain text password to hash.

Returns:
    str: The hashed password.

Notes:
    1. Use bcrypt to hash the password.
    2. No database or network access in this function.

---

## function: `authenticate_user(db: Session, username: str, password: str) -> Optional['User']`

Authenticate a user by username and password.

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

---

## function: `create_access_token(data: dict, expires_delta: Optional[timedelta]) -> str`

Create a JWT access token.

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

---

## `SecurityManager` class

Manages user authentication and authorization using password hashing and JWT tokens.

Attributes:
    settings (Settings): Configuration settings for the security system.
    access_token_expire_minutes (int): Duration in minutes for access token expiration.
    secret_key (str): Secret key used for signing JWT tokens.
    algorithm (str): Algorithm used for JWT encoding.

---
## method: `SecurityManager.__init__(self: UnknownType) -> UnknownType`

Initialize the SecurityManager with configuration settings.

---

===

===
# File: `auth.py`

## function: `get_current_user(db: Session, token: str) -> User`

Retrieve the authenticated user from the provided JWT token.

Args:
    db: Database session dependency used to query the database for the user.
    token: JWT token extracted from the request header, used to authenticate the user.

Returns:
    User: The authenticated User object corresponding to the token's subject (username).

Notes:
    1. Initialize an HTTP 401 exception with a generic error message and "Bearer" authentication header.
    2. Decode the JWT token using the secret key and algorithm to extract the subject (username).
    3. If the subject (username) is missing from the token payload, raise the credentials exception.
    4. If the JWT token is invalid or malformed, catch the JWTError and raise the credentials exception.
    5. Query the database using the retrieved username to find the corresponding User record.
    6. If the user is not found in the database, raise the credentials exception.
    7. Return the User object if all authentication checks pass.

---


===

===
# File: `__init__.py`


===

===
# File: `database.py`

## function: `get_engine() -> UnknownType`

Get or create the database engine.

Args:
    None
    
Returns:
    Engine: The SQLAlchemy engine instance used to connect to the database.
    
Notes:
    1. Create the engine only when first accessed to avoid premature connection.
    2. Reuse the same engine instance on subsequent calls to ensure consistency.
    3. Network access occurs when creating the engine, using the database URL from settings.

---

## function: `get_session_local() -> UnknownType`

Get or create the session local factory.

Args:
    None
    
Returns:
    sessionmaker: The SQLAlchemy sessionmaker instance used to create database sessions.
    
Notes:
    1. Create the sessionmaker only when first accessed to avoid premature configuration.
    2. Reuse the same sessionmaker instance on subsequent calls to ensure consistent session behavior.
    3. No network access in this function itself; it uses the previously created engine.

---

## function: `get_db() -> Generator[Session, None, None]`

Dependency to provide database sessions to route handlers.

Args:
    None

Returns:
    Generator[Session, None, None]: A generator that yields a database session for use in route handlers.

Notes:
    1. Create a new database session using the sessionmaker factory.
    2. Yield the session to be used in route handlers.
    3. Ensure the session is closed after use to release resources.
    4. No network access in this function itself; the session is created from the existing engine.

---


===

===
# File: `__init__.py`


===

===
# File: `user.py`

## `User` class

User model for authentication and session management.

Attributes:
    id (int): Unique identifier for the user.
    username (str): Unique username for the user.
    email (str): Unique email address for the user.
    hashed_password (str): Hashed password for the user.
    is_active (bool): Whether the user account is active.

---
## method: `User.__init__(self: UnknownType, username: str, email: str, hashed_password: str, is_active: bool) -> UnknownType`

Initialize a User instance.

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

---
## method: `User.validate_username(self: UnknownType, key: UnknownType, username: UnknownType) -> UnknownType`

Validate the username field.

Args:
    key (str): The field name being validated (should be 'username').
    username (str): The username value to validate. Must be a non-empty string.

Returns:
    str: The validated username (stripped of leading/trailing whitespace).

Notes:
    1. Ensure username is a string.
    2. Ensure username is not empty after stripping whitespace.

---
## method: `User.validate_email(self: UnknownType, key: UnknownType, email: UnknownType) -> UnknownType`

Validate the email field.

Args:
    key (str): The field name being validated (should be 'email').
    email (str): The email value to validate. Must be a non-empty string.

Returns:
    str: The validated email (stripped of leading/trailing whitespace).

Notes:
    1. Ensure email is a string.
    2. Ensure email is not empty after stripping whitespace.

---
## method: `User.validate_hashed_password(self: UnknownType, key: UnknownType, hashed_password: UnknownType) -> UnknownType`

Validate the hashed_password field.

Args:
    key (str): The field name being validated (should be 'hashed_password').
    hashed_password (str): The hashed password value to validate. Must be a non-empty string.

Returns:
    str: The validated hashed password (stripped of leading/trailing whitespace).

Notes:
    1. Ensure hashed_password is a string.
    2. Ensure hashed_password is not empty after stripping whitespace.

---
## method: `User.validate_is_active(self: UnknownType, key: UnknownType, is_active: UnknownType) -> UnknownType`

Validate the is_active field.

Args:
    key (str): The field name being validated (should be 'is_active').
    is_active (bool): The is_active value to validate. Must be a boolean.

Returns:
    bool: The validated is_active value.

Notes:
    1. Ensure is_active is a boolean.

---

===

===
# File: `user.py`


===

===
# File: `__init__.py`


===

===
# File: `user.py`

## `User` class

User model for authentication and session management.

Attributes:
    id (int): Unique identifier for the user.
    username (str): Unique username for the user.
    email (str): Unique email address for the user.
    hashed_password (str): Hashed password for the user.
    is_active (bool): Whether the user account is active.

---
## method: `User.__init__(self: UnknownType, username: str, email: str, hashed_password: str, is_active: bool) -> UnknownType`

Initialize a User instance.

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

---
## method: `User.validate_username(self: UnknownType, key: UnknownType, username: UnknownType) -> UnknownType`

Validate the username field.

Args:
    key (str): The field name being validated (should be 'username').
    username (str): The username value to validate. Must be a non-empty string.

Returns:
    str: The validated username (stripped of leading/trailing whitespace).

Notes:
    1. Ensure username is a string.
    2. Ensure username is not empty after stripping whitespace.

---
## method: `User.validate_email(self: UnknownType, key: UnknownType, email: UnknownType) -> UnknownType`

Validate the email field.

Args:
    key (str): The field name being validated (should be 'email').
    email (str): The email value to validate. Must be a non-empty string.

Returns:
    str: The validated email (stripped of leading/trailing whitespace).

Notes:
    1. Ensure email is a string.
    2. Ensure email is not empty after stripping whitespace.

---
## method: `User.validate_hashed_password(self: UnknownType, key: UnknownType, hashed_password: UnknownType) -> UnknownType`

Validate the hashed_password field.

Args:
    key (str): The field name being validated (should be 'hashed_password').
    hashed_password (str): The hashed password value to validate. Must be a non-empty string.

Returns:
    str: The validated hashed password (stripped of leading/trailing whitespace).

Notes:
    1. Ensure hashed_password is a string.
    2. Ensure hashed_password is not empty after stripping whitespace.

---
## method: `User.validate_is_active(self: UnknownType, key: UnknownType, is_active: UnknownType) -> UnknownType`

Validate the is_active field.

Args:
    key (str): The field name being validated (should be 'is_active').
    is_active (bool): The is_active value to validate. Must be a boolean.

Returns:
    bool: The validated is_active value.

Notes:
    1. Ensure is_active is a boolean.

---

===

