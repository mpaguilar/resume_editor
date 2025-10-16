import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from resume_editor.app.core.security import get_password_hash, verify_password
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)


def change_password(
    db: Session,
    user: User,
    new_password: str,
    current_password: str | None = None,
) -> None:
    """Change a user's password and unset the force_password_change flag.

    Args:
        db (Session): The database session used to persist changes to the user record.
        user (User): The user object whose password is being changed.
        new_password (str): The new password to set for the user.
        current_password (str | None): The user's current password, used for verification. Required for standard changes, optional for forced changes.

    Returns:
        None: This function does not return a value.

    Raises:
        HTTPException: For a standard password change, if the current password is not provided or is incorrect, a 400 Bad Request error is raised.

    Notes:
        1. Determine if it's a forced password change by checking the user's attributes.
        2. For a standard password change (when `force_password_change` is False), verify that `current_password` is provided and correct. If not, raise an HTTPException.
        3. For a forced password change, the current password check is bypassed.
        4. Hash the new password using get_password_hash.
        5. Update the user's hashed_password attribute with the new hash.
        6. Ensure the user's attributes are initialized as a dictionary if they are None.
        7. Set the 'force_password_change' key in attributes to False.
        8. Mark the attributes as modified to ensure SQLAlchemy tracks changes.
        9. Commit the transaction to persist changes to the database.
        10. Database access: The function performs a write operation to update the user's password and attributes in the database.

    """
    _msg = f"Changing password for user {user.username}"
    log.debug(_msg)

    is_forced_change = user.attributes is not None and user.attributes.get(
        "force_password_change",
    )

    # For a standard password change, the current password must be provided and correct.
    if not is_forced_change and (
        not current_password
        or not verify_password(current_password, user.hashed_password)
    ):
        _msg = "Incorrect current password for a standard password change."
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
