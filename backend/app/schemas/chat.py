"""
Pydantic models for the AI seismic chat assistant.

Defines the structure for messages, conversation history, and the natural
language responses from the SeismicAI engine.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single turn in the AI conversation."""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="The message body.")


class ChatRequest(BaseModel):
    """User query payload to the seismic chat assistant."""

    message: str = Field(..., description="The user's latest query.")
    history: List[ChatMessage] = Field(
        default_factory=list,
        description="Previous messages in the conversation for session context.",
    )
    context_summary: Optional[str] = Field(
        None,
        description=(
            "Optional textual summary of the current dataset (e.g., filter state, "
            "count, top events). If omitted, the backend will generate context "
            "from its internal caches."
        ),
    )


class SuggestedAction(BaseModel):
    """Optional navigation or filter hints returned by the AI assistant."""
    type: str = Field(..., description="Action type: (NAVIGATE | SET_DATE | SET_FILTER)")
    target: str = Field(..., description="Action target (e.g., 'Geographic', '2024-01-01')")


class ChatResponse(BaseModel):
    """The AI assistant's conversational response."""

    response: str = Field(..., description="Markdown-formatted AI response.")
    suggested_actions: List[SuggestedAction] = Field(
        default_factory=list,
        description="Optional tool/navigation hints parsed from the AI output."
    )
    metadata: Dict[str, str | float | None] = Field(
        default_factory=dict, description="Metadata such as model name or quota usage."
    )
