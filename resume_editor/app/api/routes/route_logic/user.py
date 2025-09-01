import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from resume_editor.app.core.security import get_password_hash, verify_password
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)


def change_password(db: Session, user: User, current_password: str, new_password: str):
    """Change a user's password and unset the force_password_change flag.

    Args:
        db (Session): The database session used to persist changes to the user record.
        user (User): The user object whose password is being changed.
        current_password (str): The user's current password, used for verification.
        new_password (str): The new password to set for the user.

    Returns:
        None: This function does not return a value.

    Raises:
        HTTPException: If the current password does not match the stored hash, a 400 Bad Request error is raised with the detail "Incorrect current password".

    Notes:
        1. Verify the current password against the stored hash using verify_password.
        2. If the current password is invalid, raise an HTTPException with status 400.
        3. Hash the new password using get_password_hash.
        4. Update the user's hashed_password attribute with the new hash.
        5. Ensure the user's attributes are initialized as a dictionary.
        6. Set the 'force_password_change' key in attributes to False.
        7. Mark the attributes as modified to ensure SQLAlchemy tracks changes.
        8. Commit the transaction to persist changes to the database.
    """
    _msg = f"Changing password for user {user.username}"
    log.debug(_msg)

    if not verify_password(current_password, user.hashed_password):
        _msg = "Incorrect current password"
        log.warning(_msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    user.hashed_password = get_password_hash(new_password)
    if not isinstance(user.attributes, dict):
        user.attributes = {}
    user.attributes["force_password_change"] = False
    flag_modified(user, "attributes")
    db.commit()

    _msg = "Password updated successfully"
    log.debug(_msg)
