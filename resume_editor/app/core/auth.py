import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from resume_editor.app.core.config import get_settings
from resume_editor.app.core.security import oauth2_scheme
from resume_editor.app.database.database import get_db
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    """Retrieve the authenticated user from the provided JWT token.

    Args:
        token: JWT token extracted from the request header, used to authenticate the user.
            Type: str
            Purpose: The JWT token that contains the user's identity and is used for authentication.
        db: Database session dependency used to query the database for the user.
            Type: Session
            Purpose: Provides a connection to the database to retrieve the user record by username.

    Returns:
        User: The authenticated User object corresponding to the token's subject (username).
            Type: User
            Purpose: Returns the user object if authentication is successful.

    Raises:
        HTTPException: Raised when the credentials are invalid or the user is not found.
            Status Code: 401 UNAUTHORIZED
            Detail: "Could not validate credentials"
            Headers: {"WWW-Authenticate": "Bearer"}

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

    """
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_user_from_cookie(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Retrieve the authenticated user from the JWT token in the request cookie.

    For browser-based requests that fail authentication, this function will
    raise an HTTPException that results in a redirect to the login page.
    For API requests, it will raise a 401 HTTPException.

    Args:
        request: The request object, used to access cookies and headers.
        db: Database session dependency.

    Returns:
        User: The authenticated User object if the token is valid.

    Raises:
        HTTPException: Raised for API requests when the token is missing, invalid, or the user is not found.
            Also raised to redirect users to the login page or to the change password page.

    Notes:
        1.  Determine if the request is from a browser by checking the 'Accept' header.
        2.  Attempt to get the 'access_token' from cookies. On failure, redirect
            browser requests to '/login' or raise 401 for API requests.
        3.  Decode the JWT. On failure, redirect or raise 401.
        4.  Verify the username from the JWT payload. On failure, redirect or raise 401.
        5.  Retrieve the user from the database. On failure, redirect or raise 401.
        6.  If the user is successfully authenticated, check for a forced password change.
            If required, redirect the user to the change password page.
        7.  Return the authenticated User object if all checks pass.

    Database Access:
        - Queries the User table to retrieve a user record by username.

    """
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={},
    )

    # Check if request prefers HTML over JSON. If the client does not explicitly ask for
    # JSON, we assume it's a browser and can handle a redirect.
    accept_header = request.headers.get("Accept", "")
    prefers_html = "application/json" not in accept_header

    def handle_auth_failure():
        if prefers_html:
            login_url = request.url_for("login_page")
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": str(login_url)},
                detail="Not authenticated, redirecting to login.",
            )
        raise credentials_exception

    token = request.cookies.get("access_token")
    if not token:
        handle_auth_failure()

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        username: str = payload.get("sub")
        if username is None:
            handle_auth_failure()
    except JWTError:
        handle_auth_failure()

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        handle_auth_failure()

    if user.attributes and user.attributes.get("force_password_change"):
        path = request.url.path
        # Allow access to the change password page, logout, and static assets
        allowed_paths = [
            "/api/users/change-password",
            "/logout",
        ]
        if not any(path.startswith(p) for p in allowed_paths) and not path.startswith(
            "/static",
        ):
            redirect_url = request.url_for("change_password_page")
            # For HTMX requests, we can't send a normal redirect.
            # Instead, we send a special header to trigger a client-side redirect.
            # For regular requests, we send a 307 Temporary Redirect.
            if "hx-request" in request.headers:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    headers={"HX-Redirect": str(redirect_url)},
                    detail="Password change required",
                )
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": str(redirect_url)},
                detail="Password change required",
            )

    return user


def get_optional_current_user_from_cookie(
    request: Request,
    db: Session = Depends(get_db),
) -> User | None:
    """Retrieve an optional authenticated user from the JWT token in the request cookie.

    Args:
        request: The request object, used to access cookies.
            Type: Request
            Purpose: Provides access to the HTTP request, including cookies.
        db: Database session dependency.
            Type: Session
            Purpose: Provides a connection to the database to retrieve the user record.

    Returns:
        User | None: The authenticated User object if the token is valid, otherwise None.
            Type: User | None
            Purpose: Returns the user object if authentication succeeds, or None if no valid token is present.

    Notes:
        1. Attempt to retrieve the authenticated user using `get_current_user_from_cookie`.
        2. If `get_current_user_from_cookie` raises an HTTPException for a forced password change,
           this function propagates that exception.
        3. For any other HTTPException (e.g., login redirect for browsers, 401 for APIs),
           this function returns `None` as the user is not authenticated.
        4. If authentication is successful, the User object is returned.

    Database Access:
        - Queries the User table to retrieve a user record by username.

    """
    try:
        return get_current_user_from_cookie(request=request, db=db)
    except HTTPException as e:
        # A redirect for a forced password change is not an authentication failure,
        # so it should be propagated. This is identified by the detail message.
        if e.detail == "Password change required":
            raise e

        # For any other HTTPException (like missing token or invalid token,
        # which results in a 307 redirect to login for browsers or a 401 for API),
        # we return None as this dependency is for an *optional* user.
        return None


def verify_admin_privileges(user: User) -> User:
    """Verify that a user has admin privileges.

    Args:
        user (User): The user object to check for admin privileges.
            Type: User
            Purpose: The user whose roles are checked to determine if they are an admin.

    Returns:
        User: The user object if they have admin privileges.
            Type: User
            Purpose: Returns the user object if the check passes.

    Raises:
        HTTPException: Raised if the user does not have admin privileges.
            Status Code: 403 FORBIDDEN
            Detail: "The user does not have admin privileges"

    Notes:
        1. Iterate through the user's roles.
        2. Check if any role has the name 'admin'.
        3. If no role with the name 'admin' is found, log a warning and raise an HTTPException with status 403.
        4. Return the user object if an 'admin' role is found.

    """
    if not any(role.name == "admin" for role in user.roles):
        _msg = f"User {user.username} does not have admin privileges"
        log.warning(_msg)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have admin privileges",
        )
    return user


def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Verify that the current user has administrator privileges.

    This dependency relies on `get_current_user` to retrieve the authenticated user.
    It then checks the user's roles to determine if they are an administrator.

    Args:
        current_user (User): The user object obtained from the `get_current_user`
            dependency.
            Type: User
            Purpose: The authenticated user whose roles are checked for admin privileges.

    Returns:
        User: The user object if the user has the 'admin' role.
            Type: User
            Purpose: Returns the user object if the user is an admin.

    Raises:
        HTTPException: A 403 Forbidden error if the user is not an admin.
            Status Code: 403 FORBIDDEN
            Detail: "The user does not have admin privileges"

    Notes:
        1. Log a debug message indicating the function has started.
        2. Call `verify_admin_privileges` to check if the user has admin roles.
        3. Log a debug message indicating the function is returning.
        4. Return the user object if the user has admin privileges.

    """
    _msg = "get_current_admin_user starting"
    log.debug(_msg)

    verify_admin_privileges(user=current_user)

    _msg = "get_current_admin_user returning"
    log.debug(_msg)
    return current_user


def get_current_admin_user_from_cookie(
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
) -> User:
    """Verify that the current user (from cookie) has admin privileges.

    This dependency relies on `get_current_user_from_cookie` to retrieve the authenticated user.
    It then checks the user's roles to determine if they are an administrator.

    Args:
        current_user (User): The user object obtained from the `get_current_user_from_cookie`
            dependency.
            Type: User
            Purpose: The authenticated user whose roles are checked for admin privileges.

    Returns:
        User: The user object if the user has the 'admin' role.
            Type: User
            Purpose: Returns the user object if the user is an admin.

    Raises:
        HTTPException: A 403 Forbidden error if the user is not an admin.
            Status Code: 403 FORBIDDEN
            Detail: "The user does not have admin privileges"

    Notes:
        1. Log a debug message indicating the function has started.
        2. Call `verify_admin_privileges` to check if the user has admin roles.
        3. Log a debug message indicating the function is returning.
        4. Return the user object if the user has admin privileges.

    """
    _msg = "get_current_admin_user_from_cookie starting"
    log.debug(_msg)

    verify_admin_privileges(user=current_user)

    _msg = "get_current_admin_user_from_cookie returning"
    log.debug(_msg)
    return current_user
