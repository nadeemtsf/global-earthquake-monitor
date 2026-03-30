"""
/api/v1/chat — AI-powered seismic chat endpoint.

This router wraps the SeismicAI service (backed by Google Gemini) behind a
single POST endpoint that accepts a user message plus optional conversation
history, and returns a plain-text AI response.

Full implementation is delivered in issue #10 (Port AI chat endpoint).

Currently scaffolded endpoints
-------------------------------
POST /api/v1/chat
    Accept a ChatRequest body (message + history) and return an AI response.
    Streamed responses will be considered in issue #10.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from app.core.config import Settings
from app.core.dependencies import get_settings
from app.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "",
    summary="AI seismic chat",
    response_model=ChatResponse,
    description=(
        "Send a natural language query to the Gemini-powered seismic AI assistant. "
        "The assistant understands earthquake datasets, filter mutations, and "
        "navigation commands. Full implementation lands in issue #10."
    ),
)
def chat(
    body: ChatRequest,
    cfg: Settings = Depends(get_settings),
) -> dict:
    logger.info("POST /chat — message=%.80s", body.message)

    if not cfg.GOOGLE_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="AI service unavailable — GOOGLE_API_KEY is not configured.",
        )

    # Placeholder return matching ChatResponse shape
    return {
        "response": (
            "This is a placeholder response. The AI chat implementation "
            "will be completed in issue #10."
        ),
        "suggested_actions": [],
        "metadata": {"status": "scaffolded"},
    }
