"""Pydantic schemas for input data."""

from datetime import datetime

from pydantic import BaseModel, field_validator


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
