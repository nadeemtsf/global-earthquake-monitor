"""
Shared FastAPI dependency providers.

Dependency functions declared here are injected into route handlers via
FastAPI's Depends() mechanism. This keeps service construction out of
individual routers and makes unit testing straightforward — tests can
override any dependency via app.dependency_overrides.

Usage in a router:
    from fastapi import Depends
    from app.core.dependencies import get_settings, get_pipeline

    @router.get("/example")
    async def example(pipeline = Depends(get_pipeline)):
        events = await pipeline.get_earthquakes()
"""

from __future__ import annotations

from app.core.config import Settings, settings
from app.services.xml_pipeline import XMLPipelineService, get_compiled_xslt


def get_settings() -> Settings:
    """Return the application settings singleton.

    Injecting settings through Depends() rather than importing the module-level
    singleton directly makes it trivial to swap out settings in tests.
    """
    return settings


def get_pipeline() -> XMLPipelineService:
    """Return an XMLPipelineService wired to the pre-compiled XSLT transforms.

    The compiled_xslt dict is populated once during the app lifespan startup
    and shared across every request for the lifetime of the process.
    """
    return XMLPipelineService(compiled_xslt=get_compiled_xslt())
