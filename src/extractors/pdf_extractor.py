"""Main PDF Extractor - Unified interface for all extraction features."""

import os
from typing import Optional
from ..types.models import PDFExtractResult, PDFPage
from ..utils.logger import get_logger
from .text_extractor import TextExtractor
from .image_extractor import ImageExtractor
from .metadata_extractor import MetadataExtractor
from .table_extractor import TableExtractor
from .exceptions import FileNotFoundError, PDFExtractorError

logger = get_logger(__name__)


class PDFExtractor:
    """
    Unified PDF extraction interface.

    Combines text, image, metadata, and table extraction into a single interface.
    """

    def __init__(
        self,
        output_dir: str = "./temp_images",
        extract_images: bool = True,
        extract_tables: bool = True,
    ):
        """
        Initialize PDFExtractor.

        Args:
            output_dir: Directory to save extracted images
            extract_images: Whether to extract images (default: True)
            extract_tables: Whether to extract tables (default: True)
        """
        self.output_dir = output_dir
        self.extract_images_flag = extract_images
        self.extract_tables_flag = extract_tables

        self.text_extractor = TextExtractor()
        self.image_extractor = ImageExtractor(output_dir=output_dir)
        self.metadata_extractor = MetadataExtractor()
        self.table_extractor = TableExtractor()

        logger.info(
            f"PDFExtractor initialized (images={extract_images}, tables={extract_tables})"
        )

    def extract(self, pdf_path: str) -> PDFExtractResult:
        """
        Extract all content from PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            PDFExtractResult containing all extracted content

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            PDFExtractorError: If extraction fails
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        logger.info(f"Starting full PDF extraction: {pdf_path}")
        logger.info("=" * 80)

        try:
            # Extract metadata first
            logger.info("Step 1/4: Extracting metadata...")
            metadata = self.metadata_extractor.extract_metadata(pdf_path)
            logger.info(f"Metadata extracted: {metadata.total_pages} pages")

            # Extract text
            logger.info("Step 2/4: Extracting text...")
            all_texts = self.text_extractor.extract_text(pdf_path)
            logger.info(f"Text extracted: {len(all_texts)} text blocks")

            # Extract images (optional)
            all_images = []
            if self.extract_images_flag:
                logger.info("Step 3/4: Extracting images...")
                all_images = self.image_extractor.extract_images(pdf_path)
                logger.info(f"Images extracted: {len(all_images)} images")
            else:
                logger.info("Step 3/4: Skipping image extraction")

            # Extract tables (optional)
            all_tables = []
            if self.extract_tables_flag:
                logger.info("Step 4/4: Extracting tables...")
                all_tables = self.table_extractor.extract_tables(pdf_path)
                logger.info(f"Tables extracted: {len(all_tables)} tables")
            else:
                logger.info("Step 4/4: Skipping table extraction")

            # Organize by pages
            logger.info("Organizing content by pages...")
            pages = []
            for page_num in range(1, metadata.total_pages + 1):
                page_texts = [t for t in all_texts if t.page_number == page_num]
                page_images = [i for i in all_images if i.page_number == page_num]
                page_tables = [t for t in all_tables if t.page_number == page_num]

                page = PDFPage(
                    page_number=page_num,
                    text=page_texts,
                    images=page_images,
                    tables=page_tables,
                )
                pages.append(page)

            result = PDFExtractResult(metadata=metadata, pages=pages)

            logger.info("=" * 80)
            logger.info("PDF extraction completed successfully!")
            logger.info(f"Total pages: {len(pages)}")
            logger.info(f"Total text blocks: {len(all_texts)}")
            logger.info(f"Total images: {len(all_images)}")
            logger.info(f"Total tables: {len(all_tables)}")
            logger.info("=" * 80)

            return result

        except Exception as e:
            logger.error(f"Error during PDF extraction: {e}")
            raise PDFExtractorError(f"Failed to extract PDF: {str(e)}")

    def extract_page(self, pdf_path: str, page_number: int) -> PDFPage:
        """
        Extract content from a specific page.

        Args:
            pdf_path: Path to the PDF file
            page_number: Page number (1-indexed)

        Returns:
            PDFPage object containing page content

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            PDFExtractorError: If extraction fails
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        logger.info(f"Extracting content from page {page_number}: {pdf_path}")

        try:
            # Extract text from specific page
            all_texts = self.text_extractor.extract_text(pdf_path)
            page_texts = [t for t in all_texts if t.page_number == page_number]

            # Extract images from specific page
            page_images = []
            if self.extract_images_flag:
                all_images = self.image_extractor.extract_images(pdf_path)
                page_images = [i for i in all_images if i.page_number == page_number]

            # Extract tables from specific page
            page_tables = []
            if self.extract_tables_flag:
                page_tables = self.table_extractor.extract_tables_from_page(
                    pdf_path, page_number
                )

            page = PDFPage(
                page_number=page_number,
                text=page_texts,
                images=page_images,
                tables=page_tables,
            )

            logger.info(
                f"Page {page_number} extracted: "
                f"{len(page_texts)} texts, {len(page_images)} images, {len(page_tables)} tables"
            )

            return page

        except Exception as e:
            logger.error(f"Error extracting page {page_number}: {e}")
            raise PDFExtractorError(f"Failed to extract page {page_number}: {str(e)}")

    def extract_text_only(self, pdf_path: str) -> str:
        """
        Extract only plain text from PDF (fast mode).

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Plain text content

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            PDFExtractorError: If extraction fails
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        logger.info(f"Extracting plain text: {pdf_path}")

        try:
            text = self.text_extractor.extract_simple_text(pdf_path)
            logger.info(f"Extracted {len(text)} characters")
            return text

        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            raise PDFExtractorError(f"Failed to extract text: {str(e)}")

    def cleanup(self) -> None:
        """
        Clean up temporary files.

        Removes the temporary image directory and all extracted images.
        """
        logger.info("Cleaning up temporary files...")
        self.image_extractor.cleanup()

    def get_metadata(self, pdf_path: str):
        """
        Get only metadata from PDF (fast mode).

        Args:
            pdf_path: Path to the PDF file

        Returns:
            PDFMetadata object

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            PDFExtractorError: If extraction fails
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        logger.info(f"Extracting metadata: {pdf_path}")

        try:
            metadata = self.metadata_extractor.extract_metadata(pdf_path)
            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            raise PDFExtractorError(f"Failed to extract metadata: {str(e)}")
