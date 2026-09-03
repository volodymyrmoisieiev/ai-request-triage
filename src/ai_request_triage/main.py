"""Application runner for request triage."""

import argparse
import os
from pathlib import Path

from ai_request_triage.csv_reader import read_input_requests
from ai_request_triage.exceptions import (
    InvalidCSVRowError,
    MissingGeminiAPIKeyError,
    MissingInputFileError,
    MissingRequiredColumnsError,
)
from ai_request_triage.processor import (
    ProcessedRequest,
    ProcessingStatus,
    process_requests,
)
from ai_request_triage.report import write_markdown_report, write_output_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run AI request triage.")
    parser.add_argument("--input", default="input_requests.csv", help="Input CSV path.")
    parser.add_argument("--output-dir", default="output", help="Output directory.")
    parser.add_argument(
        "--request-delay",
        type=float,
        default=0.0,
        help="Delay between requests in seconds.",
    )
    return parser


def run(
    input_path: str | Path,
    output_dir: str | Path,
    request_delay: float = 0.0,
) -> int:
    try:
        _ensure_gemini_api_key()
        requests = read_input_requests(input_path)
        processed_requests = process_requests(requests, delay_seconds=request_delay)

        output_directory = Path(output_dir)
        output_directory.mkdir(parents=True, exist_ok=True)

        json_path = output_directory / "output.json"
        report_path = output_directory / "report.md"

        write_output_json(processed_requests, json_path)
        write_markdown_report(processed_requests, report_path)

        _print_summary(processed_requests, json_path, report_path)
    except (
        MissingGeminiAPIKeyError,
        MissingInputFileError,
        MissingRequiredColumnsError,
        InvalidCSVRowError,
    ) as exc:
        print(f"Error: {exc}")
        return 1
    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    return 0


def main() -> int:
    args = build_parser().parse_args()
    return run(
        input_path=args.input,
        output_dir=args.output_dir,
        request_delay=args.request_delay,
    )


def _ensure_gemini_api_key() -> None:
    if not os.getenv("GEMINI_API_KEY"):
        raise MissingGeminiAPIKeyError("GEMINI_API_KEY is not configured")


def _print_summary(
    processed_requests: list[ProcessedRequest],
    json_path: Path,
    report_path: Path,
) -> None:
    total_count = len(processed_requests)
    success_count = sum(
        request.processing_status == ProcessingStatus.SUCCESS
        for request in processed_requests
    )
    failed_count = total_count - success_count

    print(f"Processed: {total_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Output: {json_path}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    raise SystemExit(main())
