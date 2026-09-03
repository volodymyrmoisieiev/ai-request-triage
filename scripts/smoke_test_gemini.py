"""Manual smoke test for Gemini classification."""

from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

from ai_request_triage.llm import classify_request
from ai_request_triage.schemas import InputRequest


def main() -> None:
    request = InputRequest(
        id="SMOKE-001",
        channel="Manual",
        timestamp=datetime(2026, 6, 8, 9, 0),
        raw_text=(
            "Потрібно автоматично щопонеділка формувати звіт по Google Ads "
            "і надсилати його в Telegram."
        ),
    )

    result = classify_request(request)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
