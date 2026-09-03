"""Custom exceptions for input loading."""


class MissingInputFileError(FileNotFoundError):
    """Raised when the input CSV file does not exist."""


class MissingRequiredColumnsError(ValueError):
    """Raised when the input CSV file is missing required columns."""


class InvalidCSVRowError(ValueError):
    """Raised when a CSV row cannot be validated."""
