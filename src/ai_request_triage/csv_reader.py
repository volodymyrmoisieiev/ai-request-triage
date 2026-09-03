"""CSV loading for input requests."""

import csv
from pathlib import Path

from pydantic import ValidationError

from ai_request_triage.exceptions import (
    InvalidCSVRowError,
    MissingInputFileError,
    MissingRequiredColumnsError,
)
from ai_request_triage.schemas import InputRequest

REQUIRED_COLUMNS = {"id", "channel", "timestamp", "raw_text"}


def read_input_requests(csv_path: str | Path) -> list[InputRequest]:
    """Read and validate input requests from a CSV file."""

    path = Path(csv_path)
    if not path.exists():
        raise MissingInputFileError(f"Input file not found: {path}")

    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = set(reader.fieldnames or [])
        missing_columns = REQUIRED_COLUMNS - fieldnames

        if missing_columns:
            columns = ", ".join(sorted(missing_columns))
            raise MissingRequiredColumnsError(f"Missing required columns: {columns}")

        requests: list[InputRequest] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                requests.append(InputRequest(**row))
            except ValidationError as exc:
                raise InvalidCSVRowError(f"Invalid CSV row {row_number}: {exc}") from exc

    return requests
