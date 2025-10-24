"""Section segmentation algorithm for document structuring."""

import re
from typing import List, Optional, Tuple
from ..types.models import PDFExtractResult, PDFPage, Section, PageRange
from .exceptions import SegmentationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SectionSegmenter:
    """Segments document into hierarchical sections based on headings."""

    def __init__(
        self,
        min_heading_font_size: float = 12.0,
        font_size_ratio_threshold: float = 1.2,
    ):
        """
        Initialize section segmenter.

        Args:
            min_heading_font_size: Minimum font size to consider as heading
            font_size_ratio_threshold: Font size ratio to consider as heading (relative to average)
        """
        self.min_heading_font_size = min_heading_font_size
        self.font_size_ratio_threshold = font_size_ratio_threshold

        # Heading patterns for Korean documents
        self.heading_patterns = [
            # "1. 제목", "2. 제목"
            r"^(\d+)\.\s+(.+)$",
            # "1.1 제목", "2.3 제목"
            r"^(\d+\.\d+)\s+(.+)$",
            # "1.1.1 제목"
            r"^(\d+\.\d+\.\d+)\s+(.+)$",
            # "## 제목" (Markdown style)
            r"^(#{1,6})\s+(.+)$",
            # "가. 제목", "나. 제목" (Korean enumeration)
            r"^([가-힣])\.\s+(.+)$",
            # "[1] 제목"
            r"^\[(\d+)\]\s+(.+)$",
        ]

    def segment(self, pdf_result: PDFExtractResult) -> List[Section]:
        """
        Segment PDF content into hierarchical sections.

        Args:
            pdf_result: Extracted PDF content

        Returns:
            List of top-level sections with nested subsections

        Raises:
            SegmentationError: If segmentation fails
        """
        try:
            logger.info("Starting section segmentation")

            # Calculate average font size for reference
            avg_font_size = self._calculate_average_font_size(pdf_result.pages)
            logger.debug(f"Average font size: {avg_font_size:.2f}")

            # Extract text with metadata
            text_items = self._extract_text_items(pdf_result.pages)

            if not text_items:
                logger.warning("No text items found for segmentation")
                return []

            # Identify headings
            headings = self._identify_headings(text_items, avg_font_size)
            logger.info(f"Identified {len(headings)} headings")

            # Build section hierarchy
            sections = self._build_section_hierarchy(headings, text_items)
            logger.info(f"Built {len(sections)} top-level sections")

            return sections

        except Exception as e:
            logger.error(f"Section segmentation failed: {e}")
            raise SegmentationError(f"Failed to segment sections: {e}") from e

    def _calculate_average_font_size(self, pages: List[PDFPage]) -> float:
        """
        Calculate average font size across all pages.

        Args:
            pages: List of PDF pages

        Returns:
            Average font size
        """
        font_sizes = []
        for page in pages:
            for text_block in page.text:
                if text_block.metadata and text_block.metadata.font_size:
                    font_sizes.append(text_block.metadata.font_size)

        if not font_sizes:
            return 12.0  # Default font size

        return sum(font_sizes) / len(font_sizes)

    def _extract_text_items(
        self, pages: List[PDFPage]
    ) -> List[Tuple[int, str, Optional[float], Optional[float]]]:
        """
        Extract text items with page number, text, font size, and position.

        Args:
            pages: List of PDF pages

        Returns:
            List of tuples: (page_number, text, font_size, y_position)
        """
        text_items = []
        for page in pages:
            for text_block in page.text:
                font_size = None
                y_position = None

                if text_block.metadata:
                    font_size = text_block.metadata.font_size
                    if text_block.metadata.position:
                        y_position = text_block.metadata.position.y

                text_items.append(
                    (page.page_number, text_block.text, font_size, y_position)
                )

        return text_items

    def _identify_headings(
        self,
        text_items: List[Tuple[int, str, Optional[float], Optional[float]]],
        avg_font_size: float,
    ) -> List[Tuple[int, int, str, int, Optional[float]]]:
        """
        Identify heading text items.

        Args:
            text_items: List of text items
            avg_font_size: Average font size for comparison

        Returns:
            List of tuples: (index, page_number, heading_text, level, font_size)
        """
        headings = []

        for idx, (page_num, text, font_size, y_pos) in enumerate(text_items):
            text_stripped = text.strip()
            if not text_stripped:
                continue

            # Check if text matches heading pattern
            level, heading_text = self._match_heading_pattern(text_stripped)

            if level is not None:
                headings.append((idx, page_num, heading_text, level, font_size))
                continue

            # Check if text has heading-like font size
            if font_size and font_size >= self.min_heading_font_size:
                if font_size >= avg_font_size * self.font_size_ratio_threshold:
                    # Infer level based on font size
                    inferred_level = self._infer_level_from_font_size(
                        font_size, avg_font_size
                    )
                    headings.append((idx, page_num, text_stripped, inferred_level, font_size))

        return headings

    def _match_heading_pattern(self, text: str) -> Tuple[Optional[int], Optional[str]]:
        """
        Match text against heading patterns.

        Args:
            text: Text to match

        Returns:
            Tuple of (level, heading_text) or (None, None) if no match
        """
        for pattern in self.heading_patterns:
            match = re.match(pattern, text)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    number_part = groups[0]
                    heading_text = groups[1].strip()

                    # Determine level from number_part
                    level = self._determine_level(number_part)
                    return level, heading_text

        return None, None

    def _determine_level(self, number_part: str) -> int:
        """
        Determine heading level from numbering.

        Args:
            number_part: Numbering part (e.g., "1", "1.1", "##")

        Returns:
            Heading level (1, 2, 3, ...)
        """
        # Count dots for numbered headings
        if "." in number_part:
            # "1.1.1" → level 3
            return number_part.count(".") + 1

        # Count hashes for Markdown-style headings
        if "#" in number_part:
            return len(number_part)

        # Default to level 1
        return 1

    def _infer_level_from_font_size(
        self, font_size: float, avg_font_size: float
    ) -> int:
        """
        Infer heading level from font size.

        Args:
            font_size: Font size of the text
            avg_font_size: Average font size

        Returns:
            Inferred heading level
        """
        ratio = font_size / avg_font_size

        if ratio >= 1.8:
            return 1
        elif ratio >= 1.5:
            return 2
        elif ratio >= 1.2:
            return 3
        else:
            return 4

    def _build_section_hierarchy(
        self,
        headings: List[Tuple[int, int, str, int, Optional[float]]],
        text_items: List[Tuple[int, str, Optional[float], Optional[float]]],
    ) -> List[Section]:
        """
        Build hierarchical section structure from headings.

        Args:
            headings: List of identified headings
            text_items: All text items

        Returns:
            List of top-level sections with nested subsections
        """
        if not headings:
            # No headings found, create single section with all content
            all_text = "\n".join([text for _, text, _, _ in text_items])
            if all_text.strip():
                return [
                    Section(
                        title="Document Content",
                        level=1,
                        content=all_text.strip(),
                        page_range=PageRange(
                            start=text_items[0][0] if text_items else 1,
                            end=text_items[-1][0] if text_items else 1,
                        ),
                        subsections=[],
                    )
                ]
            return []

        sections = []
        stack = []  # Stack to track parent sections

        for i, (idx, page_num, heading_text, level, font_size) in enumerate(headings):
            # Get content between this heading and next
            start_idx = idx + 1
            end_idx = headings[i + 1][0] if i + 1 < len(headings) else len(text_items)

            # Extract content
            content_items = text_items[start_idx:end_idx]
            content = "\n".join([text for _, text, _, _ in content_items if text.strip()])

            # Determine page range
            end_page = (
                headings[i + 1][1] if i + 1 < len(headings) else text_items[-1][0]
            )

            # Create section
            section = Section(
                title=heading_text,
                level=level,
                content=content,
                page_range=PageRange(start=page_num, end=end_page),
                subsections=[],
            )

            # Build hierarchy
            # Pop stack until we find a parent with lower level
            while stack and stack[-1][0] >= level:
                stack.pop()

            if not stack:
                # Top-level section
                sections.append(section)
                stack.append((level, section))
            else:
                # Add as subsection to parent
                parent_section = stack[-1][1]
                parent_section.subsections.append(section)
                stack.append((level, section))

        return sections

    def flatten_sections(self, sections: List[Section]) -> List[Section]:
        """
        Flatten hierarchical sections into a flat list.

        Args:
            sections: Hierarchical sections

        Returns:
            Flattened list of sections
        """
        flat = []
        for section in sections:
            flat.append(section)
            if section.subsections:
                flat.extend(self.flatten_sections(section.subsections))
        return flat

    def get_section_by_title(
        self, sections: List[Section], title: str
    ) -> Optional[Section]:
        """
        Find section by title (case-insensitive).

        Args:
            sections: List of sections to search
            title: Section title to find

        Returns:
            Section if found, None otherwise
        """
        title_lower = title.lower()
        for section in sections:
            if section.title.lower() == title_lower:
                return section
            # Search recursively in subsections
            if section.subsections:
                found = self.get_section_by_title(section.subsections, title)
                if found:
                    return found
        return None
