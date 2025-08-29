import logging

from sqlalchemy.orm import Session

from resume_editor.app.core.security import get_password_hash
from resume_editor.app.models.user import User
from resume_editor.app.schemas.user import AdminUserCreate

log = logging.getLogger(__name__)


def create_user_admin(db: Session, user_data: AdminUserCreate) -> User:
    """
    Create a new user as an administrator.

    Args:
        db (Session): The database session.
        user_data (AdminUserCreate): The user data.

    Returns:
        User: The created user.

    Notes:
        1. Hashes the user's password.
        2. Creates a new User instance.
        3. Adds the user to the database, commits, and refreshes.
        4. This function performs a database write operation.

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
        is_active=user_data.is_active,
        attributes=user_data.attributes,
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


def get_user_by_id_admin(db: Session, user_id: int) -> User | None:
    """
    Retrieve a single user by ID as an administrator.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user to retrieve.

    Returns:
        User | None: The user object if found, otherwise None.

    Notes:
        1. Queries the database for a user with the given ID.
        2. This function performs a database read operation.

    """
    return db.query(User).filter(User.id == user_id).first()


def get_users_admin(db: Session) -> list[User]:
    """
    Retrieve all users as an administrator.

    Args:
        db (Session): The database session.

    Returns:
        list[User]: A list of all user objects.

    Notes:
        1. Queries the database for all users.
        2. This function performs a database read operation.

    """
    return db.query(User).all()


def delete_user_admin(db: Session, user: User) -> None:
    """
    Delete a user as an administrator.

    Args:
        db (Session): The database session.
        user (User): The user object to delete.

    Returns:
        None

    Notes:
        1. Deletes the given user from the database and commits the change.
        2. This function performs a database write operation.

    """
    db.delete(user)
    db.commit()
