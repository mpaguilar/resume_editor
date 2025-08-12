import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from resume_editor.app.api.routes.resume import router as resume_router
from resume_editor.app.api.routes.user import router as user_router
from resume_editor.app.database.database import get_engine
from resume_editor.app.models import Base

log = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        None

    Returns:
        FastAPI: The configured FastAPI application instance.

    Notes:
        1. Initialize the FastAPI application with the title "Resume Editor API".
        2. Create the database tables by calling Base.metadata.create_all with the database engine.
        3. Add CORS middleware to allow requests from any origin (for development only).
        4. Include the user router to handle user-related API endpoints.
        5. Include the resume router to handle resume-related API endpoints.
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
    templates = Jinja2Templates(directory="templates")

    # Include API routers
    app.include_router(user_router)
    app.include_router(resume_router)

    @app.get("/health")
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

    @app.get("/")
    async def root():
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

    @app.get("/dashboard")
    async def dashboard(request: Request):
        """Serve the dashboard page.

        Args:
            request: The HTTP request object.

        Returns:
            TemplateResponse: The rendered dashboard template.

        Notes:
            1. Render the dashboard.html template.
            2. Pass the request object to the template.

        """
        _msg = "Dashboard page requested"
        log.debug(_msg)
        return templates.TemplateResponse("dashboard.html", {"request": request})

    @app.get("/dashboard/create-resume-form")
    async def create_resume_form():
        """Serve the form for creating a new resume.

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
        return html_content

    _msg = "FastAPI application created successfully"
    log.debug(_msg)
    return app


def initialize_database():
    """Initialize the database tables.

    Args:
        None

    Returns:
        None

    Notes:
        1. Create database tables by calling Base.metadata.create_all with the database engine.
        2. This function should be called after the app is created but before it starts serving requests.
        3. Database access is performed via the engine returned by get_engine().

    """
    _msg = "Creating database tables"
    log.debug(_msg)
    Base.metadata.create_all(bind=get_engine())


# Only create the app instance when this module is run directly
if __name__ == "__main__":
    app = create_app()
    initialize_database()
else:
    # For imports, just define the function without creating the app
    app = None
