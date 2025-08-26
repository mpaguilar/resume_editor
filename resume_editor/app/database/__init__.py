"""This module provides database configuration and session management for the application.

The module sets up the database engine and session factory, which are used to interact with the database.
It includes utilities for getting the database engine and a session local factory for creating database sessions.

Classes:
    None

Functions:
    get_engine: Returns the SQLAlchemy engine instance for the database.

Args:
            None
        Returns:
            Engine: The SQLAlchemy engine configured to connect to the database.

Notes:
            1. Retrieves the database URL from the application settings.
            2. Creates a SQLAlchemy engine using the URL with appropriate configuration options.
            3. Returns the configured engine instance.
            4. Database access: Establishes a connection to the database using the provided URL.

    get_session_local: Returns the SQLAlchemy session factory for creating database sessions.

Args:
            None
        Returns:
            sessionmaker: A factory for creating database sessions.

Notes:
            1. Creates a session factory using the previously created engine.
            2. Configures the session to be autocommit=False and autoflush=False.
            3. Returns the session factory.
            4. Database access: The session factory can be used to create sessions that connect to the database.

"""

from .database import get_engine, get_session_local

__all__ = ["get_engine", "get_session_local"]
