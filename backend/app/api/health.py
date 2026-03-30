"""
/health endpoint — lightweight liveness probe.

Returns a 200 JSON response that confirms the API process is alive and
reports the current runtime environment. No database or external service
checks are performed here; those belong in a separate /readiness probe
if needed in production.

Route: GET /health
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    env: str
    version: str
    timestamp: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
    description=(
        "Returns 200 OK when the API process is running. "
        "Intended for load balancer health checks and CI smoke tests."
    ),
)
def health_check() -> HealthResponse:
    now_utc = datetime.now(timezone.utc).isoformat()
    logger.debug("Health check called at %s", now_utc)
    return HealthResponse(
        status="ok",
        env=settings.ENV,
        version=settings.API_VERSION,
        timestamp=now_utc,
    )
