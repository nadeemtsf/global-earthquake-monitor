"""
Pydantic models for earthquake events and dataset summaries.

These schemas define the "frozen" API contracts for the /earthquakes
endpoints, derived from the canonicalized XML pipeline.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class EarthquakeEvent(BaseModel):
    """Canonical representation of a single seismic event."""

    id: str = Field(..., description="Unique event identifier (source link or UUID).")
    title: str = Field(..., description="Human-readable event title.")
    main_time: datetime = Field(..., description="Primary event timestamp (UTC).")
    magnitude: float = Field(..., ge=0.0, le=10.0, description="Richter magnitude.")
    magnitude_type: str = Field("", description="Scale type (e.g., Mw, Ml).")
    depth_km: Optional[float] = Field(None, description="Event depth in kilometers.")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS84 Latitude.")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS84 Longitude.")
    place: str = Field(..., description="Textual description of the location.")
    country: str = Field("Unknown", description="Extracted country or region name.")
    alert_level: str = Field("Green", description="Categorical alert (Green, Yellow, Orange, Red).")
    alert_score: Optional[float] = Field(None, description="Numerical alert score if provided by source.")
    tsunami: int = Field(0, description="1 if a tsunami advisory was issued, 0 otherwise.")
    felt: Optional[int] = Field(None, description="Number of felt reports (USGS-specific).")
    status: str = Field("", description="Review status (e.g., automatic, manual).")
    source: str = Field(..., description="Data provider (e.g., USGS, GDACS).")
    event_type: str = Field("Earthquake", description="Event classification.")
    link: str = Field(..., description="Direct link to source detail page.")
    severity_text: Optional[str] = Field(None, description="Detailed severity description (GDACS-specific).")
    population_text: Optional[str] = Field(None, description="Impacted population description (GDACS-specific).")


class AlertLevelBreakdown(BaseModel):
    """Distribution of events by alert level."""
    green: int = 0
    yellow: int = 0
    orange: int = 0
    red: int = 0
    unknown: int = 0


class EarthquakeSummary(BaseModel):
    """Aggregate statistics for a filtered earthquake dataset."""

    total_count: int = Field(..., description="Total number of events matching filters.")
    average_magnitude: float = Field(..., description="Mean magnitude of the dataset.")
    max_magnitude: float = Field(..., description="Highest magnitude in the dataset.")
    tsunami_count: int = Field(..., description="Total number of tsunami advisories.")
    alert_breakdown: AlertLevelBreakdown = Field(..., description="Count of events per alert category.")
    top_regions: List[Dict[str, int]] = Field(
        ..., description="Top 5-10 regions by event count."
    )


class EarthquakeListResponse(BaseModel):
    """Standard wrapper for bulk earthquake listings."""
    items: List[EarthquakeEvent]
    count: int
    metadata: Dict[str, str | float | None] = Field(
        default_factory=dict, description="Query-specific metadata (offsets, filters applied)."
    )
