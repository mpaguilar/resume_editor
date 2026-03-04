import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from resume_editor.app.api.dependencies import get_resume_for_user
from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    reconstruct_resume_with_new_introduction,
)
from resume_editor.app.api.routes.route_logic.resume_crud import (
    ResumeCreateParams,
    ResumeUpdateParams,
    get_resume_by_id_and_user,
    update_resume,
)
from resume_editor.app.api.routes.route_logic.resume_crud import (
    create_resume as create_resume_db,
)
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.api.routes.route_logic.resume_validation import (
    validate_company_and_notes,
)
from resume_editor.app.api.routes.route_logic.resume_parsing import (
    validate_resume_content,
)
from resume_editor.app.api.routes.route_logic.settings_crud import (
    get_user_settings,
    update_user_settings,
)
from resume_editor.app.api.routes.route_models import SettingsUpdateForm
from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.core.config import Settings, get_settings
from resume_editor.app.core.security import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    verify_password,
)
from resume_editor.app.database.database import get_db
from resume_editor.app.models.user import User
from resume_editor.app.schemas.user import (
    UserSettingsUpdateRequest,
)

log = logging.getLogger(__name__)

router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/")
async def root() -> RedirectResponse:
    """Redirect root to dashboard.

    Args:
        None

    Returns:
        RedirectResponse: Redirect to the dashboard page.

    Notes:
        1. Redirect the root path to the dashboard.

    """
    _msg = "Root path requested, redirecting to dashboard"
    log.debug(_msg)
    return RedirectResponse(url="/dashboard")


@router.get("/login", response_class=HTMLResponse, name="login_page")
async def login_page(request: Request) -> HTMLResponse:
    """Serve the login page.

    Args:
        request: The HTTP request object.

    Returns:
        TemplateResponse: The rendered login template.

    """
    _msg = "Login page requested"
    log.debug(_msg)
    return templates.TemplateResponse(request, "login.html")


@router.post("/login", response_class=HTMLResponse, response_model=None)
async def login_for_access_token(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RedirectResponse | HTMLResponse:
    """Handle user login and create a session cookie.

    Args:
        request: The HTTP request object.
        username (str): The username from the form.
        password (str): The password from the form.
        db (Session): The database session.
        settings (Settings): The application settings.

    Returns:
        RedirectResponse: Redirects to the dashboard on successful login.
        TemplateResponse: Re-renders the login page with an error on failure.

    Notes:
        1. Authenticate the user with username and password.
        2. If authentication fails, re-render the login page with an error message.
        3. If successful, create a JWT access token.
        4. Set the token in a secure, HTTP-only cookie.
        5. Redirect to the dashboard.

    """
    _msg = "Login attempt for user"
    log.debug(_msg)
    user = authenticate_user(db=db, username=username, password=password)
    if not user:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error_message": "Invalid username or password"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Get user's session timeout preference
    user_settings = get_user_settings(db, user.id)
    expires_delta = None
    if user_settings and user_settings.access_token_expire_minutes:
        from datetime import timedelta

        expires_delta = timedelta(minutes=user_settings.access_token_expire_minutes)

    access_token = create_access_token(
        data={"sub": user.username},
        settings=settings,
        expires_delta=expires_delta,
    )
    response = RedirectResponse(
        url="/dashboard",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        path="/",
        secure=False,  # Should be True in production & depend on settings
    )
    return response


@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    """Handle user logout and clear the session cookie.

    Args:
        request (Request): The incoming HTTP request, used to generate the redirect URL.

    Returns:
        RedirectResponse: Redirects to the login page.

    Notes:
        1. Create a redirect response to the login page using the request context.
        2. Clear the `access_token` cookie.
        3. Return the response.

    """
    _msg = "User logout"
    log.debug(_msg)
    response = RedirectResponse(
        url=str(request.url_for("login_page")),
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
    response.delete_cookie("access_token")
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
) -> HTMLResponse:
    """Serve the dashboard page.

    Args:
        request: The HTTP request object.
        current_user: The authenticated user.

    Returns:
        TemplateResponse: The rendered dashboard template.

    Notes:
        1. Depends on `get_current_user_from_cookie`. If the user is not
           authenticated, a redirect to the login page is automatically handled
           by the dependency.
        2. On success, render the `dashboard.html` template.

    """
    _msg = "Dashboard page requested"
    log.debug(_msg)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"current_user": current_user},
    )


@router.get("/resumes/{resume_id}/edit", response_class=HTMLResponse)
async def resume_editor_page(
    request: Request,
    resume_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
) -> HTMLResponse:
    """Serve the dedicated editor page for a single resume."""
    resume = get_resume_by_id_and_user(
        db=db,
        resume_id=resume_id,
        user_id=current_user.id,
    )
    return templates.TemplateResponse(
        request,
        "editor.html",
        {
            "resume": resume,
            "current_user": current_user,
        },
    )


@router.get("/resumes/{resume_id}/view", response_class=HTMLResponse)
async def get_resume_view_page(
    request: Request,
    resume_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
) -> HTMLResponse:
    """Serve the dedicated view page for a single resume."""
    resume = get_resume_by_id_and_user(
        db=db,
        resume_id=resume_id,
        user_id=current_user.id,
    )
    return templates.TemplateResponse(
        request,
        "pages/resume_view.html",
        {
            "resume": resume,
            "current_user": current_user,
        },
    )


class ResumeViewUpdateForm:
    """Form data for resume view updates.

    Attributes:
        introduction: The updated introduction (optional).
        notes: The updated notes (optional).
        company: The updated company (optional).

    """

    def __init__(
        self,
        introduction: Annotated[str | None, Form()] = None,
        notes: Annotated[str | None, Form()] = None,
        company: Annotated[str | None, Form()] = None,
    ):
        self.introduction = introduction
        self.notes = notes
        self.company = company


@dataclass
class HandleResumeViewUpdateParams:
    """Parameters for handling resume view updates.

    Attributes:
        request: The HTTP request.
        resume: The resume being viewed.
        db: The database session.
        form_data: The form data containing company, notes, and introduction.

    """

    request: Request
    resume: DatabaseResume
    db: Session
    form_data: ResumeViewUpdateForm


def _validate_view_update_params(
    params: HandleResumeViewUpdateParams,
) -> tuple[bool, str | None]:
    """Validate view update parameters.

    Args:
        params: The parameters to validate.

    Returns:
        tuple[bool, str | None]: A tuple of (is_valid, error_message).

    """
    validation = validate_company_and_notes(
        params.form_data.company,
        params.form_data.notes,
    )
    if not validation.is_valid:
        error_message = "; ".join(validation.errors.values())
        return False, error_message
    return True, None


def _handle_validation_error(
    params: HandleResumeViewUpdateParams,
    error_message: str,
) -> HTMLResponse:
    """Handle validation error with appropriate response.

    Args:
        params: The update parameters.
        error_message: The error message to display.

    Returns:
        HTMLResponse: Error HTML or redirect response.

    """
    _msg = "Validation failed for company or notes"
    log.debug(_msg)

    # Return error for HTMX requests
    if "HX-Request" in params.request.headers:
        error_html = f"<div class='text-red-500 p-2'><p>{error_message}</p></div>"
        return HTMLResponse(content=error_html)

    # For regular requests, redirect
    return RedirectResponse(
        url=f"/resumes/{params.resume.id}/view",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/resumes/{resume_id}/view", response_class=HTMLResponse)
async def handle_resume_view_update(
    request: Request,
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
    db: Annotated[Session, Depends(get_db)],
    form_data: Annotated[ResumeViewUpdateForm, Depends()],
) -> HTMLResponse:
    """Handle updates to the view page (introduction, notes, company).

    This also reconstructs the main resume content to reflect the updated
    introduction in the banner section.

    Args:
        request: The HTTP request.
        resume: The resume being viewed.
        db: The database session.
        form_data: The form data containing introduction, notes, and company.

    Returns:
        HTMLResponse: Redirect to view page or error message.

    Notes:
        1. Validate company and notes using validate_company_and_notes.
        2. If validation fails, return error HTML for HTMX requests
           or redirect for regular requests.
        3. Reconstruct resume content with new introduction.
        4. Update the resume with all provided fields.
        5. Redirect back to the view page.

    """
    _msg = f"handle_resume_view_update starting for resume {resume.id}"
    log.debug(_msg)

    params = HandleResumeViewUpdateParams(
        request=request,
        resume=resume,
        db=db,
        form_data=form_data,
    )

    is_valid, error_message = _validate_view_update_params(params)
    if not is_valid:
        return _handle_validation_error(params, error_message)

    # Reconstruct resume content with new introduction
    new_content = reconstruct_resume_with_new_introduction(
        resume_content=str(resume.content),
        introduction=form_data.introduction,
    )

    # Update the resume
    update_params = ResumeUpdateParams(
        introduction=form_data.introduction,
        notes=form_data.notes,
        company=form_data.company,
        content=new_content,
    )
    update_resume(
        db=db,
        resume=resume,
        params=update_params,
    )

    _msg = "handle_resume_view_update returning"
    log.debug(_msg)

    # Redirect back to view page
    return RedirectResponse(
        url=f"/resumes/{resume.id}/view",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/resumes/create", response_class=HTMLResponse)
async def create_resume_page(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
) -> HTMLResponse:
    """Serve the page for creating a new resume."""
    return templates.TemplateResponse(
        request,
        "create_resume.html",
        {
            "current_user": current_user,
            "name": None,
            "content": None,
            "error": None,
        },
    )


@router.post("/resumes/create", response_class=HTMLResponse, response_model=None)
async def handle_create_resume(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
    name: Annotated[str, Form(...)],
    content: Annotated[str, Form(...)],
) -> RedirectResponse | HTMLResponse:
    """Handle the form submission for creating a new resume."""
    try:
        validate_resume_content(content)
    except HTTPException as e:
        return templates.TemplateResponse(
            request,
            "create_resume.html",
            {
                "current_user": current_user,
                "name": name,
                "content": content,
                "error": e.detail,
            },
            status_code=422,
        )

    create_params = ResumeCreateParams(
        user_id=current_user.id,
        name=name,
        content=content,
    )
    resume = create_resume_db(
        db=db,
        params=create_params,
    )
    return RedirectResponse(
        url=f"/resumes/{resume.id}/edit",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/resumes/{resume_id}/refine", response_class=HTMLResponse)
async def refine_resume_page(
    request: Request,
    resume_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
) -> HTMLResponse:
    """Serve the dedicated page for refining a resume."""
    resume = get_resume_by_id_and_user(db, resume_id, current_user.id)
    return templates.TemplateResponse(
        request,
        "refine.html",
        {
            "resume": resume,
            "current_user": current_user,
            "target_section": "experience",
        },
    )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
    db: Annotated[Session, Depends(get_db)],
) -> HTMLResponse:
    """Serve the user settings page.

    Args:
        request: The HTTP request object.
        current_user: The authenticated user.
        db (Session): The database session.

    Returns:
        TemplateResponse: The rendered settings template.

    Notes:
        1. Depends on `get_current_user_from_cookie` for authentication.
           Unauthenticated users are automatically redirected to the login page.
        2. Fetch user settings from the database.
        3. On success, render the `settings.html` template with user settings.

    """
    _msg = "Settings page requested"
    log.debug(_msg)
    user_settings = get_user_settings(db=db, user_id=current_user.id)
    context = {
        "current_user": current_user,
        "llm_endpoint": user_settings.llm_endpoint if user_settings else None,
        "llm_model_name": user_settings.llm_model_name if user_settings else None,
        "api_key_is_set": bool(user_settings and user_settings.encrypted_api_key),
        "access_token_expire_minutes": user_settings.access_token_expire_minutes
        if user_settings
        else None,
    }
    return templates.TemplateResponse(request, "settings.html", context=context)


@router.post("/settings", response_class=HTMLResponse)
async def update_settings(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
    form_data: Annotated[SettingsUpdateForm, Depends()],
) -> HTMLResponse:
    """Handle user settings update.

    Args:
        form_data (SettingsUpdateForm): The form data containing settings values.
        db (Session): The database session.
        current_user: The authenticated user.

    Returns:
        HTMLResponse: A success message snippet on success, or an error message
            if validation fails.

    Notes:
        1. Depends on `get_current_user_from_cookie` for authentication.
        2. Validate the access_token_expire_minutes value if provided.
        3. Construct a UserSettingsUpdateRequest object from form data.
        4. Call update_user_settings to persist changes.
        5. Return an HTML snippet with a success or error message.

    """
    _msg = "Settings update submitted"
    log.debug(_msg)

    # Parse and validate access_token_expire_minutes
    timeout_minutes: int | None = None
    if (
        form_data.access_token_expire_minutes
        and form_data.access_token_expire_minutes.strip()
    ):
        try:
            timeout_minutes = int(form_data.access_token_expire_minutes)
            if timeout_minutes < 15 or timeout_minutes > 1440:
                _msg = "Login timeout must be between 15 minutes and 24 hours (1440 minutes)."
                return HTMLResponse(
                    content=f'<div class="p-4 mb-4 text-sm text-red-800 rounded-lg bg-red-50" role="alert"><span class="font-medium">Error!</span> {_msg}</div>',
                )
        except ValueError:
            _msg = "Login timeout must be a valid number."
            return HTMLResponse(
                content=f'<div class="p-4 mb-4 text-sm text-red-800 rounded-lg bg-red-50" role="alert"><span class="font-medium">Error!</span> {_msg}</div>',
            )

    settings_data = UserSettingsUpdateRequest(
        llm_endpoint=form_data.llm_endpoint,
        llm_model_name=form_data.llm_model_name,
        api_key=form_data.api_key,
        access_token_expire_minutes=timeout_minutes,
    )

    try:
        update_user_settings(
            db=db,
            user_id=current_user.id,
            settings_data=settings_data,
        )
    except ValueError as e:
        _msg = str(e)
        return HTMLResponse(
            content=f'<div class="p-4 mb-4 text-sm text-red-800 rounded-lg bg-red-50" role="alert"><span class="font-medium">Error!</span> {_msg}</div>',
        )

    return HTMLResponse(
        '<div class="p-4 mb-4 text-sm text-green-800 rounded-lg bg-green-50" role="alert"><span class="font-medium">Success!</span> Your settings have been updated.</div>',
    )


@router.post("/change-password", response_class=HTMLResponse)
async def change_password_form(
    current_password: Annotated[str, Form()],
    new_password: Annotated[str, Form()],
    confirm_new_password: Annotated[str, Form()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
) -> HTMLResponse:
    """Handle user password change from form.

    Args:
        current_password (str): The current password from the form.
        new_password (str): The new password from the form.
        confirm_new_password (str): The new password confirmation from the form.
        db (Session): The database session.
        current_user: The authenticated user.

    Returns:
        HTMLResponse: A success or error message snippet.

    Notes:
        1. Depends on `get_current_user_from_cookie` for authentication.
        2. Check if new password and confirmation match. If not, return an error.
        3. Verify current password. If incorrect, return an error.
        4. Hash new password and update user record.
        5. Return a success message.

    """
    _msg = "Password change form submitted"
    log.debug(_msg)

    if new_password != confirm_new_password:
        return HTMLResponse(
            '<div class="p-4 mb-4 text-sm text-red-800 rounded-lg bg-red-50" role="alert"><span class="font-medium">Error!</span> New passwords do not match.</div>',
        )

    if not verify_password(current_password, current_user.hashed_password):
        return HTMLResponse(
            '<div class="p-4 mb-4 text-sm text-red-800 rounded-lg bg-red-50" role="alert"><span class="font-medium">Error!</span> Incorrect current password.</div>',
        )

    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()

    return HTMLResponse(
        '<div class="p-4 mb-4 text-sm text-green-800 rounded-lg bg-green-50" role="alert"><span class="font-medium">Success!</span> Your password has been changed.</div>',
    )


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint to verify the application is running.

    Args:
        None

    Returns:
        dict[str, str]: A dictionary with a single key "status" and value "ok".

    Notes:
        1. Return a JSON dictionary with the key "status" and value "ok".
        2. No database or network access required.

    """
    _msg = "Health check endpoint called"
    log.debug(_msg)
    return {"status": "ok"}
