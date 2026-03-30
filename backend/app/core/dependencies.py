"""
Shared FastAPI dependency providers.

Dependency functions declared here are injected into route handlers via
FastAPI's Depends() mechanism. This keeps service construction out of
individual routers and makes unit testing straightforward — tests can
override any dependency via app.dependency_overrides.

Usage in a router:
    from fastapi import Depends
    from app.core.dependencies import get_settings

    @router.get("/example")
    def example(cfg: Settings = Depends(get_settings)):
        return {"env": cfg.ENV}
"""

from __future__ import annotations

from app.core.config import Settings, settings


def get_settings() -> Settings:
    """Return the application settings singleton.

    Injecting settings through Depends() rather than importing the module-level
    singleton directly makes it trivial to swap out settings in tests.
    """
    return settings
