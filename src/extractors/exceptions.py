"""Custom exceptions for PDF extraction."""


class PDFExtractorError(Exception):
    """Base exception for PDF extractor errors."""

    pass


class FileNotFoundError(PDFExtractorError):
    """Raised when PDF file is not found."""

    pass


class PDFParseError(PDFExtractorError):
    """Raised when PDF parsing fails due to corrupted file."""

    pass


class EncryptedPDFError(PDFExtractorError):
    """Raised when PDF is encrypted and cannot be processed."""

    pass


class ImageExtractionError(PDFExtractorError):
    """Raised when image extraction fails."""

    pass


class DiskSpaceError(PDFExtractorError):
    """Raised when there is insufficient disk space."""

    pass
