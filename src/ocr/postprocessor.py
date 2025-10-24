"""OCR result postprocessing for improved text quality."""

import re
from typing import Optional
from ..types.models import OCRResult, OCRWord
from ..utils.logger import get_logger

logger = get_logger(__name__)


class OCRPostprocessor:
    """Postprocess OCR results to improve text quality."""

    # Common OCR misrecognition patterns
    MISRECOGNITION_PATTERNS = {
        # Number vs Letter confusion
        r'\b0(?=[A-Za-z])': 'O',  # 0 -> O when followed by letters
        r'(?<=[A-Za-z])0\b': 'O',  # 0 -> O when preceded by letters
        r'\bl(?=\d)': '1',  # l -> 1 when followed by digits
        r'(?<=\d)l\b': '1',  # l -> 1 when preceded by digits
        r'\bI(?=\d)': '1',  # I -> 1 when followed by digits
        # Special character corrections
        r'，': ',',  # Full-width comma to half-width
        r'．': '.',  # Full-width period to half-width
        r'：': ':',  # Full-width colon to half-width
        r'；': ';',  # Full-width semicolon to half-width
    }

    def __init__(
        self,
        normalize_whitespace: bool = True,
        fix_misrecognition: bool = True,
        filter_low_confidence: bool = False,
        confidence_threshold: float = 30.0,
        remove_special_chars: bool = False,
    ):
        """
        Initialize OCRPostprocessor.

        Args:
            normalize_whitespace: Normalize whitespace characters (default: True)
            fix_misrecognition: Apply common misrecognition fixes (default: True)
            filter_low_confidence: Filter out low confidence words (default: False)
            confidence_threshold: Minimum confidence for words (default: 30.0)
            remove_special_chars: Remove special characters (default: False)
        """
        self.normalize_whitespace = normalize_whitespace
        self.fix_misrecognition = fix_misrecognition
        self.filter_low_confidence = filter_low_confidence
        self.confidence_threshold = confidence_threshold
        self.remove_special_chars = remove_special_chars

        logger.info(
            f"OCRPostprocessor initialized: normalize_whitespace={normalize_whitespace}, "
            f"fix_misrecognition={fix_misrecognition}, "
            f"filter_low_confidence={filter_low_confidence}({confidence_threshold}%), "
            f"remove_special_chars={remove_special_chars}"
        )

    def postprocess(self, result: OCRResult) -> OCRResult:
        """
        Postprocess OCR result.

        Args:
            result: Original OCR result

        Returns:
            Postprocessed OCR result
        """
        logger.info("Starting postprocessing...")

        text = result.text

        # 1. Normalize whitespace
        if self.normalize_whitespace:
            text = self._normalize_whitespace(text)

        # 2. Fix common misrecognitions
        if self.fix_misrecognition:
            text = self._fix_misrecognition(text)

        # 3. Remove special characters if requested
        if self.remove_special_chars:
            text = self._remove_special_chars(text)

        # 4. Filter low confidence words
        filtered_words = None
        if self.filter_low_confidence and result.words:
            filtered_words = self._filter_words(result.words)
            # Rebuild text from filtered words
            if filtered_words:
                text = " ".join([word.text for word in filtered_words])

        # Create new result with processed text
        processed_result = OCRResult(
            text=text,
            confidence=result.confidence,
            words=filtered_words if filtered_words else result.words,
            processing_time=result.processing_time,
        )

        logger.info(
            f"Postprocessing complete: "
            f"original_length={len(result.text)}, "
            f"processed_length={len(text)}"
        )

        return processed_result

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace characters.

        Args:
            text: Input text

        Returns:
            Text with normalized whitespace
        """
        logger.debug("Normalizing whitespace")

        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)

        # Replace multiple newlines with single newline
        text = re.sub(r'\n+', '\n', text)

        # Remove spaces before punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)

        # Trim leading/trailing whitespace
        text = text.strip()

        return text

    def _fix_misrecognition(self, text: str) -> str:
        """
        Fix common OCR misrecognition patterns.

        Args:
            text: Input text

        Returns:
            Text with corrections applied
        """
        logger.debug("Fixing misrecognition patterns")

        for pattern, replacement in self.MISRECOGNITION_PATTERNS.items():
            text = re.sub(pattern, replacement, text)

        return text

    def _remove_special_chars(self, text: str) -> str:
        """
        Remove special characters.

        Args:
            text: Input text

        Returns:
            Text with special characters removed
        """
        logger.debug("Removing special characters")

        # Keep alphanumeric, Korean, spaces, and basic punctuation
        text = re.sub(r'[^\w\s가-힣.,;:!?()\-]', '', text, flags=re.UNICODE)

        return text

    def _filter_words(self, words: list[OCRWord]) -> list[OCRWord]:
        """
        Filter out low confidence words.

        Args:
            words: List of OCR words

        Returns:
            Filtered list of words
        """
        original_count = len(words)

        filtered = [
            word for word in words
            if word.confidence >= self.confidence_threshold
        ]

        filtered_count = original_count - len(filtered)

        if filtered_count > 0:
            logger.info(
                f"Filtered {filtered_count} words below confidence threshold "
                f"({self.confidence_threshold}%)"
            )

        return filtered

    def postprocess_batch(self, results: list[OCRResult]) -> list[OCRResult]:
        """
        Postprocess multiple OCR results.

        Args:
            results: List of OCR results

        Returns:
            List of postprocessed results
        """
        logger.info(f"Postprocessing batch of {len(results)} results...")

        processed_results = []
        for i, result in enumerate(results, 1):
            try:
                processed = self.postprocess(result)
                processed_results.append(processed)
            except Exception as e:
                logger.error(f"Failed to postprocess result {i}: {e}")
                # Keep original result on failure
                processed_results.append(result)

        logger.info(f"Batch postprocessing complete: {len(processed_results)} results")

        return processed_results

    def clean_text(self, text: str) -> str:
        """
        Clean raw text (without OCRResult wrapper).

        Useful for simple text cleaning without full OCR result.

        Args:
            text: Input text

        Returns:
            Cleaned text
        """
        if self.normalize_whitespace:
            text = self._normalize_whitespace(text)

        if self.fix_misrecognition:
            text = self._fix_misrecognition(text)

        if self.remove_special_chars:
            text = self._remove_special_chars(text)

        return text

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"OCRPostprocessor(normalize_whitespace={self.normalize_whitespace}, "
            f"fix_misrecognition={self.fix_misrecognition}, "
            f"filter_low_confidence={self.filter_low_confidence}, "
            f"threshold={self.confidence_threshold}%)"
        )


def create_default_postprocessor() -> OCRPostprocessor:
    """
    Create a default OCRPostprocessor with standard settings.

    Returns:
        OCRPostprocessor instance
    """
    return OCRPostprocessor(
        normalize_whitespace=True,
        fix_misrecognition=True,
        filter_low_confidence=False,
        remove_special_chars=False,
    )
