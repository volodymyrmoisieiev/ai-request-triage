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

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


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
        raise GeminiClassificationError("Gemini classification failed") from exc

    parsed_response = getattr(response, "parsed", None)
    if not isinstance(parsed_response, TriageResult):
        raise InvalidStructuredResponseError(
            "Gemini did not return a valid TriageResult"
        )

    return parsed_response
