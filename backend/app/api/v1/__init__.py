"""
API v1 root router.

Aggregates all /api/v1/* sub-routers and re-exports a single `router`
object that is mounted by the application factory in app/main.py.

Route prefixes registered here:
    /api/v1/earthquakes  — earthquake query and summary endpoints
    /api/v1/chat         — AI-powered seismic chat endpoint
    /api/v1/export       — data export (XML, CSV, PDF)
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.earthquakes import router as earthquakes_router
from app.api.v1.chat import router as chat_router
from app.api.v1.export import router as export_router

router = APIRouter()

router.include_router(earthquakes_router, prefix="/earthquakes", tags=["earthquakes"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(export_router, prefix="/export", tags=["export"])
