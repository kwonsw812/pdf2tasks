"""Custom exceptions for FileSplitter module."""


class FileSplitterError(Exception):
    """Base exception for FileSplitter errors."""

    pass


class FileWriteError(FileSplitterError):
    """Raised when file writing fails."""

    pass


class PermissionError(FileSplitterError):
    """Raised when there are permission issues accessing files or directories."""

    pass


class DirectoryCreationError(FileSplitterError):
    """Raised when directory creation fails."""

    pass


class InvalidTaskDataError(FileSplitterError):
    """Raised when task data is invalid or incomplete."""

    pass
