"""Custom exceptions for OpenAPI module."""


class OpenAPIError(Exception):
    """Base exception for OpenAPI module."""

    pass


class OpenAPILoadError(OpenAPIError):
    """Failed to load OpenAPI spec file."""

    pass


class OpenAPIParseError(OpenAPIError):
    """Failed to parse OpenAPI spec."""

    pass
