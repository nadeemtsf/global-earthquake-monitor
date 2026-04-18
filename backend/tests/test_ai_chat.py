"""Tests for the AI chat endpoint (POST /api/v1/chat).

These tests mock the external Gemini SDK (google.generativeai) so they can
run deterministically without network access.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient


def _make_client_with_settings(custom_settings):
    from app.core.dependencies import get_settings
    from app.main import create_app

    application = create_app(cfg=custom_settings)
    application.dependency_overrides[get_settings] = lambda: custom_settings
    return TestClient(application, raise_server_exceptions=False)


async def _mock_get_earthquakes_with_event(event):
    """Return an async mock for get_earthquakes that yields a single event."""
    async def _mock(self, *a, **kw):
        return [event]
    return _mock


def test_chat_success_parses_actions(monkeypatch) -> None:
    """When Gemini returns actionable [[...]] tags they should be parsed."""
    from app.schemas.earthquakes import EarthquakeEvent
    from app.core.config import Settings

    event = EarthquakeEvent(
        id="ev1",
        title="Test Quake",
        main_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        magnitude=5.5,
        magnitude_type="Mw",
        depth_km=10.0,
        latitude=0.0,
        longitude=0.0,
        place="Somewhere",
        country="Nowhere",
        alert_level="Yellow",
        alert_score=1.0,
        tsunami=0,
        felt=0,
        status="automatic",
        source="USGS",
        link="http://example",
    )

    # Mock pipeline — must return a coroutine since get_earthquakes is async
    async def mock_get_earthquakes(self, *a, **kw):
        return [event]

    monkeypatch.setattr(
        "app.services.xml_pipeline.XMLPipelineService.get_earthquakes",
        mock_get_earthquakes,
    )

    class DummyResponse:
        def __init__(self, text: str):
            self.text = text

    class DummyModel:
        def __init__(self, name: str):
            self.name = name

        def generate_content(self, prompt: str):
            return DummyResponse(
                "Top events found.\n[[NAVIGATE: Overview]]\n[[SET_DATE: 2024-01-01, 2024-01-02]]"
            )

    monkeypatch.setattr("app.services.ai.genai.GenerativeModel", DummyModel)

    custom = Settings(GOOGLE_API_KEY="test-key", XSLT_DIR="transforms", CACHE_DIR="backend/.cache")
    client = _make_client_with_settings(custom)

    payload = {
        "message": "Show me the biggest quakes",
        "history": [],
        "start_date": "2024-01-01",
        "end_date": "2024-01-02",
        "min_magnitude": 4.5,
        "source": "USGS",
    }

    r = client.post("/api/v1/chat", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "response" in data
    assert "suggested_actions" in data
    types = {a["type"] for a in data["suggested_actions"]}
    assert "NAVIGATE" in types
    assert "SET_DATE" in types


def test_chat_quota_exhaustion_returns_429(monkeypatch) -> None:
    """If all models raise quota errors the endpoint should return 429."""
    from app.core.config import Settings

    async def mock_get_earthquakes(self, *a, **kw):
        return []

    monkeypatch.setattr(
        "app.services.xml_pipeline.XMLPipelineService.get_earthquakes",
        mock_get_earthquakes,
    )

    class FailModel:
        def __init__(self, name: str):
            self.name = name

        def generate_content(self, prompt: str):
            raise Exception("429 Too Many Requests")

    monkeypatch.setattr("app.services.ai.genai.GenerativeModel", FailModel)

    custom = Settings(GOOGLE_API_KEY="test-key", XSLT_DIR="transforms", CACHE_DIR="backend/.cache")
    client = _make_client_with_settings(custom)

    payload = {"message": "Anything", "history": []}
    r = client.post("/api/v1/chat", json=payload)
    assert r.status_code == 429
