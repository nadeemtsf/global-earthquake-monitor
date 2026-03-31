"""
AI service wrapper for Google Gemini (Generative AI) used by the chat
endpoint. Encapsulates model fallback, prompt construction, and simple
context generation from `EarthquakeEvent` models.

This module intentionally keeps framework dependencies out of the core
service (raises service-specific exceptions) so the FastAPI endpoint can
translate errors into appropriate HTTP responses.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import List, Dict, Any

import google.generativeai as genai

from app.schemas.earthquakes import EarthquakeEvent
from app.core.config import settings

logger = logging.getLogger(__name__)


# Models to attempt in order
MODEL_POOL = [
    "gemini-2.0-flash",
    "gemini-flash-latest",
    "gemini-pro-latest",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-001",
    "gemini-flash-lite-latest",
]


class AIServiceError(Exception):
    """Base class for AI service errors."""


class QuotaExceeded(AIServiceError):
    """Raised when all models are exhausted / quota reached."""


class PermanentAIError(AIServiceError):
    """Raised for non-transient errors (invalid key, malformed request).
    """


class AIService:
    """Encapsulate Google Generative AI interactions with model fallback.

    The service intentionally provides a simple async-friendly API while
    calling the synchronous `google.generativeai` SDK in a thread.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.GOOGLE_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
        else:
            logger.warning("AIService initialized without GOOGLE_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate_context_from_events(self, events: List[EarthquakeEvent]) -> str:
        if not events:
            return "No earthquakes match the current filters."

        total = len(events)
        mags = [e.magnitude for e in events if e.magnitude is not None]
        avg_mag = sum(mags) / len(mags) if mags else 0.0
        tsunami_count = sum(1 for e in events if getattr(e, "tsunami", 0) == 1)

        # Sort by magnitude descending for top events
        latest = sorted(events, key=lambda e: (e.magnitude or 0.0), reverse=True)[:5]

        ctx = [f"Total earthquakes: {total}", f"Average magnitude: {avg_mag:.2f}", f"Tsunami advisories: {tsunami_count}", "Latest significant events:"]
        for e in latest:
            country = e.country or "Unknown"
            time_str = getattr(e.main_time, "isoformat", lambda: str(e.main_time))()
            ctx.append(f"- {e.place} ({country}): Magnitude {e.magnitude} at {time_str}")
            if getattr(e, "alert_level", None):
                ctx.append(f"  (Alert: {e.alert_level})")

        return "\n".join(ctx)

    def _build_prompt(self, user_query: str, context: str) -> str:
        return f"""
        You are a seismic activity expert. Use the following context and chat history to answer the user query.

        CONTEXT:
        {context}

        CAPABILITIES:
        - [[NAVIGATE: TabName]] to switch tabs (Overview, Distribution, Geographic, Time Series, AI Assistant).
        - [[SET_DATE: YYYY-MM-DD, YYYY-MM-DD]] to change date range.
        - [[SET_SOURCE: USGS|GDACS|Both]] to change source.
        - [[SET_ALERT: green|yellow|orange|red]] to filter by alert (comma separated).
        - [[SET_COUNTRY: CountryName]] to filter (comma separated).
        - [[CHART: type=scatter|bar|pie|histogram|line|box, title=..., x=..., y=..., color=..., filter_alert=..., filter_country=...]]

        USER QUERY: {user_query}
        """

    def _call_model_sync(self, model_name: str, prompt: str, history: List[Dict[str, str]] | None) -> str:
        """Synchronous call to the genai model. Kept in a separate method so
        it can be invoked via `asyncio.to_thread` for non-blocking behaviour.
        """
        model = genai.GenerativeModel(model_name)

        if not history:
            response = model.generate_content(prompt)
            text = str(getattr(response, "text", ""))
        else:
            gemini_history = []
            for m in history:
                role = "user" if m.get("role") == "user" else "model"
                gemini_history.append({"role": role, "parts": [m.get("content", "")]})

            chat = model.start_chat(history=gemini_history)
            response = chat.send_message(prompt)
            text = str(getattr(response, "text", ""))

        return text

    async def generate_chat_response(self, user_query: str, context: str, history: List[Dict[str, str]] | None = None) -> Dict[str, Any]:
        """Generate a chat response using the configured model pool.

        Returns a dict with keys: `text` and `model` on success.
        Raises `QuotaExceeded` when all models report quota exhaustion.
        Raises `PermanentAIError` for non-recoverable failures.
        """
        if not self.is_available():
            raise PermanentAIError("AI service is not configured (missing API key).")

        prompt = self._build_prompt(user_query, context)

        last_exc: Exception | None = None
        for model_name in MODEL_POOL:
            try:
                text = await asyncio.to_thread(self._call_model_sync, model_name, prompt, history)
                # success
                return {"text": text, "model": model_name}
            except Exception as e:  # pragma: no cover - behavior exercised via tests
                last_exc = e
                err_str = str(e)
                logger.warning("Model %s failed: %s", model_name, err_str)
                if "429" in err_str or "quota" in err_str.lower() or "404" in err_str:
                    # try next model
                    continue
                else:
                    # Non-transient error — expose to caller
                    raise PermanentAIError(err_str)

        # If we reach here, all models failed
        if last_exc is not None and ("429" in str(last_exc) or "quota" in str(last_exc).lower()):
            raise QuotaExceeded(str(last_exc))

        raise PermanentAIError(str(last_exc) if last_exc is not None else "Unknown AI failure")


def parse_action_tags(text: str) -> (str, List[Dict[str, str]]):
    """Extracts internal [[...]] action tags from AI text and returns the
    cleaned text plus a list of suggested action dicts with `type` and `target`.
    """
    suggested: List[Dict[str, str]] = []
    cleaned = text

    # NAVIGATE
    for m in re.finditer(r"\[\[NAVIGATE:\s*(.*?)\]\]", cleaned):
        suggested.append({"type": "NAVIGATE", "target": m.group(1).strip()})
        cleaned = cleaned.replace(m.group(0), "").strip()

    # SET_DATE
    for m in re.finditer(r"\[\[SET_DATE:\s*(.*?),\s*(.*?)\]\]", cleaned):
        suggested.append({"type": "SET_DATE", "target": f"{m.group(1).strip()},{m.group(2).strip()}"})
        cleaned = cleaned.replace(m.group(0), "").strip()

    # SET_SOURCE
    for m in re.finditer(r"\[\[SET_SOURCE:\s*(.*?)\]\]", cleaned):
        suggested.append({"type": "SET_SOURCE", "target": m.group(1).strip()})
        cleaned = cleaned.replace(m.group(0), "").strip()

    # SET_ALERT
    for m in re.finditer(r"\[\[SET_ALERT:\s*(.*?)\]\]", cleaned):
        suggested.append({"type": "SET_ALERT", "target": m.group(1).strip()})
        cleaned = cleaned.replace(m.group(0), "").strip()

    # SET_COUNTRY
    for m in re.finditer(r"\[\[SET_COUNTRY:\s*(.*?)\]\]", cleaned):
        suggested.append({"type": "SET_COUNTRY", "target": m.group(1).strip()})
        cleaned = cleaned.replace(m.group(0), "").strip()

    # CHART specs (raw spec retained as target)
    for m in re.finditer(r"\[\[CHART:\s*(.*?)\]\]", cleaned, re.DOTALL):
        suggested.append({"type": "CHART", "target": m.group(1).strip()})
        cleaned = cleaned.replace(m.group(0), "").strip()

    return cleaned, suggested
