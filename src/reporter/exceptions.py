"""Custom exceptions for Reporter module."""


class ReporterError(Exception):
    """Base exception for Reporter module."""

    pass


class ReportGenerationError(ReporterError):
    """Exception raised when report generation fails."""

    pass


class ReportSaveError(ReporterError):
    """Exception raised when saving report fails."""

    pass


class InvalidMetricsError(ReporterError):
    """Exception raised when metrics data is invalid."""

    pass
