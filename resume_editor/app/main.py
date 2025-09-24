import html
import logging
from pathlib import Path
from typing import Annotated
from urllib.parse import quote_plus

from fastapi import Depends, FastAPI, Form, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.admin import router as admin_router
from resume_editor.app.api.routes.html_fragments import _generate_resume_detail_html
from resume_editor.app.api.routes.resume import router as resume_router
from resume_editor.app.api.routes.resume_export import router as resume_export_router
from resume_editor.app.api.routes.route_logic.resume_crud import (
    create_resume as create_resume_db,
    get_resume_by_id_and_user,
    update_resume,
)
from resume_editor.app.api.routes.route_logic.resume_parsing import (
    validate_resume_content,
)
from resume_editor.app.api.routes.route_logic.settings_crud import (
    get_user_settings,
    update_user_settings,
)
from resume_editor.app.api.routes.route_logic import user_crud
from resume_editor.app.api.routes.user import router as user_router
from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.core.config import Settings, get_settings
from resume_editor.app.core.security import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    verify_password,
)
from resume_editor.app.database.database import get_db, get_session_local
from resume_editor.app.models.user import User
from resume_editor.app.schemas.user import (
    UserSettingsUpdateRequest,
)
from resume_editor.app.web.admin import router as admin_web_router
from resume_editor.app.web.admin_forms import router as admin_forms_router
from resume_editor.app.api.routes.pages.setup import router as setup_router
from starlette.middleware.base import BaseHTTPMiddleware

from resume_editor.app.api.routes.resume_ai import router as resume_ai_router
from resume_editor.app.middleware import refresh_session_middleware

log = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        None

    Returns:
        FastAPI: The configured FastAPI application instance.

    Notes:
        1. Initialize the FastAPI application with the title "Resume Editor API".
        2. Add CORS middleware to allow requests from any origin (for development only).
        3. Include the user router to handle user-related API endpoints.
        4. Include the resume router to handle resume-related API endpoints.
        5. Include the admin router to handle administrative API endpoints.
        6. Define a health check endpoint at "/health" that returns a JSON object with status "ok".
        7. Add static file serving for CSS/JS assets.
        8. Add template rendering for HTML pages.
        9. Define dashboard routes for the HTMX-based interface.
        10. Log a success message indicating the application was created.

    """
    _msg = "Creating FastAPI application"
    log.debug(_msg)

    app = FastAPI(title="Resume Editor API")

    app.middleware("http")(refresh_session_middleware)

    @app.middleware("http")
    async def setup_check_middleware(request: Request, call_next):
        """
        Redirect to setup page if no users exist.
        """
        # Excluded paths that should be accessible even if no users are set up
        excluded_paths = [
            "/setup",
            "/static",
            "/docs",
            "/openapi.json",
            "/health",
            "/login",
            "/logout",
            "/change-password",
        ]
        if any(request.url.path.startswith(p) for p in excluded_paths):
            return await call_next(request)

        # For all other paths, check if users exist
        redirect_to_setup = False
        SessionLocal = get_session_local()
        db = SessionLocal()
        try:
            if user_crud.user_count(db=db) == 0:
                redirect_to_setup = True
        finally:
            db.close()

        if redirect_to_setup:
            return RedirectResponse(url="/setup")

        # Proceed with the request if users exist
        response = await call_next(request)
        return response

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(BaseHTTPMiddleware, dispatch=refresh_session_middleware)

    # Setup templates
    TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    # Mount static files
    STATIC_DIR = Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Include API routers
    app.include_router(user_router)
    app.include_router(resume_router)
    app.include_router(resume_export_router, prefix="/api/resumes", tags=["resumes"])
    app.include_router(resume_ai_router, prefix="/api/resumes", tags=["resumes"])
    app.include_router(admin_router)
    app.include_router(admin_web_router)
    app.include_router(admin_forms_router)
    app.include_router(setup_router)

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """
        Health check endpoint to verify the application is running.

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

    @app.get("/")
    async def root():
        """
        Redirect root to dashboard.

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

    @app.get("/login", response_class=HTMLResponse, name="login_page")
    async def login_page(request: Request):
        """
        Serve the login page.

        Args:
            request: The HTTP request object.

        Returns:
            TemplateResponse: The rendered login template.

        """
        _msg = "Login page requested"
        log.debug(_msg)
        return templates.TemplateResponse(request, "login.html")

    @app.post("/login")
    async def login_for_access_token(
        request: Request,
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
        db: Session = Depends(get_db),
        settings: Settings = Depends(get_settings),
    ):
        """
        Handle user login and create a session cookie.

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

        access_token = create_access_token(
            data={"sub": user.username},
            settings=settings,
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

    @app.get("/logout")
    async def logout(request: Request):
        """
        Handle user logout and clear the session cookie.

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

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard(
        request: Request,
        current_user: User = Depends(get_current_user_from_cookie),
    ):
        """
        Serve the dashboard page.

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

    @app.get("/resumes/{resume_id}/edit", response_class=HTMLResponse)
    async def resume_editor_page(
        request: Request,
        resume_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_from_cookie),
    ):
        """Serve the dedicated editor page for a single resume."""
        resume = get_resume_by_id_and_user(db, resume_id, current_user.id)
        return templates.TemplateResponse(
            request,
            "editor.html",
            {
                "resume": resume,
                "current_user": current_user,
            },
        )

    @app.get("/resumes/create", response_class=HTMLResponse)
    async def create_resume_page(
        request: Request,
        current_user: User = Depends(get_current_user_from_cookie),
    ):
        """Serve the page for creating a new resume."""
        return templates.TemplateResponse(
            request,
            "create_resume.html",
            {"current_user": current_user, "name": None, "content": None, "error": None},
        )

    @app.post("/resumes/create")
    async def handle_create_resume(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_from_cookie),
        name: str = Form(...),
        content: str = Form(...),
    ):
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

        resume = create_resume_db(
            db=db, user_id=current_user.id, name=name, content=content
        )
        return RedirectResponse(
            url=f"/resumes/{resume.id}/edit", status_code=status.HTTP_303_SEE_OTHER
        )

    @app.get("/resumes/{resume_id}/refine", response_class=HTMLResponse)
    async def refine_resume_page(
        request: Request,
        resume_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_from_cookie),
    ):
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



    @app.get("/settings", response_class=HTMLResponse)
    async def settings_page(
        request: Request,
        current_user: User = Depends(get_current_user_from_cookie),
        db: Session = Depends(get_db),
    ):
        """
        Serve the user settings page.

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
        }
        return templates.TemplateResponse(request, "settings.html", context=context)

    @app.post("/settings", response_class=HTMLResponse)
    async def update_settings(
        request: Request,
        llm_endpoint: Annotated[str, Form()],
        llm_model_name: Annotated[str, Form()],
        api_key: Annotated[str, Form()],
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_from_cookie),
    ):
        """
        Handle user settings update.

        Args:
            request: The HTTP request object.
            llm_endpoint (str): The LLM endpoint from the form.
            api_key (str): The API key from the form.
            db (Session): The database session.
            current_user: The authenticated user.

        Returns:
            HTMLResponse: A success message snippet on success.

        Notes:
            1. Depends on `get_current_user_from_cookie` for authentication.
            2. Construct a UserSettingsUpdateRequest object from form data.
            3. Call update_user_settings to persist changes.
            4. Return an HTML snippet with a success message.

        """
        _msg = "Settings update submitted"
        log.debug(_msg)

        settings_data = UserSettingsUpdateRequest(
            llm_endpoint=llm_endpoint,
            llm_model_name=llm_model_name,
            api_key=api_key,
        )

        update_user_settings(
            db=db,
            user_id=current_user.id,
            settings_data=settings_data,
        )

        return HTMLResponse(
            '<div class="p-4 mb-4 text-sm text-green-800 rounded-lg bg-green-50" role="alert"><span class="font-medium">Success!</span> Your settings have been updated.</div>',
        )

    @app.post("/change-password", response_class=HTMLResponse)
    async def change_password_form(
        request: Request,
        current_password: Annotated[str, Form()],
        new_password: Annotated[str, Form()],
        confirm_new_password: Annotated[str, Form()],
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_from_cookie),
    ):
        """
        Handle user password change from form.

        Args:
            request: The HTTP request object.
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


    _msg = "FastAPI application created successfully"
    log.debug(_msg)
    return app


app = create_app()


def initialize_database():
    """
    Initialize the database.

    Args:
        None

    Returns:
        None

    Notes:
        1. Database initialization is now handled by Alembic migrations.
        2. This function is kept for structural consistency but performs no actions.

    """
    _msg = "Database initialization is now handled by Alembic. Skipping create_all."
    log.debug(_msg)


