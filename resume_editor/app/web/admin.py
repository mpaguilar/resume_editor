import logging
from pathlib import Path

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

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/users", response_class=HTMLResponse)
async def admin_users_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user_from_cookie),
):
    """Serves the admin page for managing users.

    Args:
        request: The HTTP request object containing client request data.
        db: Database session dependency used to interact with the database.
        current_user: The authenticated user, if any, retrieved from the session cookie.

    Returns:
        TemplateResponse: The rendered admin users management page with user data.
        RedirectResponse: Redirects to the login page if the user is not authenticated.

    Raises:
        HTTPException: If the authenticated user does not have admin privileges.

    Notes:
        1. Logs a debug message indicating the admin users page was requested.
        2. Checks if the current user is authenticated. If not, redirects to the login page.
        3. Verifies that the authenticated user has admin privileges.
        4. Retrieves all users from the database using the get_users_admin function.
        5. Converts each user to an AdminUserResponse model for consistent response formatting.
        6. Renders the "admin/users.html" template with the list of users and current user context.
        7. Database access: Reads all users from the database via get_users_admin.
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
    """Handles the deletion of a user from the admin web interface.

    Args:
        request: The HTTP request object containing client request data.
        user_id: The unique identifier of the user to be deleted.
        db: Database session dependency used to interact with the database.
        current_user: The authenticated admin user, if any, retrieved from the session cookie.

    Returns:
        TemplateResponse: The rendered partial template for the updated user list.

    Raises:
        HTTPException: If the user is not found, or if the current user is not an admin.
        HTTPException: If the current user attempts to delete themselves.

    Notes:
        1. Logs a debug message indicating the delete request for the specified user.
        2. Checks if the current user is authenticated. If not, redirects to the login page.
        3. Verifies that the authenticated user has admin privileges.
        4. Retrieves the user to be deleted from the database using the user_id.
        5. Raises a 404 error if the user is not found.
        6. Prevents the admin from deleting themselves by raising a 400 error.
        7. Deletes the user from the database using the delete_user_admin function.
        8. Retrieves the updated list of users from the database.
        9. Converts each user to an AdminUserResponse model for consistent response formatting.
        10. Renders the "admin/partials/user_list.html" template with the updated user list and current user context.
        11. Database access: Reads and deletes a user from the database via get_user_by_id_admin and delete_user_admin.
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
            status_code=400,
            detail="Administrators cannot delete themselves.",
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
