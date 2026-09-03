"""Sequential request processing."""

from datetime import datetime
from enum import Enum

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


def process_requests(requests: list[InputRequest]) -> list[ProcessedRequest]:
    """Classify input requests one by one."""

    processed_requests: list[ProcessedRequest] = []

    for request in requests:
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

    return processed_requests


def _format_error(exc: Exception) -> str:
    message = str(exc).strip()
    if not message:
        return exc.__class__.__name__

    first_line = message.splitlines()[0]
    return f"{exc.__class__.__name__}: {first_line}"
