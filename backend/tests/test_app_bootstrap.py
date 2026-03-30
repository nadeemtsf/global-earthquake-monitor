"""
Smoke tests for the FastAPI application bootstrap.

Verifies that:
  - The application starts without errors.
  - GET /health returns 200 with the expected JSON shape.
  - The three /api/v1/* route groups are registered and reachable.
  - CORS headers are present for an allowed origin.

These tests intentionally stay at the scaffold/smoke level. Full router
tests land in later issues as the endpoints are implemented.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Module-scoped TestClient so the app is only created once per module."""
    return TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_shape(client: TestClient) -> None:
    data = client.get("/health").json()
    assert data["status"] == "ok"
    assert "env" in data
    assert "version" in data
    assert "timestamp" in data


# ---------------------------------------------------------------------------
# Router registration — endpoints exist (even if 501)
# ---------------------------------------------------------------------------


def test_earthquakes_route_registered(client: TestClient) -> None:
    response = client.get("/api/v1/earthquakes")
    # 501 means the route is registered and matched — not 404
    assert response.status_code != 404, "Earthquakes route should be registered."


def test_earthquakes_summary_route_registered(client: TestClient) -> None:
    response = client.get("/api/v1/earthquakes/summary")
    assert response.status_code != 404


def test_chat_route_registered(client: TestClient) -> None:
    response = client.post("/api/v1/chat", json={"message": "hello"})
    assert response.status_code != 404


def test_export_xml_route_registered(client: TestClient) -> None:
    response = client.get("/api/v1/export/xml")
    assert response.status_code != 404


def test_export_csv_route_registered(client: TestClient) -> None:
    response = client.get("/api/v1/export/csv")
    assert response.status_code != 404


def test_export_pdf_route_registered(client: TestClient) -> None:
    response = client.get("/api/v1/export/pdf")
    assert response.status_code != 404


# ---------------------------------------------------------------------------
# CORS headers
# ---------------------------------------------------------------------------


def test_cors_header_present_for_allowed_origin(client: TestClient) -> None:
    """OPTIONS pre-flight from the local React dev server should get CORS headers."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    # The server should echo back the allow-origin header
    assert "access-control-allow-origin" in response.headers


# ---------------------------------------------------------------------------
# Settings sanity
# ---------------------------------------------------------------------------


def test_settings_fields_are_populated() -> None:
    from app.core.config import settings

    assert settings.PROJECT_NAME
    assert settings.API_VERSION
    assert settings.USGS_API_BASE
    assert settings.GDACS_RSS_URL
    assert settings.CACHE_TTL_SECONDS > 0
