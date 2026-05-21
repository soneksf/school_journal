"""Thin wrapper around the Anthropic API.

We isolate the SDK behind a small interface so tests can monkey-patch
`send_messages` and so the rest of the app stays vendor-agnostic.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


class AnthropicError(RuntimeError):
    """Anything that goes wrong talking to the API."""


def _get_client():
    """Lazy import so the app doesn't fail at import time when SDK is missing."""
    if not settings.ANTHROPIC_API_KEY:
        raise AnthropicError("ANTHROPIC_API_KEY is not configured")
    try:
        import anthropic  # type: ignore
    except ImportError as exc:
        raise AnthropicError("anthropic SDK is not installed") from exc
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def send_messages(
    *,
    system: str,
    messages: list[dict[str, Any]],
    max_tokens: int = 1500,
    temperature: float = 0.3,
) -> str:
    """Call the Anthropic Messages API and return the assembled text response."""
    client = _get_client()
    try:
        resp = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=messages,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Anthropic API call failed")
        raise AnthropicError(str(exc)) from exc

    parts = []
    for block in resp.content:
        # Each block has a `.type` attribute; we keep only text content.
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "\n".join(parts).strip()


def parse_json_response(text: str) -> dict:
    """Extract a JSON object from a model response.

    Tolerates ```json fences and minor preamble.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    # If the model wrapped JSON in extra text, find the outermost braces.
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start:end + 1]

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AnthropicError(f"Model returned non-JSON: {exc}") from exc
