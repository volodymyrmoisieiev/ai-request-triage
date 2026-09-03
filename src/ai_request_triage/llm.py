"""Gemini structured classification."""

import os

from google import genai

from ai_request_triage.exceptions import (
    GeminiClassificationError,
    InvalidStructuredResponseError,
    MissingGeminiAPIKeyError,
)
from ai_request_triage.prompts import build_triage_prompt
from ai_request_triage.schemas import InputRequest, TriageResult

DEFAULT_GEMINI_MODEL = "gemini-3.7-flash"


def classify_request(request: InputRequest) -> TriageResult:
    """Classify one input request with Gemini structured output."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise MissingGeminiAPIKeyError("GEMINI_API_KEY is not configured")

    model_name = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=build_triage_prompt(request),
            config={
                "response_mime_type": "application/json",
                "response_schema": TriageResult,
            },
        )
    except Exception as exc:
        raise GeminiClassificationError(_format_gemini_error(exc)) from exc

    parsed_response = getattr(response, "parsed", None)
    if not isinstance(parsed_response, TriageResult):
        raise InvalidStructuredResponseError(
            "Gemini did not return a valid TriageResult"
        )

    return parsed_response


def _format_gemini_error(exc: Exception) -> str:
    status_code = _get_status_code(exc)
    error_text = str(exc)

    if (
        status_code == 429
        or "429" in error_text
        or "RESOURCE_EXHAUSTED" in error_text
    ):
        return "Gemini rate limit or quota is exceeded"

    if status_code == 503 or "503" in error_text:
        return "Gemini service is temporarily unavailable"

    return "Gemini API request failed"


def _get_status_code(exc: Exception) -> int | None:
    for attribute_name in ("status_code", "code"):
        value = getattr(exc, attribute_name, None)
        if isinstance(value, int):
            return value

    error = getattr(exc, "error", None)
    if error is not None:
        for attribute_name in ("status_code", "code"):
            value = getattr(error, attribute_name, None)
            if isinstance(value, int):
                return value

    return None
