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

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.config import Settings
from app.core.dependencies import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response models (full schema defined in issue #05)
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text.")


class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's query to the seismic AI assistant.")
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Previous messages in the conversation, ordered oldest-first.",
    )
    context_summary: str | None = Field(
        None,
        description=(
            "Optional pre-computed dataset summary string (counts, avg magnitude, "
            "top events). If omitted, the backend will generate it from cached data."
        ),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "",
    summary="AI seismic chat",
    description=(
        "Send a natural language query to the Gemini-powered seismic AI assistant. "
        "The assistant understands earthquake datasets, filter mutations, and "
        "navigation commands. Full implementation lands in issue #10."
    ),
)
def chat(
    body: ChatRequest,
    cfg: Settings = Depends(get_settings),
) -> JSONResponse:
    logger.info("POST /chat — message=%.80s", body.message)

    if not cfg.GOOGLE_API_KEY:
        return JSONResponse(
            status_code=503,
            content={
                "detail": "AI service unavailable — GOOGLE_API_KEY is not configured.",
            },
        )

    return JSONResponse(
        status_code=501,
        content={
            "detail": "Not yet implemented — see issue #10 (Port AI Chat Endpoint).",
            "received_message": body.message,
        },
    )
