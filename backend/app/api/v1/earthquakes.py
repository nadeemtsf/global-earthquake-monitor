"""
/api/v1/earthquakes — earthquake data query endpoints.

This router provides read-only endpoints for fetching, filtering, and
summarising earthquake event data from the upstream USGS and GDACS
providers. Full implementation is delivered in a later issue (#08).

Currently scaffolded endpoints
-------------------------------
GET /api/v1/earthquakes
    Query earthquakes by date range, magnitude, source, and optional filters.
    Returns a paginated list of EarthquakeEvent models.

GET /api/v1/earthquakes/summary
    Return aggregated summary statistics (count, avg/max magnitude, tsunami
    advisory count) for the current filter set.

These handlers return placeholder 501 responses until the XML/XSLT
pipeline (issue #06) and core REST endpoint logic (issue #08) are wired in.
"""

from __future__ import annotations

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.core.config import Settings
from app.core.dependencies import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Type aliases for reusable query param annotations
# ---------------------------------------------------------------------------

StartDate = Annotated[
    str | None,
    Query(description="Start of the date range in YYYY-MM-DD format (UTC)."),
]
EndDate = Annotated[
    str | None,
    Query(description="End of the date range in YYYY-MM-DD format (UTC)."),
]
MinMagnitude = Annotated[
    float,
    Query(ge=0.0, le=10.0, description="Minimum Richter magnitude (inclusive)."),
]
DataSource = Annotated[
    Literal["USGS", "GDACS", "BOTH"],
    Query(description="Data provider. USGS (GeoJSON/QuakeML), GDACS (RSS/XML), or BOTH."),
]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get(
    "",
    summary="List earthquake events",
    description=(
        "Fetch earthquake events from the specified provider within the given date "
        "range and minimum magnitude. Responses are sourced from the canonicalized "
        "XML/XSLT pipeline. Full implementation lands in issue #08."
    ),
)
def list_earthquakes(
    start_date: StartDate = None,
    end_date: EndDate = None,
    min_magnitude: MinMagnitude = 2.5,
    source: DataSource = "USGS",
    cfg: Settings = Depends(get_settings),
) -> JSONResponse:
    logger.info(
        "GET /earthquakes — source=%s start=%s end=%s min_mag=%.1f",
        source,
        start_date,
        end_date,
        min_magnitude,
    )
    return JSONResponse(
        status_code=501,
        content={
            "detail": "Not yet implemented — see issue #08 (Build Core REST Endpoints).",
            "params": {
                "source": source,
                "start_date": start_date,
                "end_date": end_date,
                "min_magnitude": min_magnitude,
            },
        },
    )


@router.get(
    "/summary",
    summary="Earthquake dataset summary",
    description=(
        "Return aggregated statistics (total count, average/max magnitude, "
        "tsunami advisory count) for the filtered earthquake dataset."
    ),
)
def earthquake_summary(
    start_date: StartDate = None,
    end_date: EndDate = None,
    min_magnitude: MinMagnitude = 2.5,
    source: DataSource = "USGS",
    cfg: Settings = Depends(get_settings),
) -> JSONResponse:
    logger.info("GET /earthquakes/summary — source=%s", source)
    return JSONResponse(
        status_code=501,
        content={
            "detail": "Not yet implemented — see issue #08 (Build Core REST Endpoints).",
        },
    )
