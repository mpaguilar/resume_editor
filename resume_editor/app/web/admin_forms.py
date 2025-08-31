import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
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


@router.get("/admin/users/create-form", response_class=HTMLResponse)
async def get_admin_create_user_form(
    request: Request,
    current_user: User | None = Depends(get_optional_current_user_from_cookie),
):
    """Serves the form to create a new user."""
    if not current_user:
        return RedirectResponse(
            url="/login",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )
    verify_admin_privileges(user=current_user)
    return HTMLResponse(
        """
        <div id="modal-content">
            <form hx-post="/admin/users/create" hx-target="#user-list-container" hx-swap="innerHTML">
                <h2 class="text-2xl font-bold mb-4">Create New User</h2>
                <div class="mb-4">
                    <label for="username">Username</label>
                    <input type="text" name="username" required class="w-full p-2 border rounded">
                </div>
                <div class="mb-4">
                    <label for="email">Email</label>
                    <input type="email" name="email" required class="w-full p-2 border rounded">
                </div>
                <div class="mb-4">
                    <label for="password">Password</label>
                    <input type="password" name="password" required class="w-full p-2 border rounded">
                </div>
                <div class="mb-4">
                    <input type="checkbox" name="force_password_change" value="true" class="mr-2">
                    <label for="force_password_change">Force password change on next login</label>
                </div>
                <div class="flex justify-end space-x-2">
                    <button type="button" onclick="document.getElementById('modal').style.display='none'" class="bg-gray-400 text-white px-4 py-2 rounded">Cancel</button>
                    <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded">Create User</button>
                </div>
            </form>
        </div>
        """,
    )


@router.post("/admin/users/create", response_class=HTMLResponse)
async def handle_admin_create_user_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user_from_cookie),
):
    """Handles the submission of the create user form."""
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

    attributes = {"force_password_change": True} if force_password_change else None
    user_data = AdminUserCreate(
        username=username,
        email=email,
        password=password,
        attributes=attributes,
    )
    admin_crud.create_user_admin(db=db, user_data=user_data)
    response = Response(status_code=status.HTTP_200_OK)
    response.headers["HX-Trigger"] = "userListChanged"
    response.headers["HX-Redirect"] = "/admin/users"
    return response


@router.get("/admin/users/{user_id}/edit-form", response_class=HTMLResponse)
async def get_admin_edit_user_form(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user_from_cookie),
):
    """Serves the form to edit an existing user."""
    if not current_user:
        return RedirectResponse(
            url="/login",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )
    verify_admin_privileges(user=current_user)
    user = admin_crud.get_user_by_id_admin(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    force_change = (
        user.attributes.get("force_password_change", False)
        if user.attributes
        else False
    )
    checked = "checked" if force_change else ""

    return HTMLResponse(
        f"""
        <div id="modal-content">
            <form hx-post="/admin/users/{user_id}/edit" hx-target="#user-row-{user_id}" hx-swap="outerHTML">
                <h2 class="text-2xl font-bold mb-4">Edit User: {user.username}</h2>
                <div class="mb-4">
                    <label for="email">Email</label>
                    <input type="email" name="email" value="{user.email}" required class="w-full p-2 border rounded">
                </div>
                <div class="mb-4">
                    <input type="checkbox" name="force_password_change" value="true" {checked} class="mr-2">
                    <label for="force_password_change">Force password change on next login</label>
                </div>
                <div class="flex justify-end space-x-2">
                    <button type="button" onclick="document.getElementById('modal').style.display='none'" class="bg-gray-400 text-white px-4 py-2 rounded">Cancel</button>
                    <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded">Save Changes</button>
                </div>
            </form>
        </div>
        """,
    )


@router.post("/admin/users/{user_id}/edit", response_class=HTMLResponse)
async def handle_admin_edit_user_form(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user_from_cookie),
):
    """Handles the submission of the edit user form."""
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
    admin_crud.update_user_admin(db=db, user=user, update_data=update_data)

    response = Response(status_code=status.HTTP_200_OK)
    response.headers["HX-Trigger"] = "userListChanged"
    response.headers["HX-Redirect"] = "/admin/users"
    return response
