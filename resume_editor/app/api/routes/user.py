import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_logic import settings_crud
from resume_editor.app.core.auth import get_current_user
from resume_editor.app.core.config import Settings, get_settings
from resume_editor.app.core.security import (
    authenticate_user,
    create_access_token,
    get_password_hash,
)
from resume_editor.app.database.database import get_db
from resume_editor.app.models.user import User
from resume_editor.app.schemas.user import (
    Token,
    UserCreate,
    UserResponse,
    UserSettingsResponse,
    UserSettingsUpdateRequest,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])


def get_user_by_username(db: Session, username: str) -> User | None:
    """Retrieve a user from the database using their username.

    Args:
        db: Database session dependency used to query the database.
        username: The unique username to search for in the database.

    Returns:
        User | None: The User object if found, otherwise None.

    Notes:
        1. Query the database for a user with the given username.
        2. Return the first match or None if no user is found.
        3. Database access: Performs a read operation on the User table.
    """
    _msg = f"Querying database for username: {username}"
    log.debug(_msg)
    result = db.query(User).filter(User.username == username).first()
    _msg = f"Query result for username {username}: {result}"
    log.debug(_msg)
    return result


def get_user_by_email(db: Session, email: str) -> User | None:
    """Retrieve a user from the database using their email address.

    Args:
        db: Database session dependency used to query the database.
        email: The unique email address to search for in the database.

    Returns:
        User | None: The User object if found, otherwise None.

    Notes:
        1. Query the database for a user with the given email.
        2. Return the first match or None if no user is found.
        3. Database access: Performs a read operation on the User table.
    """
    _msg = f"Querying database for email: {email}"
    log.debug(_msg)
    result = db.query(User).filter(User.email == email).first()
    _msg = f"Query result for email {email}: {result}"
    log.debug(_msg)
    return result


def create_new_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user in the database with the provided data.

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
    """
    _msg = f"Hashing password for user: {user_data.username}"
    log.debug(_msg)
    hashed_password = get_password_hash(user_data.password)

    _msg = f"Creating new user: {user_data.username}"
    log.debug(_msg)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
    )

    _msg = f"Adding user {user_data.username} to database"
    log.debug(_msg)
    db.add(db_user)

    _msg = f"Committing user {user_data.username} to database"
    log.debug(_msg)
    db.commit()

    _msg = f"Refreshing user {user_data.username} from database"
    log.debug(_msg)
    db.refresh(db_user)

    return db_user


def get_users(db: Session) -> list[User]:
    """Retrieve all users from the database.

    Args:
        db (Session): The database session.

    Returns:
        list[User]: A list of all user objects.

    """
    return db.query(User).all()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Retrieve a single user by ID.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user to retrieve.

    Returns:
        User | None: The user object if found, otherwise None.

    """
    return db.query(User).filter(User.id == user_id).first()


def delete_user(db: Session, user: User) -> None:
    """Delete a user from the database.

    Args:
        db (Session): The database session.
        user (User): The user object to delete.

    """
    db.delete(user)
    db.commit()


@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    """Register a new user with the provided credentials.

    Args:
        user: Data containing username, email, and password for the new user.
        db: Database session dependency used to interact with the user database.

    Returns:
        UserResponse: The created user's data, excluding the password.

    Raises:
        HTTPException: If the username or email is already registered.

    Notes:
        1. Check if the provided username already exists in the database.
        2. If the username exists, raise a 400 error.
        3. Check if the provided email already exists in the database.
        4. If the email exists, raise a 400 error.
        5. Create a new user with the provided data and store it in the database.
        6. Return the newly created user's data (without the password).
        7. Database access: Performs read and write operations on the User table.
    """
    _msg = f"Starting register_user for username: {user.username}"
    log.debug(_msg)

    # Check if user already exists
    _msg = f"Checking if username {user.username} already exists"
    log.debug(_msg)
    db_user = get_user_by_username(db, user.username)
    if db_user:
        _msg = f"Username {user.username} already registered"
        log.debug(_msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    _msg = f"Checking if email {user.email} already exists"
    log.debug(_msg)
    db_user = get_user_by_email(db, user.email)
    if db_user:
        _msg = f"Email {user.email} already registered"
        log.debug(_msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    _msg = f"Creating new user: {user.username}"
    log.debug(_msg)
    db_user = create_new_user(db, user)

    _msg = f"Returning registered user: {user.username}"
    log.debug(_msg)
    return db_user


@router.get("/settings", response_model=UserSettingsResponse)
def get_user_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current user's settings.

    Args:
        db (Session): The database session.
        current_user (User): The authenticated user.

    Returns:
        UserSettingsResponse: The user's settings.

    Notes:
        1. Retrieve the user's settings from the database.
        2. If no settings exist, return an empty response.
        3. Database access: Performs a read operation on the UserSettings table.
    """
    _msg = "Getting settings for current user"
    log.debug(_msg)
    settings = settings_crud.get_user_settings(db, current_user.id)
    if not settings:
        return UserSettingsResponse()

    return UserSettingsResponse(
        llm_endpoint=settings.llm_endpoint,
        api_key_is_set=bool(settings.encrypted_api_key),
    )


@router.put("/settings", response_model=UserSettingsResponse)
def update_user_settings(
    settings_data: UserSettingsUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the current user's settings.

    Args:
        settings_data (UserSettingsUpdateRequest): The settings data to update.
        db (Session): The database session.
        current_user (User): The authenticated user.

    Returns:
        UserSettingsResponse: The updated user's settings.

    Notes:
        1. Update the user's settings in the database with the provided data.
        2. Return the updated settings.
        3. Database access: Performs a write operation on the UserSettings table.
    """
    _msg = "Updating settings for current user"
    log.debug(_msg)
    settings = settings_crud.update_user_settings(db, current_user.id, settings_data)
    return UserSettingsResponse(
        llm_endpoint=settings.llm_endpoint,
        api_key_is_set=bool(settings.encrypted_api_key),
    )


@router.post("/login", response_model=Token)
def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Token:
    """Authenticate a user and return an access token.

    Args:
        form_data: Form data containing username and password for authentication.
        db: Database session dependency used to verify user credentials.

    Returns:
        Token: An access token for the authenticated user, formatted as a JWT.

    Raises:
        HTTPException: If the username or password is incorrect.

    Notes:
        1. Attempt to authenticate the user using the provided username and password.
        2. If authentication fails, raise a 401 error.
        3. Generate a JWT access token with a defined expiration time.
        4. Return the access token to the client.
        5. Database access: Performs a read operation on the User table to verify credentials.
    """
    _msg = f"Starting login_user for username: {form_data.username}"
    log.debug(_msg)

    _msg = f"Authenticating user: {form_data.username}"
    log.debug(_msg)
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        _msg = f"Authentication failed for user: {form_data.username}"
        log.debug(_msg)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _msg = f"Creating access token for user: {form_data.username}"
    log.debug(_msg)
    access_token = create_access_token(data={"sub": user.username}, settings=settings)

    _msg = f"Returning access token for user: {form_data.username}"
    log.debug(_msg)
    return Token(access_token=access_token, token_type="bearer")
