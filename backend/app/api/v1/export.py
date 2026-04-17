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
from datetime import datetime, timezone

import io

import pandas as pd
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.core.config import Settings
from app.core.dependencies import get_settings
from app.services.pdf_report import generate_situation_report
from app.services.xml_pipeline import XMLPipelineService

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
        "Fields map to the EarthquakeEvent JSON model. "
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
) -> Response:
    logger.info("GET /export/xml — source=%s", source)
    pipeline = XMLPipelineService()
    params = {
        "starttime": start_date,
        "endtime": end_date,
        "minmagnitude": min_magnitude,
        "orderby": "time",
    }
    if source == "BOTH":
        # Fetch both sources and concatenate their canonical XML event nodes
        from lxml import etree  # noqa: PLC0415

        root = etree.Element("EarthquakeDataset")
        for src in ("USGS", "GDACS"):
            try:
                raw_xml = pipeline.fetch_raw_xml(src, dict(params))
                canonical_xml = pipeline.apply_xslt(raw_xml, src)
                src_root = etree.fromstring(canonical_xml.encode("utf-8"))
                for node in src_root:
                    root.append(node)
            except Exception as exc:
                logger.warning("XML fetch failed for source %s: %s", src, exc)
        canonical_bytes = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8")
    else:
        raw_xml = pipeline.fetch_raw_xml(source, params)
        canonical_xml = pipeline.apply_xslt(raw_xml, source)
        canonical_bytes = canonical_xml.encode("utf-8")

    headers = {"Content-Disposition": "attachment; filename=earthquakes_canonical.xml"}
    return Response(content=canonical_bytes, media_type="application/xml", headers=headers)


@router.get(
    "/csv",
    summary="Export CSV",
    description="Return a CSV file of earthquake events matching the query parameters.",
    responses={
        200: {
            "content": {"text/csv": {}},
            "description": "Earthquake dataset as a CSV download. Field names match the EarthquakeEvent schema.",
        }
    },
)
def export_csv(
    start_date: StartDate = None,
    end_date: EndDate = None,
    min_magnitude: MinMagnitude = 2.5,
    source: DataSource = "USGS",
    cfg: Settings = Depends(get_settings),
) -> Response:
    logger.info("GET /export/csv — source=%s", source)
    pipeline = XMLPipelineService()
    events: list = []
    if source == "BOTH":
        events.extend(pipeline.get_earthquakes("USGS", start_date, end_date, min_magnitude))
        events.extend(pipeline.get_earthquakes("GDACS", start_date, end_date, min_magnitude))
    else:
        events = pipeline.get_earthquakes(source, start_date, end_date, min_magnitude)

    rows = [e.model_dump() if hasattr(e, "model_dump") else e.dict() for e in events]
    df = pd.DataFrame(rows)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    csv_bytes = buf.getvalue().encode("utf-8")

    headers = {"Content-Disposition": "attachment; filename=earthquakes.csv"}
    return Response(content=csv_bytes, media_type="text/csv", headers=headers)


@router.get(
    "/pdf",
    summary="Export PDF situation report",
    description=(
        "Generate and return a PDF situation report summarising the filtered "
        "earthquake dataset. Charts and KPIs match the EarthquakeSummary schema."
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
    alerts: list[str] | None = Query(None, description="Filter by alert level; repeatable"),
    countries: list[str] | None = Query(None, description="Filter by country; repeatable"),
    cfg: Settings = Depends(get_settings),
) -> Response:
    logger.info(
        "GET /export/pdf — source=%s start=%s end=%s min_mag=%s alerts=%s countries=%s",
        source,
        start_date,
        end_date,
        min_magnitude,
        alerts,
        countries,
    )

    # Fetch events via the XML pipeline service. Support BOTH by merging sources.
    pipeline = XMLPipelineService()
    events: list = []
    if source == "BOTH":
        events.extend(pipeline.get_earthquakes("USGS", start_date, end_date, min_magnitude))
        events.extend(pipeline.get_earthquakes("GDACS", start_date, end_date, min_magnitude))
    else:
        events = pipeline.get_earthquakes(source, start_date, end_date, min_magnitude)

    # Build filters dict for the PDF generator
    filters = {
        "source": source,
        "start_date": start_date,
        "end_date": end_date,
        "min_mag": min_magnitude,
        "alerts": alerts or [],
        "countries": countries or [],
    }

    # Generate PDF bytes
    pdf_bytes = generate_situation_report(events, filters, datetime.now(timezone.utc))

    headers = {"Content-Disposition": "attachment; filename=Situation_Report.pdf"}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
