"""OCR module for text recognition from images."""

from .ocr_engine import OCREngine, create_ocr_engine
from .config import TesseractConfig, get_default_config, set_tesseract_cmd
from .preprocessor import ImagePreprocessor, create_default_preprocessor
from .recognizer import OCRRecognizer
from .postprocessor import OCRPostprocessor, create_default_postprocessor
from .batch_processor import BatchOCRProcessor
from .exceptions import (
    OCRError,
    ImageLoadError,
    OCRTimeoutError,
    TesseractNotFoundError,
    LanguageDataNotFoundError,
    PreprocessingError,
    LowConfidenceError,
)

__all__ = [
    # Main interface
    "OCREngine",
    "create_ocr_engine",
    # Configuration
    "TesseractConfig",
    "get_default_config",
    "set_tesseract_cmd",
    # Components
    "ImagePreprocessor",
    "create_default_preprocessor",
    "OCRRecognizer",
    "OCRPostprocessor",
    "create_default_postprocessor",
    "BatchOCRProcessor",
    # Exceptions
    "OCRError",
    "ImageLoadError",
    "OCRTimeoutError",
    "TesseractNotFoundError",
    "LanguageDataNotFoundError",
    "PreprocessingError",
    "LowConfidenceError",
]
