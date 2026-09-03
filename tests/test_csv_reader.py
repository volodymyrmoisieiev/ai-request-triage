import pytest

from ai_request_triage.csv_reader import read_input_requests
from ai_request_triage.exceptions import (
    InvalidCSVRowError,
    MissingInputFileError,
    MissingRequiredColumnsError,
)


def test_valid_csv_is_loaded_correctly(tmp_path) -> None:
    csv_path = tmp_path / "requests.csv"
    csv_path.write_text(
        "id,channel,timestamp,raw_text\n"
        "REQ-001,Slack,2026-06-08 09:14,Please automate the weekly report.\n",
        encoding="utf-8",
    )

    requests = read_input_requests(csv_path)

    assert len(requests) == 1
    assert requests[0].id == "REQ-001"
    assert requests[0].channel == "Slack"
    assert requests[0].raw_text == "Please automate the weekly report."


def test_missing_file(tmp_path) -> None:
    missing_path = tmp_path / "missing.csv"

    with pytest.raises(MissingInputFileError):
        read_input_requests(missing_path)


def test_missing_required_column(tmp_path) -> None:
    csv_path = tmp_path / "requests.csv"
    csv_path.write_text(
        "id,channel,timestamp\n"
        "REQ-001,Slack,2026-06-08 09:14\n",
        encoding="utf-8",
    )

    with pytest.raises(MissingRequiredColumnsError):
        read_input_requests(csv_path)


def test_invalid_row(tmp_path) -> None:
    csv_path = tmp_path / "requests.csv"
    csv_path.write_text(
        "id,channel,timestamp,raw_text\n"
        ",Slack,2026-06-08 09:14,Please automate the weekly report.\n",
        encoding="utf-8",
    )

    with pytest.raises(InvalidCSVRowError):
        read_input_requests(csv_path)
