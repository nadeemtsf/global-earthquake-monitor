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

from app.core.config import Settings
from app.core.dependencies import get_settings
from app.schemas.earthquakes import EarthquakeListResponse, EarthquakeSummary
from app.services.xml_pipeline import XMLPipelineService

logger = logging.getLogger(__name__)

router = APIRouter()
pipeline = XMLPipelineService()

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
    response_model=EarthquakeListResponse,
    description=(
        "Fetch earthquake events from the specified provider within the given date "
        "range and minimum magnitude. Responses are sourced from the canonicalized "
        "XML/XSLT pipeline."
    ),
)
def list_earthquakes(
    start_date: StartDate = None,
    end_date: EndDate = None,
    min_magnitude: MinMagnitude = 2.5,
    source: DataSource = "USGS",
    cfg: Settings = Depends(get_settings),
) -> dict:
    logger.info(
        "GET /earthquakes — source=%s start=%s end=%s min_mag=%.1f",
        source,
        start_date,
        end_date,
        min_magnitude,
    )
    
    # Process "BOTH" or single source
    sources = ["USGS", "GDACS"] if source == "BOTH" else [source]
    all_events = []
    
    for src in sources:
        events = pipeline.get_earthquakes(
            source=src,
            start_date=start_date,
            end_date=end_date,
            min_mag=min_magnitude,
        )
        all_events.extend(events)
        
    # Sort by time descending (newest first)
    all_events.sort(key=lambda x: x.main_time, reverse=True)
    
    return {
        "items": all_events,
        "count": len(all_events),
        "metadata": {
            "source": source,
            "start_date": start_date,
            "end_date": end_date,
            "min_magnitude": min_magnitude,
            "data_flow": "XML/XSLT -> Pydantic",
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
def earthquake_summary(
    start_date: StartDate = None,
    end_date: EndDate = None,
    min_magnitude: MinMagnitude = 2.5,
    source: DataSource = "USGS",
    cfg: Settings = Depends(get_settings),
) -> dict:
    logger.info("GET /earthquakes/summary — source=%s", source)
    
    # Reuse list logic for simplicity in this version
    # (Future optimizations would calculate stats directly on the canonical XML)
    response = list_earthquakes(start_date, end_date, min_magnitude, source, cfg)
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
        l = e.alert_level.lower()
        if l in breakdown: 
            breakdown[l] += 1
        else:
            breakdown["unknown"] += 1

    # Top regions (simplified counts)
    from collections import Counter
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
