import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
        7. Log a success message indicating the application was created.

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
