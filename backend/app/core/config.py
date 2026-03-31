"""
Structured settings management for the Global Earthquake Monitor backend.

All runtime configuration is read from environment variables (or a .env file
loaded by python-dotenv). Pydantic's BaseSettings handles parsing, type
coercion, and validation. Sensitive values must never be committed — see
.env.example for the required keys.

Security settings added in issue #09
-------------------------------------
``API_KEY``
    Shared secret that callers must supply via the ``X-API-Key`` header.  Leave
    blank to disable without also setting ``API_KEY_ENABLED=false``.

``API_KEY_ENABLED``
    Set to ``False`` (the default) to skip key checking entirely.  Recommended
    for local React development so Vite can call the API without extra config.
    Set to ``True`` in staging/production.

``RATE_LIMIT_ENABLED``
    Toggle the sliding-window rate limiter on/off.

``RATE_LIMIT_REQUESTS``
    Maximum allowed requests per ``RATE_LIMIT_WINDOW_SECONDS``.

``RATE_LIMIT_WINDOW_SECONDS``
    Length of the rate-limit sliding window in seconds.

Usage:
    from app.core.config import settings

    print(settings.USGS_API_BASE)
    print(settings.CORS_ALLOWED_ORIGINS)
"""

from __future__ import annotations

from typing import List

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application metadata
    # ------------------------------------------------------------------

    PROJECT_NAME: str = "Global Earthquake Monitor API"
    API_VERSION: str = "0.1.0"
    ENV: str = Field("development", description="Runtime environment: development | staging | production")
    ENABLE_DOCS: bool = Field(
        True,
        description="Expose /docs, /redoc, and /openapi.json. Set False in production.",
    )

    # ------------------------------------------------------------------
    # CORS — comma-separated origins in env, parsed into a list here
    # ------------------------------------------------------------------

    CORS_ALLOWED_ORIGINS_STR: str = Field(
        "http://localhost:5173,http://localhost:3000",
        alias="CORS_ALLOWED_ORIGINS",
        description=(
            "Comma-separated list of allowed CORS origins for the React frontend. "
            "Example: http://localhost:5173,https://your-app.vercel.app"
        ),
    )

    @property
    def CORS_ALLOWED_ORIGINS(self) -> List[str]:  # noqa: N802
        """Parse the raw comma-separated string into a validated list."""
        return [o.strip() for o in self.CORS_ALLOWED_ORIGINS_STR.split(",") if o.strip()]

    # ------------------------------------------------------------------
    # USGS provider settings
    # ------------------------------------------------------------------

    USGS_API_BASE: AnyHttpUrl = Field(  # type: ignore[assignment]
        "https://earthquake.usgs.gov/fdsnws/event/1/query",
        description="Base URL for the USGS FDSN Web Services earthquake query endpoint.",
    )

    # ------------------------------------------------------------------
    # GDACS provider settings
    # ------------------------------------------------------------------

    GDACS_RSS_URL: AnyHttpUrl = Field(  # type: ignore[assignment]
        "https://www.gdacs.org/xml/rss.xml",
        description="GDACS RSS/XML feed URL.",
    )

    # ------------------------------------------------------------------
    # Cache settings
    # ------------------------------------------------------------------

    CACHE_TTL_SECONDS: int = Field(
        600,
        description="Time-to-live in seconds for in-memory provider cache entries.",
    )
    CACHE_DIR: str = Field(
        ".cache",
        description="Directory used for CSV and XML on-disk file caches.",
    )

    # ------------------------------------------------------------------
    # AI / Gemini settings
    # ------------------------------------------------------------------

    GOOGLE_API_KEY: str | None = Field(
        None,
        description="Google Gemini API key used by the SeismicAI chat service.",
    )

    # ------------------------------------------------------------------
    # Data pipeline settings
    # ------------------------------------------------------------------

    DEFAULT_MIN_MAGNITUDE: float = Field(
        2.5,
        description="Default minimum magnitude for earthquake queries.",
    )
    XSLT_DIR: str = Field(
        "transforms",
        description=(
            "Path to the top-level transforms/ directory that contains the XSLT "
            "stylesheets used in the XML canonicalization pipeline."
        ),
    )

    # ------------------------------------------------------------------
    # Security — API key authentication (issue #09)
    # ------------------------------------------------------------------

    API_KEY: str | None = Field(
        None,
        description=(
            "Shared API key that clients must supply via the X-API-Key header. "
            "Only enforced when API_KEY_ENABLED=true."
        ),
    )
    API_KEY_ENABLED: bool = Field(
        False,
        description=(
            "Enable X-API-Key enforcement on public endpoints.  "
            "Defaults to False so local React development (Vite) works without "
            "extra configuration.  Set True in staging and production."
        ),
    )

    # ------------------------------------------------------------------
    # Rate limiting (issue #09)
    # ------------------------------------------------------------------

    RATE_LIMIT_ENABLED: bool = Field(
        True,
        description="Enable sliding-window rate limiting on public API endpoints.",
    )
    RATE_LIMIT_REQUESTS: int = Field(
        60,
        ge=1,
        description="Maximum requests allowed within RATE_LIMIT_WINDOW_SECONDS.",
    )
    RATE_LIMIT_WINDOW_SECONDS: int = Field(
        60,
        ge=1,
        description="Duration of the rate-limit sliding window in seconds.",
    )

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    LOG_LEVEL: str = Field(
        "INFO",
        description="Root logging level: DEBUG | INFO | WARNING | ERROR | CRITICAL.",
    )


# Module-level singleton — import this everywhere instead of re-instantiating.
settings = Settings()
