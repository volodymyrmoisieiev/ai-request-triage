from ai_request_triage.main import main, run
from ai_request_triage.processor import ProcessedRequest, ProcessingStatus
from ai_request_triage.schemas import InputRequest, TriageCategory, TriageResult


def make_triage_result() -> TriageResult:
    return TriageResult(
        category=TriageCategory.AUTOMATION,
        target_department=None,
        priority="medium",
        short_summary="Automate a report.",
        requested_actions=["Create automation."],
        needs_clarification=False,
        clarification_questions=[],
        triage_status="ready",
        systems=["Google Ads"],
        references_previous_request=False,
        related_request_id=None,
    )


def make_processed_request(
    request: InputRequest,
    *,
    triage: TriageResult | None,
    error: str | None,
) -> ProcessedRequest:
    return ProcessedRequest(
        id=request.id,
        channel=request.channel,
        timestamp=request.timestamp,
        raw_text=request.raw_text,
        processing_status=ProcessingStatus.FAILED if error else ProcessingStatus.SUCCESS,
        triage=triage,
        error=error,
    )


def test_run_processes_csv_and_writes_outputs(tmp_path, monkeypatch, capsys) -> None:
    input_path = tmp_path / "requests.csv"
    output_dir = tmp_path / "output"
    input_path.write_text(
        "id,channel,timestamp,raw_text\n"
        "REQ-001,Slack,2026-06-08 09:14,Automate the weekly report.\n"
        "REQ-002,Slack,2026-06-08 09:15,This request fails.\n",
        encoding="utf-8",
    )

    def fake_process_requests(requests: list[InputRequest]) -> list[ProcessedRequest]:
        return [
            make_processed_request(
                requests[0],
                triage=make_triage_result(),
                error=None,
            ),
            make_processed_request(
                requests[1],
                triage=None,
                error="RuntimeError: Gemini error",
            ),
        ]

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        "ai_request_triage.main.process_requests",
        fake_process_requests,
    )

    exit_code = run(input_path=input_path, output_dir=output_dir)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert (output_dir / "output.json").exists()
    assert (output_dir / "report.md").exists()
    assert "Processed: 2" in captured.out
    assert "Successful: 1" in captured.out
    assert "Failed: 1" in captured.out
    assert f"Output: {output_dir / 'output.json'}" in captured.out
    assert f"Report: {output_dir / 'report.md'}" in captured.out
    assert "test-key" not in captured.out


def test_run_returns_non_zero_for_missing_input_file(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    exit_code = run(input_path=tmp_path / "missing.csv", output_dir=tmp_path / "output")

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error:" in captured.out
    assert "Input file not found" in captured.out


def test_run_returns_non_zero_for_invalid_csv(tmp_path, monkeypatch, capsys) -> None:
    input_path = tmp_path / "requests.csv"
    input_path.write_text(
        "id,channel,timestamp,raw_text\n"
        ",Slack,2026-06-08 09:14,Automate the weekly report.\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    exit_code = run(input_path=input_path, output_dir=tmp_path / "output")

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error:" in captured.out
    assert "Invalid CSV row" in captured.out


def test_run_returns_non_zero_for_missing_api_key(tmp_path, monkeypatch, capsys) -> None:
    input_path = tmp_path / "requests.csv"
    input_path.write_text(
        "id,channel,timestamp,raw_text\n"
        "REQ-001,Slack,2026-06-08 09:14,Automate the weekly report.\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    exit_code = run(input_path=input_path, output_dir=tmp_path / "output")

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "GEMINI_API_KEY is not configured" in captured.out


def test_main_uses_argparse_values(tmp_path, monkeypatch) -> None:
    input_path = tmp_path / "requests.csv"
    output_dir = tmp_path / "output"
    input_path.write_text(
        "id,channel,timestamp,raw_text\n"
        "REQ-001,Slack,2026-06-08 09:14,Automate the weekly report.\n",
        encoding="utf-8",
    )

    def fake_process_requests(requests: list[InputRequest]) -> list[ProcessedRequest]:
        return [
            make_processed_request(
                requests[0],
                triage=make_triage_result(),
                error=None,
            )
        ]

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        "ai_request_triage.main.process_requests",
        fake_process_requests,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "python -m ai_request_triage.main",
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    exit_code = main()

    assert exit_code == 0
    assert (output_dir / "output.json").exists()
    assert (output_dir / "report.md").exists()
