import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.user import (
    create_new_user,
    delete_user as db_delete_user,
    get_user_by_id,
    get_users as db_get_users,
)
from resume_editor.app.core.auth import get_current_admin_user
from resume_editor.app.database.database import get_db
from resume_editor.app.models.user import User
from resume_editor.app.schemas.user import UserCreate, UserResponse

log = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin_user)],
)


@router.post(
    "/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED
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
