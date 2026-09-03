from datetime import datetime

import pytest

from ai_request_triage.processor import ProcessingStatus, process_requests
from ai_request_triage.schemas import InputRequest, TriageCategory, TriageResult


def make_input_request(request_id: str, raw_text: str) -> InputRequest:
    return InputRequest(
        id=request_id,
        channel="Slack",
        timestamp=datetime(2026, 6, 8, 9, 14),
        raw_text=raw_text,
    )


def make_triage_result(summary: str) -> TriageResult:
    return TriageResult(
        category=TriageCategory.AUTOMATION,
        target_department=None,
        priority="medium",
        short_summary=summary,
        requested_actions=["Create automation."],
        needs_clarification=False,
        clarification_questions=[],
        triage_status="ready",
        systems=[],
        references_previous_request=False,
        related_request_id=None,
    )


def test_multiple_successful_requests(monkeypatch) -> None:
    requests = [
        make_input_request("REQ-001", "Automate weekly report."),
        make_input_request("REQ-002", "Automate daily summary."),
    ]

    def fake_classify_request(request: InputRequest) -> TriageResult:
        return make_triage_result(f"Summary for {request.id}")

    monkeypatch.setattr(
        "ai_request_triage.processor.classify_request",
        fake_classify_request,
    )

    processed = process_requests(requests)

    assert len(processed) == 2
    assert processed[0].processing_status == ProcessingStatus.SUCCESS
    assert processed[0].triage is not None
    assert processed[0].triage.short_summary == "Summary for REQ-001"
    assert processed[0].error is None
    assert processed[1].processing_status == ProcessingStatus.SUCCESS
    assert processed[1].triage is not None
    assert processed[1].triage.short_summary == "Summary for REQ-002"
    assert processed[1].error is None


def test_one_failed_request_does_not_stop_batch(monkeypatch) -> None:
    requests = [
        make_input_request("REQ-001", "Automate weekly report."),
        make_input_request("REQ-002", "This request fails."),
        make_input_request("REQ-003", "Automate daily summary."),
    ]

    def fake_classify_request(request: InputRequest) -> TriageResult:
        if request.id == "REQ-002":
            raise RuntimeError("Gemini error")
        return make_triage_result(f"Summary for {request.id}")

    monkeypatch.setattr(
        "ai_request_triage.processor.classify_request",
        fake_classify_request,
    )

    processed = process_requests(requests)

    assert len(processed) == 3
    assert processed[0].processing_status == ProcessingStatus.SUCCESS
    assert processed[1].processing_status == ProcessingStatus.FAILED
    assert processed[1].triage is None
    assert processed[1].error == "RuntimeError: Gemini error"
    assert processed[2].processing_status == ProcessingStatus.SUCCESS


def test_original_request_fields_are_preserved(monkeypatch) -> None:
    request = make_input_request("REQ-001", "Automate weekly report.")

    def fake_classify_request(request: InputRequest) -> TriageResult:
        return make_triage_result("Summary")

    monkeypatch.setattr(
        "ai_request_triage.processor.classify_request",
        fake_classify_request,
    )

    processed = process_requests([request])[0]

    assert processed.id == request.id
    assert processed.channel == request.channel
    assert processed.timestamp == request.timestamp
    assert processed.raw_text == request.raw_text


def test_correct_success_and_failed_statuses(monkeypatch) -> None:
    requests = [
        make_input_request("REQ-001", "Automate weekly report."),
        make_input_request("REQ-002", "This request fails."),
    ]

    def fake_classify_request(request: InputRequest) -> TriageResult:
        if request.id == "REQ-002":
            raise ValueError("Invalid response")
        return make_triage_result("Summary")

    monkeypatch.setattr(
        "ai_request_triage.processor.classify_request",
        fake_classify_request,
    )

    processed = process_requests(requests)

    assert processed[0].processing_status == ProcessingStatus.SUCCESS
    assert processed[0].triage is not None
    assert processed[0].error is None
    assert processed[1].processing_status == ProcessingStatus.FAILED
    assert processed[1].triage is None
    assert processed[1].error == "ValueError: Invalid response"


def test_delay_between_requests(monkeypatch) -> None:
    requests = [
        make_input_request("REQ-001", "Automate weekly report."),
        make_input_request("REQ-002", "Automate daily summary."),
        make_input_request("REQ-003", "Automate monthly report."),
    ]
    sleep_calls = []

    def fake_classify_request(request: InputRequest) -> TriageResult:
        return make_triage_result(f"Summary for {request.id}")

    monkeypatch.setattr(
        "ai_request_triage.processor.classify_request",
        fake_classify_request,
    )
    monkeypatch.setattr(
        "ai_request_triage.processor.time.sleep",
        lambda delay: sleep_calls.append(delay),
    )

    process_requests(requests, delay_seconds=1.5)

    assert sleep_calls == [1.5, 1.5]


def test_no_delay_after_last_request(monkeypatch) -> None:
    request = make_input_request("REQ-001", "Automate weekly report.")
    sleep_calls = []

    def fake_classify_request(request: InputRequest) -> TriageResult:
        return make_triage_result("Summary")

    monkeypatch.setattr(
        "ai_request_triage.processor.classify_request",
        fake_classify_request,
    )
    monkeypatch.setattr(
        "ai_request_triage.processor.time.sleep",
        lambda delay: sleep_calls.append(delay),
    )

    process_requests([request], delay_seconds=1.5)

    assert sleep_calls == []


def test_zero_delay(monkeypatch) -> None:
    requests = [
        make_input_request("REQ-001", "Automate weekly report."),
        make_input_request("REQ-002", "Automate daily summary."),
    ]
    sleep_calls = []

    def fake_classify_request(request: InputRequest) -> TriageResult:
        return make_triage_result(f"Summary for {request.id}")

    monkeypatch.setattr(
        "ai_request_triage.processor.classify_request",
        fake_classify_request,
    )
    monkeypatch.setattr(
        "ai_request_triage.processor.time.sleep",
        lambda delay: sleep_calls.append(delay),
    )

    process_requests(requests)

    assert sleep_calls == []


def test_negative_delay() -> None:
    with pytest.raises(ValueError, match="delay_seconds must not be negative"):
        process_requests([], delay_seconds=-1)


def test_progress_output(monkeypatch, capsys) -> None:
    requests = [
        make_input_request("REQ-001", "Automate weekly report."),
        make_input_request("REQ-002", "Automate daily summary."),
    ]

    def fake_classify_request(request: InputRequest) -> TriageResult:
        return make_triage_result(f"Summary for {request.id}")

    monkeypatch.setattr(
        "ai_request_triage.processor.classify_request",
        fake_classify_request,
    )

    process_requests(requests)

    captured = capsys.readouterr()
    assert "Processing 1/2: REQ-001" in captured.out
    assert "Processing 2/2: REQ-002" in captured.out
    assert "Automate weekly report." not in captured.out
