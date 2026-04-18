"""Tests for the export endpoints (PDF, XML, CSV).

These tests patch the XML pipeline to avoid network calls and verify that
each export endpoint returns the expected content-type, headers, and payload.
"""

from __future__ import annotations

import datetime

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.earthquakes import EarthquakeEvent


def _make_dummy_event() -> EarthquakeEvent:
    return EarthquakeEvent(
        id="test-1",
        title="Test earthquake",
        main_time=datetime.datetime(2024, 1, 1, 0, 0),
        magnitude=5.5,
        magnitude_type="Mw",
        depth_km=10.0,
        latitude=10.0,
        longitude=20.0,
        place="Test Place",
        country="Testland",
        alert_level="Yellow",
        alert_score=None,
        tsunami=0,
        felt=None,
        status="automatic",
        source="USGS",
        link="http://example.com/event/test-1",
    )


_CANONICAL_XML = b"""<?xml version='1.0' encoding='utf-8'?>
<EarthquakeDataset>
  <event>
    <id>test-1</id>
    <title>Test earthquake</title>
    <main_time>2024-01-01T00:00:00</main_time>
    <magnitude>5.5</magnitude>
    <magnitude_type>Mw</magnitude_type>
    <depth_km>10.0</depth_km>
    <latitude>10.0</latitude>
    <longitude>20.0</longitude>
    <place>Test Place</place>
    <country>Testland</country>
    <alert_level>Yellow</alert_level>
    <tsunami>0</tsunami>
    <status>automatic</status>
    <source>USGS</source>
    <link>http://example.com/event/test-1</link>
  </event>
</EarthquakeDataset>"""


def test_export_pdf_returns_pdf_and_headers(monkeypatch) -> None:
    client = TestClient(app)

    dummy = _make_dummy_event()

    async def mock_get_earthquakes(self, source, start_date, end_date, min_mag):
        return [dummy]

    monkeypatch.setattr(
        "app.services.xml_pipeline.XMLPipelineService.get_earthquakes",
        mock_get_earthquakes,
    )

    response = client.get("/api/v1/export/pdf")

    assert response.status_code == 200
    assert response.headers.get("content-type") == "application/pdf"
    cd = response.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert "Situation_Report.pdf" in cd
    assert response.content.startswith(b"%PDF")


def test_export_xml_returns_xml_and_headers(monkeypatch) -> None:
    client = TestClient(app)

    async def mock_fetch_raw_xml(self, source, params):
        return _CANONICAL_XML.decode("utf-8")

    monkeypatch.setattr(
        "app.services.xml_pipeline.XMLPipelineService.fetch_raw_xml",
        mock_fetch_raw_xml,
    )
    monkeypatch.setattr(
        "app.services.xml_pipeline.XMLPipelineService.apply_xslt",
        lambda self, raw_xml, provider: _CANONICAL_XML.decode("utf-8"),
    )

    response = client.get("/api/v1/export/xml")

    assert response.status_code == 200
    ct = response.headers.get("content-type", "")
    assert "xml" in ct
    cd = response.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert "earthquakes_canonical.xml" in cd
    assert b"<" in response.content


def test_export_csv_returns_csv_and_headers(monkeypatch) -> None:
    client = TestClient(app)

    dummy = _make_dummy_event()

    async def mock_get_earthquakes(self, source, start_date, end_date, min_mag):
        return [dummy]

    monkeypatch.setattr(
        "app.services.xml_pipeline.XMLPipelineService.get_earthquakes",
        mock_get_earthquakes,
    )

    response = client.get("/api/v1/export/csv")

    assert response.status_code == 200
    ct = response.headers.get("content-type", "")
    assert "csv" in ct or "text" in ct
    cd = response.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert "earthquakes.csv" in cd
    lines = response.content.decode("utf-8").splitlines()
    assert len(lines) >= 2
    assert "magnitude" in lines[0]
