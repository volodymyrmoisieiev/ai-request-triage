FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src

RUN python -m pip install --no-cache-dir .

ENTRYPOINT ["python", "-m", "ai_request_triage.main"]
