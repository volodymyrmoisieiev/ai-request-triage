from datetime import datetime

import pytest
from pydantic import ValidationError

from ai_request_triage.schemas import InputRequest, TriageCategory, TriageResult


def test_valid_input_request() -> None:
    request = InputRequest(
        id="REQ-001",
        channel="Slack",
        timestamp="2026-06-08 09:14",
        raw_text="Please automate the weekly report.",
    )

    assert request.id == "REQ-001"
    assert request.channel == "Slack"
    assert isinstance(request.timestamp, datetime)
    assert request.raw_text == "Please automate the weekly report."


def test_empty_id() -> None:
    with pytest.raises(ValidationError):
        InputRequest(
            id="",
            channel="Slack",
            timestamp="2026-06-08 09:14",
            raw_text="Please automate the weekly report.",
        )


def test_empty_channel() -> None:
    with pytest.raises(ValidationError):
        InputRequest(
            id="REQ-001",
            channel="",
            timestamp="2026-06-08 09:14",
            raw_text="Please automate the weekly report.",
        )


def test_empty_raw_text() -> None:
    with pytest.raises(ValidationError):
        InputRequest(
            id="REQ-001",
            channel="Slack",
            timestamp="2026-06-08 09:14",
            raw_text="",
        )


def test_invalid_timestamp() -> None:
    with pytest.raises(ValidationError):
        InputRequest(
            id="REQ-001",
            channel="Slack",
            timestamp="not a timestamp",
            raw_text="Please automate the weekly report.",
        )


def make_triage_result(**overrides) -> TriageResult:
    data = {
        "category": "автоматизація",
        "target_department": "Marketing",
        "priority": "medium",
        "short_summary": "Automate a weekly report.",
        "requested_actions": ["Create an automated report."],
        "needs_clarification": False,
        "clarification_questions": [],
        "triage_status": "ready",
        "systems": ["Google Ads"],
        "references_previous_request": False,
        "related_request_id": None,
    }
    data.update(overrides)
    return TriageResult(**data)


def test_valid_triage_result() -> None:
    result = make_triage_result()

    assert result.category == TriageCategory.AUTOMATION
    assert result.target_department == "Marketing"
    assert result.priority == "medium"
    assert result.short_summary == "Automate a weekly report."
    assert result.requested_actions == ["Create an automated report."]
    assert result.needs_clarification is False
    assert result.clarification_questions == []
    assert result.triage_status == "ready"
    assert result.systems == ["Google Ads"]
    assert result.references_previous_request is False
    assert result.related_request_id is None


@pytest.mark.parametrize(
    "category",
    [
        "автоматизація",
        "інтеграція",
        "звіт/аналітика",
        "баг/підтримка",
        "питання/консультація",
        "поза скоупом",
    ],
)
def test_every_valid_category(category: str) -> None:
    result = make_triage_result(category=category)

    assert result.category.value == category


def test_invalid_category() -> None:
    with pytest.raises(ValidationError):
        make_triage_result(category="other")


def test_invalid_priority() -> None:
    with pytest.raises(ValidationError):
        make_triage_result(priority="urgent")


def test_invalid_triage_status() -> None:
    with pytest.raises(ValidationError):
        make_triage_result(triage_status="waiting")


def test_empty_short_summary() -> None:
    with pytest.raises(ValidationError):
        make_triage_result(short_summary="")


def test_needs_clarification_without_clarification_questions() -> None:
    with pytest.raises(ValidationError):
        make_triage_result(
            needs_clarification=True,
            clarification_questions=[],
        )


def test_needs_clarification_status_with_needs_clarification_false() -> None:
    with pytest.raises(ValidationError):
        make_triage_result(
            triage_status="needs_clarification",
            needs_clarification=False,
        )


def test_related_request_id_when_references_previous_request_false() -> None:
    with pytest.raises(ValidationError):
        make_triage_result(
            references_previous_request=False,
            related_request_id="REQ-001",
        )


def test_no_action_with_non_empty_requested_actions() -> None:
    with pytest.raises(ValidationError):
        make_triage_result(
            triage_status="no_action",
            requested_actions=["Send a reply."],
        )
