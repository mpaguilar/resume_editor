import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_logic.admin_crud import (
    delete_user_admin,
    get_user_by_id_admin,
    get_users_admin,
)
from resume_editor.app.core.auth import (
    get_optional_current_user_from_cookie,
    verify_admin_privileges,
)
from resume_editor.app.database.database import get_db
from resume_editor.app.models.user import User
from resume_editor.app.schemas.user import AdminUserResponse

log = logging.getLogger(__name__)

# This router will be for web pages, not API
router = APIRouter(
    prefix="/admin",
    tags=["admin_web"],
)

templates = Jinja2Templates(directory="templates")


@router.get("/users", response_class=HTMLResponse)
async def admin_users_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user_from_cookie),
):
    """
    Serves the admin page for managing users.

    Args:
        request: The HTTP request object.
        db: Database session dependency.
        current_user: The authenticated admin user, if one exists.

    Returns:
        TemplateResponse: The rendered admin users management page.
        RedirectResponse: Redirects to login if user is not authenticated.

    Raises:
        HTTPException: If the user is not an admin.

    """
    _msg = "Admin users page requested"
    log.debug(_msg)

    if not current_user:
        return RedirectResponse(
            url="/login",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    verify_admin_privileges(user=current_user)

    db_users = get_users_admin(db=db)
    users = [AdminUserResponse.model_validate(user) for user in db_users]
    return templates.TemplateResponse(
        request,
        "admin/users.html",
        {"users": users, "current_user": current_user},
    )


@router.delete("/users/{user_id}", response_class=HTMLResponse)
async def admin_delete_user_web(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user_from_cookie),
):
    """
    Handles the deletion of a user from the admin web interface.

    Args:
        request: The HTTP request object.
        user_id: The ID of the user to delete.
        db: Database session dependency.
        current_user: The authenticated admin user.

    Returns:
        TemplateResponse: The rendered partial for the updated user list.

    Raises:
        HTTPException: If user is not found, or if the current user is not an admin.
    """
    _msg = f"Admin delete user web requested for user_id: {user_id}"
    log.debug(_msg)

    if not current_user:
        return RedirectResponse(
            url="/login",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    verify_admin_privileges(user=current_user)

    user_to_delete = get_user_by_id_admin(db=db, user_id=user_id)
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from deleting themselves
    if user_to_delete.id == current_user.id:
        raise HTTPException(
            status_code=400, detail="Administrators cannot delete themselves."
        )

    delete_user_admin(db=db, user=user_to_delete)

    # Return the updated list
    db_users = get_users_admin(db=db)
    users = [AdminUserResponse.model_validate(user) for user in db_users]

    return templates.TemplateResponse(
        request=request,
        name="admin/partials/user_list.html",
        context={"users": users, "current_user": current_user},
    )
