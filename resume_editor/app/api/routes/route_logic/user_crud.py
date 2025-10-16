import logging

from sqlalchemy.orm import Session

from resume_editor.app.models.user import User

log = logging.getLogger(__name__)


def user_count(db: Session) -> int:
    """Counts the total number of users in the database.

    Args:
        db (Session): The database session.

    Returns:
        int: The total number of users.

    Notes:
        1. Queries the User model to get a count of all records.
        2. Returns the count as an integer.
        3. This function performs a database read operation.

    """
    _msg = "user_count starting"
    log.debug(_msg)
    count = db.query(User).count()
    _msg = "user_count returning"
    log.debug(_msg)
    return count
