"""Custom exceptions for preprocessor module."""


class PreprocessorError(Exception):
    """Base exception for preprocessor errors."""

    pass


class NormalizationError(PreprocessorError):
    """Raised when text normalization fails."""

    pass


class SegmentationError(PreprocessorError):
    """Raised when section segmentation fails."""

    pass


class GroupingError(PreprocessorError):
    """Raised when functional grouping fails."""

    pass


class InvalidContentError(PreprocessorError):
    """Raised when content is invalid or empty."""

    pass
