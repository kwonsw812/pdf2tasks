"""Custom exceptions for OCR processing."""


class OCRError(Exception):
    """Base exception for OCR errors."""

    pass


class ImageLoadError(OCRError):
    """Raised when image loading fails."""

    pass


class OCRTimeoutError(OCRError):
    """Raised when OCR processing times out."""

    pass


class TesseractNotFoundError(OCRError):
    """Raised when Tesseract OCR is not installed or not found."""

    pass


class LanguageDataNotFoundError(OCRError):
    """Raised when required language data is not available."""

    pass


class PreprocessingError(OCRError):
    """Raised when image preprocessing fails."""

    pass


class LowConfidenceError(OCRError):
    """Raised when OCR confidence is too low."""

    pass
