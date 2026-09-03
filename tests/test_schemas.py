from datetime import datetime

import pytest
from pydantic import ValidationError

from ai_request_triage.schemas import InputRequest


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
