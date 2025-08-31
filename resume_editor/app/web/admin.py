import logging

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_logic.admin_crud import get_users_admin
from resume_editor.app.core.auth import (
    _verify_admin_privileges,
    get_optional_current_user_from_cookie,
)
from resume_editor.app.database.database import get_db
from resume_editor.app.models.user import User

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

    _verify_admin_privileges(user=current_user)

    users = get_users_admin(db=db)
    return templates.TemplateResponse(
        request,
        "admin/users.html",
        {"users": users, "current_user": current_user},
    )
