import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_logic.admin_crud import create_initial_admin
from resume_editor.app.api.routes.route_logic.user_crud import user_count
from resume_editor.app.database.database import get_db

log = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="resume_editor/app/templates")


@router.get("/setup", response_class=HTMLResponse)
async def get_setup_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Renders the initial setup page for creating the first admin user.

    If users already exist in the database, it redirects to the login page.

    Args:
        request (Request): The incoming HTTP request.
        db (Session): The database session.

    Returns:
        HTMLResponse: The rendered setup page.
        RedirectResponse: A redirect to the login page if setup is not needed.

    """
    _msg = "GET /setup starting"
    log.debug(_msg)

    if user_count(db) > 0:
        _msg = "Users already exist, redirecting to login."
        log.info(_msg)
        return RedirectResponse(url="/login")

    _msg = "get_setup_page returning"
    log.debug(_msg)
    return templates.TemplateResponse(request, "pages/setup.html", {})


@router.post("/setup")
async def handle_setup_form(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    confirm_password: Annotated[str, Form()],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Handles the submission of the initial admin user creation form.

    Validates form data, creates the admin user if no other users exist,
    and redirects to the login page on success.

    Args:
        request (Request): The incoming HTTP request.
        username (str): The username from the form.
        password (str): The password from the form.
        confirm_password (str): The password confirmation from the form.
        db (Session): The database session.

    Returns:
        RedirectResponse: Redirects to the login page on success or if setup is not needed.
        HTMLResponse: Re-renders the setup page with an error message on failure.

    """
    _msg = "POST /setup starting"
    log.debug(_msg)

    if user_count(db) > 0:
        _msg = "Users already exist, redirecting to login."
        log.info(_msg)
        return RedirectResponse(url="/login")

    if password != confirm_password:
        _msg = "Passwords do not match."
        log.warning(_msg)
        return templates.TemplateResponse(
            request,
            "pages/setup.html",
            {"error_message": "Passwords do not match."},
            status_code=400,
        )

    _msg = "Creating initial admin user."
    log.info(_msg)
    create_initial_admin(db=db, username=username, password=password)

    _msg = "Initial admin created, redirecting to login."
    log.info(_msg)
    return RedirectResponse(url="/login", status_code=303)
