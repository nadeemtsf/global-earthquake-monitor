"""
In-memory sliding-window rate limiter for the Global Earthquake Monitor API.

Design
------
The limiter is implemented as a pure-Python ASGI middleware (no Redis or
third-party dependency required).  It stores per-IP request timestamps in a
``collections.deque`` and enforces a configurable sliding window.

IP buckets are held in a ``cachetools.TTLCache`` so that stale entries for
IPs that have stopped sending requests are automatically evicted, preventing
unbounded memory growth under high-cardinality traffic (e.g. rotating IPs,
DDoS).

Configuration
-------------
All values come from ``app.core.config.Settings``:

``RATE_LIMIT_REQUESTS``
    Maximum number of requests allowed within the window.  Default: 60.

``RATE_LIMIT_WINDOW_SECONDS``
    Duration of the sliding window in seconds.  Default: 60 (one minute).

``RATE_LIMIT_ENABLED``
    Set to ``False`` to disable limiting entirely (useful in tests or when
    an upstream proxy/CDN already handles rate-limiting).  Default: ``True``.

Exempted paths
--------------
``/health`` and ``/docs``-family paths are excluded from rate limiting so
that health checks and documentation browsing are never blocked.

Client identification
---------------------
The client IP is derived from the ``X-Forwarded-For`` header (first entry) if
present, falling back to the direct connection address.  This is correct for
deployments behind a single trusted reverse proxy; update the extraction logic
if your deployment uses multiple proxy layers.

Thread safety
-------------
The ``threading.Lock`` guards the shared ``_buckets`` cache.  This is safe for
Uvicorn's single-process mode.  In a multi-worker deployment use an external
store (e.g. Redis) instead.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from typing import TYPE_CHECKING

from cachetools import TTLCache
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

if TYPE_CHECKING:
    from app.core.config import Settings

from app.core.config import settings as _default_settings

logger = logging.getLogger(__name__)

# Paths that are never subject to rate limiting
_EXEMPT_PREFIXES = ("/health", "/docs", "/redoc", "/openapi.json")


def _client_ip(request: Request) -> str:
    """Extract the best-effort client IP from the request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For: <client>, <proxy1>, <proxy2>
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate-limit middleware.

    Attach to a FastAPI/Starlette application via ``add_middleware``:

        app.add_middleware(RateLimitMiddleware)

    The middleware reads its configuration from the module-level
    ``app.core.config.settings`` singleton at construction time so that test
    overrides applied before the middleware is instantiated take effect.
    """

    def __init__(self, app: ASGIApp, settings: Settings | None = None) -> None:
        super().__init__(app)
        cfg = settings if settings is not None else _default_settings
        self._enabled: bool = cfg.RATE_LIMIT_ENABLED
        self._max_requests: int = cfg.RATE_LIMIT_REQUESTS
        self._window: float = float(cfg.RATE_LIMIT_WINDOW_SECONDS)
        # Auto-expiring bucket store: IPs that stop sending requests are
        # evicted after 2× the window, preventing unbounded memory growth.
        self._buckets: TTLCache[str, deque[float]] = TTLCache(
            maxsize=10_000,
            ttl=self._window * 2,
        )
        self._lock = threading.Lock()
        logger.info(
            "RateLimitMiddleware initialised — enabled=%s max=%d window=%ds",
            self._enabled,
            self._max_requests,
            self._window,
        )

    def _is_exempt(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in _EXEMPT_PREFIXES)

    def _check_and_record(self, client_ip: str) -> tuple[bool, int]:
        """Record a request and check whether the limit is exceeded.

        Returns:
            (allowed, remaining) where ``allowed`` is True if the request
            should proceed and ``remaining`` is the number of requests left in
            the current window.
        """
        now = time.monotonic()
        window_start = now - self._window

        with self._lock:
            bucket = self._buckets.get(client_ip)
            if bucket is None:
                bucket = deque()

            # Evict timestamps that have fallen outside the window
            while bucket and bucket[0] <= window_start:
                bucket.popleft()

            count = len(bucket)
            if count >= self._max_requests:
                remaining = 0
                allowed = False
            else:
                bucket.append(now)
                remaining = self._max_requests - count - 1
                allowed = True

            # Re-insert to refresh the TTL expiry on every access
            self._buckets[client_ip] = bucket

        return allowed, remaining

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        if not self._enabled or self._is_exempt(request.url.path):
            return await call_next(request)

        client_ip = _client_ip(request)
        allowed, remaining = self._check_and_record(client_ip)

        if not allowed:
            logger.warning(
                "Rate limit exceeded — client=%s path=%s",
                client_ip,
                request.url.path,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        "Too many requests.  "
                        f"Limit: {self._max_requests} requests per "
                        f"{int(self._window)} seconds."
                    ),
                    "type": "rate_limit_exceeded",
                },
                headers={
                    "Retry-After": str(int(self._window)),
                    "X-RateLimit-Limit": str(self._max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Window": str(int(self._window)),
                },
            )

        response: Response = await call_next(request)
        # Inform clients of their remaining quota via response headers
        response.headers["X-RateLimit-Limit"] = str(self._max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(int(self._window))
        return response
