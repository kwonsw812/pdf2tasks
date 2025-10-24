"""Header and footer removal logic for PDF preprocessing."""

import re
from typing import List, Set, Tuple, Optional
from collections import Counter
from ..types.models import PDFExtractResult, PDFPage, ExtractedText
from ..utils.logger import get_logger

logger = get_logger(__name__)


class HeaderFooterRemover:
    """Removes headers and footers from extracted PDF content."""

    def __init__(
        self,
        min_repetition: int = 3,
        position_threshold: float = 50.0,
        similarity_threshold: float = 0.9,
    ):
        """
        Initialize header/footer remover.

        Args:
            min_repetition: Minimum number of page repetitions to consider as header/footer
            position_threshold: Y-position threshold for header (top) and footer (bottom) in points
            similarity_threshold: Text similarity threshold (0.0-1.0) to consider as same pattern
        """
        self.min_repetition = min_repetition
        self.position_threshold = position_threshold
        self.similarity_threshold = similarity_threshold
        self.detected_header_patterns: Set[str] = set()
        self.detected_footer_patterns: Set[str] = set()

    def remove_headers_footers(
        self, pdf_result: PDFExtractResult
    ) -> Tuple[PDFExtractResult, List[str], List[str]]:
        """
        Remove headers and footers from PDF extraction result.

        Args:
            pdf_result: Extracted PDF content

        Returns:
            Tuple of (cleaned_result, header_patterns, footer_patterns)
        """
        logger.info("Starting header/footer detection and removal")

        # Reset detected patterns
        self.detected_header_patterns.clear()
        self.detected_footer_patterns.clear()

        # Detect header/footer patterns
        header_patterns = self._detect_header_patterns(pdf_result.pages)
        footer_patterns = self._detect_footer_patterns(pdf_result.pages)

        logger.info(
            f"Detected {len(header_patterns)} header patterns and {len(footer_patterns)} footer patterns"
        )

        # Store detected patterns
        self.detected_header_patterns.update(header_patterns)
        self.detected_footer_patterns.update(footer_patterns)

        # Create cleaned pages
        cleaned_pages = []
        for page in pdf_result.pages:
            cleaned_page = self._remove_patterns_from_page(
                page, header_patterns, footer_patterns
            )
            cleaned_pages.append(cleaned_page)

        # Create new result with cleaned pages
        cleaned_result = PDFExtractResult(
            metadata=pdf_result.metadata, pages=cleaned_pages
        )

        return cleaned_result, list(header_patterns), list(footer_patterns)

    def _detect_header_patterns(self, pages: List[PDFPage]) -> Set[str]:
        """
        Detect header patterns by analyzing top text blocks across pages.

        Args:
            pages: List of PDF pages

        Returns:
            Set of header text patterns
        """
        if len(pages) < self.min_repetition:
            return set()

        # Collect top text blocks from each page
        top_texts = []
        for page in pages:
            page_top_texts = self._get_top_texts(page)
            top_texts.append(page_top_texts)

        # Find repeated patterns
        patterns = self._find_repeated_patterns(top_texts)

        logger.debug(f"Detected header patterns: {patterns}")
        return patterns

    def _detect_footer_patterns(self, pages: List[PDFPage]) -> Set[str]:
        """
        Detect footer patterns by analyzing bottom text blocks across pages.

        Args:
            pages: List of PDF pages

        Returns:
            Set of footer text patterns
        """
        if len(pages) < self.min_repetition:
            return set()

        # Collect bottom text blocks from each page
        bottom_texts = []
        for page in pages:
            page_bottom_texts = self._get_bottom_texts(page)
            bottom_texts.append(page_bottom_texts)

        # Find repeated patterns
        patterns = self._find_repeated_patterns(bottom_texts)

        logger.debug(f"Detected footer patterns: {patterns}")
        return patterns

    def _get_top_texts(self, page: PDFPage) -> List[str]:
        """
        Get text blocks from the top region of a page.

        Args:
            page: PDF page

        Returns:
            List of text strings from top region
        """
        top_texts = []
        for text_block in page.text:
            if text_block.metadata and text_block.metadata.position:
                # Check if text is in top region
                if text_block.metadata.position.y <= self.position_threshold:
                    top_texts.append(text_block.text.strip())

        return top_texts

    def _get_bottom_texts(self, page: PDFPage) -> List[str]:
        """
        Get text blocks from the bottom region of a page.

        Args:
            page: PDF page

        Returns:
            List of text strings from bottom region
        """
        bottom_texts = []

        # Find maximum Y position on this page to determine bottom region
        max_y = 0.0
        for text_block in page.text:
            if text_block.metadata and text_block.metadata.position:
                max_y = max(max_y, text_block.metadata.position.y)

        # Calculate bottom threshold (e.g., last 50 points from bottom)
        bottom_threshold = max_y - self.position_threshold

        for text_block in page.text:
            if text_block.metadata and text_block.metadata.position:
                # Check if text is in bottom region
                if text_block.metadata.position.y >= bottom_threshold:
                    bottom_texts.append(text_block.text.strip())

        return bottom_texts

    def _find_repeated_patterns(
        self, page_texts: List[List[str]]
    ) -> Set[str]:
        """
        Find text patterns that repeat across multiple pages.

        Args:
            page_texts: List of text lists (one per page)

        Returns:
            Set of repeated text patterns
        """
        # Flatten all texts and count occurrences
        all_texts = [text for texts in page_texts for text in texts if text]

        if not all_texts:
            return set()

        # Count text occurrences
        text_counter = Counter(all_texts)

        # Filter by minimum repetition
        patterns = {
            text
            for text, count in text_counter.items()
            if count >= self.min_repetition
        }

        # Also check for page number patterns (e.g., "Page 1", "1 / 10")
        page_number_patterns = self._detect_page_number_patterns(all_texts)
        patterns.update(page_number_patterns)

        return patterns

    def _detect_page_number_patterns(self, texts: List[str]) -> Set[str]:
        """
        Detect page number patterns using regex.

        Args:
            texts: List of text strings

        Returns:
            Set of page number pattern strings
        """
        patterns = set()

        # Common page number patterns
        page_patterns = [
            r"^\d+$",  # Just a number
            r"^Page\s+\d+$",  # "Page 1"
            r"^\d+\s*/\s*\d+$",  # "1 / 10"
            r"^-\s*\d+\s*-$",  # "- 1 -"
            r"^\d+\s+페이지$",  # "1 페이지"
            r"^p\.\s*\d+$",  # "p. 1"
        ]

        for text in texts:
            for pattern in page_patterns:
                if re.match(pattern, text.strip(), re.IGNORECASE):
                    patterns.add(text)
                    break

        return patterns

    def _remove_patterns_from_page(
        self, page: PDFPage, header_patterns: Set[str], footer_patterns: Set[str]
    ) -> PDFPage:
        """
        Remove header/footer patterns from a single page.

        Args:
            page: PDF page
            header_patterns: Set of header patterns to remove
            footer_patterns: Set of footer patterns to remove

        Returns:
            Cleaned PDF page
        """
        # Filter out text blocks matching patterns
        cleaned_text = []
        for text_block in page.text:
            text_stripped = text_block.text.strip()

            # Check if text matches any pattern
            is_header_footer = False

            # Exact match
            if text_stripped in header_patterns or text_stripped in footer_patterns:
                is_header_footer = True

            # Fuzzy match for slight variations
            if not is_header_footer:
                for pattern in header_patterns | footer_patterns:
                    if self._is_similar(text_stripped, pattern):
                        is_header_footer = True
                        break

            if not is_header_footer:
                cleaned_text.append(text_block)

        # Create cleaned page
        cleaned_page = PDFPage(
            page_number=page.page_number,
            text=cleaned_text,
            images=page.images,
            tables=page.tables,
        )

        return cleaned_page

    def _is_similar(self, text1: str, text2: str) -> bool:
        """
        Check if two texts are similar based on threshold.

        Args:
            text1: First text
            text2: Second text

        Returns:
            True if texts are similar
        """
        if not text1 or not text2:
            return False

        # Simple similarity: Levenshtein-like ratio
        # For efficiency, use a simple character overlap ratio
        set1 = set(text1.lower())
        set2 = set(text2.lower())

        if not set1 or not set2:
            return False

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        similarity = intersection / union if union > 0 else 0.0

        return similarity >= self.similarity_threshold

    def get_detected_patterns(self) -> Tuple[List[str], List[str]]:
        """
        Get detected header and footer patterns.

        Returns:
            Tuple of (header_patterns, footer_patterns)
        """
        return list(self.detected_header_patterns), list(
            self.detected_footer_patterns
        )
