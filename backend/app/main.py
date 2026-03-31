"""
FastAPI application entrypoint for the Global Earthquake Monitor backend.

This module creates and configures the FastAPI application instance via the
create_app() factory, registers all routers, CORS middleware, structured
exception handlers, and logging. It is the sole entry point consumed by:

    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import Settings, settings
from app.core.logging import configure_logging
from app.core.rate_limit import RateLimitMiddleware
from app.api.v1 import router as api_v1_router
from app.api.health import router as health_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

configure_logging()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown hooks)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    """Run startup and shutdown side-effects."""
    logger.info(
        "Global Earthquake Monitor API starting — environment=%s",
        settings.ENV,
    )
    yield
    logger.info("Global Earthquake Monitor API shutting down.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app(
    cfg: Settings | None = None,
) -> FastAPI:
    """Construct and return the fully configured FastAPI application.

    Args:
        cfg: Optional settings override.  When None the module-level
             ``settings`` singleton is used.  Pass a custom ``Settings``
             instance in tests to control security and rate-limit behaviour
             without altering the global singleton.
    """
    effective_cfg = cfg if cfg is not None else settings
    application = FastAPI(
        title=effective_cfg.PROJECT_NAME,
        description=(
            "REST API for the Global Earthquake Monitor. "
            "Provides earthquake data from USGS and GDACS via an XML/XSLT pipeline, "
            "AI-powered chat analysis, and structured data export."
        ),
        version=effective_cfg.API_VERSION,
        docs_url="/docs" if effective_cfg.ENABLE_DOCS else None,
        redoc_url="/redoc" if effective_cfg.ENABLE_DOCS else None,
        openapi_url="/openapi.json" if effective_cfg.ENABLE_DOCS else None,
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------
    # CORS — environment-driven allowed origins
    # ------------------------------------------------------------------
    application.add_middleware(
        CORSMiddleware,
        allow_origins=effective_cfg.CORS_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        # Explicit header allowlist: includes the X-API-Key used for auth
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-API-Key",
            "X-Requested-With",
            "Accept",
            "Origin",
        ],
        expose_headers=[
            "X-Process-Time-Ms",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Window",
        ],
    )

    # ------------------------------------------------------------------
    # Rate limiting (issue #09) — must be added *after* CORS so that
    # OPTIONS pre-flights are handled by CORS before the limiter sees them.
    # ------------------------------------------------------------------
    application.add_middleware(RateLimitMiddleware, settings=effective_cfg)

    # ------------------------------------------------------------------
    # Request timing + structured access logging middleware
    # ------------------------------------------------------------------
    @application.middleware("http")
    async def log_and_time_requests(request: Request, call_next):  # type: ignore[no-untyped-def]
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        logger.info(
            "%s %s → %s (%.2f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response

    # ------------------------------------------------------------------
    # Global exception handlers
    # ------------------------------------------------------------------
    @application.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "Unhandled exception for %s %s: %s",
            request.method,
            request.url.path,
            exc,
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal server error occurred.",
                "type": type(exc).__name__,
            },
        )

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------
    application.include_router(health_router)
    application.include_router(api_v1_router, prefix="/api/v1")

    logger.info(
        "Registered routes: %s",
        [route.path for route in application.routes],  # type: ignore[attr-defined]
    )

    return application


# ---------------------------------------------------------------------------
# Module-level app instance — consumed by uvicorn
# ---------------------------------------------------------------------------

app = create_app()
