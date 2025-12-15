import logging
from collections.abc import Awaitable, Callable
from pathlib import Path

import nltk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from resume_editor.app.api.routes.admin import router as admin_router
from resume_editor.app.api.routes.pages.setup import router as setup_router
from resume_editor.app.api.routes.resume import router as resume_router
from resume_editor.app.api.routes.resume_ai import router as resume_ai_router
from resume_editor.app.api.routes.resume_export import router as resume_export_router
from resume_editor.app.api.routes.route_logic import user_crud
from resume_editor.app.api.routes.user import router as user_router
from resume_editor.app.database.database import get_session_local
from resume_editor.app.middleware import refresh_session_middleware
from resume_editor.app.web.admin import router as admin_web_router
from resume_editor.app.web.admin_forms import router as admin_forms_router
from resume_editor.app.web.pages import router as web_pages_router

log = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

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

    # Download required NLTK data on startup to prevent slow first-request parsing
    # This "warms up" each worker process.
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt")

    app = FastAPI(title="Resume Editor API")

    app.middleware("http")(refresh_session_middleware)

    @app.middleware("http")
    async def setup_check_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ):
        """Redirect to setup page if no users exist."""
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
    app.include_router(web_pages_router)

    _msg = "FastAPI application created successfully"
    log.debug(_msg)
    return app


app = create_app()


def initialize_database() -> None:
    """Initialize the database.

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
