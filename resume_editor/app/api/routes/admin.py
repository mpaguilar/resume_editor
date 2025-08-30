import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_logic import admin_crud
from resume_editor.app.core.auth import get_current_admin_user
from resume_editor.app.core.config import Settings, get_settings
from resume_editor.app.core.security import create_access_token
from resume_editor.app.database.database import get_db
from resume_editor.app.models.user import User
from resume_editor.app.schemas.user import AdminUserCreate, Token, UserResponse

log = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin_user)],
)


@router.post(
    "/users/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_user(user_data: AdminUserCreate, db: Session = Depends(get_db)):
    """
    Admin endpoint to create a new user.

    Args:
        user_data (AdminUserCreate): The data required to create a new user, including username, password, and optional email.
        db (Session): The database session used to interact with the database.

    Returns:
        UserResponse: The created user's data, including the user's ID, username, and any other public fields.

    Notes:
        1. Logs the admin's attempt to create a user.
        2. Reuses the existing logic from create_new_user to create the user.
        3. Commits the new user to the database.
        4. Logs the completion of user creation.
        5. Database access occurs during user creation and commit.

    """
    _msg = f"Admin creating user with username: {user_data.username}"
    log.debug(_msg)
    db_user = admin_crud.create_user_admin(db=db, user_data=user_data)
    _msg = "Admin finished creating user"
    log.debug(_msg)
    return db_user


@router.get("/users/", response_model=list[UserResponse])
def admin_get_users(db: Session = Depends(get_db)):
    """
    Admin endpoint to list all users.

    Args:
        db (Session): The database session used to interact with the database.

    Returns:
        list[UserResponse]: A list of all users' data, including their ID, username, and other public fields.

    Notes:
        1. Logs the admin's request to fetch all users.
        2. Retrieves all users from the database using db_get_users.
        3. Logs the completion of the fetch operation.
        4. Database access occurs during the retrieval of users.

    """
    _msg = "Admin fetching all users"
    log.debug(_msg)
    users = admin_crud.get_users_admin(db)
    _msg = "Admin finished fetching all users"
    log.debug(_msg)
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
def admin_get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Admin endpoint to get a single user by ID.

    Args:
        user_id (int): The unique identifier of the user to retrieve.
        db (Session): The database session used to interact with the database.

    Returns:
        UserResponse: The data of the requested user, including their ID, username, and other public fields.

    Raises:
        HTTPException: If the user with the given ID is not found, raises a 404 error.

    Notes:
        1. Logs the admin's request to fetch a user by ID.
        2. Retrieves the user from the database using get_user_by_id.
        3. If the user is not found, raises a 404 HTTPException.
        4. Logs the completion of the fetch operation.
        5. Database access occurs during the user retrieval.

    """
    _msg = f"Admin fetching user with id: {user_id}"
    log.debug(_msg)
    db_user = admin_crud.get_user_by_id_admin(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    _msg = f"Admin finished fetching user with id: {user_id}"
    log.debug(_msg)
    return db_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Admin endpoint to delete a user.

    Args:
        user_id (int): The unique identifier of the user to delete.
        db (Session): The database session used to interact with the database.

    Raises:
        HTTPException: If the user with the given ID is not found, raises a 404 error.

    Notes:
        1. Logs the admin's request to delete a user.
        2. Retrieves the user from the database using get_user_by_id.
        3. If the user is not found, raises a 404 HTTPException.
        4. Deletes the user from the database using db_delete_user.
        5. Commits the deletion to the database.
        6. Logs the completion of the deletion.
        7. Database access occurs during user retrieval, deletion, and commit.

    """
    _msg = f"Admin deleting user with id: {user_id}"
    log.debug(_msg)
    db_user = admin_crud.get_user_by_id_admin(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    admin_crud.delete_user_admin(db, user=db_user)
    _msg = f"Admin finished deleting user with id: {user_id}"
    log.debug(_msg)
    return None


@router.post(
    "/users/{user_id}/roles/{role_name}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def admin_assign_role_to_user(
    user_id: int,
    role_name: str,
    db: Session = Depends(get_db),
):
    """
    Admin endpoint to assign a role to a user.

    Args:
        user_id (int): The unique identifier of the user to assign the role to.
        role_name (str): The name of the role to assign.
        db (Session): The database session used to interact with the database.

    Returns:
        UserResponse: The updated user data, including the newly assigned role.

    Raises:
        HTTPException: If the user or role is not found (404 error), or if the user already has the role (400 error).

    Notes:
        1. Logs the admin's attempt to assign a role to a user.
        2. Retrieves the user from the database using get_user_by_id.
        3. If the user is not found, raises a 404 HTTPException.
        4. Retrieves the role from the database using get_role_by_name.
        5. If the role is not found, raises a 404 HTTPException.
        6. Checks if the user already has the role; if so, returns the user without modification.
        7. Appends the role to the user's roles list.
        8. Commits the change to the database.
        9. Refreshes the user object from the database.
        10. Logs the completion of the role assignment.
        11. Database access occurs during user and role retrieval, modification, and commit.

    """
    _msg = f"Admin assigning role '{role_name}' to user with id: {user_id}"
    log.debug(_msg)

    db_user = admin_crud.get_user_by_id_admin(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    role = admin_crud.get_role_by_name_admin(db, name=role_name)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")

    if role in db_user.roles:
        _msg = f"User {user_id} already has role {role_name}"
        log.debug(_msg)
        return db_user

    db_user = admin_crud.assign_role_to_user_admin(db=db, user=db_user, role=role)

    _msg = f"Admin finished assigning role '{role_name}' to user with id: {user_id}"
    log.debug(_msg)
    return db_user


@router.delete(
    "/users/{user_id}/roles/{role_name}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def admin_remove_role_from_user(
    user_id: int,
    role_name: str,
    db: Session = Depends(get_db),
):
    """
    Admin endpoint to remove a role from a user.

    Args:
        user_id (int): The unique identifier of the user to remove the role from.
        role_name (str): The name of the role to remove.
        db (Session): The database session used to interact with the database.

    Returns:
        UserResponse: The updated user data, excluding the removed role.

    Raises:
        HTTPException: If the user or role is not found (404 error), or if the user does not have the role (400 error).

    Notes:
        1. Logs the admin's attempt to remove a role from a user.
        2. Retrieves the user from the database using get_user_by_id.
        3. If the user is not found, raises a 404 HTTPException.
        4. Retrieves the role from the database using get_role_by_name.
        5. If the role is not found, raises a 404 HTTPException.
        6. Checks if the user has the role; if not, raises a 400 HTTPException.
        7. Removes the role from the user's roles list.
        8. Commits the change to the database.
        9. Refreshes the user object from the database.
        10. Logs the completion of the role removal.
        11. Database access occurs during user and role retrieval, modification, and commit.

    """
    _msg = f"Admin removing role '{role_name}' from user with id: {user_id}"
    log.debug(_msg)

    db_user = admin_crud.get_user_by_id_admin(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    role = admin_crud.get_role_by_name_admin(db, name=role_name)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")

    if role not in db_user.roles:
        raise HTTPException(status_code=400, detail="User does not have this role")

    db_user = admin_crud.remove_role_from_user_admin(db=db, user=db_user, role=role)

    _msg = f"Admin finished removing role '{role_name}' from user with id: {user_id}"
    log.debug(_msg)
    return db_user


@router.post("/impersonate/{username}", response_model=Token)
def admin_impersonate_user(
    username: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
    settings: Settings = Depends(get_settings),
):
    """
    Admin endpoint to impersonate a user.

    Args:
        username (str): The username of the user to impersonate.
        db (Session): The database session used to interact with the database.
        admin_user (User): The currently authenticated admin user.

    Returns:
        Token: A JWT access token for the impersonated user, with the admin's username as the impersonator.

    Raises:
        HTTPException: If the user to impersonate is not found, raises a 404 error.

    Notes:
        1. Logs the admin's attempt to impersonate a user.
        2. Retrieves the target user from the database by username.
        3. If the target user is not found, raises a 404 HTTPException.
        4. Creates a JWT access token with the admin's username as the impersonator.
        5. Logs the successful creation of the impersonation token.

    """
    _msg = f"Admin '{admin_user.username}' attempting to impersonate user: {username}"
    log.debug(_msg)

    target_user = admin_crud.get_user_by_username_admin(db=db, username=username)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    access_token = create_access_token(
        data={"sub": target_user.username},
        settings=settings,
        impersonator=admin_user.username,
    )

    _msg = f"Admin successfully created impersonation token for user with username: {username}"
    log.debug(_msg)
    return {"access_token": access_token, "token_type": "bearer"}
