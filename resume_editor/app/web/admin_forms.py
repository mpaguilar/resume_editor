import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_logic import admin_crud
from resume_editor.app.core.auth import (
    get_optional_current_user_from_cookie,
    verify_admin_privileges,
)
from resume_editor.app.database.database import get_db
from resume_editor.app.models.user import User
from resume_editor.app.schemas.user import AdminUserCreate, AdminUserUpdateRequest

log = logging.getLogger(__name__)

router = APIRouter(tags=["admin-forms"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/admin/users/create-form", response_class=HTMLResponse)
async def get_admin_create_user_form(
    request: Request,
    current_user: User | None = Depends(get_optional_current_user_from_cookie),
):
    """Serves the form to create a new user.

    Args:
        request (Request): The incoming HTTP request object.
        current_user (User | None): The currently authenticated user, retrieved from the session cookie. If not present, redirects to login.

    Returns:
        HTMLResponse: The HTML form for creating a new user, or a redirect to the login page if the user is not authenticated.

    Raises:
        HTTPException: If the current user is not authenticated, raises a 307 redirect to the login page.

    Notes:
        1. Checks if the current user is authenticated via the session cookie.
        2. If not authenticated, redirects to the login page.
        3. Verifies that the authenticated user has admin privileges.
        4. Renders the create user form template with the request context.
    """
    if not current_user:
        return RedirectResponse(
            url="/login",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )
    verify_admin_privileges(user=current_user)
    return templates.TemplateResponse(
        request,
        "admin/partials/create_user_form.html",
        {"request": request},
    )


@router.post("/admin/users/create", response_class=HTMLResponse)
async def handle_admin_create_user_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user_from_cookie),
):
    """Handles the submission of the create user form.

    Args:
        request (Request): The incoming HTTP request object containing form data.
        db (Session): The database session dependency for interacting with the database.
        current_user (User | None): The currently authenticated user, retrieved from the session cookie. If not present, redirects to login.

    Returns:
        HTMLResponse: The updated user list HTML fragment, or a redirect to the login page if the user is not authenticated.

    Raises:
        HTTPException: If the current user is not authenticated, raises a 307 redirect to the login page.

    Notes:
        1. Checks if the current user is authenticated via the session cookie.
        2. If not authenticated, redirects to the login page.
        3. Verifies that the authenticated user has admin privileges.
        4. Parses form data from the request (username, email, password, force_password_change).
        5. Constructs an AdminUserCreate schema with the form data.
        6. Calls the admin_crud.create_user_admin function to persist the new user to the database.
        7. Retrieves the updated list of users from the database.
        8. Renders the user list template with the updated user list and current user context.
    """
    if not current_user:
        return RedirectResponse(
            url="/login",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )
    verify_admin_privileges(user=current_user)

    form_data = await request.form()
    username = form_data.get("username")
    email = form_data.get("email")
    password = form_data.get("password")
    force_password_change = form_data.get("force_password_change") == "true"

    attributes = {"force_password_change": True} if force_password_change else {}
    user_data = AdminUserCreate(
        username=username,
        email=email,
        password=password,
        attributes=attributes,
    )
    admin_crud.create_user_admin(db=db, user_data=user_data)

    db_users = admin_crud.get_users_admin(db=db)
    return templates.TemplateResponse(
        request,
        "admin/partials/user_list.html",
        {"request": request, "users": db_users, "current_user": current_user},
    )


@router.get("/admin/users/{user_id}/edit-form", response_class=HTMLResponse)
async def get_admin_edit_user_form(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user_from_cookie),
):
    """Serves the form to edit an existing user.

    Args:
        request (Request): The incoming HTTP request object.
        user_id (int): The unique identifier of the user to be edited.
        db (Session): The database session dependency for interacting with the database.
        current_user (User | None): The currently authenticated user, retrieved from the session cookie. If not present, redirects to login.

    Returns:
        HTMLResponse: The HTML form for editing the user, or a redirect to the login page if the user is not authenticated.

    Raises:
        HTTPException: If the current user is not authenticated, raises a 307 redirect to the login page. If the user with the given ID is not found, raises a 404 error.

    Notes:
        1. Checks if the current user is authenticated via the session cookie.
        2. If not authenticated, redirects to the login page.
        3. Verifies that the authenticated user has admin privileges.
        4. Queries the database to retrieve the user with the given ID.
        5. If the user is not found, raises a 404 HTTP exception.
        6. Renders the edit user form template with the request context and user data.
    """
    if not current_user:
        return RedirectResponse(
            url="/login",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )
    verify_admin_privileges(user=current_user)
    user = admin_crud.get_user_by_id_admin(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse(
        request,
        "admin/partials/edit_user_form.html",
        {"request": request, "user": user},
    )


@router.post("/admin/users/{user_id}/edit", response_class=HTMLResponse)
async def handle_admin_edit_user_form(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user_from_cookie),
):
    """Handles the submission of the edit user form.

    Args:
        request (Request): The incoming HTTP request object containing form data.
        user_id (int): The unique identifier of the user to be edited.
        db (Session): The database session dependency for interacting with the database.
        current_user (User | None): The currently authenticated user, retrieved from the session cookie. If not present, redirects to login.

    Returns:
        HTMLResponse: The updated user list HTML fragment, or a redirect to the login page if the user is not authenticated.

    Raises:
        HTTPException: If the current user is not authenticated, raises a 307 redirect to the login page. If the user with the given ID is not found, raises a 404 error.

    Notes:
        1. Checks if the current user is authenticated via the session cookie.
        2. If not authenticated, redirects to the login page.
        3. Verifies that the authenticated user has admin privileges.
        4. Parses form data from the request (email, force_password_change).
        5. Queries the database to retrieve the user with the given ID.
        6. If the user is not found, raises a 404 HTTP exception.
        7. Constructs an AdminUserUpdateRequest schema with the form data.
        8. Calls the admin_crud.update_user_admin function to update the user in the database.
        9. Retrieves the updated list of users from the database.
        10. Finds the updated user in the list to pass to the template.
        11. Renders the user list template with the updated user list and current user context.
        12. Sends an HX-Trigger header to notify the frontend that the user list has changed.
    """
    if not current_user:
        return RedirectResponse(
            url="/login",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )
    verify_admin_privileges(user=current_user)

    form_data = await request.form()
    email = form_data.get("email")
    force_password_change = form_data.get("force_password_change") == "true"

    user = admin_crud.get_user_by_id_admin(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = AdminUserUpdateRequest(
        email=email,
        force_password_change=force_password_change,
    )
    updated_user = admin_crud.update_user_admin(
        db=db, user=user, update_data=update_data,
    )

    db_users = admin_crud.get_users_admin(db=db)
    # Find the updated user in the list to pass to the template
    user_for_template = next(
        (u for u in db_users if u.id == updated_user.id),
        None,
    )
    return templates.TemplateResponse(
        request,
        "admin/partials/user_list.html",
        {"request": request, "users": db_users, "current_user": current_user},
        headers={"HX-Trigger": "userListChanged"},
    )
