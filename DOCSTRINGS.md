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
    5. Include the resume router to handle resume-related API endpoints.
    6. Define a health check endpoint at "/health" that returns a JSON object with status "ok".
    7. Log a success message indicating the application was created.

---

## function: `initialize_database() -> UnknownType`

Initialize the database tables.

Args:
    None

Returns:
    None

Notes:
    1. Create database tables by calling Base.metadata.create_all with the database engine.
    2. This function should be called after the app is created but before it starts serving requests.
    3. Database access is performed via the engine returned by get_engine().

---


===

===
# File: `__init__.py`

## function: `get_app() -> FastAPI`

Creates and configures the FastAPI application instance.

This function initializes a FastAPI app with the following features:
- Includes the authentication and resume management routes.
- Configures middleware for logging and error handling.
- Sets up CORS to allow frontend access from different origins.

Args:
    None.

Returns:
    FastAPI: A configured FastAPI application instance.

Notes:
    1. The application is initialized with a title, version, and description.
    2. Routes are included from the main application setup.
    3. CORS is enabled with allow_origins set to allow requests from 'http://localhost:3000'.
    4. The middleware stack includes logging and exception handling.
    5. The database session is provided via dependency injection through the 'get_db' function.
    6. The function performs no disk or network I/O.
    7. The function does not perform any database access.

---


===

===
# File: `resume.py`

## function: `get_current_user() -> UnknownType`

Placeholder for current user dependency.

In a real implementation, this would verify the user's authentication token
and return the current user object.

Returns:
    User: The current authenticated user.

---


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
    5. This function performs disk access to read the .env file at startup.

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

## function: `create_access_token(data: dict, expires_delta: timedelta | None) -> str`

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

Database Access:
    - Queries the User table to retrieve a user record by username.

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
    7. This operation does not involve network, disk, or database access.

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
    3. This operation does not involve network, disk, or database access.

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
    3. This operation does not involve network, disk, or database access.

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
    3. This operation does not involve network, disk, or database access.

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
    2. This operation does not involve network, disk, or database access.

---

===

===
# File: `resume_model.py`

## `Resume` class

Resume model for storing user resumes.

Attributes:
    id (int): Unique identifier for the resume.
    user_id (int): Foreign key to User model.
    name (str): User-assigned descriptive name for the resume.
    content (str): The Markdown text content of the resume.
    created_at (datetime): Timestamp when the resume was created.
    updated_at (datetime): Timestamp when the resume was last updated.
    is_active (bool): Whether the resume is active.

---
## method: `Resume.__init__(self: UnknownType, user_id: int, name: str, content: str, is_active: bool) -> UnknownType`

Initialize a Resume instance.

Args:
    user_id (int): Foreign key to User model, identifying the user who owns the resume.
    name (str): User-assigned descriptive name for the resume, must be non-empty.
    content (str): The Markdown text content of the resume, must be non-empty.
    is_active (bool): Whether the resume is currently active, defaults to True.

Returns:
    None

Notes:
    1. Validate that user_id is an integer.
    2. Validate that name is a non-empty string.
    3. Validate that content is a non-empty string.
    4. Validate that is_active is a boolean.
    5. Assign all values to instance attributes.
    6. Log the initialization of the resume with its name.
    7. This function performs no database access.

---

===

===
# File: `resume.py`


===

===
# File: `education.py`

## `Degree` class

Represents details of a specific academic degree earned.

Attributes:
    school (str): The name of the educational institution.
    degree (str | None): The type of degree (e.g., Bachelor, Master).
    start_date (datetime | None): The start date of the program.
    end_date (datetime | None): The end date of the program.
    major (str | None): The major field of study.
    gpa (str | None): The grade point average.

---
## method: `Degree.validate_school(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the school field.

Args:
    v: The school value to validate. Must be a non-empty string.

Returns:
    str: The validated school (stripped of leading/trailing whitespace).

Notes:
    1. Ensure school is a string.
    2. Ensure school is not empty after stripping whitespace.

---
## method: `Degree.validate_degree(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the degree field.

Args:
    v: The degree value to validate. Must be a non-empty string or None.

Returns:
    str: The validated degree (stripped of leading/trailing whitespace).

Notes:
    1. Ensure degree is a string or None.
    2. Ensure degree is not empty after stripping whitespace.

---
## method: `Degree.validate_major(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the major field.

Args:
    v: The major value to validate. Must be a non-empty string or None.

Returns:
    str: The validated major (stripped of leading/trailing whitespace).

Notes:
    1. Ensure major is a string or None.
    2. Ensure major is not empty after stripping whitespace.

---
## method: `Degree.validate_gpa(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the gpa field.

Args:
    v: The gpa value to validate. Must be a non-empty string or None.

Returns:
    str: The validated gpa (stripped of leading/trailing whitespace).

Notes:
    1. Ensure gpa is a string or None.
    2. Ensure gpa is not empty after stripping whitespace.

---
## method: `Degree.validate_dates(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the date fields.

Args:
    v: The date value to validate. Must be a datetime object or None.

Returns:
    datetime: The validated date.

Notes:
    1. Ensure date is a datetime object or None.

---
## method: `Degree.validate_end_date(cls: UnknownType, v: UnknownType, info: UnknownType) -> UnknownType`

Validate that start_date is not after end_date.

Args:
    v: The date value to validate.
    info: Validation info containing data.

Returns:
    datetime: The validated date.

Notes:
    1. If both start_date and end_date are provided, ensure start_date is not after end_date.

---
## `Degrees` class

Represents a collection of academic degrees earned.

Attributes:
    degrees (list[Degree]): A list of Degree objects representing educational achievements.

---
## method: `Degrees.validate_degrees(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the degrees field.

Args:
    v: The degrees value to validate. Must be a list of Degree objects.

Returns:
    list[Degree]: The validated degrees list.

Notes:
    1. Ensure degrees is a list.
    2. Ensure all items in degrees are instances of Degree.

---
## method: `Degrees.__iter__(self: UnknownType) -> UnknownType`

Iterate over the degrees.

Returns:
    Iterator over the degrees list.

---
## method: `Degrees.__len__(self: UnknownType) -> UnknownType`

Return the number of degrees.

Returns:
    int: The number of degrees in the list.

---
## method: `Degrees.__getitem__(self: UnknownType, index: UnknownType) -> UnknownType`

Return the degree at the given index.

Args:
    index: The index of the degree to retrieve.

Returns:
    The Degree object at the specified index.

---

===

===
# File: `certifications.py`

## `Certification` class

Represents a professional certification.

Attributes:
    name (str): The name of the certification.
    issuer (str | None): The organization that issued the certification.
    issued (datetime | None): The date the certification was issued.
    expires (datetime | None): The date the certification expires.
    certification_id (str | None): An identifier for the certification.

---
## method: `Certification.validate_name(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the name field.

Args:
    v: The name value to validate. Must be a non-empty string.

Returns:
    str: The validated name.

Notes:
    1. Ensure name is a string.
    2. Ensure name is not empty.

---
## method: `Certification.validate_optional_strings(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate optional string fields.

Args:
    v: The field value to validate. Must be a string or None.

Returns:
    str: The validated field value.

Notes:
    1. Ensure field is a string or None.

---
## method: `Certification.validate_dates(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the date fields.

Args:
    v: The date value to validate. Must be a datetime object or None.

Returns:
    datetime: The validated date.

Notes:
    1. Ensure date is a datetime object or None.

---
## method: `Certification.validate_date_order(cls: UnknownType, v: UnknownType, info: UnknownType) -> UnknownType`

Validate that issued date is not after expires date.

Args:
    v: The expires date value to validate.
    info: Validation info containing data.

Returns:
    datetime: The validated expires date.

Notes:
    1. If both issued and expires dates are provided, ensure issued is not after expires.

---
## `Certifications` class

Represents a collection of professional certifications.

Attributes:
    certifications (list[Certification]): A list of Certification objects.

---
## method: `Certifications.validate_certifications(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the certifications field.

Args:
    v: The certifications value to validate. Must be a list of Certification objects.

Returns:
    list[Certification]: The validated certifications list.

Notes:
    1. Ensure certifications is a list.
    2. Ensure all items in certifications are instances of Certification.

---
## method: `Certifications.__iter__(self: UnknownType) -> UnknownType`

Iterate over the certifications.

Returns:
    An iterator over the list of certification objects.

Notes:
    1. Return an iterator over the certifications list.

---
## method: `Certifications.__len__(self: UnknownType) -> UnknownType`

Return the number of certifications.

Returns:
    The integer count of certifications in the list.

Notes:
    1. Return the length of the certifications list.

---
## method: `Certifications.__getitem__(self: UnknownType, index: UnknownType) -> UnknownType`

Return the certification at the given index.

Args:
    index: The index of the certification to retrieve.

Returns:
    The Certification object at the specified index.

Notes:
    1. Retrieve and return the certification at the given index.

---
## method: `Certifications.list_class(self: UnknownType) -> UnknownType`

Return the type that will be contained in the list.

Returns:
    The Certification class.

Notes:
    1. Return the Certification class.

---

===

===
# File: `personal.py`

## `ContactInfo` class

Holds personal contact details such as name, email, phone, and location.

Attributes:
    name (str): The full name of the person.
    email (str | None): The email address of the person, or None if not provided.
    phone (str | None): The phone number of the person, or None if not provided.
    location (str | None): The physical location (e.g., city and country) of the person, or None if not provided.

---
## method: `ContactInfo.validate_name(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the name field.

Args:
    v: The name value to validate. Must be a non-empty string.

Returns:
    str: The validated name (stripped of leading/trailing whitespace).

Notes:
    1. Ensure name is a string.
    2. Ensure name is not empty after stripping whitespace.

---
## method: `ContactInfo.validate_email(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the email field.

Args:
    v: The email value to validate. Must be a non-empty string or None.

Returns:
    str: The validated email (stripped of leading/trailing whitespace).

Notes:
    1. Ensure email is a string or None.
    2. Ensure email is not empty after stripping whitespace.

---
## method: `ContactInfo.validate_phone(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the phone field.

Args:
    v: The phone value to validate. Must be a non-empty string or None.

Returns:
    str: The validated phone (stripped of leading/trailing whitespace).

Notes:
    1. Ensure phone is a string or None.
    2. Ensure phone is not empty after stripping whitespace.

---
## method: `ContactInfo.validate_location(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the location field.

Args:
    v: The location value to validate. Must be a non-empty string or None.

Returns:
    str: The validated location (stripped of leading/trailing whitespace).

Notes:
    1. Ensure location is a string or None.
    2. Ensure location is not empty after stripping whitespace.

---
## `Websites` class

Holds personal website and social media links.

Attributes:
    website (str | None): The personal website URL, or None if not provided.
    github (str | None): The GitHub profile URL, or None if not provided.
    linkedin (str | None): The LinkedIn profile URL, or None if not provided.
    twitter (str | None): The Twitter profile URL, or None if not provided.

---
## method: `Websites.validate_website(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the website field.

Args:
    v: The website value to validate. Must be a non-empty string or None.

Returns:
    str: The validated website (stripped of leading/trailing whitespace).

Notes:
    1. Ensure website is a string or None.
    2. Ensure website is not empty after stripping whitespace.

---
## method: `Websites.validate_github(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the github field.

Args:
    v: The github value to validate. Must be a non-empty string or None.

Returns:
    str: The validated github (stripped of leading/trailing whitespace).

Notes:
    1. Ensure github is a string or None.
    2. Ensure github is not empty after stripping whitespace.

---
## method: `Websites.validate_linkedin(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the linkedin field.

Args:
    v: The linkedin value to validate. Must be a non-empty string or None.

Returns:
    str: The validated linkedin (stripped of leading/trailing whitespace).

Notes:
    1. Ensure linkedin is a string or None.
    2. Ensure linkedin is not empty after stripping whitespace.

---
## method: `Websites.validate_twitter(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the twitter field.

Args:
    v: The twitter value to validate. Must be a non-empty string or None.

Returns:
    str: The validated twitter (stripped of leading/trailing whitespace).

Notes:
    1. Ensure twitter is a string or None.
    2. Ensure twitter is not empty after stripping whitespace.

---
## `VisaStatus` class

Holds information about work authorization and sponsorship requirements.

Attributes:
    work_authorization (str | None): The current work authorization status (e.g., "US Citizen", "H-1B"), or None if not provided.
    require_sponsorship (bool | None): A boolean indicating if sponsorship is required, or None if not provided.

---
## method: `VisaStatus.validate_work_authorization(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the work_authorization field.

Args:
    v: The work_authorization value to validate. Must be a non-empty string or None.

Returns:
    str: The validated work_authorization (stripped of leading/trailing whitespace).

Notes:
    1. Ensure work_authorization is a string or None.
    2. Ensure work_authorization is not empty after stripping whitespace.

---
## method: `VisaStatus.validate_require_sponsorship(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the require_sponsorship field.

Args:
    v: The require_sponsorship value to validate. Must be a boolean, string ("yes"/"no"), or None.

Returns:
    bool: The validated require_sponsorship value.

Notes:
    1. Ensure require_sponsorship is a boolean, string ("yes"/"no"), or None.
    2. If require_sponsorship is a string, convert "yes" to True and "no" to False.
    3. If require_sponsorship is not None and not a string, assign it directly.
    4. Otherwise, set require_sponsorship to None.

---
## `Banner` class

Holds a personal banner message with cleaned text content.

Attributes:
    text (str): The cleaned text content of the banner, with leading/trailing and internal blank lines removed.

---
## method: `Banner.validate_text(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the text field and clean it.

Args:
    v: The raw text content of the banner, potentially including leading/trailing or internal blank lines.

Returns:
    str: The cleaned text content of the banner.

Notes:
    1. Ensure text is a string.
    2. Split the input text into lines.
    3. Remove leading blank lines.
    4. Remove trailing blank lines.
    5. Filter out any lines that are blank after stripping whitespace.
    6. Join the remaining lines back into a single string.

---
## `Note` class

Holds a personal note with cleaned text content.

Attributes:
    text (str): The cleaned text content of the note, with leading/trailing and internal blank lines removed.

---
## method: `Note.validate_text(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the text field and clean it.

Args:
    v: The raw text content of the note, potentially including leading/trailing or internal blank lines.

Returns:
    str: The cleaned text content of the note.

Notes:
    1. Ensure text is a string.
    2. Split the input text into lines.
    3. Remove leading blank lines.
    4. Remove trailing blank lines.
    5. Filter out any lines that are blank after stripping whitespace.
    6. Join the remaining lines back into a single string.

---

===

===
# File: `__init__.py`


===

===
# File: `experience.py`

## `RoleSummary` class

Represents a brief description of a professional role.

Attributes:
    summary (str): The text content of the role summary.

---
## method: `RoleSummary.validate_summary(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the summary field.

Args:
    v: The summary value to validate. Must be a string.

Returns:
    str: The validated summary.

Notes:
    1. Ensure summary is a string.
    2. Raise a ValueError if summary is not a string.

---
## `RoleResponsibilities` class

Represents detailed descriptions of role responsibilities.

Attributes:
    text (str): The text content of the responsibilities.

---
## method: `RoleResponsibilities.validate_text(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the text field.

Args:
    v: The text value to validate. Must be a string.

Returns:
    str: The validated text.

Notes:
    1. Ensure text is a string.
    2. Raise a ValueError if text is not a string.

---
## `RoleSkills` class

Represents skills used in a professional role.

Attributes:
    skills (List[str]): A list of non-empty, stripped skill strings.

---
## method: `RoleSkills.validate_skills(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the skills field.

Args:
    v: The skills value to validate. Must be a list of strings.

Returns:
    list[str]: The validated and cleaned skills list.

Notes:
    1. Ensure skills is a list.
    2. Ensure all items in skills are strings.
    3. Strip whitespace from each skill and filter out empty strings.
    4. Raise a ValueError if skills is not a list or if any skill is not a string.
    5. Return the cleaned list of non-empty skills.

---
## method: `RoleSkills.__iter__(self: UnknownType) -> UnknownType`

Iterate over the skills.

Returns:
    Iterator over the skills list.

---
## method: `RoleSkills.__len__(self: UnknownType) -> UnknownType`

Return the number of skills.

Returns:
    int: The number of skills.

---
## method: `RoleSkills.__getitem__(self: UnknownType, index: UnknownType) -> UnknownType`

Return the skill at the given index.

Args:
    index (int): The index of the skill to return.

Returns:
    str: The skill at the specified index.

---
## `RoleBasics` class

Represents basic information about a professional role.

Attributes:
    company (str): The name of the company.
    start_date (datetime): The start date of the role.
    end_date (datetime | None): The end date of the role or None if still ongoing.
    title (str): The job title.
    reason_for_change (str | None): The reason for leaving the role or None.
    location (str | None): The job location or None.
    job_category (str | None): The category of the job or None.
    employment_type (str | None): The employment type or None.
    agency_name (str | None): The name of the agency or None.

---
## method: `RoleBasics.validate_company(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the company field.

Args:
    v: The company value to validate. Must be a non-empty string.

Returns:
    str: The validated company.

Notes:
    1. Ensure company is a string.
    2. Ensure company is not empty.
    3. Strip whitespace from the company name.
    4. Raise a ValueError if company is not a string or is empty.

---
## method: `RoleBasics.validate_title(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the title field.

Args:
    v: The title value to validate. Must be a non-empty string.

Returns:
    str: The validated title.

Notes:
    1. Ensure title is a string.
    2. Ensure title is not empty.
    3. Strip whitespace from the title.
    4. Raise a ValueError if title is not a string or is empty.

---
## method: `RoleBasics.validate_start_date(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the start_date field.

Args:
    v: The start_date value to validate. Must be a datetime object.

Returns:
    datetime: The validated start_date.

Notes:
    1. Ensure start_date is a datetime object.
    2. Raise a ValueError if start_date is not a datetime object.

---
## method: `RoleBasics.validate_end_date(cls: UnknownType, v: UnknownType, info: UnknownType) -> UnknownType`

Validate the end_date field.

Args:
    v: The end_date value to validate. Must be a datetime object or None.
    info: Validation info containing data.

Returns:
    datetime: The validated end_date.

Notes:
    1. Ensure end_date is a datetime object or None.
    2. If end_date is provided, ensure it is not before start_date.
    3. Raise a ValueError if end_date is not a datetime object or None, or if end_date is before start_date.

---
## method: `RoleBasics.validate_optional_string_fields(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate optional string fields.

Args:
    v: The field value to validate. Must be a string or None.

Returns:
    str: The validated field value.

Notes:
    1. Ensure field is a string or None.
    2. Raise a ValueError if field is neither a string nor None.

---
## `Roles` class

Represents a collection of professional roles.

Attributes:
    roles (List[Role]): A list of Role objects.

---
## method: `Roles.validate_roles(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the roles field.

Args:
    v: The roles value to validate. Must be a list of Role objects.

Returns:
    list[Role]: The validated roles list.

Notes:
    1. Ensure roles is a list.
    2. Ensure all items in roles are Role objects.
    3. Raise a ValueError if roles is not a list or if any item is not a Role object.
    4. Return the validated list of roles.

---
## method: `Roles.__iter__(self: UnknownType) -> UnknownType`

Iterate over the roles.

Returns:
    Iterator over the roles list.

---
## method: `Roles.__len__(self: UnknownType) -> UnknownType`

Return the number of roles.

Returns:
    int: The number of roles.

---
## method: `Roles.__getitem__(self: UnknownType, index: UnknownType) -> UnknownType`

Return the role at the given index.

Args:
    index (int): The index of the role to return.

Returns:
    Role: The role at the specified index.

---
## method: `Roles.list_class(self: UnknownType) -> UnknownType`

Return the class for the list.

Returns:
    The Role class.

---
## `ProjectSkills` class

Represents skills used in a project.

Attributes:
    skills (List[str]): A list of non-empty, stripped skill strings.

---
## method: `ProjectSkills.validate_skills(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the skills field.

Args:
    v: The skills value to validate. Must be a list of strings.

Returns:
    list[str]: The validated and cleaned skills list.

Notes:
    1. Ensure skills is a list.
    2. Ensure all items in skills are strings.
    3. Strip whitespace from each skill and filter out empty strings.
    4. Raise a ValueError if skills is not a list or if any skill is not a string.
    5. Return the cleaned list of non-empty skills.

---
## method: `ProjectSkills.__iter__(self: UnknownType) -> UnknownType`

Iterate over the skills.

Returns:
    Iterator over the skills list.

---
## method: `ProjectSkills.__len__(self: UnknownType) -> UnknownType`

Return the number of skills.

Returns:
    int: The number of skills.

---
## method: `ProjectSkills.__getitem__(self: UnknownType, index: UnknownType) -> UnknownType`

Return the skill at the given index.

Args:
    index (int): The index of the skill to return.

Returns:
    str: The skill at the specified index.

---
## `ProjectOverview` class

Represents basic details of a project.

Attributes:
    title (str): The title of the project.
    url (str | None): The URL for the project or None.
    url_description (str | None): A description of the URL or None.
    start_date (datetime | None): The start date as a datetime object or None.
    end_date (datetime | None): The end date as a datetime object or None.

---
## method: `ProjectOverview.validate_title(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the title field.

Args:
    v: The title value to validate. Must be a non-empty string.

Returns:
    str: The validated title.

Notes:
    1. Ensure title is a string.
    2. Ensure title is not empty.
    3. Strip whitespace from the title.
    4. Raise a ValueError if title is not a string or is empty.

---
## method: `ProjectOverview.validate_optional_strings(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate optional string fields.

Args:
    v: The field value to validate. Must be a string or None.

Returns:
    str: The validated field value.

Notes:
    1. Ensure field is a string or None.
    2. Raise a ValueError if field is neither a string nor None.

---
## method: `ProjectOverview.validate_dates(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the date fields.

Args:
    v: The date value to validate. Must be a datetime object or None.

Returns:
    datetime: The validated date.

Notes:
    1. Ensure date is a datetime object or None.
    2. Raise a ValueError if date is not a datetime object or None.

---
## method: `ProjectOverview.validate_date_order(cls: UnknownType, v: UnknownType, info: UnknownType) -> UnknownType`

Validate that start_date is not after end_date.

Args:
    v: The end_date value to validate.
    info: Validation info containing data.

Returns:
    datetime: The validated end_date.

Notes:
    1. If both start_date and end_date are provided, ensure start_date is not after end_date.
    2. Raise a ValueError if end_date is before start_date.

---
## `ProjectDescription` class

Represents a brief description of a project.

Attributes:
    text (str): The text content of the project description.

---
## method: `ProjectDescription.validate_text(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the text field.

Args:
    v: The text value to validate. Must be a string.

Returns:
    str: The validated text.

Notes:
    1. Ensure text is a string.
    2. Raise a ValueError if text is not a string.

---
## `Projects` class

Represents a collection of projects.

Attributes:
    projects (List[Project]): A list of Project objects.

---
## method: `Projects.validate_projects(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the projects field.

Args:
    v: The projects value to validate. Must be a list of Project objects.

Returns:
    list[Project]: The validated projects list.

Notes:
    1. Ensure projects is a list.
    2. Ensure all items in projects are Project objects.
    3. Raise a ValueError if projects is not a list or if any item is not a Project object.
    4. Return the validated list of projects.

---
## method: `Projects.__iter__(self: UnknownType) -> UnknownType`

Iterate over the projects.

Returns:
    Iterator over the projects list.

---
## method: `Projects.__len__(self: UnknownType) -> UnknownType`

Return the number of projects.

Returns:
    int: The number of projects.

---
## method: `Projects.__getitem__(self: UnknownType, index: UnknownType) -> UnknownType`

Return the project at the given index.

Args:
    index (int): The index of the project to return.

Returns:
    Project: The project at the specified index.

---
## method: `Projects.list_class(self: UnknownType) -> UnknownType`

Return the class of the list.

Returns:
    The Project class.

---

===

===
# File: `user.py`


===

===
# File: `__init__.py`


===

