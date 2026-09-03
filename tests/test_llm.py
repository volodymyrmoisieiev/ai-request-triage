from datetime import datetime
from types import SimpleNamespace

import pytest

from ai_request_triage.exceptions import (
    GeminiClassificationError,
    InvalidStructuredResponseError,
    MissingGeminiAPIKeyError,
)
from ai_request_triage.llm import DEFAULT_GEMINI_MODEL, classify_request
from ai_request_triage.schemas import InputRequest, TriageResult


def make_input_request() -> InputRequest:
    return InputRequest(
        id="REQ-001",
        channel="Slack",
        timestamp=datetime(2026, 6, 8, 9, 14),
        raw_text="Please automate the weekly report.",
    )


def make_triage_result() -> TriageResult:
    return TriageResult(
        category="автоматизація",
        target_department="Marketing",
        priority="medium",
        short_summary="Automate a weekly report.",
        requested_actions=["Create an automated report."],
        needs_clarification=False,
        clarification_questions=[],
        triage_status="ready",
        systems=["Google Ads"],
        references_previous_request=False,
        related_request_id=None,
    )


class FakeModels:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.called_with = None

    def generate_content(self, **kwargs):
        self.called_with = kwargs
        if self.error:
            raise self.error
        return self.response


class FakeClient:
    models = None
    api_key = None

    def __init__(self, api_key):
        self.__class__.api_key = api_key
        self.models = self.__class__.models


class SimpleNamespaceError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


def test_successful_classification(monkeypatch) -> None:
    result = make_triage_result()
    fake_models = FakeModels(response=SimpleNamespace(parsed=result))
    FakeClient.models = fake_models

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setattr("ai_request_triage.llm.genai.Client", FakeClient)

    response = classify_request(make_input_request())

    assert response == result
    assert FakeClient.api_key == "test-key"
    assert fake_models.called_with["model"] == DEFAULT_GEMINI_MODEL
    assert fake_models.called_with["config"]["response_schema"] is TriageResult
    assert fake_models.called_with["config"]["response_mime_type"] == "application/json"
    assert "Please automate the weekly report." in fake_models.called_with["contents"]


def test_default_gemini_model() -> None:
    assert DEFAULT_GEMINI_MODEL == "gemini-3.7-flash"


def test_missing_api_key(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(MissingGeminiAPIKeyError):
        classify_request(make_input_request())


def test_api_failure(monkeypatch) -> None:
    fake_models = FakeModels(error=RuntimeError("API error"))
    FakeClient.models = fake_models

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("ai_request_triage.llm.genai.Client", FakeClient)

    with pytest.raises(GeminiClassificationError):
        classify_request(make_input_request())


@pytest.mark.parametrize(
    ("error", "expected_message"),
    [
        (
            SimpleNamespaceError(status_code=429, message="RESOURCE_EXHAUSTED key=secret"),
            "Gemini rate limit or quota is exceeded",
        ),
        (
            SimpleNamespaceError(status_code=503, message="raw service response"),
            "Gemini service is temporarily unavailable",
        ),
        (
            SimpleNamespaceError(status_code=500, message="raw service response"),
            "Gemini API request failed",
        ),
    ],
)
def test_api_error_messages_are_safe(monkeypatch, error, expected_message: str) -> None:
    fake_models = FakeModels(error=error)
    FakeClient.models = fake_models

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("ai_request_triage.llm.genai.Client", FakeClient)

    with pytest.raises(GeminiClassificationError) as exc_info:
        classify_request(make_input_request())

    assert str(exc_info.value) == expected_message
    assert "test-key" not in str(exc_info.value)
    assert "raw service response" not in str(exc_info.value)
    assert "secret" not in str(exc_info.value)


def test_invalid_structured_response(monkeypatch) -> None:
    fake_models = FakeModels(response=SimpleNamespace(parsed={"category": "other"}))
    FakeClient.models = fake_models

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("ai_request_triage.llm.genai.Client", FakeClient)

    with pytest.raises(InvalidStructuredResponseError):
        classify_request(make_input_request())
