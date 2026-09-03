"""Custom exceptions for input loading."""


class MissingInputFileError(FileNotFoundError):
    """Raised when the input CSV file does not exist."""


class MissingRequiredColumnsError(ValueError):
    """Raised when the input CSV file is missing required columns."""


class InvalidCSVRowError(ValueError):
    """Raised when a CSV row cannot be validated."""


class MissingGeminiAPIKeyError(ValueError):
    """Raised when GEMINI_API_KEY is not configured."""


class GeminiClassificationError(RuntimeError):
    """Raised when Gemini classification fails."""


class InvalidStructuredResponseError(ValueError):
    """Raised when Gemini does not return a valid TriageResult."""
