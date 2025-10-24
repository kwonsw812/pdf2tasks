"""OCR text recognition using Tesseract."""

import os
import time
from typing import Optional
import pytesseract
from PIL import Image
from ..types.models import OCRResult, OCRWord, BoundingBox
from ..utils.logger import get_logger
from .config import TesseractConfig, get_default_config
from .exceptions import ImageLoadError, OCRTimeoutError, OCRError

logger = get_logger(__name__)


class OCRRecognizer:
    """Recognize text from images using Tesseract OCR."""

    def __init__(
        self,
        config: Optional[TesseractConfig] = None,
        timeout: int = 30,
        include_words: bool = False,
    ):
        """
        Initialize OCRRecognizer.

        Args:
            config: Tesseract configuration (default: auto-detect)
            timeout: Processing timeout in seconds (default: 30)
            include_words: Include word-level details (default: False)
        """
        self.config = config or get_default_config()
        self.timeout = timeout
        self.include_words = include_words

        # Set tesseract command path
        pytesseract.pytesseract.tesseract_cmd = self.config.tesseract_cmd

        logger.info(
            f"OCRRecognizer initialized: config={self.config}, "
            f"timeout={timeout}s, include_words={include_words}"
        )

    def recognize(self, image_path: str) -> OCRResult:
        """
        Recognize text from an image.

        Args:
            image_path: Path to image file

        Returns:
            OCRResult with recognized text and confidence

        Raises:
            ImageLoadError: If image cannot be loaded
            OCRTimeoutError: If OCR processing times out
            OCRError: If OCR processing fails
        """
        if not os.path.exists(image_path):
            raise ImageLoadError(f"Image file not found: {image_path}")

        logger.info(f"Starting OCR on: {image_path}")
        start_time = time.time()

        try:
            # Load image
            img = Image.open(image_path)

            # Prepare config dict
            config_dict = self.config.get_config_dict()

            # Extract text
            text = pytesseract.image_to_string(
                img,
                lang=config_dict["lang"],
                config=config_dict["config"],
                timeout=self.timeout
            )

            # Get detailed data for confidence and word-level info
            data = pytesseract.image_to_data(
                img,
                lang=config_dict["lang"],
                config=config_dict["config"],
                output_type=pytesseract.Output.DICT,
                timeout=self.timeout
            )

            # Calculate overall confidence
            confidences = [
                float(conf) for conf in data["conf"]
                if conf != -1 and str(conf).replace('.', '', 1).isdigit()
            ]

            if confidences:
                overall_confidence = sum(confidences) / len(confidences)
            else:
                overall_confidence = 0.0

            # Extract word-level details if requested
            words = None
            if self.include_words:
                words = self._extract_words(data)

            processing_time = time.time() - start_time

            result = OCRResult(
                text=text.strip(),
                confidence=overall_confidence,
                words=words,
                processing_time=processing_time,
            )

            logger.info(
                f"OCR completed: confidence={overall_confidence:.2f}%, "
                f"chars={len(result.text)}, time={processing_time:.2f}s"
            )

            return result

        except IOError as e:
            raise ImageLoadError(f"Failed to load image: {str(e)}")
        except RuntimeError as e:
            if "timeout" in str(e).lower():
                raise OCRTimeoutError(
                    f"OCR processing timed out after {self.timeout}s"
                )
            raise OCRError(f"OCR processing failed: {str(e)}")
        except Exception as e:
            raise OCRError(f"Unexpected error during OCR: {str(e)}")

    def _extract_words(self, data: dict) -> list[OCRWord]:
        """
        Extract word-level details from OCR data.

        Args:
            data: OCR data from image_to_data

        Returns:
            List of OCRWord objects
        """
        words = []
        n_boxes = len(data["text"])

        for i in range(n_boxes):
            # Skip empty text
            text = data["text"][i].strip()
            if not text:
                continue

            # Skip low confidence (-1)
            conf = data["conf"][i]
            if conf == -1:
                continue

            # Convert confidence to float
            try:
                confidence = float(conf)
            except (ValueError, TypeError):
                confidence = 0.0

            # Extract bounding box
            x = data["left"][i]
            y = data["top"][i]
            w = data["width"][i]
            h = data["height"][i]

            bbox = BoundingBox(x0=x, y0=y, x1=x + w, y1=y + h)

            word = OCRWord(text=text, confidence=confidence, bbox=bbox)
            words.append(word)

        logger.info(f"Extracted {len(words)} words")
        return words

    def recognize_region(
        self, image_path: str, bbox: tuple[int, int, int, int]
    ) -> OCRResult:
        """
        Recognize text from a specific region of an image.

        Args:
            image_path: Path to image file
            bbox: Bounding box as (left, top, right, bottom)

        Returns:
            OCRResult with recognized text

        Raises:
            ImageLoadError: If image cannot be loaded
            OCRError: If OCR processing fails
        """
        if not os.path.exists(image_path):
            raise ImageLoadError(f"Image file not found: {image_path}")

        logger.info(f"Starting OCR on region {bbox} of: {image_path}")
        start_time = time.time()

        try:
            # Load image
            img = Image.open(image_path)

            # Crop to region
            img_region = img.crop(bbox)

            # Prepare config dict
            config_dict = self.config.get_config_dict()

            # Extract text
            text = pytesseract.image_to_string(
                img_region,
                lang=config_dict["lang"],
                config=config_dict["config"],
                timeout=self.timeout
            )

            # Get confidence
            data = pytesseract.image_to_data(
                img_region,
                lang=config_dict["lang"],
                config=config_dict["config"],
                output_type=pytesseract.Output.DICT,
                timeout=self.timeout
            )

            confidences = [
                float(conf) for conf in data["conf"]
                if conf != -1 and str(conf).replace('.', '', 1).isdigit()
            ]

            overall_confidence = (
                sum(confidences) / len(confidences) if confidences else 0.0
            )

            processing_time = time.time() - start_time

            result = OCRResult(
                text=text.strip(),
                confidence=overall_confidence,
                processing_time=processing_time,
            )

            logger.info(
                f"Region OCR completed: confidence={overall_confidence:.2f}%, "
                f"time={processing_time:.2f}s"
            )

            return result

        except IOError as e:
            raise ImageLoadError(f"Failed to load image: {str(e)}")
        except Exception as e:
            raise OCRError(f"Region OCR failed: {str(e)}")

    def get_languages(self) -> list[str]:
        """
        Get list of available Tesseract languages.

        Returns:
            List of language codes
        """
        try:
            langs = pytesseract.get_languages(config=self.config.tesseract_cmd)
            return langs
        except Exception as e:
            logger.error(f"Failed to get languages: {e}")
            return []

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"OCRRecognizer(config={self.config}, timeout={self.timeout}s, "
            f"include_words={self.include_words})"
        )
