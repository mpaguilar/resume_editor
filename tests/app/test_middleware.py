import jwt
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from resume_editor.app.core.config import get_settings
from resume_editor.app.core.security import create_access_token
from resume_editor.app.middleware import refresh_session_middleware


def create_test_app() -> FastAPI:
    """Create a test FastAPI app with the middleware."""
    app = FastAPI()
    app.add_middleware(BaseHTTPMiddleware, dispatch=refresh_session_middleware)

    @app.get("/")
    async def read_root(request: Request):
        return Response("Hello World")

    return app


def test_refresh_on_valid_token():
    """
    Test that a valid token is refreshed and a new one is set in the cookie.
    """
    app = create_test_app()
    client = TestClient(app)
    settings = get_settings()

    # Create a valid token
    username = "testuser"
    token = create_access_token(data={"sub": username}, settings=settings)

    # Make a request with the valid token in cookies
    client.cookies = {"access_token": token}
    response = client.get("/")

    # Check that the response is successful
    assert response.status_code == 200

    # Check that a new token was set in the cookies
    assert "access_token" in response.cookies
    new_token = response.cookies["access_token"]
    assert new_token is not None

    # Verify the new token
    payload = jwt.decode(new_token, settings.secret_key, algorithms=[settings.algorithm])
    assert payload["sub"] == username
    assert payload["exp"] > datetime.now(timezone.utc).timestamp()


def test_no_refresh_on_missing_token():
    """
    Test that no token is set if no token is provided.
    """
    app = create_test_app()
    client = TestClient(app)

    # Make a request without a token
    response = client.get("/")

    # Check that the response is successful
    assert response.status_code == 200

    # Check that no new token was set in the cookies
    assert "access_token" not in response.cookies


def test_no_refresh_on_invalid_token():
    """
    Test that no new token is set if an invalid token is provided.
    """
    app = create_test_app()
    client = TestClient(app)

    # Make a request with an invalid token
    client.cookies = {"access_token": "invalidtoken"}
    response = client.get("/")

    # Check that the response is successful
    assert response.status_code == 200

    # Check that no new token was set in the cookies
    assert "access_token" not in response.cookies


def test_refresh_preserves_impersonator_claim():
    """
    Test that the 'impersonator' claim is preserved when refreshing a token.
    """
    app = create_test_app()
    client = TestClient(app)
    settings = get_settings()

    username = "impersonated_user"
    admin_user = "admin"

    token = create_access_token(
        data={"sub": username}, settings=settings, impersonator=admin_user
    )

    client.cookies = {"access_token": token}
    response = client.get("/")

    assert response.status_code == 200
    assert "access_token" in response.cookies
    new_token = response.cookies["access_token"]
    assert new_token is not None

    # Verify the new token contains both sub and impersonator
    payload = jwt.decode(new_token, settings.secret_key, algorithms=[settings.algorithm])
    assert payload["sub"] == username
    assert payload["impersonator"] == admin_user
    assert payload["exp"] > datetime.now(timezone.utc).timestamp()


def test_no_refresh_on_valid_token_without_sub():
    """
    Test that no refresh occurs for a valid token that is missing the 'sub' claim.
    """
    app = create_test_app()
    client = TestClient(app)
    settings = get_settings()

    # Create a valid token with no 'sub' claim
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {"exp": expire, "some_other_claim": "value"}
    token = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    client.cookies = {"access_token": token}
    response = client.get("/")

    assert response.status_code == 200
    assert "access_token" not in response.cookies
