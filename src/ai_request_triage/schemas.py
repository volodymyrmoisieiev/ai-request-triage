"""Pydantic schemas for request triage data."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, field_validator, model_validator


class InputRequest(BaseModel):
    """One row from the input requests CSV."""

    id: str
    channel: str
    timestamp: datetime
    raw_text: str

    @field_validator("id", "channel", "raw_text")
    @classmethod
    def validate_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Value must not be empty")
        return value


class TriageCategory(str, Enum):
    AUTOMATION = "автоматизація"
    INTEGRATION = "інтеграція"
    REPORT_ANALYTICS = "звіт/аналітика"
    BUG_SUPPORT = "баг/підтримка"
    QUESTION_CONSULTATION = "питання/консультація"
    OUT_OF_SCOPE = "поза скоупом"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TriageStatus(str, Enum):
    READY = "ready"
    NEEDS_CLARIFICATION = "needs_clarification"
    NO_ACTION = "no_action"
    OUT_OF_SCOPE = "out_of_scope"


class TriageResult(BaseModel):
    """Structured triage result for a request."""

    category: TriageCategory
    target_department: str | None
    priority: Priority
    short_summary: str
    requested_actions: list[str]
    needs_clarification: bool
    clarification_questions: list[str]
    triage_status: TriageStatus
    systems: list[str]
    references_previous_request: bool
    related_request_id: str | None = None

    @field_validator("short_summary")
    @classmethod
    def validate_short_summary_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("short_summary must not be empty")
        return value

    @model_validator(mode="after")
    def validate_consistency(self) -> "TriageResult":
        if (
            self.triage_status == TriageStatus.NEEDS_CLARIFICATION
            and not self.needs_clarification
        ):
            raise ValueError(
                "needs_clarification must be true when triage_status is "
                "needs_clarification"
            )

        if self.needs_clarification and not self.clarification_questions:
            raise ValueError(
                "clarification_questions must contain at least one question "
                "when needs_clarification is true"
            )

        if not self.references_previous_request and self.related_request_id is not None:
            raise ValueError(
                "related_request_id must be null when references_previous_request "
                "is false"
            )

        if self.triage_status == TriageStatus.NO_ACTION and self.requested_actions:
            raise ValueError(
                "requested_actions must be empty when triage_status is no_action"
            )

        return self
