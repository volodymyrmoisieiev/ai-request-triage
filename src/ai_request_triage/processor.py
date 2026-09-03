"""Sequential request processing."""

from datetime import datetime
from enum import Enum
import time

from pydantic import BaseModel

from ai_request_triage.llm import classify_request
from ai_request_triage.schemas import InputRequest, TriageResult


class ProcessingStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class ProcessedRequest(BaseModel):
    """Input request with processing result."""

    id: str
    channel: str
    timestamp: datetime
    raw_text: str
    processing_status: ProcessingStatus
    triage: TriageResult | None
    error: str | None


def process_requests(
    requests: list[InputRequest],
    delay_seconds: float = 0.0,
) -> list[ProcessedRequest]:
    """Classify input requests one by one."""

    if delay_seconds < 0:
        raise ValueError("delay_seconds must not be negative")

    processed_requests: list[ProcessedRequest] = []
    total_requests = len(requests)

    for index, request in enumerate(requests):
        print(f"Processing {index + 1}/{total_requests}: {request.id}")

        try:
            triage = classify_request(request)
        except Exception as exc:
            processed_requests.append(
                ProcessedRequest(
                    id=request.id,
                    channel=request.channel,
                    timestamp=request.timestamp,
                    raw_text=request.raw_text,
                    processing_status=ProcessingStatus.FAILED,
                    triage=None,
                    error=_format_error(exc),
                )
            )
            _sleep_between_requests(index, total_requests, delay_seconds)
            continue

        processed_requests.append(
            ProcessedRequest(
                id=request.id,
                channel=request.channel,
                timestamp=request.timestamp,
                raw_text=request.raw_text,
                processing_status=ProcessingStatus.SUCCESS,
                triage=triage,
                error=None,
            )
        )
        _sleep_between_requests(index, total_requests, delay_seconds)

    return processed_requests


def _sleep_between_requests(
    index: int,
    total_requests: int,
    delay_seconds: float,
) -> None:
    if delay_seconds > 0 and index < total_requests - 1:
        time.sleep(delay_seconds)


def _format_error(exc: Exception) -> str:
    message = str(exc).strip()
    if not message:
        return exc.__class__.__name__

    first_line = message.splitlines()[0]
    return f"{exc.__class__.__name__}: {first_line}"
