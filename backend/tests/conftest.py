"""
pytest configuration and shared fixtures for the backend test suite.

Any fixture defined here is available to all test modules without an import.
"""

from __future__ import annotations

import os


# ---------------------------------------------------------------------------
# Ensure a minimal .env is present so Settings() doesn't raise on import
# during test collection. Real env vars take precedence over these defaults.
# ---------------------------------------------------------------------------

os.environ.setdefault("ENV", "test")
os.environ.setdefault("ENABLE_DOCS", "true")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("GOOGLE_API_KEY", "")  # blank = AI disabled in tests
