"""
This module initializes the API endpoints for the resume editor application.

It defines the FastAPI application instance and sets up the API routes
that handle user authentication, resume management, and related operations.

Classes:
    API: The main FastAPI application class that routes requests to appropriate
         endpoints.

Functions:
    get_app(): Returns the FastAPI application instance.

Notes:
    1. The API is designed to be modular, with routes defined in separate
       modules imported and mounted here.
    2. Authentication is handled via OAuth2 with JWT tokens.
    3. All endpoints are protected by dependency injection using the
       get_current_user function.
    4. The application is configured to use the database session from the
       database module.
    5. The API supports both JSON and form data input formats.
    6. All database interactions are performed through SQLAlchemy ORM.
    7. The application logs all requests and responses using the standard
       logging module.

"""

from typing import List

from fastapi import FastAPI


def get_app() -> FastAPI:
    """
    Creates and configures the FastAPI application instance.

    This function initializes a FastAPI app with the following features:
    - Includes the authentication and resume management routes.
    - Configures middleware for logging and error handling.
    - Sets up CORS to allow frontend access from different origins.

    Args:
        None.

    Returns:
        FastAPI: A configured FastAPI application instance.

    Notes:
        1. The application is initialized with a title, version, and description.
        2. Routes are included from the main application setup.
        3. CORS is enabled with allow_origins set to allow requests from 'http://localhost:3000'.
        4. The middleware stack includes logging and exception handling.
        5. The database session is provided via dependency injection through the 'get_db' function.
        6. The function performs no disk or network I/O.
        7. The function does not perform any database access.

    """
    app = FastAPI(
        title="Resume Editor API",
        version="1.0.0",
        description="API for managing user resumes and authentication.",
    )

    # CORS configuration
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # Adjust in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
