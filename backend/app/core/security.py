"""
API key verification for the Global Earthquake Monitor backend.

Authentication strategy
-----------------------
Requests must supply the API key via the ``X-API-Key`` header.  The value is
compared against the ``API_KEY`` setting using a constant-time comparison to
resist timing attacks.

Development bypass
------------------
When ``ENV`` is ``"development"`` **and** ``API_KEY_ENABLED`` is ``False``
(the default for the provided ``.env.example``), the key check is skipped
entirely.  This lets the local React dev server (Vite on port 5173) call the
API without configuring a key.

Production
----------
Set ``API_KEY_ENABLED=true`` and a non-empty ``API_KEY`` in the deployment
environment to enforce key verification on every request to protected routes.

Usage in a router
-----------------
::

    from fastapi import Depends
    from app.core.security import require_api_key

    @router.get("/protected")
    def protected_route(key: str = Depends(require_api_key)):
        ...
"""

from __future__ import annotations

import hmac
import logging

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import Settings
from app.core.dependencies import get_settings

logger = logging.getLogger(__name__)

# FastAPI will extract this header automatically and surface a 403 (not 422)
# when the header is absent and auto_error=True.
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _constant_time_equal(a: str, b: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    return hmac.compare_digest(a.encode(), b.encode())


def require_api_key(
    provided_key: str | None = Security(_api_key_header),
    cfg: Settings = Depends(get_settings),
) -> str | None:
    """FastAPI dependency that enforces API key authentication.

    Returns the provided key string (or ``None`` in dev bypass mode) so that
    callers can log which key was used if needed.

    Raises:
        HTTPException 401: if the key is absent when enforcement is active.
        HTTPException 403: if the key is present but does not match.
    """
    if not cfg.API_KEY_ENABLED:
        # Development bypass — log once per request so it is visible in logs
        logger.debug(
            "API key enforcement disabled (ENV=%s, API_KEY_ENABLED=False).",
            cfg.ENV,
        )
        return None

    if not provided_key:
        logger.warning("Rejected request: missing X-API-Key header.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key.  Supply the X-API-Key request header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    expected = cfg.API_KEY or ""
    if not expected:
        # Misconfiguration guard: enforcement enabled but no key configured.
        logger.error(
            "API_KEY_ENABLED=true but API_KEY is not set — rejecting all requests."
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key verification is misconfigured on the server.",
        )

    if not _constant_time_equal(provided_key, expected):
        logger.warning("Rejected request: invalid X-API-Key value.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    logger.debug("Request authenticated via X-API-Key.")
    return provided_key
