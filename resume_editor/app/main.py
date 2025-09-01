import logging
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Form, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.admin import router as admin_router
from resume_editor.app.api.routes.resume import router as resume_router
from resume_editor.app.api.routes.route_logic.settings_crud import (
    get_user_settings,
    update_user_settings,
)
from resume_editor.app.api.routes.user import router as user_router
from resume_editor.app.core.auth import (
    get_optional_current_user_from_cookie,
)
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
from resume_editor.app.web.admin import router as admin_web_router
from resume_editor.app.web.admin_forms import router as admin_forms_router
from resume_editor.app.api.routes.pages.setup import router as setup_router

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

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup templates
    TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    # Include API routers
    app.include_router(user_router)
    app.include_router(resume_router)
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

    @app.get("/login", response_class=HTMLResponse)
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
        return templates.TemplateResponse(request, name="login.html")

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
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
        )
        return response

    @app.get("/logout")
    async def logout():
        """
        Handle user logout and clear the session cookie.

        Returns:
            RedirectResponse: Redirects to the login page.

        Notes:
            1. Create a redirect response to the login page.
            2. Clear the `access_token` cookie.
            3. Return the response.

        """
        _msg = "User logout"
        log.debug(_msg)
        response = RedirectResponse(
            url="/login",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )
        response.delete_cookie("access_token")
        return response

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard(
        request: Request,
        current_user: User | None = Depends(get_optional_current_user_from_cookie),
    ):
        """
        Serve the dashboard page.

        Args:
            request: The HTTP request object.
            current_user: The authenticated user, if one exists.

        Returns:
            TemplateResponse: The rendered dashboard template if the user is authenticated.
            RedirectResponse: A redirect to the login page if the user is not authenticated.

        Notes:
            1. Depend on `get_optional_current_user_from_cookie` to get the current user.
            2. If no user is returned (i.e., authentication fails), redirect to the `/login` page.
            3. On success, render the `dashboard.html` template.

        """
        _msg = "Dashboard page requested"
        log.debug(_msg)

        if not current_user:
            return RedirectResponse(
                url="/login",
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            )

        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {"request": request, "current_user": current_user},
        )

    @app.get("/settings", response_class=HTMLResponse)
    async def settings_page(
        request: Request,
        current_user: User | None = Depends(get_optional_current_user_from_cookie),
        db: Session = Depends(get_db),
    ):
        """
        Serve the user settings page.

        Args:
            request: The HTTP request object.
            current_user: The authenticated user, if one exists.
            db (Session): The database session.

        Returns:
            TemplateResponse: The rendered settings template if authenticated.
            RedirectResponse: Redirect to login if not authenticated.

        Notes:
            1. Depend on `get_optional_current_user_from_cookie` to get the current user.
            2. If no user is returned, redirect to the `/login` page.
            3. Fetch user settings from the database.
            4. On success, render the `settings.html` template with user settings.

        """
        _msg = "Settings page requested"
        log.debug(_msg)
        if not current_user:
            return RedirectResponse(
                url="/login",
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            )

        user_settings = get_user_settings(db=db, user_id=current_user.id)
        context = {
            "llm_endpoint": user_settings.llm_endpoint if user_settings else None,
            "api_key_is_set": bool(user_settings and user_settings.encrypted_api_key),
        }
        return templates.TemplateResponse(request, "settings.html", context)

    @app.post("/settings", response_class=HTMLResponse)
    async def update_settings(
        request: Request,
        llm_endpoint: Annotated[str, Form()],
        api_key: Annotated[str, Form()],
        db: Session = Depends(get_db),
        current_user: User | None = Depends(get_optional_current_user_from_cookie),
    ):
        """
        Handle user settings update.

        Args:
            request: The HTTP request object.
            llm_endpoint (str): The LLM endpoint from the form.
            api_key (str): The API key from the form.
            db (Session): The database session.
            current_user: The authenticated user, if one exists.

        Returns:
            HTMLResponse: A success message snippet on success.
            RedirectResponse: Redirects to login if user is not authenticated.

        Notes:
            1. Redirect to login if user is not authenticated.
            2. Construct a UserSettingsUpdateRequest object from form data.
            3. Call update_user_settings to persist changes.
            4. Return an HTML snippet with a success message.

        """
        _msg = "Settings update submitted"
        log.debug(_msg)

        if not current_user:
            return RedirectResponse(
                url="/login",
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            )

        settings_data = UserSettingsUpdateRequest(
            llm_endpoint=llm_endpoint,
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
        current_user: User | None = Depends(get_optional_current_user_from_cookie),
    ):
        """
        Handle user password change from form.

        Args:
            request: The HTTP request object.
            current_password (str): The current password from the form.
            new_password (str): The new password from the form.
            confirm_new_password (str): The new password confirmation from the form.
            db (Session): The database session.
            current_user: The authenticated user, if one exists.

        Returns:
            HTMLResponse: A success or error message snippet.
            RedirectResponse: Redirects to login if user is not authenticated.

        Notes:
            1. Redirect to login if user is not authenticated.
            2. Check if new password and confirmation match. If not, return an error.
            3. Verify current password. If incorrect, return an error.
            4. Hash new password and update user record.
            5. Return a success message.

        """
        _msg = "Password change form submitted"
        log.debug(_msg)

        if not current_user:
            return RedirectResponse(
                url="/login",
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            )

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

    @app.get("/dashboard/create-resume-form")
    async def create_resume_form():
        """
        Serve the form for creating a new resume.

        Args:
            None

        Returns:
            HTMLResponse: A form for creating a new resume.

        Notes:
            1. Return an HTML form with a textarea for resume content.
            2. Include a submit button to save the resume.

        """
        _msg = "Create resume form requested"
        log.debug(_msg)
        html_content = """
        <div class="h-full flex flex-col">
            <h2 class="text-xl font-semibold mb-4">Create New Resume</h2>
            <form hx-post="/api/resumes" hx-target="#resume-list" hx-swap="innerHTML" hx-trigger="submit">
                <div class="mb-4">
                    <label for="name" class="block text-sm font-medium text-gray-700 mb-1">Resume Name</label>
                    <input 
                        type="text" 
                        id="name" 
                        name="name" 
                        required
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="My Professional Resume">
                </div>
                <div class="mb-4">
                    <label for="content" class="block text-sm font-medium text-gray-700 mb-1">Resume Content (Markdown)</label>
                    <textarea 
                        id="content" 
                        name="content" 
                        rows="20"
                        required
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                        placeholder="# John Doe&#10;&#10;## Contact Information&#10;- Email: john.doe@example.com&#10;- Phone: (555) 123-4567&#10;&#10;## Experience&#10;### Software Engineer&#10;Company Name | Jan 2020 - Present&#10;- Developed web applications using Python and JavaScript&#10;- Collaborated with cross-functional teams"></textarea>
                </div>
                <div class="flex space-x-3">
                    <button 
                        type="submit"
                        class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium">
                        Save Resume
                    </button>
                    <button 
                        type="button"
                        hx-get="/dashboard"
                        hx-target="#resume-content"
                        hx-swap="innerHTML"
                        class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium">
                        Cancel
                    </button>
                </div>
            </form>
        </div>
        """
        return HTMLResponse(content=html_content)

    @app.get("/dashboard/resumes/{resume_id}/edit/personal")
    async def edit_personal_info(request: Request, resume_id: int):
        """
        Serve the form for editing personal information.

        Args:
            request: The HTTP request object.
            resume_id: The ID of the resume to edit.

        Returns:
            HTMLResponse: A form for editing personal information.

        Notes:
            1. Return an HTML form with fields for personal information.
            2. Include submit and cancel buttons.

        """
        _msg = f"Edit personal info form requested for resume {resume_id}"
        log.debug(_msg)
        html_content = f"""
        <div class="h-full flex flex-col">
            <h2 class="text-xl font-semibold mb-4">Edit Personal Information</h2>
            <form hx-post="/api/resumes/{resume_id}/edit/personal" hx-target="#resume-content" hx-swap="innerHTML">
                <div class="mb-4">
                    <label for="name" class="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                    <input 
                        type="text" 
                        id="name" 
                        name="name" 
                        required
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="John Doe">
                </div>
                <div class="mb-4">
                    <label for="email" class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    <input 
                        type="email" 
                        id="email" 
                        name="email" 
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="john.doe@example.com">
                </div>
                <div class="mb-4">
                    <label for="phone" class="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                    <input 
                        type="text" 
                        id="phone" 
                        name="phone" 
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="(555) 123-4567">
                </div>
                <div class="mb-4">
                    <label for="location" class="block text-sm font-medium text-gray-700 mb-1">Location</label>
                    <input 
                        type="text" 
                        id="location" 
                        name="location" 
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="San Francisco, CA">
                </div>
                <div class="mb-4">
                    <label for="website" class="block text-sm font-medium text-gray-700 mb-1">Website</label>
                    <input 
                        type="url" 
                        id="website" 
                        name="website" 
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="https://johndoe.com">
                </div>
                <div class="flex space-x-3">
                    <button 
                        type="submit"
                        class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium">
                        Save Changes
                    </button>
                    <button 
                        type="button"
                        hx-get="/api/resumes/{resume_id}"
                        hx-target="#resume-content"
                        hx-swap="innerHTML"
                        class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium">
                        Cancel
                    </button>
                </div>
            </form>
        </div>
        """
        return HTMLResponse(content=html_content)

    @app.get(
        "/dashboard/resumes/{resume_id}/edit/education",
        response_class=HTMLResponse,
    )
    async def edit_education(request: Request, resume_id: int):
        """
        Serve the form for editing education information.

        Args:
            request: The HTTP request object.
            resume_id: The ID of the resume to edit.

        Returns:
            HTMLResponse: A form for editing education information.

        Notes:
            1. Return an HTML form with fields for education information.
            2. Include submit and cancel buttons.

        """
        _msg = f"Edit education form requested for resume {resume_id}"
        log.debug(_msg)
        html_content = f"""
        <div class="h-full flex flex-col">
            <h2 class="text-xl font-semibold mb-4">Edit Education</h2>
            <form hx-post="/api/resumes/{resume_id}/edit/education" hx-target="#resume-content" hx-swap="innerHTML">
                <div class="mb-4">
                    <label for="school" class="block text-sm font-medium text-gray-700 mb-1">School</label>
                    <input 
                        type="text" 
                        id="school" 
                        name="school" 
                        required
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="University of Example">
                </div>
                <div class="mb-4">
                    <label for="degree" class="block text-sm font-medium text-gray-700 mb-1">Degree</label>
                    <input 
                        type="text" 
                        id="degree" 
                        name="degree" 
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Bachelor of Science">
                </div>
                <div class="mb-4">
                    <label for="major" class="block text-sm font-medium text-gray-700 mb-1">Major</label>
                    <input 
                        type="text" 
                        id="major" 
                        name="major" 
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Computer Science">
                </div>
                <div class="mb-4">
                    <label for="start_date" class="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                    <input 
                        type="date" 
                        id="start_date" 
                        name="start_date" 
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <div class="mb-4">
                    <label for="end_date" class="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                    <input 
                        type="date" 
                        id="end_date" 
                        name="end_date" 
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <div class="flex space-x-3">
                    <button 
                        type="submit"
                        class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium">
                        Save Changes
                    </button>
                    <button 
                        type="button"
                        hx-get="/api/resumes/{resume_id}"
                        hx-target="#resume-content"
                        hx-swap="innerHTML"
                        class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium">
                        Cancel
                    </button>
                </div>
            </form>
        </div>
        """
        return HTMLResponse(content=html_content)

    @app.get(
        "/dashboard/resumes/{resume_id}/edit/experience",
        response_class=HTMLResponse,
    )
    async def edit_experience(request: Request, resume_id: int):
        """
        Serve the form for editing experience information.

        Args:
            request: The HTTP request object.
            resume_id: The ID of the resume to edit.

        Returns:
            HTMLResponse: A form for editing experience information.

        Notes:
            1. Return an HTML form with fields for experience information.
            2. Include submit and cancel buttons.

        """
        _msg = f"Edit experience form requested for resume {resume_id}"
        log.debug(_msg)
        html_content = f"""
        <div class="h-full flex flex-col">
            <h2 class="text-xl font-semibold mb-4">Edit Experience</h2>
            <form hx-post="/api/resumes/{resume_id}/edit/experience" hx-target="#resume-content" hx-swap="innerHTML">
                <div class="mb-4">
                    <label for="company" class="block text-sm font-medium text-gray-700 mb-1">Company</label>
                    <input 
                        type="text" 
                        id="company" 
                        name="company" 
                        required
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Example Corp">
                </div>
                <div class="mb-4">
                    <label for="title" class="block text-sm font-medium text-gray-700 mb-1">Job Title</label>
                    <input 
                        type="text" 
                        id="title" 
                        name="title" 
                        required
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Software Engineer">
                </div>
                <div class="mb-4">
                    <label for="start_date" class="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                    <input 
                        type="date" 
                        id="start_date" 
                        name="start_date" 
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <div class="mb-4">
                    <label for="end_date" class="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                    <input 
                        type="date" 
                        id="end_date" 
                        name="end_date" 
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <div class="mb-4">
                    <label for="description" class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                    <textarea 
                        id="description" 
                        name="description" 
                        rows="4"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Describe your responsibilities and achievements..."></textarea>
                </div>
                <div class="flex space-x-3">
                    <button 
                        type="submit"
                        class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium">
                        Save Changes
                    </button>
                    <button 
                        type="button"
                        hx-get="/api/resumes/{resume_id}"
                        hx-target="#resume-content"
                        hx-swap="innerHTML"
                        class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium">
                        Cancel
                    </button>
                </div>
            </form>
        </div>
        """
        return HTMLResponse(content=html_content)

    @app.get(
        "/dashboard/resumes/{resume_id}/edit/projects",
        response_class=HTMLResponse,
    )
    async def edit_projects(request: Request, resume_id: int):
        """
        Serve the form for editing projects information.

        Args:
            request: The HTTP request object.
            resume_id: The ID of the resume to edit.

        Returns:
            HTMLResponse: A form for editing projects information.

        Notes:
            1. Return an HTML form with fields for projects information.
            2. Include submit and cancel buttons.

        """
        _msg = f"Edit projects form requested for resume {resume_id}"
        log.debug(_msg)
        html_content = f"""
        <div class="h-full flex flex-col">
            <h2 class="text-xl font-semibold mb-4">Edit Projects</h2>
            <form hx-post="/api/resumes/{resume_id}/edit/projects" hx-target="#resume-content" hx-swap="innerHTML">
                <div class="mb-4">
                    <label for="project_title" class="block text-sm font-medium text-gray-700 mb-1">Project Title</label>
                    <input 
                        type="text" 
                        id="project_title" 
                        name="project_title" 
                        required
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Resume Editor Application">
                </div>
                <div class="mb-4">
                    <label for="project_description" class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                    <textarea 
                        id="project_description" 
                        name="project_description" 
                        rows="3"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="A web-based application for resume editing..."></textarea>
                </div>
                <div class="mb-4">
                    <label for="project_url" class="block text-sm font-medium text-gray-700 mb-1">URL</label>
                    <input 
                        type="url" 
                        id="project_url" 
                        name="project_url" 
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="https://github.com/example/resume-editor">
                </div>
                <div class="mb-4">
                    <label for="project_start_date" class="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                    <input 
                        type="date" 
                        id="project_start_date" 
                        name="project_start_date" 
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <div class="mb-4">
                    <label for="project_end_date" class="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                    <input 
                        type="date" 
                        id="project_end_date" 
                        name="project_end_date" 
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <div class="flex space-x-3">
                    <button 
                        type="submit"
                        class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium">
                        Save Changes
                    </button>
                    <button 
                        type="button"
                        hx-get="/api/resumes/{resume_id}"
                        hx-target="#resume-content"
                        hx-swap="innerHTML"
                        class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium">
                        Cancel
                    </button>
                </div>
            </form>
        </div>
        """
        return HTMLResponse(content=html_content)

    @app.get(
        "/dashboard/resumes/{resume_id}/edit/certifications",
        response_class=HTMLResponse,
    )
    async def edit_certifications(request: Request, resume_id: int):
        """
        Serve the form for editing certifications information.

        Args:
            request: The HTTP request object.
            resume_id: The ID of the resume to edit.

        Returns:
            HTMLResponse: A form for editing certifications information.

        Notes:
            1. Return an HTML form with fields for certifications information.
            2. Include submit and cancel buttons.

        """
        _msg = f"Edit certifications form requested for resume {resume_id}"
        log.debug(_msg)
        html_content = f"""
        <div class="h-full flex flex-col">
            <h2 class="text-xl font-semibold mb-4">Edit Certifications</h2>
            <form hx-post="/api/resumes/{resume_id}/edit/certifications" hx-target="#resume-content" hx-swap="innerHTML">
                <div class="mb-4">
                    <label for="cert_name" class="block text-sm font-medium text-gray-700 mb-1">Certification Name</label>
                    <input 
                        type="text" 
                        id="cert_name" 
                        name="cert_name" 
                        required
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="AWS Certified Solutions Architect">
                </div>
                <div class="mb-4">
                    <label for="cert_issuer" class="block text-sm font-medium text-gray-700 mb-1">Issuer</label>
                    <input 
                        type="text" 
                        id="cert_issuer" 
                        name="cert_issuer" 
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Amazon Web Services">
                </div>
                <div class="mb-4">
                    <label for="cert_id" class="block text-sm font-medium text-gray-700 mb-1">Certification ID</label>
                    <input 
                        type="text" 
                        id="cert_id" 
                        name="cert_id" 
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="ABC123XYZ">
                </div>
                <div class="mb-4">
                    <label for="cert_issued_date" class="block text-sm font-medium text-gray-700 mb-1">Issued Date</label>
                    <input 
                        type="date" 
                        id="cert_issued_date" 
                        name="cert_issued_date" 
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <div class="mb-4">
                    <label for="cert_expiry_date" class="block text-sm font-medium text-gray-700 mb-1">Expiry Date</label>
                    <input 
                        type="date" 
                        id="cert_expiry_date" 
                        name="cert_expiry_date" 
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <div class="flex space-x-3">
                    <button 
                        type="submit"
                        class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium">
                        Save Changes
                    </button>
                    <button 
                        type="button"
                        hx-get="/api/resumes/{resume_id}"
                        hx-target="#resume-content"
                        hx-swap="innerHTML"
                        class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium">
                        Cancel
                    </button>
                </div>
            </form>
        </div>
        """
        return HTMLResponse(content=html_content)

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


def main():
    """Entry point for running the application directly."""
    import uvicorn

    initialize_database()
    uvicorn.run(app, host="0.0.0.0", port=8000)


# Only run uvicorn when this module is run directly
if __name__ == "__main__":
    main()
