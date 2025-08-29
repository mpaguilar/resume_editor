import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_logic.admin_crud import (
    impersonate_user_admin,
)
from resume_editor.app.api.routes.user import (
    create_new_user,
    get_user_by_id,
)
from resume_editor.app.api.routes.user import (
    delete_user as db_delete_user,
)
from resume_editor.app.api.routes.user import (
    get_users as db_get_users,
)
from resume_editor.app.core.auth import get_current_admin_user
from resume_editor.app.database.database import get_db
from resume_editor.app.models.role import Role
from resume_editor.app.schemas.user import Token, UserCreate, UserResponse

log = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin_user)],
)


def get_role_by_name(db: Session, name: str) -> Role | None:
    """
    Retrieve a role from the database by its name.

    Args:
        db (Session): The database session.
        name (str): The name of the role to retrieve.

    Returns:
        Role | None: The role object if found, otherwise None.

    """
    return db.query(Role).filter(Role.name == name).first()


@router.post(
    "/users/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Admin endpoint to create a new user."""
    _msg = f"Admin creating user with username: {user_data.username}"
    log.debug(_msg)
    # This reuses the existing logic for creating a user
    db_user = create_new_user(db=db, user_data=user_data)
    _msg = "Admin finished creating user"
    log.debug(_msg)
    return db_user


@router.get("/users/", response_model=list[UserResponse])
def admin_get_users(db: Session = Depends(get_db)):
    """Admin endpoint to list all users."""
    _msg = "Admin fetching all users"
    log.debug(_msg)
    users = db_get_users(db)
    _msg = "Admin finished fetching all users"
    log.debug(_msg)
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
def admin_get_user(user_id: int, db: Session = Depends(get_db)):
    """Admin endpoint to get a single user by ID."""
    _msg = f"Admin fetching user with id: {user_id}"
    log.debug(_msg)
    db_user = get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    _msg = f"Admin finished fetching user with id: {user_id}"
    log.debug(_msg)
    return db_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_user(user_id: int, db: Session = Depends(get_db)):
    """Admin endpoint to delete a user."""
    _msg = f"Admin deleting user with id: {user_id}"
    log.debug(_msg)
    db_user = get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_delete_user(db, user=db_user)
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
    """Admin endpoint to assign a role to a user."""
    _msg = f"Admin assigning role '{role_name}' to user with id: {user_id}"
    log.debug(_msg)

    db_user = get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    role = get_role_by_name(db, name=role_name)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")

    if role in db_user.roles:
        _msg = f"User {user_id} already has role {role_name}"
        log.debug(_msg)
        return db_user

    db_user.roles.append(role)
    db.commit()
    db.refresh(db_user)

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
    """Admin endpoint to remove a role from a user."""
    _msg = f"Admin removing role '{role_name}' from user with id: {user_id}"
    log.debug(_msg)

    db_user = get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    role = get_role_by_name(db, name=role_name)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")

    if role not in db_user.roles:
        raise HTTPException(status_code=400, detail="User does not have this role")

    db_user.roles.remove(role)
    db.commit()
    db.refresh(db_user)

    _msg = f"Admin finished removing role '{role_name}' from user with id: {user_id}"
    log.debug(_msg)
    return db_user


@router.post("/users/{user_id}/impersonate", response_model=Token)
def admin_impersonate_user(user_id: int, db: Session = Depends(get_db)):
    """Admin endpoint to impersonate a user."""
    _msg = f"Admin attempting to impersonate user with id: {user_id}"
    log.debug(_msg)

    access_token = impersonate_user_admin(db=db, user_id=user_id)

    if not access_token:
        raise HTTPException(status_code=404, detail="User not found")

    _msg = f"Admin successfully created impersonation token for user with id: {user_id}"
    log.debug(_msg)
    return {"access_token": access_token, "token_type": "bearer"}
