"""Custom exceptions for LLM operations."""


class LLMError(Exception):
    """Base exception for LLM errors."""

    pass


class APIConnectionError(LLMError):
    """Raised when connection to LLM API fails."""

    pass


class APIKeyError(LLMError):
    """Raised when API key is missing or invalid."""

    pass


class APIRateLimitError(LLMError):
    """Raised when API rate limit is exceeded."""

    pass


class APITimeoutError(LLMError):
    """Raised when API request times out."""

    pass


class JSONParseError(LLMError):
    """Raised when JSON parsing fails."""

    pass


class PromptTooLongError(LLMError):
    """Raised when prompt exceeds token limit."""

    pass


class TaskIdentificationError(LLMError):
    """Raised when task identification fails."""

    pass


class DependencyAnalysisError(LLMError):
    """Raised when dependency analysis fails."""

    pass


# TaskWriter-specific exceptions


class TaskWriterError(LLMError):
    """Base exception for TaskWriter errors."""

    pass


class PromptBuildError(TaskWriterError):
    """Raised when prompt generation fails."""

    pass


class LLMCallError(TaskWriterError):
    """Raised when LLM API call fails."""

    pass


class MarkdownParseError(TaskWriterError):
    """Raised when Markdown parsing fails."""

    pass


class SubTaskValidationError(TaskWriterError):
    """Raised when sub-task validation fails."""

    pass
