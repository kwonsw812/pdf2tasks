"""Text normalization functions for preprocessing."""

import re
import unicodedata
from typing import Optional
from .exceptions import NormalizationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TextNormalizer:
    """Text normalization handler for PDF content."""

    def __init__(
        self,
        normalize_unicode: bool = True,
        remove_control_chars: bool = True,
        normalize_whitespace: bool = True,
    ):
        """
        Initialize text normalizer.

        Args:
            normalize_unicode: Apply Unicode NFC normalization
            remove_control_chars: Remove control characters
            normalize_whitespace: Normalize whitespace (consecutive spaces, etc.)
        """
        self.normalize_unicode = normalize_unicode
        self.remove_control_chars = remove_control_chars
        self.normalize_whitespace = normalize_whitespace

    def normalize(self, text: str) -> str:
        """
        Normalize text with all enabled options.

        Args:
            text: Input text to normalize

        Returns:
            Normalized text

        Raises:
            NormalizationError: If normalization fails
        """
        try:
            if not text:
                return ""

            result = text

            # Unicode normalization (NFC)
            if self.normalize_unicode:
                result = self._normalize_unicode(result)

            # Remove control characters
            if self.remove_control_chars:
                result = self._remove_control_characters(result)

            # Normalize whitespace
            if self.normalize_whitespace:
                result = self._normalize_whitespace(result)

            return result

        except Exception as e:
            logger.error(f"Text normalization failed: {e}")
            raise NormalizationError(f"Failed to normalize text: {e}") from e

    def _normalize_unicode(self, text: str) -> str:
        """
        Normalize Unicode text using NFC (Canonical Composition).

        Args:
            text: Input text

        Returns:
            Unicode normalized text
        """
        # NFC: Canonical decomposition followed by canonical composition
        return unicodedata.normalize("NFC", text)

    def _remove_control_characters(self, text: str) -> str:
        """
        Remove control characters except tab, newline, and carriage return.

        Args:
            text: Input text

        Returns:
            Text with control characters removed
        """
        # Keep tab (\t), newline (\n), carriage return (\r)
        return "".join(
            char
            for char in text
            if unicodedata.category(char)[0] != "C" or char in ["\t", "\n", "\r"]
        )

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.

        - Multiple consecutive spaces → single space
        - Multiple consecutive newlines → double newline (preserve paragraph breaks)
        - Remove trailing/leading whitespace per line

        Args:
            text: Input text

        Returns:
            Text with normalized whitespace
        """
        # Split into lines to preserve line structure
        lines = text.split("\n")

        # Process each line
        normalized_lines = []
        for line in lines:
            # Replace consecutive spaces with single space
            line = re.sub(r"[ \t]+", " ", line)
            # Remove leading/trailing whitespace
            line = line.strip()
            normalized_lines.append(line)

        # Join lines
        result = "\n".join(normalized_lines)

        # Replace 3+ consecutive newlines with 2 newlines (preserve paragraph breaks)
        result = re.sub(r"\n{3,}", "\n\n", result)

        return result.strip()

    def normalize_batch(self, texts: list[str]) -> list[str]:
        """
        Normalize multiple texts in batch.

        Args:
            texts: List of texts to normalize

        Returns:
            List of normalized texts
        """
        return [self.normalize(text) for text in texts]

    def clean_special_characters(
        self, text: str, keep_chars: Optional[str] = None
    ) -> str:
        """
        Remove special characters, keeping only alphanumeric and specified characters.

        Args:
            text: Input text
            keep_chars: Additional characters to keep (e.g., ".,!?")

        Returns:
            Text with special characters removed
        """
        if keep_chars is None:
            # Default: keep common punctuation
            keep_chars = ".,!?;:()[]{}'\"-\n\t "

        # Build pattern: keep alphanumeric (including Korean), whitespace, and specified chars
        pattern = r"[^\w\s" + re.escape(keep_chars) + "]"

        # Remove characters not matching the pattern
        result = re.sub(pattern, "", text, flags=re.UNICODE)

        return result

    def remove_excessive_punctuation(self, text: str) -> str:
        """
        Remove excessive consecutive punctuation marks.

        Args:
            text: Input text

        Returns:
            Text with excessive punctuation removed
        """
        # Replace 3+ consecutive punctuation marks with 2
        result = re.sub(r"([.,!?;:]){3,}", r"\1\1", text)
        return result

    def normalize_quotes(self, text: str) -> str:
        """
        Normalize different types of quotes to standard quotes.

        Args:
            text: Input text

        Returns:
            Text with normalized quotes
        """
        # Single quotes
        text = re.sub(r"[''`]", "'", text)

        # Double quotes
        text = re.sub(r"[""「」『』]", '"', text)

        return text

    def remove_urls(self, text: str) -> str:
        """
        Remove URLs from text.

        Args:
            text: Input text

        Returns:
            Text with URLs removed
        """
        # Pattern for URLs
        url_pattern = r"https?://\S+|www\.\S+"
        return re.sub(url_pattern, "", text)

    def normalize_numbers(self, text: str) -> str:
        """
        Normalize number formats (e.g., full-width to half-width).

        Args:
            text: Input text

        Returns:
            Text with normalized numbers
        """
        # Full-width digits to half-width
        trans_table = str.maketrans("０１２３４５６７８９", "0123456789")
        return text.translate(trans_table)
