import logging
from collections.abc import Awaitable, Callable

import jwt
from fastapi import Request
from fastapi.responses import Response

from resume_editor.app.core.config import Settings, get_settings
from resume_editor.app.core.security import create_access_token

log = logging.getLogger(__name__)


async def refresh_session_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Refreshes session token on each request.

    If a valid, unexpired access token is found in the cookies, a new token
    with a renewed expiration time is issued and set in the response cookies.
    This creates a "sliding session" for active users.

    Args:
        request (Request): The incoming request object.
        call_next: The next middleware or route handler.

    Returns:
        Response: The response from the next middleware or route handler,
                  potentially with a new session cookie.

    Notes:
        1.  Attempt to retrieve the `access_token` from the request cookies.
        2.  If a token is present, attempt to decode it.
        3.  If the token is successfully decoded, create a new token with a fresh
            expiration date, preserving the original claims (`sub`, `impersonator`).
        4.  Call `response = await call_next(request)` to pass control to the
            next handler.
        5.  If a new token was generated, set it on the `response` as a cookie.
        6.  If the token is missing, invalid, or expired, the middleware does
            nothing; subsequent auth dependencies will handle redirection or
            deny access.

    """
    log.debug("refresh_session_middleware: starting")
    new_token: str | None = None
    access_token: str | None = request.cookies.get("access_token")

    if not access_token:
        # No token, nothing to do.
        log.debug("refresh_session_middleware: no token, passing through")
        return await call_next(request)

    settings: Settings = get_settings()

    try:
        payload = jwt.decode(
            access_token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        claims_to_preserve = {
            "sub": payload.get("sub"),
            "impersonator": payload.get("impersonator"),
        }
        # Filter out None values to avoid passing them to create_access_token
        claims_to_preserve = {
            k: v for k, v in claims_to_preserve.items() if v is not None
        }

        if claims_to_preserve.get("sub"):
            new_token = create_access_token(
                data={"sub": claims_to_preserve["sub"]},
                settings=settings,
                impersonator=claims_to_preserve.get("impersonator"),
            )
            _msg = "Token refreshed."
            log.debug(_msg)

    except jwt.PyJWTError as e:
        # Token is invalid or expired. Do nothing. The get_current_user dependency
        # will handle the unauthenticated state.
        _msg = f"Token decoding failed: {e}. Letting auth dependency handle it."
        log.debug(_msg)

    response = await call_next(request)

    if new_token:
        # These cookie parameters should match what is used during login.
        response.set_cookie(
            key="access_token",
            value=new_token,
            httponly=True,
            samesite="lax",
            path="/",
            secure=False,  # Should be True in production & depend on settings
        )
        _msg = "New session token set in response cookie."
        log.debug(_msg)

    log.debug("refresh_session_middleware: returning")
    return response
