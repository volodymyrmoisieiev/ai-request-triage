# AI Request Triage

AI Request Triage reads internal company requests from a CSV file. It classifies and structures each request with Gemini. Pydantic validates the input data and the structured output.

The app creates two files:

- `output/output.json`
- `output/report.md`

## Main Features

- CSV validation
- Gemini structured output
- Categories and priorities
- Clarification detection
- Per-request failure handling
- Progress output
- Optional request delay
- Markdown report generation
- Docker support

## Project Structure

- `src/ai_request_triage/schemas.py` - Pydantic models for input requests and triage results
- `src/ai_request_triage/csv_reader.py` - CSV loading and validation
- `src/ai_request_triage/llm.py` - Gemini classification call
- `src/ai_request_triage/prompts.py` - Prompt text for classification
- `src/ai_request_triage/processor.py` - Sequential processing for many requests
- `src/ai_request_triage/report.py` - JSON output and Markdown report generation
- `src/ai_request_triage/main.py` - Command line application runner
- `scripts/smoke_test_gemini.py` - Manual Gemini smoke test
- `tests/` - Automated tests

## Requirements

- Python 3.11+
- Gemini API key
- Docker is optional

## Local Setup

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Install the package:

```powershell
python -m pip install -e .
```

## Environment Variables

`GEMINI_API_KEY` is required. It must contain your Gemini API key.

`GEMINI_MODEL` is optional. The default model is `gemini-3.7-flash`.

Set the required API key in Windows PowerShell:

```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

You can also set the optional model override:

```powershell
$env:GEMINI_MODEL="gemini-3.7-flash"
```

Do not store a real API key in the repository.

## Run the Application

```powershell
python -m ai_request_triage.main --input input_requests.csv --output-dir output --request-delay 2
```

Options:

- `--input` - path to the input CSV file
- `--output-dir` - directory for generated files
- `--request-delay` - delay between requests in seconds

## Output

`output/output.json` contains the full processed result for each request.

`output/report.md` contains a short summary report with counts by category, priority, and department.

Generated output files are ignored by git.

## Docker

Build the image:

```powershell
docker build -t ai-request-triage .
```

Run the container from Windows PowerShell:

```powershell
docker run --rm `
  -e GEMINI_API_KEY=$env:GEMINI_API_KEY `
  -v "${PWD}:/data" `
  ai-request-triage `
  --input /data/input_requests.csv `
  --output-dir /data/output `
  --request-delay 2
```

`GEMINI_MODEL` can optionally be passed with:

```powershell
-e GEMINI_MODEL=$env:GEMINI_MODEL
```

API keys are passed at runtime. They are not stored in the image.

## Tests

Run tests:

```powershell
python -m pytest -v
```

The current local test suite has 59 tests.

## Real Validation

The application was tested on the provided assignment dataset:

- 18 requests processed
- 18 successful
- 0 failed

The original request texts and assignment dataset are not included in this repository.

## Error Handling

One failed LLM request does not stop the full batch.

Invalid structured responses are handled as failed requests.

Gemini 429 and 503 errors are converted into short safe messages.

API keys and raw API responses are not written to output.

## Limitations

- LLM output can be nondeterministic
- API usage has cost and rate limits
- Current processing is sequential
- References to previous requests can be detected, but related request IDs are not resolved automatically
- Model availability and API limits can change
- Request delay helps with rate limits, but it is not a full rate limiter

## Future Improvements

- Controlled async or concurrent processing
- Context resolution for previous requests
- Provider abstraction and optional OpenAI fallback
- Evaluation dataset and classification metrics
- Optional integrations such as Google Sheets or Telegram digest
