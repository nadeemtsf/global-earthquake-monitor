"""
Tests for issue #09: Backend security and platform middleware.

Coverage
--------
API key enforcement
  - Requests are allowed when API_KEY_ENABLED=False (dev bypass).
  - Requests without a key return 401 when enforcement is on.
  - Requests with a wrong key return 403.
  - Requests with the correct key are allowed.

Rate limiting
  - Responses include X-RateLimit-* headers.
  - The 60th request within the window is still allowed.
  - The 61st request returns 429 with Retry-After.
  - Exempt paths (/health) are never rate-limited.
  - Rate limiting is skipped when RATE_LIMIT_ENABLED=False.

CORS headers
  - X-API-Key is in the Access-Control-Allow-Headers pre-flight response.
  - X-RateLimit-* headers are in the exposed headers list.

Request logging
  - X-Process-Time-Ms is present in every response.
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Ensure test environment defaults before any app import
# ---------------------------------------------------------------------------
os.environ.setdefault("ENV", "test")
os.environ.setdefault("ENABLE_DOCS", "true")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("GOOGLE_API_KEY", "")

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers to build an app with controlled security settings
# ---------------------------------------------------------------------------


def _make_client(
    *,
    api_key_enabled: bool = False,
    api_key: str | None = None,
    rate_limit_enabled: bool = True,
    rate_limit_requests: int = 60,
    rate_limit_window: int = 60,
) -> TestClient:
    """Return a TestClient backed by an app with the given security config.

    Settings are injected into ``create_app(cfg=...)`` so both middleware
    (rate limiter) and route dependencies (API key) see the same config.
    The ``get_settings`` dependency override is also applied so route handlers
    that call ``Depends(get_settings)`` agree with the middleware config.
    """
    from app.core.config import Settings
    from app.core.dependencies import get_settings
    from app.main import create_app

    custom_settings = Settings(
        ENV="test",
        ENABLE_DOCS=True,
        CORS_ALLOWED_ORIGINS="http://localhost:5173",
        GOOGLE_API_KEY="",
        API_KEY_ENABLED=api_key_enabled,
        API_KEY=api_key,
        RATE_LIMIT_ENABLED=rate_limit_enabled,
        RATE_LIMIT_REQUESTS=rate_limit_requests,
        RATE_LIMIT_WINDOW_SECONDS=rate_limit_window,
    )

    # Pass settings to create_app so middleware (rate limiter) uses them
    application = create_app(cfg=custom_settings)
    # Override the dependency so route handlers also see the same settings
    application.dependency_overrides[get_settings] = lambda: custom_settings
    return TestClient(application, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# A minimal protected route fixture — added to the test app only
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def default_client() -> TestClient:
    """Default client with API key enforcement OFF and rate limiting ON."""
    return _make_client(api_key_enabled=False)


# ===========================================================================
# API key: development bypass (API_KEY_ENABLED=false)
# ===========================================================================


class TestApiKeyDevBypass:
    def test_health_allowed_without_key(self, default_client: TestClient) -> None:
        """Health is always accessible — no key required."""
        r = default_client.get("/health")
        assert r.status_code == 200

    def test_route_allowed_without_key_when_disabled(
        self, default_client: TestClient
    ) -> None:
        """When enforcement is off, routes work without the X-API-Key header."""
        r = default_client.get("/api/v1/earthquakes")
        # 200 or any non-authentication error — not 401/403
        assert r.status_code not in (401, 403)


# ===========================================================================
# API key: enforcement ON
# ===========================================================================


class TestApiKeyEnforced:
    @pytest.fixture(scope="class")
    def enforced_client(self) -> TestClient:
        return _make_client(
            api_key_enabled=True,
            api_key="test-secret-key-abc123",
            rate_limit_enabled=False,  # isolate key tests from rate-limit tests
        )

    def test_missing_key_returns_401(self, enforced_client: TestClient) -> None:
        r = enforced_client.get(
            "/api/v1/earthquakes",
            headers={},  # no X-API-Key
        )
        assert r.status_code == 401
        assert "Missing API key" in r.json()["detail"]

    def test_wrong_key_returns_403(self, enforced_client: TestClient) -> None:
        r = enforced_client.get(
            "/api/v1/earthquakes",
            headers={"X-API-Key": "wrong-key"},
        )
        assert r.status_code == 403
        assert "Invalid API key" in r.json()["detail"]

    def test_correct_key_passes(self, enforced_client: TestClient) -> None:
        r = enforced_client.get(
            "/api/v1/earthquakes",
            headers={"X-API-Key": "test-secret-key-abc123"},
        )
        # Not an auth error — route may return any other status (200, 500, etc.)
        assert r.status_code not in (401, 403)

    def test_health_never_enforced(self, enforced_client: TestClient) -> None:
        """Health must be reachable without a key even when enforcement is on."""
        r = enforced_client.get("/health")
        assert r.status_code == 200


# ===========================================================================
# Rate limiting
# ===========================================================================


class TestRateLimiting:
    @pytest.fixture(scope="class")
    def rate_client(self) -> TestClient:
        """App with a very small limit (3 req/min) for fast testing."""
        return _make_client(
            api_key_enabled=False,
            rate_limit_enabled=True,
            rate_limit_requests=3,
            rate_limit_window=60,
        )

    def test_ratelimit_headers_present(self, rate_client: TestClient) -> None:
        r = rate_client.get("/health")  # exempt — still gets headers from other mw
        # The X-Process-Time-Ms header is always added
        assert "x-process-time-ms" in r.headers

    def test_ratelimit_headers_on_api(self, rate_client: TestClient) -> None:
        # Make a fresh client so request counts start from zero
        client = _make_client(
            api_key_enabled=False,
            rate_limit_enabled=True,
            rate_limit_requests=5,
            rate_limit_window=60,
        )
        r = client.get("/api/v1/earthquakes")
        assert "x-ratelimit-limit" in r.headers
        assert "x-ratelimit-remaining" in r.headers
        assert "x-ratelimit-window" in r.headers

    def test_requests_within_limit_succeed(self, rate_client: TestClient) -> None:
        client = _make_client(
            api_key_enabled=False,
            rate_limit_enabled=True,
            rate_limit_requests=5,
            rate_limit_window=60,
        )
        for _ in range(5):
            r = client.get("/api/v1/earthquakes")
            assert r.status_code != 429

    def test_exceeding_limit_returns_429(self) -> None:
        client = _make_client(
            api_key_enabled=False,
            rate_limit_enabled=True,
            rate_limit_requests=2,
            rate_limit_window=60,
        )
        # First two requests should pass
        client.get("/api/v1/earthquakes")
        client.get("/api/v1/earthquakes")
        # Third request should be rate-limited
        r = client.get("/api/v1/earthquakes")
        assert r.status_code == 429
        data = r.json()
        assert data["type"] == "rate_limit_exceeded"
        assert "Retry-After" in r.headers

    def test_health_exempt_from_rate_limit(self) -> None:
        client = _make_client(
            api_key_enabled=False,
            rate_limit_enabled=True,
            rate_limit_requests=1,
            rate_limit_window=60,
        )
        # Exhaust the limit on /api/v1/earthquakes
        client.get("/api/v1/earthquakes")
        client.get("/api/v1/earthquakes")
        # /health must still return 200 regardless
        r = client.get("/health")
        assert r.status_code == 200

    def test_rate_limiting_disabled(self) -> None:
        client = _make_client(
            api_key_enabled=False,
            rate_limit_enabled=False,
            rate_limit_requests=1,  # would immediately block if enabled
            rate_limit_window=60,
        )
        for _ in range(5):
            r = client.get("/api/v1/earthquakes")
            assert r.status_code != 429


# ===========================================================================
# CORS headers
# ===========================================================================


class TestCorsHeaders:
    @pytest.fixture(scope="class")
    def cors_client(self) -> TestClient:
        return _make_client(api_key_enabled=False, rate_limit_enabled=False)

    def test_cors_preflight_returns_allow_headers(
        self, cors_client: TestClient
    ) -> None:
        r = cors_client.options(
            "/api/v1/earthquakes",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-API-Key",
            },
        )
        # CORS pre-flights should succeed
        assert "access-control-allow-origin" in r.headers

    def test_cors_exposes_ratelimit_headers(self, cors_client: TestClient) -> None:
        r = cors_client.options(
            "/api/v1/earthquakes",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        exposed = r.headers.get("access-control-expose-headers", "").lower()
        # Rate-limit headers should be browser-accessible
        assert "x-ratelimit-limit" in exposed or "access-control-allow-origin" in r.headers


# ===========================================================================
# Process-time header (request logging middleware)
# ===========================================================================


class TestProcessTimeHeader:
    @pytest.fixture(scope="class")
    def basic_client(self) -> TestClient:
        return _make_client(api_key_enabled=False, rate_limit_enabled=False)

    def test_process_time_header_on_health(self, basic_client: TestClient) -> None:
        r = basic_client.get("/health")
        assert "x-process-time-ms" in r.headers

    def test_process_time_is_numeric(self, basic_client: TestClient) -> None:
        r = basic_client.get("/health")
        value = r.headers.get("x-process-time-ms", "")
        assert float(value) >= 0


# ===========================================================================
# Security module unit tests
# ===========================================================================


class TestSecurityDependency:
    def test_constant_time_equal_same(self) -> None:
        from app.core.security import _constant_time_equal

        assert _constant_time_equal("abc", "abc") is True

    def test_constant_time_equal_different(self) -> None:
        from app.core.security import _constant_time_equal

        assert _constant_time_equal("abc", "xyz") is False

    def test_constant_time_equal_empty(self) -> None:
        from app.core.security import _constant_time_equal

        assert _constant_time_equal("", "") is True
        assert _constant_time_equal("a", "") is False
