import json
from datetime import datetime

from ai_request_triage.processor import ProcessedRequest, ProcessingStatus
from ai_request_triage.report import (
    build_markdown_report,
    write_markdown_report,
    write_output_json,
)
from ai_request_triage.schemas import TriageCategory, TriageResult


def make_triage_result(
    *,
    category: TriageCategory = TriageCategory.AUTOMATION,
    priority: str = "medium",
    target_department: str | None = "Marketing",
    short_summary: str = "Automate the weekly report.",
    needs_clarification: bool = False,
) -> TriageResult:
    return TriageResult(
        category=category,
        target_department=target_department,
        priority=priority,
        short_summary=short_summary,
        requested_actions=["Create automation."],
        needs_clarification=needs_clarification,
        clarification_questions=(
            ["Which metrics should be included?"] if needs_clarification else []
        ),
        triage_status="needs_clarification" if needs_clarification else "ready",
        systems=["Google Ads"],
        references_previous_request=False,
        related_request_id=None,
    )


def make_processed_request(
    request_id: str,
    *,
    raw_text: str = "Потрібно сформувати звіт.",
    triage: TriageResult | None = None,
    error: str | None = None,
) -> ProcessedRequest:
    return ProcessedRequest(
        id=request_id,
        channel="Slack",
        timestamp=datetime(2026, 6, 8, 9, 14),
        raw_text=raw_text,
        processing_status=(
            ProcessingStatus.FAILED if error else ProcessingStatus.SUCCESS
        ),
        triage=triage if error is None else None,
        error=error,
    )


def test_output_json_contains_all_processed_requests(tmp_path) -> None:
    output_path = tmp_path / "output.json"
    processed_requests = [
        make_processed_request("REQ-001", triage=make_triage_result()),
        make_processed_request("REQ-002", error="RuntimeError: Gemini error"),
    ]

    write_output_json(processed_requests, output_path)

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(data) == 2
    assert data[0]["id"] == "REQ-001"
    assert data[0]["processing_status"] == "success"
    assert data[0]["triage"]["short_summary"] == "Automate the weekly report."
    assert data[0]["error"] is None
    assert data[1]["id"] == "REQ-002"
    assert data[1]["processing_status"] == "failed"
    assert data[1]["triage"] is None
    assert data[1]["error"] == "RuntimeError: Gemini error"


def test_output_json_preserves_ukrainian_text(tmp_path) -> None:
    output_path = tmp_path / "output.json"
    processed_requests = [
        make_processed_request(
            "REQ-001",
            raw_text="Потрібно сформувати звіт.",
            triage=make_triage_result(short_summary="Потрібен звіт."),
        )
    ]

    write_output_json(processed_requests, output_path)

    content = output_path.read_text(encoding="utf-8")
    assert "Потрібно сформувати звіт." in content
    assert "Потрібен звіт." in content
    assert "\\u041f" not in content


def test_category_aggregation() -> None:
    report = build_markdown_report(
        [
            make_processed_request(
                "REQ-001",
                triage=make_triage_result(category=TriageCategory.AUTOMATION),
            ),
            make_processed_request(
                "REQ-002",
                triage=make_triage_result(category=TriageCategory.AUTOMATION),
            ),
            make_processed_request(
                "REQ-003",
                triage=make_triage_result(category=TriageCategory.REPORT_ANALYTICS),
            ),
        ]
    )

    assert f"- {TriageCategory.AUTOMATION.value}: 2" in report
    assert f"- {TriageCategory.REPORT_ANALYTICS.value}: 1" in report


def test_priority_aggregation() -> None:
    report = build_markdown_report(
        [
            make_processed_request("REQ-001", triage=make_triage_result(priority="low")),
            make_processed_request("REQ-002", triage=make_triage_result(priority="high")),
            make_processed_request("REQ-003", triage=make_triage_result(priority="high")),
        ]
    )

    assert "- high: 2" in report
    assert "- low: 1" in report


def test_department_aggregation_including_unknown() -> None:
    report = build_markdown_report(
        [
            make_processed_request(
                "REQ-001",
                triage=make_triage_result(target_department="Marketing"),
            ),
            make_processed_request(
                "REQ-002",
                triage=make_triage_result(target_department=None),
            ),
            make_processed_request(
                "REQ-003",
                triage=make_triage_result(target_department=None),
            ),
        ]
    )

    assert "- Marketing: 1" in report
    assert "- unknown: 2" in report


def test_clarification_list() -> None:
    report = build_markdown_report(
        [
            make_processed_request(
                "REQ-002",
                triage=make_triage_result(
                    short_summary="Need more report details.",
                    needs_clarification=True,
                ),
            )
        ]
    )

    assert "- REQ-002: Need more report details." in report


def test_markdown_report_is_written(tmp_path) -> None:
    report_path = tmp_path / "report.md"
    processed_requests = [
        make_processed_request("REQ-001", triage=make_triage_result()),
    ]

    write_markdown_report(processed_requests, report_path)

    content = report_path.read_text(encoding="utf-8")
    assert "# Triage Report" in content
    assert "- Total processed requests: 1" in content


def test_failed_requests_are_handled_correctly() -> None:
    report = build_markdown_report(
        [
            make_processed_request("REQ-001", triage=make_triage_result()),
            make_processed_request("REQ-002", error="RuntimeError: Gemini error"),
        ]
    )

    assert "- Total processed requests: 2" in report
    assert "- Successful requests: 1" in report
    assert "- Failed requests: 1" in report
    assert "RuntimeError: Gemini error" not in report
