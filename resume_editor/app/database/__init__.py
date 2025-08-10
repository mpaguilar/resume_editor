"""This module provides database configuration and session management for the application.

The module sets up the database engine and session factory, which are used to interact with the database.
It includes utilities for getting the database engine and a session local factory for creating database sessions.

Classes:
    None

Functions:
    get_engine: Returns the SQLAlchemy engine instance for the database.
    get_session_local: Returns the SQLAlchemy session factory for creating database sessions.
"""

from .database import get_engine, get_session_local

__all__ = ["get_engine", "get_session_local"]
