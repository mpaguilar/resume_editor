import logging

from sqlalchemy.orm import Session, selectinload
from sqlalchemy.orm.attributes import flag_modified

from resume_editor.app.core.security import get_password_hash
from resume_editor.app.models.role import Role
from resume_editor.app.models.user import User
from resume_editor.app.schemas.user import AdminUserCreate, AdminUserUpdateRequest

log = logging.getLogger(__name__)


def create_user_admin(db: Session, user_data: AdminUserCreate) -> User:
    """
    Create a new user as an administrator.

    Args:
        db (Session): The database session used to interact with the database.
        user_data (AdminUserCreate): The data required to create a new user, including username, email, password, and other attributes.

    Returns:
        User: The newly created user object with all fields populated, including the generated ID.

    Notes:
        1. Hashes the provided password using the `get_password_hash` utility.
        2. Creates a new `User` instance with the provided data and the hashed password.
        3. Adds the new user to the database session.
        4. Commits the transaction to persist the user to the database.
        5. Re-fetches the user to ensure relationships are eagerly loaded, preventing N+1 query issues.
        6. This function performs a database write operation.

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

    _msg = (
        f"User {user_data.username} committed to database, "
        f"re-fetching with loaded resumes."
    )
    log.debug(_msg)
    created_user = get_user_by_id_admin(db=db, user_id=db_user.id)
    assert created_user is not None, "Failed to re-fetch created user"

    return created_user


def get_user_by_id_admin(db: Session, user_id: int) -> User | None:
    """
    Retrieve a single user by their unique ID as an administrator.

    Args:
        db (Session): The database session used to query the database.
        user_id (int): The unique identifier of the user to retrieve.

    Returns:
        User | None: The user object if found, otherwise None.

    Notes:
        1. Queries the database for a user with the specified ID, eagerly loading their resumes.
        2. This function performs a database read operation.

    """
    _msg = "get_user_by_id_admin starting"
    log.debug(_msg)
    user = (
        db.query(User)
        .options(selectinload(User.resumes))
        .filter(User.id == user_id)
        .first()
    )
    _msg = "get_user_by_id_admin returning"
    log.debug(_msg)
    return user


def get_users_admin(db: Session) -> list[User]:
    """
    Retrieve all users from the database as an administrator.

    Args:
        db (Session): The database session used to query the database.

    Returns:
        list[User]: A list of all user objects in the database.

    Notes:
        1. Queries the database for all users, eagerly loading their resumes to prevent N+1 issues.
        2. This function performs a database read operation.

    """
    _msg = "get_users_admin starting"
    log.debug(_msg)
    users = db.query(User).options(selectinload(User.resumes)).all()
    _msg = "get_users_admin returning"
    log.debug(_msg)
    return users


def get_user_by_username_admin(db: Session, username: str) -> User | None:
    """
    Retrieve a single user by their username as an administrator.

    Args:
        db (Session): The database session used to query the database.
        username (str): The unique username of the user to retrieve.

    Returns:
        User | None: The user object if found, otherwise None.

    Notes:
        1. Queries the database for a user with the specified username.
        2. This function performs a database read operation.

    """
    _msg = "get_user_by_username_admin starting"
    log.debug(_msg)
    user = db.query(User).filter(User.username == username).first()
    _msg = "get_user_by_username_admin returning"
    log.debug(_msg)
    return user


def delete_user_admin(db: Session, user: User) -> None:
    """
    Delete a user from the database as an administrator.

    Args:
        db (Session): The database session used to interact with the database.
        user (User): The user object to be deleted.

    Returns:
        None

    Notes:
        1. Removes the specified user from the database session.
        2. Commits the transaction to permanently delete the user from the database.
        3. This function performs a database write operation.

    """
    _msg = "delete_user_admin starting"
    log.debug(_msg)
    db.delete(user)
    db.commit()
    _msg = "delete_user_admin returning"
    log.debug(_msg)


def get_role_by_name_admin(db: Session, name: str) -> Role | None:
    """
    Retrieve a role from the database by its unique name.

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
        User: The updated user object, re-fetched from the database with eager-loaded relationships.

    Notes:
        1. Checks if the user already has the role.
        2. If not, adds the role, commits, and re-fetches the user to prevent N+1 issues.
        3. This function performs a database write operation if the role is added.

    """
    _msg = "assign_role_to_user_admin starting"
    log.debug(_msg)
    if role not in user.roles:
        _msg = f"User '{user.username}' does not have role '{role.name}'. Assigning."
        log.info(_msg)
        user_id = user.id
        user.roles.append(role)
        db.commit()
        refetched_user = get_user_by_id_admin(db=db, user_id=user_id)
        assert refetched_user is not None, "User should exist after commit"
        user = refetched_user
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
        User: The updated user object, re-fetched from the database with eager-loaded relationships.

    Notes:
        1. Checks if the user has the role.
        2. If so, removes the role, commits, and re-fetches the user to prevent N+1 issues.
        3. This function performs a database write operation if the role is removed.

    """
    _msg = "remove_role_from_user_admin starting"
    log.debug(_msg)
    if role in user.roles:
        _msg = f"User '{user.username}' has role '{role.name}'. Removing."
        log.info(_msg)
        user_id = user.id
        user.roles.remove(role)
        db.commit()
        refetched_user = get_user_by_id_admin(db=db, user_id=user_id)
        assert refetched_user is not None, "User should exist after commit"
        user = refetched_user
    else:
        _msg = (
            f"User '{user.username}' does not have role '{role.name}'. No action taken."
        )
        log.info(_msg)
    _msg = "remove_role_from_user_admin returning"
    log.debug(_msg)
    return user


def update_user_admin(
    db: Session,
    user: User,
    update_data: AdminUserUpdateRequest,
) -> User:
    """
    Update a user's attributes as an administrator.

    Args:
        db (Session): The database session.
        user (User): The user object to update.
        update_data (AdminUserUpdateRequest): The data containing the updates.

    Returns:
        User: The updated user object.

    Notes:
        1. Updates the user's attributes dictionary with the force_password_change flag.
        2. Commits the changes to the database.
        3. Re-fetches the user to ensure relationships are eagerly loaded, preventing N+1 issues.
        4. This function performs a database write operation.

    """
    _msg = "update_user_admin starting"
    log.debug(_msg)
    user_id = user.id

    if update_data.email is not None:
        user.email = update_data.email

    if update_data.force_password_change is not None:
        if user.attributes is None:
            user.attributes = {}

        user.attributes["force_password_change"] = update_data.force_password_change
        flag_modified(user, "attributes")

    db.commit()
    refetched_user = get_user_by_id_admin(db=db, user_id=user_id)
    assert refetched_user is not None, "User should exist after commit"

    _msg = "update_user_admin returning"
    log.debug(_msg)
    return refetched_user
