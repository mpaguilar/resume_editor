import logging

from sqlalchemy.orm import Session

from resume_editor.app.core.security import get_password_hash
from resume_editor.app.models.role import Role
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


def get_role_by_name_admin(db: Session, name: str) -> Role | None:
    """
    Retrieve a role from the database by its name.

    This function is intended for administrative use to fetch a role before
    performing actions like assigning it to or removing it from a user.

    Args:
        db (Session): The SQLAlchemy database session.
        name (str): The unique name of the role to retrieve.

    Returns:
        Role | None: The `Role` object if found, otherwise `None`.

    Notes:
        1. Queries the database for a role with the given name.
        2. This function performs a database read operation.

    """
    _msg = "get_role_by_name_admin starting"
    log.debug(_msg)
    role = db.query(Role).filter(Role.name == name).first()
    _msg = "get_role_by_name_admin returning"
    log.debug(_msg)
    return role


def assign_role_to_user_admin(db: Session, user: User, role: Role) -> User:
    """
    Assign a role to a user if they do not already have it.

    This administrative function associates a `Role` with a `User`.
    It checks for the role's existence on the user before appending to prevent duplicates.
    Changes are committed to the database.

    Args:
        db (Session): The SQLAlchemy database session.
        user (User): The user object to which the role will be assigned.
        role (Role): The role object to assign.

    Returns:
        User: The updated user object, refreshed from the database if changes were made.

    Notes:
        1. Checks if the user already has the role.
        2. If not, adds the role to the user's roles and commits the change.
        3. This function performs a database write operation if the role is added.

    """
    _msg = "assign_role_to_user_admin starting"
    log.debug(_msg)
    if role not in user.roles:
        _msg = f"User '{user.username}' does not have role '{role.name}'. Assigning."
        log.info(_msg)
        user.roles.append(role)
        db.commit()
        db.refresh(user)
    else:
        _msg = (
            f"User '{user.username}' already has role '{role.name}'. No action taken."
        )
        log.info(_msg)
    _msg = "assign_role_to_user_admin returning"
    log.debug(_msg)
    return user


def remove_role_from_user_admin(db: Session, user: User, role: Role) -> User:
    """
    Remove a role from a user if they have it.

    This administrative function disassociates a `Role` from a `User`.
    It checks if the user has the role before attempting removal.
    Changes are committed to the database.

    Args:
        db (Session): The SQLAlchemy database session.
        user (User): The user object from which the role will be removed.
        role (Role): The role object to remove.

    Returns:
        User: The updated user object, refreshed from the database if changes were made.

    Notes:
        1. Checks if the user has the role.
        2. If so, removes the role from the user's roles and commits the change.
        3. This function performs a database write operation if the role is removed.

    """
    _msg = "remove_role_from_user_admin starting"
    log.debug(_msg)
    if role in user.roles:
        _msg = f"User '{user.username}' has role '{role.name}'. Removing."
        log.info(_msg)
        user.roles.remove(role)
        db.commit()
        db.refresh(user)
    else:
        _msg = (
            f"User '{user.username}' does not have role '{role.name}'. No action taken."
        )
        log.info(_msg)
    _msg = "remove_role_from_user_admin returning"
    log.debug(_msg)
    return user
