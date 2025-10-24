"""LLM-based section segmentation using Claude API."""

import json
from typing import List, Optional
from anthropic import Anthropic
from ..types.models import PDFExtractResult, PDFPage, Section, PageRange
from .exceptions import SegmentationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LLMSectionSegmenter:
    """Segments document into sections using LLM for better accuracy."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ):
        """
        Initialize LLM section segmenter.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            max_tokens: Maximum tokens for response
            temperature: Temperature for generation (0.0 for deterministic)
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = None

        if api_key:
            self.client = Anthropic(api_key=api_key)

    def segment(self, pdf_result: PDFExtractResult) -> List[Section]:
        """
        Segment PDF content into hierarchical sections using LLM.

        Args:
            pdf_result: Extracted PDF content

        Returns:
            List of top-level sections with nested subsections

        Raises:
            SegmentationError: If segmentation fails
        """
        try:
            logger.info("Starting LLM-based section segmentation")

            if not self.client:
                raise SegmentationError("API key not provided for LLM segmentation")

            # Extract all text from pages
            full_text = self._extract_full_text(pdf_result.pages)

            if not full_text.strip():
                logger.warning("No text found for segmentation")
                return []

            # Build prompt
            prompt = self._build_segmentation_prompt(full_text)

            # Call LLM
            logger.info("Calling Claude API for section segmentation...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response
            response_text = response.content[0].text
            sections = self._parse_sections_response(response_text, pdf_result.pages)

            logger.info(f"LLM identified {len(sections)} top-level sections")
            logger.info(
                f"Token usage: {response.usage.input_tokens} input, "
                f"{response.usage.output_tokens} output"
            )

            return sections

        except Exception as e:
            logger.error(f"LLM section segmentation failed: {e}")
            raise SegmentationError(f"Failed to segment sections with LLM: {e}") from e

    def _extract_full_text(self, pages: List[PDFPage]) -> str:
        """
        Extract all text from pages with page markers.

        Args:
            pages: List of PDF pages

        Returns:
            Full text with page markers
        """
        full_text = []
        for page in pages:
            page_text = []
            for text_block in page.text:
                if text_block.text.strip():
                    page_text.append(text_block.text.strip())

            if page_text:
                full_text.append(f"[Page {page.page_number}]")
                full_text.append("\n".join(page_text))

        return "\n\n".join(full_text)

    def _build_segmentation_prompt(self, full_text: str) -> str:
        """
        Build prompt for section segmentation.

        Args:
            full_text: Full document text

        Returns:
            Prompt string
        """
        # Truncate if too long (max ~30k chars)
        if len(full_text) > 30000:
            logger.warning(f"Text too long ({len(full_text)} chars), truncating to 30000")
            full_text = full_text[:30000] + "\n\n[... truncated ...]"

        prompt = f"""You are an expert document analyzer. Your task is to identify and segment a document into logical sections with hierarchical structure.

Given the following document text, please:
1. Identify all section headings (titles)
2. Determine the hierarchical level of each section (1 = top-level, 2 = subsection, etc.)
3. Extract the content for each section
4. Note the page range where each section appears

Document text:
---
{full_text}
---

Please respond with a JSON array of sections in this exact format:
{{
  "sections": [
    {{
      "title": "Section title here",
      "level": 1,
      "content": "Section content here...",
      "page_start": 1,
      "page_end": 3,
      "subsections": [
        {{
          "title": "Subsection title",
          "level": 2,
          "content": "Subsection content...",
          "page_start": 2,
          "page_end": 2,
          "subsections": []
        }}
      ]
    }}
  ]
}}

Rules:
- Only include actual sections with meaningful content
- Level 1 = main sections, Level 2 = subsections, Level 3 = sub-subsections
- Extract page numbers from [Page X] markers
- Keep content concise but complete (max 500 chars per section)
- Maintain hierarchical structure in subsections array
- Return valid JSON only, no additional text"""

        return prompt

    def _parse_sections_response(
        self, response_text: str, pages: List[PDFPage]
    ) -> List[Section]:
        """
        Parse LLM response into Section objects.

        Args:
            response_text: LLM response text
            pages: PDF pages for validation

        Returns:
            List of Section objects
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_text = response_text.strip()
            if json_text.startswith("```"):
                # Remove markdown code block
                lines = json_text.split("\n")
                json_text = "\n".join(lines[1:-1]) if len(lines) > 2 else json_text

            # Parse JSON
            data = json.loads(json_text)

            if "sections" not in data:
                raise ValueError("Response does not contain 'sections' field")

            # Convert to Section objects
            sections = []
            for section_data in data["sections"]:
                section = self._create_section_from_dict(section_data, pages)
                sections.append(section)

            return sections

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            raise SegmentationError(f"Invalid JSON response from LLM: {e}")
        except Exception as e:
            logger.error(f"Failed to parse sections: {e}")
            raise SegmentationError(f"Failed to parse LLM response: {e}")

    def _create_section_from_dict(
        self, data: dict, pages: List[PDFPage]
    ) -> Section:
        """
        Create Section object from dictionary.

        Args:
            data: Section data dictionary
            pages: PDF pages for validation

        Returns:
            Section object
        """
        # Extract fields
        title = data.get("title", "Untitled")
        level = data.get("level", 1)
        content = data.get("content", "")
        page_start = data.get("page_start", 1)
        page_end = data.get("page_end", 1)

        # Validate page range
        total_pages = len(pages)
        page_start = max(1, min(page_start, total_pages))
        page_end = max(page_start, min(page_end, total_pages))

        # Parse subsections recursively
        subsections = []
        for subsection_data in data.get("subsections", []):
            subsection = self._create_section_from_dict(subsection_data, pages)
            subsections.append(subsection)

        return Section(
            title=title,
            level=level,
            content=content,
            page_range=PageRange(start=page_start, end=page_end),
            subsections=subsections,
        )

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
