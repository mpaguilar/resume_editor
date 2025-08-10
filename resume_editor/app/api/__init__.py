"""This module initializes the API endpoints for the resume editor application.

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
