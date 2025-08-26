import logging

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from resume_editor.app.core.config import get_settings
from resume_editor.app.database.database import get_db
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(
        lambda: None,
    ),  # This will be replaced with proper OAuth2 scheme
) -> User:
    """Retrieve the authenticated user from the provided JWT token.

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

    """
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        if token is None:
            raise credentials_exception

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
