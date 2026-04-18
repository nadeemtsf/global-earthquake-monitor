"""
/api/v1/chat — AI-powered seismic chat endpoint.

POST /api/v1/chat
    Accept a ChatRequest body (message + history) and return an AI response.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from app.core.config import Settings
from app.core.dependencies import get_pipeline, get_settings
from app.schemas.chat import ChatRequest, ChatResponse, SuggestedAction as SuggestedActionSchema

from app.services.xml_pipeline import XMLPipelineService
from app.services.ai import AIService, parse_action_tags, QuotaExceeded, PermanentAIError

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
        "navigation commands."
    ),
)
async def chat(
    body: ChatRequest,
    cfg: Settings = Depends(get_settings),
    pipeline: XMLPipelineService = Depends(get_pipeline),
) -> ChatResponse:
    logger.info("POST /chat — message=%.80s", body.message)

    if not cfg.GOOGLE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service unavailable — GOOGLE_API_KEY is not configured.",
        )

    # Fetch the dataset slice matching the frontend's view so the AI can be grounded
    source = body.source or "USGS"
    min_mag = body.min_magnitude if body.min_magnitude is not None else cfg.DEFAULT_MIN_MAGNITUDE
    events = await pipeline.get_earthquakes(
        source=source, start_date=body.start_date, end_date=body.end_date, min_mag=min_mag
    )

    ai = AIService(api_key=cfg.GOOGLE_API_KEY)

    # Use provided context_summary when present, otherwise synthesize from events
    context = body.context_summary if body.context_summary is not None else ai.generate_context_from_events(events)

    history = [{"role": m.role, "content": m.content} for m in body.history] if body.history else []

    try:
        result = await ai.generate_chat_response(body.message, context, history)
    except QuotaExceeded as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except PermanentAIError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:  # pragma: no cover - unexpected
        logger.exception("Unhandled AI error: %s", e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI service error")

    text = result.get("text", "")
    model = result.get("model")

    cleaned, suggested = parse_action_tags(text)

    suggested_actions: list[SuggestedActionSchema] = []
    for s in suggested:
        suggested_actions.append(SuggestedActionSchema(type=s.get("type", ""), target=s.get("target", "")))

    return ChatResponse(response=cleaned.strip(), suggested_actions=suggested_actions, metadata={"model": model})
