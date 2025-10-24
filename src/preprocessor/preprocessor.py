"""Main preprocessor interface integrating all preprocessing steps."""

import time
from typing import Dict, List, Optional
from ..types.models import PDFExtractResult, PreprocessResult, FunctionalGroup
from .text_normalizer import TextNormalizer
from .header_footer_remover import HeaderFooterRemover
from .section_segmenter import SectionSegmenter
from .functional_grouper import FunctionalGrouper
from .llm_section_segmenter import LLMSectionSegmenter
from .llm_functional_grouper import LLMFunctionalGrouper
from .exceptions import PreprocessorError, InvalidContentError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Preprocessor:
    """Main preprocessor for PDF content normalization and structuring."""

    def __init__(
        self,
        normalize_text: bool = True,
        remove_headers_footers: bool = True,
        segment_sections: bool = True,
        group_by_function: bool = True,
        custom_keywords: Optional[Dict[str, List[str]]] = None,
        use_llm: bool = False,
        llm_api_key: Optional[str] = None,
        llm_model: str = "claude-3-5-sonnet-20241022",
    ):
        """
        Initialize preprocessor with configurable options.

        Args:
            normalize_text: Enable text normalization
            remove_headers_footers: Enable header/footer removal
            segment_sections: Enable section segmentation
            group_by_function: Enable functional grouping
            custom_keywords: Custom keyword mapping for functional grouping
            use_llm: Use LLM-based segmentation and grouping (more accurate but slower/costlier)
            llm_api_key: Anthropic API key (required if use_llm=True)
            llm_model: Claude model to use for LLM-based processing
        """
        self.normalize_text = normalize_text
        self.remove_headers_footers = remove_headers_footers
        self.segment_sections = segment_sections
        self.group_by_function = group_by_function
        self.use_llm = use_llm

        # Initialize rule-based components
        self.text_normalizer = TextNormalizer()
        self.header_footer_remover = HeaderFooterRemover()
        self.section_segmenter = SectionSegmenter()
        self.functional_grouper = FunctionalGrouper(custom_keywords=custom_keywords)

        # Initialize LLM-based components (if enabled)
        self.llm_section_segmenter = None
        self.llm_functional_grouper = None

        if use_llm:
            if not llm_api_key:
                logger.warning("LLM enabled but no API key provided. Falling back to rule-based.")
                self.use_llm = False
            else:
                logger.info("Initializing LLM-based preprocessor components")
                self.llm_section_segmenter = LLMSectionSegmenter(
                    api_key=llm_api_key,
                    model=llm_model,
                )
                self.llm_functional_grouper = LLMFunctionalGrouper(
                    api_key=llm_api_key,
                    model=llm_model,
                )

        # Statistics
        self.stats = {
            "normalization_time": 0.0,
            "header_footer_removal_time": 0.0,
            "segmentation_time": 0.0,
            "grouping_time": 0.0,
            "total_time": 0.0,
            "llm_tokens_used": 0,
        }

    def process(self, pdf_result: PDFExtractResult) -> PreprocessResult:
        """
        Process PDF extraction result through all preprocessing steps.

        Args:
            pdf_result: Extracted PDF content

        Returns:
            Preprocessed result with functional groups

        Raises:
            PreprocessorError: If preprocessing fails
            InvalidContentError: If input content is invalid
        """
        try:
            start_time = time.time()
            logger.info("Starting preprocessing pipeline")

            # Validate input
            self._validate_input(pdf_result)

            # Step 1: Normalize text
            if self.normalize_text:
                logger.info("Step 1: Text normalization")
                norm_start = time.time()
                pdf_result = self._normalize_all_text(pdf_result)
                self.stats["normalization_time"] = time.time() - norm_start
                logger.info(
                    f"Text normalization completed in {self.stats['normalization_time']:.2f}s"
                )

            # Step 2: Remove headers and footers
            header_patterns = []
            footer_patterns = []
            if self.remove_headers_footers:
                logger.info("Step 2: Header/footer removal")
                hf_start = time.time()
                pdf_result, header_patterns, footer_patterns = (
                    self.header_footer_remover.remove_headers_footers(pdf_result)
                )
                self.stats["header_footer_removal_time"] = time.time() - hf_start
                logger.info(
                    f"Header/footer removal completed in {self.stats['header_footer_removal_time']:.2f}s"
                )
                logger.info(
                    f"Removed {len(header_patterns)} header patterns and {len(footer_patterns)} footer patterns"
                )

            # Step 3: Segment into sections
            sections = []
            if self.segment_sections:
                if self.use_llm and self.llm_section_segmenter:
                    logger.info("Step 3: Section segmentation (LLM-based)")
                    seg_start = time.time()
                    sections = self.llm_section_segmenter.segment(pdf_result)
                    self.stats["segmentation_time"] = time.time() - seg_start
                    logger.info(
                        f"LLM section segmentation completed in {self.stats['segmentation_time']:.2f}s"
                    )
                else:
                    logger.info("Step 3: Section segmentation (rule-based)")
                    seg_start = time.time()
                    sections = self.section_segmenter.segment(pdf_result)
                    self.stats["segmentation_time"] = time.time() - seg_start
                    logger.info(
                        f"Rule-based section segmentation completed in {self.stats['segmentation_time']:.2f}s"
                    )
                logger.info(f"Identified {len(sections)} top-level sections")

            # Step 4: Group by functional categories
            functional_groups = []
            if self.group_by_function and sections:
                if self.use_llm and self.llm_functional_grouper:
                    logger.info("Step 4: Functional grouping (LLM-based)")
                    group_start = time.time()
                    functional_groups = self.llm_functional_grouper.group_sections(sections)
                    self.stats["grouping_time"] = time.time() - group_start
                    logger.info(
                        f"LLM functional grouping completed in {self.stats['grouping_time']:.2f}s"
                    )
                else:
                    logger.info("Step 4: Functional grouping (rule-based)")
                    group_start = time.time()
                    functional_groups = self.functional_grouper.group_sections(sections)
                    self.stats["grouping_time"] = time.time() - group_start
                    logger.info(
                        f"Rule-based functional grouping completed in {self.stats['grouping_time']:.2f}s"
                    )
                logger.info(f"Created {len(functional_groups)} functional groups")
            elif sections:
                # No grouping, create a single default group
                from ..types.models import FunctionalGroup

                functional_groups = [
                    FunctionalGroup(
                        name="전체",
                        sections=sections,
                        keywords=[],
                    )
                ]

            # Calculate total time
            self.stats["total_time"] = time.time() - start_time

            # Log statistics
            self._log_statistics(functional_groups)

            # Validate result
            self._validate_result(functional_groups)

            # Create result
            result = PreprocessResult(
                functional_groups=functional_groups,
                metadata=pdf_result.metadata,
                removed_header_patterns=header_patterns,
                removed_footer_patterns=footer_patterns,
            )

            logger.info(
                f"Preprocessing completed successfully in {self.stats['total_time']:.2f}s"
            )
            return result

        except InvalidContentError:
            raise
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            raise PreprocessorError(f"Failed to preprocess PDF content: {e}") from e

    def _validate_input(self, pdf_result: PDFExtractResult) -> None:
        """
        Validate input PDF extraction result.

        Args:
            pdf_result: PDF extraction result to validate

        Raises:
            InvalidContentError: If input is invalid
        """
        if not pdf_result:
            raise InvalidContentError("PDF extraction result is None")

        if not pdf_result.pages:
            raise InvalidContentError("PDF extraction result has no pages")

        # Check if there's any text content
        has_text = any(page.text for page in pdf_result.pages)
        if not has_text:
            logger.warning("PDF extraction result has no text content")

    def _normalize_all_text(self, pdf_result: PDFExtractResult) -> PDFExtractResult:
        """
        Normalize text in all pages.

        Args:
            pdf_result: PDF extraction result

        Returns:
            PDF result with normalized text
        """
        from ..types.models import PDFPage, ExtractedText

        normalized_pages = []
        for page in pdf_result.pages:
            normalized_text_blocks = []
            for text_block in page.text:
                normalized_text = self.text_normalizer.normalize(text_block.text)
                normalized_block = ExtractedText(
                    page_number=text_block.page_number,
                    text=normalized_text,
                    metadata=text_block.metadata,
                )
                normalized_text_blocks.append(normalized_block)

            normalized_page = PDFPage(
                page_number=page.page_number,
                text=normalized_text_blocks,
                images=page.images,
                tables=page.tables,
            )
            normalized_pages.append(normalized_page)

        return PDFExtractResult(
            metadata=pdf_result.metadata, pages=normalized_pages
        )

    def _validate_result(self, functional_groups: List[FunctionalGroup]) -> None:
        """
        Validate preprocessing result.

        Args:
            functional_groups: List of functional groups to validate

        Raises:
            InvalidContentError: If result is invalid
        """
        if not functional_groups:
            logger.warning("No functional groups created")
            return

        # Check each group
        for group in functional_groups:
            if not group.sections:
                logger.warning(f"Functional group '{group.name}' has no sections")

            # Check section titles are not empty
            for section in group.sections:
                if not section.title.strip():
                    logger.warning(
                        f"Section in group '{group.name}' has empty title"
                    )

                # Check content length (warn if too long or too short)
                if len(section.content) > 100000:
                    logger.warning(
                        f"Section '{section.title}' has very long content ({len(section.content)} chars)"
                    )
                elif len(section.content) < 10:
                    logger.warning(
                        f"Section '{section.title}' has very short content ({len(section.content)} chars)"
                    )

    def _log_statistics(self, functional_groups: List[FunctionalGroup]) -> None:
        """
        Log preprocessing statistics.

        Args:
            functional_groups: List of functional groups
        """
        logger.info("=== Preprocessing Statistics ===")
        logger.info(f"Normalization time: {self.stats['normalization_time']:.2f}s")
        logger.info(
            f"Header/footer removal time: {self.stats['header_footer_removal_time']:.2f}s"
        )
        logger.info(f"Segmentation time: {self.stats['segmentation_time']:.2f}s")
        logger.info(f"Grouping time: {self.stats['grouping_time']:.2f}s")
        logger.info(f"Total time: {self.stats['total_time']:.2f}s")
        logger.info(f"Functional groups: {len(functional_groups)}")

        total_sections = sum(len(group.sections) for group in functional_groups)
        logger.info(f"Total sections: {total_sections}")

        for group in functional_groups:
            logger.info(
                f"  - {group.name}: {len(group.sections)} sections"
            )

    def get_statistics(self) -> Dict[str, float]:
        """
        Get preprocessing statistics.

        Returns:
            Dictionary of statistics
        """
        return self.stats.copy()

    def reset_statistics(self) -> None:
        """Reset preprocessing statistics."""
        self.stats = {
            "normalization_time": 0.0,
            "header_footer_removal_time": 0.0,
            "segmentation_time": 0.0,
            "grouping_time": 0.0,
            "total_time": 0.0,
        }
