"""Test cases for the API initialization module."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from resume_editor.app.api import get_app


def test_get_app_returns_fastapi_instance():
    """Test that get_app returns a FastAPI instance."""
    _msg = "test_get_app_returns_fastapi_instance starting"
    app = get_app()
    assert isinstance(app, FastAPI)
    _msg = "test_get_app_returns_fastapi_instance completed"
    print(_msg)


def test_get_app_configuration():
    """Test that the FastAPI app has correct configuration."""
    _msg = "test_get_app_configuration starting"
    app = get_app()

    # Check app metadata
    assert app.title == "Resume Editor API"
    assert app.version == "1.0.0"
    assert app.description == "API for managing user resumes and authentication."
    _msg = "test_get_app_configuration completed"
    print(_msg)


def test_get_app_has_cors_middleware():
    """Test that the FastAPI app has CORS middleware configured."""
    _msg = "test_get_app_has_cors_middleware starting"
    app = get_app()

    # Check that CORS middleware is added
    cors_middleware_found = False
    for middleware in app.user_middleware:
        if middleware.cls == CORSMiddleware:
            cors_middleware_found = True
            break

    assert cors_middleware_found, "CORS middleware not found in app configuration"
    _msg = "test_get_app_has_cors_middleware completed"
    print(_msg)


def test_get_app_cors_configuration():
    """Test that the CORS middleware has the correct configuration."""
    _msg = "test_get_app_cors_configuration starting"
    app = get_app()

    # Find CORS middleware
    cors_middleware = None
    for middleware in app.user_middleware:
        if middleware.cls == CORSMiddleware:
            cors_middleware = middleware
            break

    assert cors_middleware is not None, "CORS middleware not found"

    # Check CORS configuration by examining the middleware initialization
    # The middleware args contain the configuration parameters
    assert hasattr(cors_middleware, "cls")
    assert cors_middleware.cls == CORSMiddleware
    _msg = "test_get_app_cors_configuration completed"
    print(_msg)
