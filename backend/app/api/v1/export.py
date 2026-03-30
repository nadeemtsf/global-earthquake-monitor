"""
/api/v1/export — data export endpoints.

Provides structured data downloads in multiple formats. The XML export is
a primary deliverable of the architecture: it must return the *canonicalized*
XML (transformed via XSLT), not raw upstream XML.

Full implementation is delivered in issue #11 (Port export/report routes).
The XML pipeline itself lands in issue #06.

Currently scaffolded endpoints
-------------------------------
GET /api/v1/export/xml
    Return canonical XSLT-transformed earthquake XML for the current dataset.

GET /api/v1/export/csv
    Return a CSV download of the filtered earthquake dataset.

GET /api/v1/export/pdf
    Generate and return a PDF situation report for the filtered dataset.
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

# Reusable query param annotations (mirrors earthquakes.py for consistency)
StartDate = Annotated[str | None, Query(description="Start date (YYYY-MM-DD, UTC).")]
EndDate = Annotated[str | None, Query(description="End date (YYYY-MM-DD, UTC).")]
MinMagnitude = Annotated[float, Query(ge=0.0, le=10.0, description="Minimum magnitude.")]
DataSource = Annotated[
    Literal["USGS", "GDACS", "BOTH"],
    Query(description="Data provider: USGS, GDACS, or BOTH."),
]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get(
    "/xml",
    summary="Export canonical XML",
    description=(
        "Return XSLT-transformed canonical earthquake XML. "
        "This route must emit the *canonicalized* schema produced by the XSLT "
        "pipeline in transforms/, never the raw upstream QuakeML or RSS XML. "
        "Full implementation lands in issue #11 / pipeline wired in issue #06."
    ),
    responses={
        200: {
            "content": {"application/xml": {}},
            "description": "Canonical earthquake XML (XSLT-transformed).",
        }
    },
)
def export_xml(
    start_date: StartDate = None,
    end_date: EndDate = None,
    min_magnitude: MinMagnitude = 2.5,
    source: DataSource = "USGS",
    cfg: Settings = Depends(get_settings),
) -> JSONResponse:
    logger.info("GET /export/xml — source=%s", source)
    return JSONResponse(
        status_code=501,
        content={
            "detail": (
                "Not yet implemented — XML/XSLT pipeline lands in issue #06; "
                "export endpoint wired in issue #11."
            ),
        },
    )


@router.get(
    "/csv",
    summary="Export CSV",
    description="Return a CSV file of earthquake events matching the query parameters.",
    responses={
        200: {
            "content": {"text/csv": {}},
            "description": "Earthquake dataset as a CSV download.",
        }
    },
)
def export_csv(
    start_date: StartDate = None,
    end_date: EndDate = None,
    min_magnitude: MinMagnitude = 2.5,
    source: DataSource = "USGS",
    cfg: Settings = Depends(get_settings),
) -> JSONResponse:
    logger.info("GET /export/csv — source=%s", source)
    return JSONResponse(
        status_code=501,
        content={
            "detail": "Not yet implemented — see issue #11 (Port Export/Report Routes).",
        },
    )


@router.get(
    "/pdf",
    summary="Export PDF situation report",
    description=(
        "Generate and return a PDF situation report summarising the filtered "
        "earthquake dataset. Mirrors the existing Streamlit PDF generator."
    ),
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF situation report download.",
        }
    },
)
def export_pdf(
    start_date: StartDate = None,
    end_date: EndDate = None,
    min_magnitude: MinMagnitude = 2.5,
    source: DataSource = "USGS",
    cfg: Settings = Depends(get_settings),
) -> JSONResponse:
    logger.info("GET /export/pdf — source=%s", source)
    return JSONResponse(
        status_code=501,
        content={
            "detail": "Not yet implemented — see issue #11 (Port Export/Report Routes).",
        },
    )
