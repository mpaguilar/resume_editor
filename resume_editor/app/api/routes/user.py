import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_logic import settings_crud
from resume_editor.app.api.routes.route_logic import user as user_logic
from resume_editor.app.api.routes.route_models import ChangePasswordForm
from resume_editor.app.core.auth import get_current_user, get_current_user_from_cookie
from resume_editor.app.core.config import Settings, get_settings
from resume_editor.app.core.security import (
    authenticate_user,
    create_access_token,
    get_password_hash,
)
from resume_editor.app.database.database import get_db
from resume_editor.app.models.user import User, UserData
from resume_editor.app.schemas.user import (
    Token,
    UserCreate,
    UserResponse,
    UserSettingsResponse,
    UserSettingsUpdateRequest,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


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
        data=UserData(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
        ),
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

    Notes:
        1. Remove the user object from the database session.
        2. Commit the transaction to persist the deletion.
        3. Database access: Performs a write operation on the User table.

    """
    db.delete(user)
    db.commit()


@router.post("/register")
def register_user(
    user: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
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


@router.get("/settings")
def get_user_settings(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserSettingsResponse:
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


@router.put("/settings")
def update_user_settings(
    settings_data: UserSettingsUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserSettingsResponse:
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


@router.post("/change-password")
def change_password(
    request: Request,
    form_data: Annotated[ChangePasswordForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
) -> Response:
    """Change the current user's password.

    This endpoint handles both standard and forced password changes. It also handles
    requests from two different forms: the full-page form and the partial form
    on the settings page.

    It performs content negotiation based on the 'Accept' and 'HX-Target' headers.

    Args:
        request (Request): The request object.
        form_data (ChangePasswordForm): The form data with new and current passwords.
        db (Session): The database session.
        current_user (User): The authenticated user.

    Returns:
        Response: A response appropriate for a request type (JSON, HTML snippet,
                  full page render, or redirect).

    """
    _msg = "Changing password for current user"
    log.debug(_msg)

    is_json_request = "application/json" in request.headers.get("accept", "")
    is_partial_htmx = request.headers.get("hx-target") == "password-notification"

    error_detail = None
    status_code = status.HTTP_400_BAD_REQUEST
    if form_data.new_password != form_data.confirm_new_password:
        error_detail = "New passwords do not match."
    else:
        try:
            user_logic.change_password(
                db=db,
                user=current_user,
                new_password=form_data.new_password,
                current_password=form_data.current_password,
            )
        except HTTPException as e:
            error_detail = e.detail
            status_code = e.status_code

    if error_detail:
        log.warning(error_detail)
        if is_json_request:
            raise HTTPException(status_code=status_code, detail=error_detail)

        error_snippet = f'<div class="p-4 mb-4 text-sm text-red-800 rounded-lg bg-red-50" role="alert"><span class="font-medium">Error!</span> {error_detail}</div>'
        if is_partial_htmx:
            return HTMLResponse(content=error_snippet, status_code=status_code)
        else:
            is_forced_change = (
                current_user.attributes is not None
                and current_user.attributes.get("force_password_change", False)
            )
            context = {
                "user": current_user,
                "error": error_detail,
                "is_forced_change": is_forced_change,
            }
            return templates.TemplateResponse(
                request,
                "pages/change_password.html",
                context,
                status_code=status_code,
            )

    # Success
    _msg = "Password updated successfully"
    log.debug(_msg)

    if is_partial_htmx:
        return HTMLResponse(
            '<div class="p-4 mb-4 text-sm text-green-800 rounded-lg bg-green-50" role="alert"><span class="font-medium">Success!</span> Your password has been changed.</div>',
        )

    redirect_url = "/dashboard"
    if "hx-request" in request.headers:
        response = Response(status_code=status.HTTP_200_OK)
        response.headers["HX-Redirect"] = redirect_url
        return response
    else:
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.get(
    "/change-password",
    response_class=HTMLResponse,
    name="change_password_page",
    include_in_schema=False,
)
def get_change_password_page(
    request: Request,
    user: Annotated[User, Depends(get_current_user_from_cookie)],
) -> HTMLResponse:
    """Renders the page for changing a password.

    This page can be used for both forced and standard password changes. The
    template will conditionally render fields based on whether the user is
    being forced to change their password.

    Args:
        request (Request): The incoming HTTP request.
        user (User): The authenticated user, retrieved from the cookie.

    Returns:
        HTMLResponse: The rendered HTML page for changing the password.

    Notes:
        1. Render the change_password.html template with the current user context.
        2. The template checks for `user.attributes.force_password_change` to
           determine which version of the form to display.
        3. Return the HTML response to the client.

    """
    _msg = "Rendering change password page"
    log.debug(_msg)
    is_forced_change = user.attributes is not None and user.attributes.get(
        "force_password_change",
        False,
    )
    context = {
        "user": user,
        "is_forced_change": is_forced_change,
    }
    return templates.TemplateResponse(request, "pages/change_password.html", context)


@router.post("/login")
def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Token:
    """Authenticate a user and return an access token.

    Args:
        form_data: Form data containing username and password for authentication.
        db: Database session dependency used to verify user credentials.
        settings: Application settings used for token creation and configuration.

    Returns:
        Token: An access token for the authenticated user, formatted as a JWT.

    Raises:
        HTTPException: If the username or password is incorrect.

    Notes:
        1. Attempt to authenticate the user using the provided username and password.
        2. If authentication fails, raise a 401 error.
        3. Update the user's last_login_at timestamp to the current UTC time.
        4. Commit the change to the database.
        5. Generate a JWT access token with a defined expiration time.
        6. Return the access token to the client.
        7. Database access: Performs read and write operations on the User table.

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

    _msg = f"Updating last_login_at for user: {user.username}"
    log.debug(_msg)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    _msg = f"Creating access token for user: {form_data.username}"
    log.debug(_msg)
    access_token = create_access_token(data={"sub": user.username}, settings=settings)

    _msg = f"Returning access token for user: {form_data.username}"
    log.debug(_msg)
    return Token(access_token=access_token, token_type="bearer")
