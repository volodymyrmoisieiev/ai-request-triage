"""Output files for processed requests."""

import json
from collections import Counter
from pathlib import Path

from ai_request_triage.processor import ProcessedRequest, ProcessingStatus

DEFAULT_JSON_OUTPUT_PATH = Path("output/output.json")
DEFAULT_MARKDOWN_REPORT_PATH = Path("output/report.md")


def write_output_json(
    processed_requests: list[ProcessedRequest],
    output_path: str | Path = DEFAULT_JSON_OUTPUT_PATH,
) -> None:
    """Write processed requests to a readable JSON file."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = [request.model_dump(mode="json") for request in processed_requests]
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_markdown_report(
    processed_requests: list[ProcessedRequest],
    report_path: str | Path = DEFAULT_MARKDOWN_REPORT_PATH,
) -> None:
    """Write a deterministic Markdown report."""

    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_markdown_report(processed_requests), encoding="utf-8")


def build_markdown_report(processed_requests: list[ProcessedRequest]) -> str:
    """Build Markdown report content from processed requests."""

    total_count = len(processed_requests)
    success_count = sum(
        request.processing_status == ProcessingStatus.SUCCESS
        for request in processed_requests
    )
    failed_count = total_count - success_count

    successful_triages = [
        request.triage
        for request in processed_requests
        if request.processing_status == ProcessingStatus.SUCCESS
        and request.triage is not None
    ]
    clarification_requests = [
        request
        for request in processed_requests
        if request.triage is not None and request.triage.needs_clarification
    ]

    category_counts = Counter(triage.category.value for triage in successful_triages)
    priority_counts = Counter(triage.priority.value for triage in successful_triages)
    department_counts = Counter(
        triage.target_department or "unknown" for triage in successful_triages
    )

    lines = [
        "# Triage Report",
        "",
        "## Summary",
        "",
        f"- Total processed requests: {total_count}",
        f"- Successful requests: {success_count}",
        f"- Failed requests: {failed_count}",
        "",
        "## Count by Category",
        "",
        *_format_counter(category_counts),
        "",
        "## Count by Priority",
        "",
        *_format_counter(priority_counts),
        "",
        "## Count by Target Department",
        "",
        *_format_counter(department_counts),
        "",
        "## Requests Needing Clarification",
        "",
        *_format_clarification_requests(clarification_requests),
        "",
    ]

    return "\n".join(lines)


def _format_counter(counter: Counter[str]) -> list[str]:
    if not counter:
        return ["- none: 0"]

    return [f"- {name}: {counter[name]}" for name in sorted(counter)]


def _format_clarification_requests(
    processed_requests: list[ProcessedRequest],
) -> list[str]:
    if not processed_requests:
        return ["- none"]

    return [
        f"- {request.id}: {request.triage.short_summary}"
        for request in sorted(processed_requests, key=lambda item: item.id)
        if request.triage is not None
    ]
