"""
/api/v1/earthquakes — earthquake data query endpoints.

This router provides read-only endpoints for fetching, filtering, and
summarising earthquake event data from the upstream USGS and GDACS
providers.

GET /api/v1/earthquakes
    Query earthquakes by date range, magnitude, source, and optional filters.
    Returns a paginated list of EarthquakeEvent models.

GET /api/v1/earthquakes/summary
    Return aggregated summary statistics (count, avg/max magnitude, tsunami
    advisory count) for the current filter set.
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.core.config import Settings
from app.core.dependencies import get_pipeline, get_settings
from app.schemas.earthquakes import EarthquakeListResponse, EarthquakeSummary
from app.services.xml_pipeline import XMLPipelineService

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
Limit = Annotated[
    int,
    Query(ge=1, le=500, description="Maximum events to return (1–500). Default 100."),
]
Offset = Annotated[
    int,
    Query(ge=0, description="Zero-based index of the first event to return."),
]
Search = Annotated[
    str | None,
    Query(description="Case-insensitive substring search on the 'place' field."),
]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get(
    "",
    summary="List earthquake events",
    response_model=EarthquakeListResponse,
    description=(
        "Fetch earthquake events from the specified provider within the given date "
        "range and minimum magnitude. Supports server-side pagination (limit/offset), "
        "alert-level filtering, country filtering, and place-name search. "
        "Responses are sourced from the canonicalized XML/XSLT pipeline. "
        "Server-side pagination is recommended for datasets exceeding ~500 events "
        "where loading the full result into the browser would degrade render performance."
    ),
)
async def list_earthquakes(
    start_date: StartDate = None,
    end_date: EndDate = None,
    min_magnitude: MinMagnitude = 2.5,
    source: DataSource = "USGS",
    limit: Limit = 100,
    offset: Offset = 0,
    search: Search = None,
    alert_levels: list[str] | None = Query(None, description="Filter by alert level (repeatable): Green, Yellow, Orange, Red."),
    countries: list[str] | None = Query(None, description="Filter by country name (repeatable)."),
    cfg: Settings = Depends(get_settings),
    pipeline: XMLPipelineService = Depends(get_pipeline),
) -> dict:
    logger.info(
        "GET /earthquakes — source=%s start=%s end=%s min_mag=%.1f limit=%d offset=%d",
        source, start_date, end_date, min_magnitude, limit, offset,
    )

    # Fetch from upstream via XML/XSLT pipeline.
    # get_earthquakes() returns a pre-sorted (newest-first), cached list.
    # For BOTH sources we merge two sorted lists and re-sort once.
    sources = ["USGS", "GDACS"] if source == "BOTH" else [source]
    all_events: list = []
    for src in sources:
        all_events.extend(
            await pipeline.get_earthquakes(
                source=src,
                start_date=start_date,
                end_date=end_date,
                min_mag=min_magnitude,
            )
        )

    if len(sources) > 1:
        all_events.sort(key=lambda x: x.main_time, reverse=True)

    # Server-side filters
    if alert_levels:
        normalized = {a.lower() for a in alert_levels}
        all_events = [e for e in all_events if e.alert_level.lower() in normalized]

    if countries:
        normalized_c = {c.lower() for c in countries}
        all_events = [e for e in all_events if e.country.lower() in normalized_c]

    if search:
        needle = search.lower()
        all_events = [e for e in all_events if needle in e.place.lower()]

    total = len(all_events)
    page = all_events[offset: offset + limit]

    return {
        "items": page,
        "count": len(page),
        "total": total,
        "offset": offset,
        "limit": limit,
        "metadata": {
            "source": source,
            "start_date": start_date,
            "end_date": end_date,
            "min_magnitude": min_magnitude,
            "data_flow": "XML/XSLT -> Pydantic",
            "server_side_threshold": "500",
        },
    }


@router.get(
    "/summary",
    summary="Earthquake dataset summary",
    response_model=EarthquakeSummary,
    description=(
        "Return aggregated statistics (total count, average/max magnitude, "
        "tsunami advisory count) for the filtered earthquake dataset."
    ),
)
async def earthquake_summary(
    start_date: StartDate = None,
    end_date: EndDate = None,
    min_magnitude: MinMagnitude = 2.5,
    source: DataSource = "USGS",
    cfg: Settings = Depends(get_settings),
    pipeline: XMLPipelineService = Depends(get_pipeline),
) -> dict:
    logger.info("GET /earthquakes/summary — source=%s", source)

    # Fetch the full unfiltered page to compute accurate summary stats
    response = await list_earthquakes(
        start_date=start_date,
        end_date=end_date,
        min_magnitude=min_magnitude,
        source=source,
        limit=500,
        offset=0,
        search=None,
        alert_levels=None,
        countries=None,
        cfg=cfg,
        pipeline=pipeline,
    )
    events = response["items"]

    if not events:
        return {
            "total_count": 0,
            "average_magnitude": 0.0,
            "max_magnitude": 0.0,
            "tsunami_count": 0,
            "alert_breakdown": {"green": 0, "yellow": 0, "orange": 0, "red": 0, "unknown": 0},
            "top_regions": [],
        }

    mags = [e.magnitude for e in events]
    tsunamis = sum(1 for e in events if e.tsunami == 1)

    # Alert breakdown
    breakdown = {"green": 0, "yellow": 0, "orange": 0, "red": 0, "unknown": 0}
    for e in events:
        level_str = e.alert_level.lower()
        if level_str in breakdown:
            breakdown[level_str] += 1
        else:
            breakdown["unknown"] += 1

    regions = Counter(e.country for e in events).most_common(5)
    top_regions = [{"region": r, "count": c} for r, c in regions]

    return {
        "total_count": len(events),
        "average_magnitude": sum(mags) / len(mags),
        "max_magnitude": max(mags),
        "tsunami_count": tsunamis,
        "alert_breakdown": breakdown,
        "top_regions": top_regions,
    }
